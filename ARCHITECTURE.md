# Public architecture

Belgee X50 HA Integration will be the Home Assistant-native owner of:

- setup and device discovery;
- vehicle, Gateway, Navigation and Relay entities;
- telemetry availability;
- automation actions;
- user-visible diagnostics;
- the supported interface to Belgee X50 Control Center.

```text
X50 Relay ─── outbound authenticated push ──┐
                                            ├─
X50 Gateway ─ outbound authenticated push ──┘
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

## Transport selection

The config entry owns a runtime-selectable transport:

- `relay` accepts only authenticated webhook updates;
- `gateway_push` accepts only Gateway's outbound authenticated updates;
- `auto` accepts both device tokens, prefers Relay while it is fresh, and
  falls back to the latest Gateway push;
- `gateway_poll` retains explicitly selected local/AVD diagnostics.

Changing transport reloads the config entry; it does not require reinstalling
the integration. Relay may therefore be paired after an initial Gateway-only
deployment. Normal Gateway push needs no HA-to-Gateway route. Relay and Gateway
have separate tokens, allowing either one to be rotated or removed safely.

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

## Relay pairing

```text
authenticated HA Config/Options Flow
    → opens five-minute one-time code
Relay + code + per-attempt nonce
    → claims session, both sides show the same fingerprint
authenticated HA user
    → confirms fingerprint
Relay + private claim secret
    → receives webhook and Bearer token
```

The code does not contain credentials. Before HA confirmation, polling returns
only `pending_confirmation`. A second device cannot take over an existing
claim, while an identical request can safely retry after a lost response.
Re-pairing rotates the telemetry token without changing the webhook ID.
