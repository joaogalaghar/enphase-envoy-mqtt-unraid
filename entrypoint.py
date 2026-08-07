#!/usr/bin/env python3

import json
import os
import re
import signal
import subprocess
import sys
from pathlib import Path


WRAPPER_VERSION = os.getenv("WRAPPER_VERSION", "dev")

DATA_DIR = Path("/app/data")
OPTIONS_FILE = DATA_DIR / "options.json"
TOKEN_FILE = DATA_DIR / "token.txt"


def fail(message):
    print(f"[wrapper] ERROR: {message}", flush=True)
    sys.exit(1)


def required(name):
    value = os.getenv(name, "").strip()

    if not value:
        fail(f"required variable {name} is empty")

    return value


def env_bool(name, default=False):
    value = os.getenv(name)

    if value is None or value == "":
        return default

    value = value.strip().lower()

    if value in ("1", "true", "yes", "on"):
        return True

    if value in ("0", "false", "no", "off"):
        return False

    fail(
        f"{name} must be one of "
        f"true/false, yes/no, on/off or 1/0"
    )


def redact(line):
    """
    Prevent credentials and Enphase authentication tokens
    from being exposed in container logs.
    """

    secrets = [
        os.getenv("MQTT_PASSWORD", ""),
        os.getenv("ENVOY_USER_PASS", ""),
    ]

    if TOKEN_FILE.exists():
        try:
            token = TOKEN_FILE.read_text().strip()

            if token:
                secrets.append(token)
        except OSError:
            pass

    for secret in secrets:
        if secret:
            line = line.replace(secret, "[REDACTED]")

    # Enphase tokens are JWTs.
    line = re.sub(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
        "[REDACTED_JWT]",
        line,
    )

    # Python dict representation used by the upstream error messages.
    line = re.sub(
        r"('user\[password\]'\s*:\s*)'[^']*'",
        r"\1'[REDACTED]'",
        line,
    )

    line = re.sub(
        r"('session_id'\s*:\s*)'[^']*'",
        r"\1'[REDACTED]'",
        line,
    )

    # JSON representation, if upstream debug output changes format.
    line = re.sub(
        r'("session_id"\s*:\s*)"[^"]*"',
        r'\1"[REDACTED]"',
        line,
    )

    # Explicit upstream token log messages.
    if "Token generated" in line:
        line = re.sub(
            r"(Token generated).*",
            r"\1 [REDACTED]",
            line,
        )

    if "Token response" in line:
        line = re.sub(
            r"(Token response).*",
            r"\1 [REDACTED]",
            line,
        )

    if "Read token from file" in line:
        line = re.sub(
            r"(Read token from file.*?:\s*).*$",
            r"\1[REDACTED]",
            line,
        )

    return line


DATA_DIR.mkdir(parents=True, exist_ok=True)

config = {
    "MQTT_HOST": required("MQTT_HOST"),
    "MQTT_USER": os.getenv("MQTT_USER", ""),
    "MQTT_PASSWORD": os.getenv("MQTT_PASSWORD", ""),
    "MQTT_PORT": os.getenv("MQTT_PORT", "1883"),
    "MQTT_TOPIC": os.getenv("MQTT_TOPIC", "envoy/json"),

    "ENVOY_HOST": required("ENVOY_HOST"),

    # Required by D7/D8 firmware, but may be left blank
    # for older firmware supported by the upstream project.
    "ENVOY_USER": os.getenv("ENVOY_USER", ""),
    "ENVOY_USER_PASS": os.getenv("ENVOY_USER_PASS", ""),

    "ENVOY_USE_HTTPS": env_bool("ENVOY_USE_HTTPS", True),
    "USE_FREEDS": env_bool("USE_FREEDS", False),
    "BATTERY_INSTALLED": env_bool("BATTERY_INSTALLED", False),
    "DEBUG": env_bool("DEBUG", False),
}

temporary_file = DATA_DIR / "options.json.tmp"

try:
    with open(temporary_file, "w") as file:
        json.dump(config, file, indent=2)

    os.chmod(temporary_file, 0o600)
    os.replace(temporary_file, OPTIONS_FILE)

except OSError as exc:
    fail(f"could not write {OPTIONS_FILE}: {exc}")


token_exists = TOKEN_FILE.exists() and TOKEN_FILE.stat().st_size > 0

protocol = "https" if config["ENVOY_USE_HTTPS"] else "http"

print(
    f"[wrapper] Enphase Envoy MQTT for Unraid {WRAPPER_VERSION}",
    flush=True,
)
print(
    f"[wrapper] Configuration written to {OPTIONS_FILE}",
    flush=True,
)
print(
    f"[wrapper] MQTT: {config['MQTT_HOST']}:{config['MQTT_PORT']} "
    f"topic={config['MQTT_TOPIC']}",
    flush=True,
)
print(
    f"[wrapper] Envoy: {protocol}://{config['ENVOY_HOST']}",
    flush=True,
)
print(
    f"[wrapper] Existing Enphase token: "
    f"{'yes' if token_exists else 'no'}",
    flush=True,
)


process = subprocess.Popen(
    ["python3", "/app/envoy_to_mqtt_json.py"],
    cwd="/app",
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
)


def forward_signal(signum, frame):
    if process.poll() is None:
        process.send_signal(signum)


signal.signal(signal.SIGTERM, forward_signal)
signal.signal(signal.SIGINT, forward_signal)


try:
    if process.stdout:
        for line in process.stdout:
            print(redact(line.rstrip("\n")), flush=True)

finally:
    return_code = process.wait()


sys.exit(return_code)
