---
summary: Network ownership, impulses vs velocity, collision groups; read before any knockback, projectile or NPC physics code
tags: physics, network-ownership, impulse, velocity, npc, collision
---
# Physics and network ownership

## Who simulates what
- Every unanchored assembly is simulated by one machine, its network owner: the server, or the client of a nearby player. A player's own character is always owned by that player's client.
- Physics you apply on a machine that does not own the assembly is overwritten by the owner's next update. That is why a server-side `ApplyImpulse` on a client-owned or resting body often does nothing.
- NPCs: call `part:SetNetworkOwner(nil)` on the server (on the root, it applies to the whole assembly) so the server owns them. Anchored parts can't take an owner: check `part:CanSetNetworkOwnership()` first.

## Pushing things
- Prefer setting `AssemblyLinearVelocity` / `AssemblyAngularVelocity` directly on the owner over `ApplyImpulse`: it is predictable and works on resting bodies.
- Ragdolled limbs are separate assemblies: set velocity on every part, not just the root.
- To knock back a player, the server can't push them: send the push to their client (a RemoteEvent) and set velocity there.

## Collisions
- Collision groups: `PhysicsService:RegisterCollisionGroup("Name")`, `PhysicsService:CollisionGroupSetCollidable(a, b, false)`, then `part.CollisionGroup = "Name"`.
- To stop two specific parts colliding, a `NoCollisionConstraint` between them is cheaper than a group.
- Flush parts at full size jam against each other; parts with no collision clip through the floor. For ragdoll limbs, weld a slightly smaller invisible massless collider into each part. Details: [[ragdolls]].
