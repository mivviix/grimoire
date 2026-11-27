---
summary: What survives a RemoteEvent or Bindable call (tables, metatables, Instances, functions), and finding instances safely by name
tags: remotes, bindables, replication, tables, serialization, findfirstchild
---
# Replication and passing data

## Remote and Bindable arguments
- Bindables (BindableEvent / BindableFunction) **deep-copy** table arguments: the handler gets a stale copy, not your shared state table. Between server modules, call a plain Lua function or callback list instead.
- Metatables are stripped; functions can't be passed.
- Mixed tables (array part plus string keys) lose data: send either an array or a dictionary. Non-string dictionary keys are turned into strings.
- An Instance the receiver can't see (server-only, or streamed out on the client) arrives as `nil`.
- `UnreliableRemoteEvent` is for frequent, droppable data (positions, cosmetic effects): ordering and delivery aren't guaranteed and the payload is small (about 1 KB).

## Finding instances
Many models share a name (every "R6" or "Rig" dummy): never pick a target with `FindFirstChild(name)` when copies may exist. Hold a reference, use a tag (`CollectionService`) or an attribute.
