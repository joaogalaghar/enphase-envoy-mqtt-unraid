# Victron Cerbo GX / Venus OS Integration

This example shows how to use the MQTT data published by **Enphase Envoy MQTT** to create virtual **Grid Meter** and **PV Inverter** devices on a Victron Cerbo GX running Venus OS.

The Node-RED flow included in this directory was tested with:

- **Victron MultiPlus-II 48V - 5000VA - 70A**
- **Victron Energy Cerbo GX MK2 Controller**
- **Enphase Envoy-S Metered**
- **Enphase Envoy firmware D8**
- **Unraid**
- **Node-RED on the Cerbo GX**
- `@victronenergy/node-red-contrib-victron` version `1.6.64`

> This integration is optional.  
> The main Enphase Envoy MQTT container works with any MQTT broker and does not require Victron hardware.

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
        │ MQTT
        ▼
Cerbo GX MQTT broker
127.0.0.1:1883
        │
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

Node-RED subscribes to that topic and converts the relevant Enphase measurements into Victron virtual devices.

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

When Node-RED is running directly on the Cerbo GX, use:

```text
Host: 127.0.0.1
Port: 1883
Topic: envoy/json
```

Using `127.0.0.1` is recommended because Node-RED and the MQTT broker are running on the same Cerbo GX.

This avoids depending on the Cerbo GX LAN IP address.

If Node-RED is running on another device, replace:

```text
127.0.0.1
```

with the IP address or hostname of the Cerbo GX.

For example:

```text
192.168.1.50
```

---

## Importing the Flow

In Node-RED on the Cerbo GX:

1. Open the Node-RED editor.
2. Select **Menu → Import**.
3. Import:

```text
node-red-flow.json
```

4. Confirm that the MQTT broker is configured correctly.
5. Click **Deploy**.

The flow should immediately start receiving `envoy/json`.

---

## Enphase Meter IDs

The flow expects the standard Enphase meter IDs used by the tested Envoy-S Metered installation:

```text
704643328 = Production / PV
704643584 = Net Consumption / Grid
```

The flow searches the incoming JSON array for these EIDs.

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

---

## PV Power

PV production is taken from the Enphase production meter.

Small negative values that may appear from the production CT at night are clamped to:

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

The flow includes a watchdog.

If no valid `envoy/json` message is received for 15 seconds, the virtual devices are marked offline and their power is set to `0 W`.

This prevents stale values from remaining visible in Venus OS if the MQTT stream stops.

---

## Status Display

When the flow is receiving valid data, the conversion Function node shows a status similar to:

```text
250 W grid · 2480 W PV · Cerbo MQTT
```

If the expected Enphase meter IDs are not found, the node reports which meter is missing.

---

## Troubleshooting

### No MQTT data

Confirm that the Cerbo GX broker is receiving the topic:

```text
envoy/json
```

If Node-RED is running on the Cerbo GX, the broker should normally be:

```text
127.0.0.1:1883
```

Also confirm that the Enphase Envoy MQTT container is configured to publish to the Cerbo GX.

---

### Flow reports a missing EID

The example expects:

```text
704643328 = PV
704643584 = Grid
```

Different Envoy models or meter configurations may expose different EIDs.

Inspect the raw `envoy/json` payload and adjust the EIDs in the Function node if necessary.

---

### Grid import/export appears reversed

The example preserves the sign reported by the Enphase net-consumption meter.

If your CT orientation or Envoy configuration reports the opposite sign, you may need to invert `gridPower` in the Function node.

---

### PV works but Grid does not

Make sure the Envoy has a configured and working **consumption / net-consumption meter**.

The PV virtual device can work from the production meter alone, but the Grid Meter requires the Enphase net-consumption data.

---

### Virtual devices do not appear in Venus OS

Confirm that:

- `@victronenergy/node-red-contrib-victron` is installed;
- the flow has been deployed;
- the `victron-virtual` nodes are enabled;
- Node-RED is running on the Cerbo GX.

---

## Notes

This example was created for a single-phase installation.

The virtual devices are configured as:

```text
Grid Meter: 1 phase
PV Inverter: 1 phase
```

Multi-phase installations may require adjustments to the virtual device configuration and phase mapping.

---

## Tested Hardware

The flow has been tested with:

- **Victron MultiPlus-II 48V - 5000VA - 70A**
- **Victron Energy Cerbo GX MK2 Controller**
- **Enphase Envoy-S Metered**

The tested setup uses the Cerbo GX local MQTT broker:

```text
127.0.0.1:1883
```

and receives Enphase data from:

```text
envoy/json
```

---

## Disclaimer

This is a community integration and is not affiliated with or endorsed by Enphase Energy or Victron Energy.

Always verify meter direction, power values, and system behaviour before relying on virtual meter data for control or automation.
