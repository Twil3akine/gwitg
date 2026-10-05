---
name: gwitg
description: Orchestrate suitable independent work with parallel 6-luna high subagents, leave running subagents completely unmonitored until terminal completion or failure, and preserve limited direct user control through /subagent. Use Jev or Clef-flah-q4 when useful to judge whether work is appropriate to delegate.
---

# gwitg

Use subagents for independent work that can be completed without frequent synchronization with the current agent.

The default worker is **6-luna with high reasoning effort**.

This policy applies recursively: a subagent that delegates work becomes the parent of its own children and must follow the same rules.

## Core rule: spawn and leave alone

After assigning work to a subagent, do not inspect that subagent again until one of these terminal events occurs:

1. the subagent reports completion;
2. the runtime explicitly reports failure, interruption, or unavailability.

Silence, elapsed time, or apparent lack of activity is not evidence of failure.

While a subagent is running, its parent must not:

- poll its status;
- request a progress update;
- inspect partial output;
- inspect intermediate logs;
- open its thread merely to see progress;
- repeatedly call status, list, retrieve, or equivalent inspection operations;
- sleep and then check again;
- interrupt, restart, accelerate, replace, or otherwise reconfigure it because it appears slow;
- duplicate its delegated work solely to verify that progress is being made.

A parent may passively await a terminal completion or failure event when the runtime supports that behavior. Waiting must not be implemented as repeated progress checks.

The parent is an orchestrator, not a progress monitor.

## Default worker configuration

When spawning a worker, use:

- model: `6-luna`;
- reasoning effort: `high`;
- Fast mode: environment default.

If the environment does not support selecting `6-luna` with high reasoning effort, do not silently substitute another worker configuration. Follow explicit user instructions or keep the work in the current agent.

## Decide whether to delegate

Delegate when the task:

- is meaningfully independent;
- has sufficiently clear inputs;
- can make useful progress without repeated parent interaction;
- has a bounded objective or acceptance condition;
- does not require tightly interleaved edits with another active worker.

Typical candidates include:

- repository investigation;
- implementation of a well-defined change;
- bug investigation;
- test writing;
- independent code review;
- documentation investigation;
- comparison of implementation approaches;
- codebase search;
- self-contained experiments;
- validation against explicit acceptance criteria.

Keep work in the current agent when it requires:

- immediate user interaction;
- frequent decisions that materially alter the task;
- tight sequencing with another running task;
- concurrent edits to the same files or shared mutable state;
- parent-level judgment before consequential actions;
- context that cannot reasonably be packaged into one delegation prompt.

## Delegation judge

When it is genuinely unclear whether work is appropriate for a subagent, the current agent may use **Jev** or **Clef-flah-q4** as a lightweight delegation judge if available.

The judge may evaluate:

- whether the task is sufficiently independent;
- whether the necessary context can be packaged into one prompt;
- whether parallel execution is safe;
- whether file or state conflicts are likely;
- whether the task should remain in the current agent.

The judge is advisory. The current agent remains responsible for the final delegation decision.

Do not invoke a judge when delegation is already clearly appropriate or clearly inappropriate.

Do not use a judge to monitor a running subagent.

## Parallelism

Prefer parallel execution when two or more tasks are independent.

Launch independent work concurrently instead of serializing it.

Parallelize by dependency, not merely by task count.

Do not create subagents merely to maximize the number of active workers.

Respect the runtime's global concurrency limit across the entire agent tree.

Avoid concurrent edits to the same files or shared mutable state unless responsibilities are explicitly partitioned and conflicts are unlikely.

## Recursive delegation

A subagent may spawn its own subagents when its assigned work contains independent subtasks that materially benefit from delegation or parallel execution.

Recursive delegation follows the same gwitg policy as root-level delegation.

A subagent that spawns children must:

- use `6-luna` with high reasoning effort by default;
- delegate only independent, bounded subtasks;
- prefer parallel execution when dependencies allow it;
- provide each child enough context to finish independently;
- not inspect a running child before a terminal completion or failure event;
- avoid conflicting edits or shared mutable state;
- integrate completed child results before reporting completion to its own parent.

Children may recursively delegate under the same rules.

Do not impose an artificial tree-depth limit when the runtime already manages concurrency, but do not create deeper levels unless they materially improve the work.

## Delegation prompt

Give each worker enough context to finish without parent interaction.

Include, when relevant:

- objective;
- repository or working directory;
- current state;
- relevant files or components;
- constraints;
- commands it may run;
- required validation;
- acceptance criteria;
- prohibited changes;
- expected final report.

Avoid vague prompts when the current agent already knows the concrete task.

A worker should be able to determine by itself when its assignment is complete.

## Human-readable worker names

When supported, assign each subagent a short, stable, human-readable name.

Examples:

- `impl-core`
- `tests`
- `review`
- `investigate-cache`

Expose these names to the user when useful so that workers can be identified through `/subagent` without relying on internal IDs.

For recursive delegation, prefer names that remain understandable in the hierarchy.

## Direct user control through /subagent

The hands-off rule restricts agents. It does not prevent the user from directly inspecting or reconfiguring a running subagent through `/subagent`.

User intervention is limited to these actions:

- inspect the subagent's current state;
- open its thread;
- enable or disable `/fast`;
- change its model or reasoning effort.

No other user intervention is part of this policy.

In particular, do not treat the following as allowed gwitg interventions:

- replacing the subagent with another agent;
- stopping or resuming it;
- sending additional task instructions to change its ongoing work.

These controls apply to descendants as well as direct children.

The user's direct `/subagent` changes take effect as supported by the runtime and must not be undone by an agent.

## No parent-mediated intervention

An agent must not proxy `/subagent` intervention for the user.

Even when explicitly asked, the parent must not inspect or reconfigure a running child on the user's behalf.

This includes:

- checking its current progress or state;
- opening or reading its running thread;
- enabling or disabling `/fast`;
- changing its model;
- changing reasoning effort;
- replacing it with another agent.

If the user wants one of the permitted direct controls, identify the relevant worker name if necessary and leave the actual action to the user through `/subagent`.

## Bottlenecks

A slow worker is not automatically a failed worker.

The parent must not inspect, accelerate, restart, replace, or reconfigure a worker merely because it appears to be the bottleneck.

If the user identifies a bottleneck, the user may directly use `/subagent` for the permitted controls:

- state inspection;
- thread opening;
- `/fast` toggling;
- model or reasoning-effort changes.

After direct user intervention, agents continue following the normal hands-off rule.

## While workers are running

The parent may continue useful independent work.

The parent may:

- launch other independent workers;
- work on unrelated or non-conflicting portions of the task;
- prepare integration work that does not depend on intermediate worker state;
- respond to the user.

If no independent work remains, leave the workers alone until a terminal event arrives.

Do not manufacture progress checks to fill idle time.

## Completion

After a worker reports completion:

1. read its final result;
2. inspect relevant completed changes or evidence;
3. integrate it with other completed work;
4. resolve conflicts between completed workers;
5. perform parent-level validation when necessary.

Post-completion validation is expected and does not violate the hands-off rule.

A subagent with children must integrate the completed child results before reporting its own completion.

## Failure handling

React to an explicit runtime failure, interruption, or unavailable-agent notification.

Depending on the failure reason, the parent may:

- retry the task;
- delegate it again;
- perform the work itself.

Failure handling begins only after an explicit terminal failure signal.

Never infer failure solely from elapsed time, silence, or lack of intermediate output.

## Priority

Apply these rules in this order:

1. explicit direct user action through `/subagent` within the allowed controls;
2. explicit runtime completion or failure events;
3. the normal gwitg hands-off policy.

A user request sent to the parent does not authorize parent-mediated inspection or reconfiguration of a running subagent.

## Normal flow

For suitable work:

1. identify independent tasks;
2. use Jev or Clef-flah-q4 only when delegation is genuinely ambiguous;
3. spawn `6-luna` high workers in parallel;
4. allow those workers to recursively delegate independent subtasks when useful;
5. continue only independent work in each parent;
6. do not inspect running children;
7. let the user directly use `/subagent` for the limited permitted controls;
8. integrate results only after completion.
