FROM ghcr.io/vk2him/enphase-envoy-mqtt-json:latest

LABEL org.opencontainers.image.title="Enphase Envoy MQTT for Unraid"
LABEL org.opencontainers.image.description="Unraid wrapper for vk2him/Enphase-Envoy-mqtt-json"
LABEL org.opencontainers.image.source="https://github.com/joaogalaghar/enphase-envoy-mqtt-unraid"
LABEL org.opencontainers.image.licenses="MIT"

COPY entrypoint.py /usr/local/bin/enphase-envoy-unraid.py

RUN chmod 755 /usr/local/bin/enphase-envoy-unraid.py

CMD ["python3", "/usr/local/bin/enphase-envoy-unraid.py"]
