# Public roadmap

## 1. Foundation

- [x] stable compact data model for the preview;
- [x] development fixtures and protocol tests;
- [x] installable Home Assistant project skeleton;
- [x] read-only setup, Bearer webhook and diagnostics;
- [x] user-confirmed Relay pairing and re-pairing by one-time code;
- [ ] live validation against a disposable Home Assistant installation;
- [ ] signed v2 messages and replay window after Relay dual-publish support.

## 2. Entities

- [x] vehicle and component devices;
- [x] core telemetry sensors and GPS tracker;
- [x] availability and version diagnostics;
- [x] Russian and English setup translations;
- [ ] complete parity report against the legacy YAML entities.

## 3. Control Center connection

- supported exchange of live state and historical events;
- compatibility diagnostics;
- recovery after temporary outages.

## 4. Controls

- Home Assistant actions;
- clear command results;
- user-facing permissions and safety checks.

## 5. Migration and stable release

- side-by-side operation with the current package;
- documented entity migration;
- installation, upgrade and rollback documentation;
- stable public API and compatibility policy.

Milestones may change while the project remains pre-release.
