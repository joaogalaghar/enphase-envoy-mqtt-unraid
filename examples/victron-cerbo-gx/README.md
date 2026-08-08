# Victron Cerbo GX / Venus OS Integration

This example shows how to use the MQTT data published by **Enphase Envoy MQTT**
to create virtual **Grid Meter** and **PV Inverter** devices on a Victron Cerbo
GX running Venus OS.

The Node-RED flow included in this directory was tested with:

- **Victron MultiPlus-II 48V - 5000VA - 70A**
- **Victron Energy Cerbo GX MK2 Controller**
- **Enphase Envoy-S Metered**
- **Enphase Envoy firmware D8**
- **Unraid**
- **Node-RED running on the Cerbo GX**
- `@victronenergy/node-red-contrib-victron` version `1.6.64`

> This integration is optional. The main Enphase Envoy MQTT container works with
> any MQTT broker and does not require Victron hardware.

---

## Architecture

The tested setup is:

```text
Enphase Envoy-S Metered
        │
        │ HTTPS
        ▼
Unraid
Enphase Envoy MQTT container
        │
        │ MQTT to the Cerbo GX LAN IP / hostname
        │ port 1883
        ▼
Cerbo GX MQTT broker
        │
        │ local Node-RED connection
        │ 127.0.0.1:1883
        ▼
Node-RED on Cerbo GX
        │
        ├──► Virtual Grid Meter
        │
        └──► Virtual PV Inverter
                 │
                 ▼
              Venus OS
```

The Unraid container publishes the raw Enphase meter data to:

```text
envoy/json
```

Node-RED subscribes to the same topic and converts the relevant Enphase
measurements into Victron virtual devices.

### Important: LAN IP vs `127.0.0.1`

There are two different MQTT connections in this setup:

1. **Unraid → Cerbo GX**  
   Configure `MQTT_HOST` in the Unraid container with the **Cerbo GX LAN IP
   address or hostname**. Do **not** use `127.0.0.1` in the Unraid container.

2. **Node-RED on Cerbo GX → local Cerbo GX MQTT broker**  
   The included Node-RED flow uses `127.0.0.1:1883`, because Node-RED and the
   MQTT broker are running on the same Cerbo GX.

Example:

```text
Unraid container MQTT_HOST = 192.168.1.50
Node-RED broker             = 127.0.0.1
MQTT port                   = 1883
MQTT topic                  = envoy/json
```

---

## Files

```text
examples/victron-cerbo-gx/
├── README.md
└── node-red-flow.json
```

`node-red-flow.json` contains the complete Node-RED flow for Grid + PV.

---

## Requirements

Before importing the flow, make sure you have:

- a working **Enphase Envoy MQTT** container;
- `envoy/json` being published to the Cerbo GX MQTT broker;
- Node-RED running on the Cerbo GX;
- MQTT enabled on the Cerbo GX;
- `@victronenergy/node-red-contrib-victron` installed.

The tested flow uses:

```text
@victronenergy/node-red-contrib-victron 1.6.64
```

---

## MQTT Broker

When Node-RED is running directly on the Cerbo GX, the included flow uses:

```text
Host: 127.0.0.1
Port: 1883
Topic: envoy/json
```

Using `127.0.0.1` for the Node-RED MQTT connection avoids depending on the Cerbo
GX LAN address.

If Node-RED is running on another device, replace `127.0.0.1` with the LAN IP
address or hostname of the Cerbo GX.

---

## Importing the Flow

In Node-RED on the Cerbo GX:

1. Open the Node-RED editor.
2. Select **Menu → Import**.
3. Import `node-red-flow.json`.
4. Confirm that the MQTT broker configuration is correct.
5. Click **Deploy**.

The flow should immediately start receiving `envoy/json` messages.

---

## Enphase Meter IDs

The flow expects the meter IDs observed on the tested Envoy-S Metered
installation:

```text
704643328 = Production / PV
704643584 = Net Consumption / Grid
```

The flow searches the incoming JSON array for these EIDs.

Different Envoy models or meter configurations may expose different IDs. If the
flow reports a missing EID, inspect the raw `envoy/json` payload and adjust the
Function node as required.

---

## Grid Power Direction

The Grid Meter preserves the sign reported by the Enphase net-consumption meter:

```text
Positive power = importing from the grid
Negative power = exporting to the grid
```

No sign inversion is performed by the Node-RED flow.

Example:

```text
+850 W  = importing 850 W from the grid
-1200 W = exporting 1200 W to the grid
```

If import and export appear reversed on your installation, verify the Enphase CT
orientation and meter configuration before changing the flow.

---

## PV Power

PV production is read from the Enphase production meter.

Small negative values that may be reported by the production CT at night are
clamped to:

```text
0 W
```

The virtual PV Inverter exposes, when available:

```text
/Ac/Power
/Ac/L1/Power
/Ac/L1/Voltage
/Ac/L1/Current
/Ac/Energy/Forward
/Ac/L1/Energy/Forward
/StatusCode
/ErrorCode
/Connected
```

---

## Grid Meter

The virtual Grid Meter exposes, when available:

```text
/Ac/Power
/Ac/L1/Power
/Ac/L1/Voltage
/Ac/L1/Current
/Ac/Frequency
/Ac/Energy/Forward
/Ac/L1/Energy/Forward
/Ac/Energy/Reverse
/Ac/L1/Energy/Reverse
/Connected
/ErrorCode
```

---

## Watchdog

The flow includes a 15-second watchdog.

If valid `envoy/json` messages stop arriving, the virtual devices are marked
offline and their power is set to `0 W`.

This prevents stale values from remaining visible in Venus OS if the MQTT stream
stops.

---

## Status Display

When the flow is receiving valid data, the conversion Function node shows a
status similar to:

```text
250 W grid · 2480 W PV · Cerbo MQTT
```

If the expected Enphase meter IDs are not found, the Function node reports the
missing meter.

---

## Troubleshooting

### No MQTT data in Node-RED

Confirm that:

- the Enphase Envoy MQTT container is running;
- its `MQTT_HOST` points to the Cerbo GX **LAN IP address or hostname**;
- its MQTT port is `1883` unless you changed it;
- its MQTT topic is `envoy/json`;
- the Cerbo GX MQTT broker is enabled;
- Node-RED is connected to `127.0.0.1:1883` when running directly on the Cerbo GX.

### Flow reports a missing EID

The example expects:

```text
704643328 = PV
704643584 = Grid
```

Inspect the raw `envoy/json` payload and adjust the EIDs in the Function node if
your Envoy uses different meter IDs.

### Grid import/export appears reversed

The example preserves the sign reported by the Enphase net-consumption meter.
Check CT orientation and the Enphase meter configuration first. If your setup is
intentionally reversed, adapt the `gridPower` handling in the Function node.

### PV works but Grid does not

Make sure the Envoy has a configured and working **consumption / net-consumption
meter**.

The PV virtual device can work from the production meter alone, while the Grid
Meter requires net-consumption data.

### Virtual devices do not appear in Venus OS

Confirm that:

- `@victronenergy/node-red-contrib-victron` is installed;
- the flow has been deployed;
- the `victron-virtual` nodes are enabled;
- Node-RED is running correctly on the Cerbo GX.

---

## Single-Phase Example

This example was created and tested on a single-phase installation.

The virtual devices are configured as:

```text
Grid Meter:  1 phase
PV Inverter: 1 phase
```

Multi-phase installations require changes to the virtual-device configuration
and phase mapping.

---

## Tested Hardware

The flow has been tested with:

- **Victron MultiPlus-II 48V - 5000VA - 70A**
- **Victron Energy Cerbo GX MK2 Controller**
- **Enphase Envoy-S Metered**
- **Enphase firmware D8**

The Node-RED flow uses the Cerbo GX local MQTT broker at:

```text
127.0.0.1:1883
```

and receives Enphase data from:

```text
envoy/json
```

---

## Disclaimer

This is a community integration and is not affiliated with or endorsed by
Enphase Energy or Victron Energy.

Always verify meter direction, power values, and system behaviour before relying
on virtual meter data for control or automation.
