# Belgee X50 — Home Assistant Integration

Home Assistant integration for Belgee X50 / Geely Coolray.

Version `0.1.1` is an installable read-only preview:

- guided setup in the Home Assistant UI;
- a private Relay webhook protected by a generated Bearer token;
- automatic vehicle, Gateway, Navigation and Relay devices;
- telemetry sensors, availability and GPS device tracker;
- support for the deployed Relay body and the planned v2 envelope;
- MapKit route payload separation from ordinary entity attributes;
- privacy-redacted Home Assistant diagnostics;
- a compact event contract for
  [Belgee X50 Control Center](https://github.com/AlteroAscension/belgee-x50-control-center).

The current production components remain in
[X50 Telemetry](https://github.com/AlteroAscension/X50_telemetry), and the
supported transition simulator remains in
[x50-simulator-addon](https://github.com/AlteroAscension/x50-simulator-addon).
This preview is intentionally read-only and can run beside the existing YAML
package. Command ownership, pairing and migration are later milestones.

## Install the preview

Copy `custom_components/belgee_x50` into Home Assistant's
`/config/custom_components/`, restart Home Assistant and add **Belgee X50**
from **Settings → Devices & services**. The flow displays the telemetry URL
and Bearer token that must be entered in X50 Relay.

For HACS development installs, add this repository as a custom integration
repository. No release archive is published yet.

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

Read-only preview `0.1.1`: implementation and protocol tests are present.
Runtime validation on a disposable Home Assistant installation is required
before publishing the first tagged release.
