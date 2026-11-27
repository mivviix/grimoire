---
summary: Ragdolling R15 characters on new AnimationConstraint rigs and old Motor6D rigs, active-ragdoll muscles, and the fixes for jitter and flinging
tags: ragdoll, r15, animationconstraint, motor6d, knockback, physics, active-ragdoll
---
# Ragdolls

## Which rig you have
New R15 rigs (Avatar Joint Upgrade, default for new places and Rig Builder dummies) have **no Motor6Ds**. Joints are `AnimationConstraint`s (15, including `Root` LowerTorso→HumanoidRootPart), plus 14 limited `BallSocketConstraint`s and 19 `NoCollisionConstraint`s already in the rig. `IsA("Motor6D")` finds nothing, so check for both kinds.

## Going limp (new rigs)
1. Every AnimationConstraint except `Root`: `Enabled = false`. The ball sockets take over.
2. `humanoid.RequiresNeck = false`, `humanoid:ChangeState(Enum.HumanoidStateType.Physics)`.
3. Limbs `CanCollide = true` (save each part's own value first and restore it; torso, head and root collide by default, limbs don't). Turn the **HumanoidRootPart's** CanCollide off while down: it shoves the limbs and the body flops like a fish.
4. Undo: re-enable the constraints, restore CanCollide, `ChangeState(GettingUp)`.

Do not use `PlatformStand` for this; it is the stiff default "ragdoll" and looks wrong.

## Old Motor6D rigs
Per joint: build two Attachments from the Motor6D's C0/C1, a `BallSocketConstraint` between them, a `NoCollisionConstraint` between the two parts, then `Motor6D.Enabled = false`.

## Who runs it
- NPC: everything on the server; `root:SetNetworkOwner(nil)` first ([[physics-and-ownership]]).
- Player: the server toggles joints (that replicates); the player's own client sets the Physics state and velocities, because it owns the body.
- A client-owned NPC set to Physics from the client may not stay down: the Humanoid keeps lifting it to hip height. Set `humanoid.EvaluateStateMachine = false` while ragdolled, true again at get-up.

## Jitter fixes
- Mesh colliders on limbs and torso overlap at neck and waist and push apart every frame: while down, give each part a plain box collider about 90% of its size and make joined parts ignore each other.
- A NaN joint Transform makes a client-owned body vanish for good: guard any computed target against NaN.

## Active ragdoll (muscles)
Keep the AnimationConstraints enabled but physical: `IsKinematic = false`, `AngularDamping = 1`, `MaxForce` 0 (the ball sockets hold position), then play an animation; the body tries to hold its poses.
- `AngularStrength` is a spring frequency (value × 60 Hz). Stiff (~0.35) with a low `MaxTorque` cap overshoots into a seizure; soft ~0.08 with a high cap works (arm ~900, leg ~1600, core ~2500).
- Clamp muscle targets inside each joint's BallSocket limits (twist about the joint X axis = bend, cone for the rest) or limbs jitter and fling.
- A hit that should look natural: play the hit animation, freeze it at the blasted pose (`track:AdjustSpeed(0)` ~0.4 s in), then tween every MaxTorque to 0 over ~1.2 s (Quad); TweenService can tween MaxTorque. Ease out of standing into the fall, never hold a pose or snap limp.
- Recover: restore saved MaxTorque/AngularStrength (keep them in attributes), `IsKinematic = true`.
