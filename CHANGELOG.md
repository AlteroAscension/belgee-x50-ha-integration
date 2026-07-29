# Changelog

## 0.3.0

- added switchable `relay`, `gateway` and `auto` connection modes;
- added direct read-only polling of a Gateway reachable from HA;
- added deduplicated MapKit route snapshot reads in direct/Auto mode;
- made the public HA URL optional for a Gateway-only installation;
- added Relay-first/Gateway-fallback transport arbitration;
- exposed configured and active transport as diagnostics;
- allowed changing topology and adding/re-pairing Relay after installation.

## 0.2.0

- added five-minute HA-to-Relay pairing using a human-readable one-time code;
- added a two-phase claim/confirm exchange: credentials remain unavailable
  until the authenticated HA user confirms the matching Relay fingerprint;
- added pairing and re-pairing to integration options, including automatic
  telemetry Bearer-token rotation;
- preserved the existing webhook identifier and all legacy HA command
  settings during re-pairing;
- added expiry, idempotent retry and claim-secret protections with protocol
  regression tests.

## 0.1.3

- fixed HTTP 500 when opening Config Flow: the public URL validator now runs
  after form submission instead of being embedded as a non-serializable
  callable in the frontend schema;
- invalid public URLs are returned as an ordinary localized field error.

## 0.1.2

- require an explicit externally reachable Home Assistant base URL during
  setup instead of silently falling back to the internal Home Assistant URL;
- allow changing that public base URL through integration options without
  rotating the webhook ID or Bearer token.

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
