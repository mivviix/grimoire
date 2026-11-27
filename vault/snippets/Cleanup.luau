-- summary: Cleanup: collect connections, instances, threads and functions, then undo them all at once (a tiny Maid/Trove)
-- tags: cleanup, maid, trove, connections, memory-leak, module
--[[
	local Cleanup = require(path.to.Cleanup)
	local c = Cleanup.new()
	c:add(part.Touched:Connect(onTouch))
	c:add(effectClone)                      -- Destroyed on clean
	c:add(task.delay(5, explode))           -- cancelled on clean
	c:add(function() humanoid.WalkSpeed = 16 end)
	c:clean()                               -- undoes everything, newest first; c can be reused
]]

local Cleanup = {}
Cleanup.__index = Cleanup

function Cleanup.new()
	return setmetatable({ _items = {} }, Cleanup)
end

function Cleanup:add(item)
	table.insert(self._items, item)
	return item
end

local function undo(item)
	local kind = typeof(item)
	if kind == "function" then
		item()
	elseif kind == "thread" then
		pcall(task.cancel, item) -- errors only if it is the running thread
	elseif kind == "RBXScriptConnection" then
		item:Disconnect()
	elseif kind == "Instance" then
		item:Destroy()
	elseif kind == "table" then
		if type(item.Destroy) == "function" then
			item:Destroy()
		elseif type(item.Disconnect) == "function" then
			item:Disconnect()
		end
	end
end

function Cleanup:clean()
	local items = self._items
	self._items = {}
	for i = #items, 1, -1 do -- reverse: undo in the opposite order of setup
		undo(items[i])
	end
end

Cleanup.Destroy = Cleanup.clean -- so a Cleanup can be added to another Cleanup

return Cleanup
