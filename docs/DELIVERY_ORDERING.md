# Live and archive delivery

Relay's `relay.deferred_upload=true` identifies historical queue delivery.
It must not replace live state, renew source freshness or suppress Gateway in
auto mode. Authenticated journal chunks, routes and trajectory snapshots are
still retained/delivered and acknowledged with HTTP 202 independently of live
connection-mode selection. The live telemetry event is emitted only for accepted
live intake. Sender wall clocks are not compared across Gateway and Relay.

Trajectory consumers use the same ordering rule per `snapshot_id`: completed
beats active regardless of delivery order; within the same completion state,
only a greater `observed_at_ms` replaces the retained copy. Duplicate or older
snapshots do not emit another trajectory event. Control Center and Simulator
apply this rule locally too, so HTTP backfill cannot overwrite a newer event.

Control Center subscribes to events before listing/fetching the Integration's
retained snapshots on every connection. Events arriving during backfill remain
queued on the WebSocket. This recovers the bounded in-memory HA snapshot store;
completed JSONL journals remain the durable full-trip archive after HA restart.
