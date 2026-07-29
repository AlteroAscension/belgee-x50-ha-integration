# Changelog

## 0.1.1

- fixed Config Flow loading on Home Assistant: the webhook component is
  imported from `homeassistant.components`, not `homeassistant.helpers`;
- added a regression test for Home Assistant import boundaries.

## 0.1.0

- first installable read-only integration preview;
- Config Flow, protected Relay webhook and compact push coordinator;
- vehicle, Gateway, Navigation and Relay devices and entities;
- current v1 and planned v2 telemetry normalization;
- heavy MapKit route transport separated from entity state.
