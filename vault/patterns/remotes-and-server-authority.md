---
summary: Server authority for remotes: what to validate, rate limiting, never trusting client damage or positions; read before adding any RemoteEvent
tags: remotes, security, server-authority, exploits, validation, rate-limit
---
# Remotes and server authority

Exploiters can fire any remote with any arguments, as often as they like. The server owns the truth; a remote from the client is a *request*.

## Every OnServerEvent handler
1. Type-check every argument (`typeof(x) == "Vector3"`, finite numbers: `x == x and math.abs(x) < 1e6`), clamp lengths of strings and tables.
2. Check the request makes sense for this player now: alive, owns the item, close enough (compare against the server's view of their character, with slack for latency), cooldown passed.
3. Compute the result on the server: damage, rewards, prices. The client says "I swung", never "I dealt 50".
4. Rate-limit per player (a timestamp per player per remote; drop excess quietly).

```lua
local last = {} -- [player] = os.clock() of last accepted request
remote.OnServerEvent:Connect(function(player, targetPos)
	if typeof(targetPos) ~= "Vector3" then return end
	local now = os.clock()
	if now - (last[player] or 0) < 0.25 then return end
	last[player] = now
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not root or (root.Position - targetPos).Magnitude > 20 then return end
	-- server-side effect here
end)
game:GetService("Players").PlayerRemoving:Connect(function(p) last[p] = nil end)
```

## Layout
- Remotes live in ReplicatedStorage, created by the server (or in the place file), one per intent (`UseAbility`, `BuyItem`), not one generic "do anything" remote.
- `RemoteFunction` from client to server is fine; server to client `InvokeClient` is not: a client can hang it forever.
- Cosmetics (effects, sounds) the client may play itself immediately and the server confirms; anything that changes game state waits for the server.
- What survives the trip: [[replication]].
