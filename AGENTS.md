# Belgee X50 HA Integration agent guide

Native Home Assistant custom integration (`custom_components/belgee_x50`). It
owns Config Flow, secure pairing/webhook intake, devices/entities/actions and
connection-mode policy. The current version is an installable read-only
preview; do not silently absorb Control Center UI responsibilities.

Read `README.md`, `ARCHITECTURE.md`, `ROADMAP.md` and `docs/`. The deployed
legacy HA package remains at `../home-assistant/`; simulator compatibility is
at `../x50-simulator-addon/`; the UI consumer is
`../belgee-x50-control-center/`.

Run `pytest` from this repository (configuration is in `pyproject.toml`). Keep
diagnostics privacy-redacted. Pairing codes, webhook URLs, Bearer tokens and
fingerprints are secrets: never hardcode them or place them in test snapshots.
