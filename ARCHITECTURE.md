# Public architecture

Belgee X50 HA Integration will be the Home Assistant-native owner of:

- setup and device discovery;
- vehicle, Gateway, Navigation and Relay entities;
- telemetry availability;
- automation actions;
- user-visible diagnostics;
- the supported interface to Belgee X50 Control Center.

```text
X50 Relay
    ↓
Belgee X50 HA Integration
    ├─ Home Assistant devices and entities
    ├─ automation actions
    └─ Belgee X50 Control Center
```

Large route, trip and diagnostic datasets will not be stored as ordinary Home
Assistant entity attributes. They belong to
[Control Center](https://github.com/AlteroAscension/belgee-x50-control-center),
while HA receives compact state suitable for dashboards, history and
automations.

MapKit capture and FakeGPS remain responsibilities of X50 Navigation. Vehicle
telemetry remains a responsibility of Gateway and Relay.

Security-sensitive implementation details are intentionally excluded from the
public pre-release architecture.

## Implemented preview boundary

The `0.1.0` preview implements the first read-only vertical slice:

```text
Relay POST + Bearer token
    → v1/v2 normalization
    → compact push coordinator
    ├─ HA devices/entities
    ├─ belgee_x50_telemetry event
    └─ belgee_x50_route_snapshot event (heavy payload, once supplied)
```

No browser or Control Center code receives Relay credentials. No command
entity or service is registered. The current YAML package may remain active
while values are compared.
