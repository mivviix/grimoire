---
summary: Saving player data with DataStoreService: UpdateAsync, retries, session locking, BindToClose, limits; read before writing any save system
tags: datastore, saving, player-data, profilestore, bindtoclose, persistence
---
# Saving player data

## Rules
- Load once on join, keep the data in a server table, save on leave, on an autosave timer (every few minutes) and in `game:BindToClose`. Never save on every change.
- Write with `UpdateAsync`, not `SetAsync`: it reads the current value first, so you can refuse to overwrite newer data.
- Wrap every DataStore call in `pcall` and retry with backoff (e.g. 1, 2, 4 s). If loading fails, **don't** let the player play on default data that will then be saved over their real data: kick them with a message or block saving for that session.
- Session locking: store a lock (server JobId + timestamp) in the record so a second server can't load and overwrite while the first still holds it (fast server hops otherwise lose progress).
- `BindToClose` has about 30 seconds; save all players in parallel (`task.spawn` per player, then wait).
- Keep one record per player key (e.g. `"player_" .. userId`) with a `version` field for migrations.

## Limits (check the docs for current numbers)
- About 4 MB per value; writes to the same key are throttled (roughly one per 6 s).
- Request budget per server scales with player count: read it with `DataStoreService:GetRequestBudgetForRequestType`.
- Studio needs "Enable Studio Access to API Services" to touch real data stores; use a separate store name for testing.

## Don't reinvent it
For a real game, ProfileStore (by loleris, the successor to ProfileService) already does session locking, autosave and BindToClose correctly. Write your own only for something small or unusual.
