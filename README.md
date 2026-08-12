# Belgee X50 — Home Assistant Integration

Home Assistant integration for Belgee X50 / Geely Coolray.

Open source under the [MIT License](LICENSE).

Version `0.5.0` is an installable read-only preview:

- guided setup in the Home Assistant UI;
- a private Relay webhook protected by a generated Bearer token;
- automatic vehicle, Gateway, Navigation and Relay devices;
- telemetry sensors, availability and GPS device tracker;
- support for the deployed Relay body and the planned v2 envelope;
- MapKit route payload separation from ordinary entity attributes;
- privacy-redacted Home Assistant diagnostics;
- five-minute code pairing with explicit Relay fingerprint confirmation and
  automatic webhook/Bearer-token delivery;
- a compact event contract for
  [Belgee X50 Control Center](https://github.com/AlteroAscension/belgee-x50-control-center).
- independent protected Relay and Gateway outbound push channels, Auto
  arbitration, and a separate local polling diagnostic mode;
- topology changes through **Configure**, without deleting the integration.
- opt-in read-only Gateway vendor-property diagnostics sent through the
  existing outbound Gateway connection.

## Connection modes

- `relay`: provide a public HA URL and complete short-code pairing on Relay.
- `gateway_push`: provide a public HA URL and pair Gateway. Gateway connects
  outward, so HA needs no VPN route or incoming head-unit address.
- `auto`: pair both independently. Fresh Relay push wins; outbound Gateway
  push takes over when Relay exceeds the availability timeout.
- `gateway_poll`: optional local/AVD diagnostics using a directly reachable
  Gateway URL.

The mode can be changed later through **Configure**. Pairing can be started
there for either device. Relay and Gateway tokens are independent.

The current production components remain in
[X50 Telemetry](https://github.com/AlteroAscension/X50_telemetry), and the
supported transition simulator remains in
[x50-simulator-addon](https://github.com/AlteroAscension/x50-simulator-addon).
This preview is intentionally read-only and can run beside the existing YAML
package. Command ownership and entity migration are later milestones.

## Install the preview

Copy `custom_components/belgee_x50` into Home Assistant's
`/config/custom_components/`, restart Home Assistant and add **Belgee X50**
from **Settings → Devices & services**. The flow displays a short-lived
eight-character code. Enter it in the selected Relay or Gateway, compare the
fingerprint shown on both sides and confirm in Home Assistant. The device then
receives its private telemetry URL and its own Bearer token automatically.

An existing entry can be paired or re-paired from **Configure** by selecting
`Create a code to pair or re-pair a device`, then selecting Relay or Gateway.
Re-pairing rotates only the selected device token.

## Pairing Gateway and Relay without a type error

In the usual `auto` topology, pair the devices one at a time. A pairing code
is intentionally bound to one device type, so it cannot be reused for the
other device.

1. In **Settings → Devices & services → Belgee X50 → Configure**, choose
   **Create a code to pair or re-pair a device** and select **Relay**.
2. Enter the displayed eight-character code and the public HA URL in
   **X50 Relay → Связь → Привязка Home Assistant**, then confirm the same
   fingerprint in HA.
3. Return to **Configure**, create a *new* code and select **Gateway**.
4. Enter that second code and the same public HA URL in
   **X50 Gateway → Home Assistant**, tap **Привязать Gateway к Home Assistant**,
   and confirm the Gateway fingerprint in HA.

Do not fill `gateway_url` when the selected connection mode is `relay`,
`gateway_push` or `auto`: it is only for the local `gateway_poll` diagnostic
mode. The expected setup has the Gateway and Relay initiate outbound HTTPS
connections to HA, so neither VPN routing nor an incoming address to the head
unit is needed. If `wrong_device_type` appears, discard the current code and
create a new one with the matching device selected.

For HACS installs, add this repository as a custom integration repository and
select the latest published semantic-version release.

## Development

Protocol normalization is deliberately independent of Home Assistant:

```bash
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
```

The integration accepts the existing v1 body during migration. If Relay sends
an `x50.telemetry.v2` envelope, its installation identity must match the
configured entry. Unknown protocol majors are rejected. A MapKit
`route_transport` is removed from both legacy duplicate locations before the
compact state is exposed to entities.

## Project documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — public component boundaries;
- [ROADMAP.md](ROADMAP.md) — public development milestones.

Detailed security, protocol and deployment designs are reviewed privately and
will be published only after they become stable public contracts.

## Status

Read-only preview `0.5.0`: independent outbound transport, opt-in research
diagnostics and protocol tests
are present.
Runtime validation on a disposable Home Assistant installation is required
before publishing the first tagged release.
