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
