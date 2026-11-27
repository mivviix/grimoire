---
summary: Modern Luau to write by default (task library, interpolation, if-expressions, generalized for) and the classic traps (# on holes, patterns aren't regex)
tags: luau, idioms, task, strings, tables, random
---
# Luau idioms and traps

## Write this
- `task.wait`, `task.spawn`, `task.defer`, `task.delay`, `task.cancel`. Never the old `wait`, `spawn`, `delay`.
- String interpolation: `` `{player.Name} has {coins} coins` ``.
- If-expression: `local speed = if sprinting then 24 else 16`.
- Generalized iteration: `for key, value in t do` (no `pairs`/`ipairs` needed).
- `continue`, compound assignment (`x += 1`), floor division `//`.
- `table.clone`, `table.freeze` (shallow; for config tables), `table.clear` (keeps capacity), `table.find`.
- `Random.new(seed)` for reproducible randomness (`:NextInteger(a, b)`, `:NextNumber()`), not `math.random` with global state.
- `--!strict` at the top of modules you want type-checked; annotate module boundaries, let locals infer.
- The `buffer` library for compact binary data (save formats, packing remote payloads).

## Traps
- `#t` is only defined for arrays with no holes. Setting `t[i] = nil` mid-array breaks it; use `table.remove`.
- String patterns are Lua patterns, not regex: `%d`, `%a`, `%s`, `-` (lazy), no `|` alternation, magic chars escaped with `%`.
- Vector3, CFrame, Color3 are immutable values: `part.Position.X = 5` errors; build a new one.
- Comparing CFrames or floats with `==` after math almost never holds; compare with a tolerance (`(a - b).Magnitude < 1e-3`).
- `pcall` returns `ok, result`; an error inside a `task.spawn` thread doesn't reach your pcall.
- A connection made inside a loop or per-character keeps running after the thing it served is gone: keep it and disconnect it ([[Cleanup.luau]]).
