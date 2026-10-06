---
name: gwitg
description: Orchestrate suitable independent work with parallel 6-luna high subagents, avoid polling and progress monitoring of running subagents, and preserve limited direct user control through /subagent. Select an optional delegation judge through the external decision-model setting.
---

# gwitg

Use subagents for independent work that can be completed without frequent synchronization with the current agent.

The default worker is **6-luna with high reasoning effort**.

This policy applies recursively: a subagent that delegates work becomes the parent of its own children and must follow the same rules.

## Core rule: delegate without progress monitoring

After assigning work, let the subagent work independently. Occasional checks of lifecycle state (running, completed, failed, interrupted, or unavailable) are allowed when needed for coordination or a user status request.

Do not repeatedly query status at short intervals, alternate sleep and status calls to watch for completion, request progress updates, inspect partial output or intermediate logs, or open a running thread merely to monitor progress. Prefer passive completion or failure notifications when available. Waiting for such notifications is allowed and is not a status check.

Silence, elapsed time, or apparent lack of activity is not evidence of failure. Do not accelerate, restart, replace, or reconfigure a worker merely because it appears slow. Do not duplicate delegated work solely to check that progress is being made.

The parent is an orchestrator, not a progress monitor.

## Limited corrections and cancellation

While a subagent is running, its parent may send only:

- a correction to a false premise;
- a newly discovered constraint relevant to the assigned task;
- an instruction to stop the assigned work.

These exceptions do not permit ordinary additional tasks, changes to the objective or deliverable, or changes to the work strategy. Do not use a new constraint as a pretext to expand scope. Keep the message limited to the correction, constraint, or cancellation; do not request a progress report in the same message.

If a correction or constraint makes the original assignment impossible, the subagent should stop and report the reason rather than invent a replacement assignment. Cancellation may use the runtime's interruption mechanism when needed. Stopping does not authorize restarting or replacing the worker without an appropriate new assignment.

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

At the start of each user task using this skill, select the delegation judge once as follows:

1. An explicit user selection of `clef`, `jev`, or `none` for this task takes precedence.
2. Otherwise, run `python3 <skill-directory>/scripts/decision_model.py` from the task's working directory, using the absolute path to this skill's script. It first reads `<project-root>/.gwitg/decision-model`. Only if that file is absent does it read `~/.config/gwitg/decision-model`. Do not change to the skill directory before running the resolver.
3. The project root is the Git repository root discovered from the working directory at task start. Outside a Git repository, or when Git is unavailable or root discovery fails, use that starting directory.
4. The file contains exactly one lowercase value: `clef`, `jev`, or `none`, with optional surrounding whitespace. If both files are absent, select `none`. A blank, invalid, unreadable, or non-UTF-8 file is an error. A project setting of `none` takes precedence over the common setting. Do not fall back to the common setting when reading the project setting fails.

Retain the selection in the task context and reuse it for all delegation judgments within that task. Pass the selection to subagents in their delegation prompts so descendants do not reread the setting for the same task. Changes to the file take effect at the start of the next user task, not during the current task. A continuation or status question does not start a new task. An explicit user selection during the task overrides the retained selection without rereading the file. Do not persist the selection across separate user tasks or run a resident process.

Never create or modify the user's setting as part of reading it. If the resolver or Python is unavailable, or reading the setting fails, disclose that limitation once and retain `none` for the task; do not retry the resolver for each decision.

- `clef`: use the available Clef delegation-judgment tool or connection (called Clef-flah-q4 in v1.0).
- `jev`: use the available Jev delegation-judgment tool or connection.
- `none`: make the judgment in the current agent without an external decision model.

Selection does not provision an API connection, install a model, or choose the worker model. Check that the selected judge has an actual callable tool or connection. If it is unavailable or its call fails, report the limitation and judge in the current agent; do not silently substitute the other external judge. Do not invent tool names, API endpoints, or model identifiers.

The delegation judge is distinct from the worker. Keep the existing `6-luna` / `high` worker default regardless of the judge selection.

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
- apply the same lifecycle-check, correction, cancellation, and no-polling rules to its children;
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

Other permitted interventions are the limited corrections and cancellation described above, delivered through the parent. Ordinary additional task instructions remain prohibited.

Do not treat replacing a running subagent, resuming canceled work, or changing its objective or strategy as permitted interventions under these exceptions.

These controls apply to descendants as well as direct children.

The user's direct `/subagent` changes take effect as supported by the runtime and must not be undone by an agent.

## Parent-mediated intervention boundaries

The parent may check lifecycle state and relay a correction, newly discovered constraint, or cancellation within the rules above, including at the user's request.

The parent must not proxy opening a running thread, toggling `/fast`, changing the model or reasoning effort, or replacing a running worker. For those permitted direct configuration controls, identify the worker name and let the user act through `/subagent`.

## Bottlenecks

A slow worker is not automatically a failed worker.

Do not use apparent slowness as a reason to monitor progress, accelerate, restart, replace, or reconfigure a worker. Occasional lifecycle checks remain subject to the no-polling rule; limited corrections and cancellation remain permitted for their stated purposes.

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

If no independent work remains, prefer passive waiting for a terminal event. Do not fill the wait with repeated lifecycle checks.

Do not manufacture progress checks to fill idle time.

## Investigation reports

When relevant, a completed investigation should include:

- what was checked;
- when the check was performed and what time the evidence describes;
- whether the finding was directly observed in the current state or came from a document or historical log;
- unverified items and limitations.

For time-sensitive investigations, distinguish currently observed facts from historical recorded facts. Reading a document today does not make its contents current. If the evidence time is unknown, say so rather than guessing.

Use only the relevant fields for simple code investigations; a long fixed template is not required.

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

React to an explicit runtime failure, interruption, or unavailable-agent notification, or the same terminal state established by a permitted lifecycle check.

Depending on the failure reason, the parent may:

- retry the task;
- delegate it again;
- perform the work itself.

Failure handling begins only after a terminal failure state is established. A requested cancellation is a stop instruction, not evidence of runtime failure.

Never infer failure solely from elapsed time, silence, or lack of intermediate output.

## Priority

Apply these rules in this order:

1. explicit user instructions, including permitted corrections, constraints, and cancellation;
2. explicit runtime terminal events or a terminal state established by a permitted lifecycle check;
3. the normal no-polling and intervention-boundary rules.

A user status request allows a lifecycle check, not progress monitoring or parent-mediated reconfiguration.

## Normal flow

For suitable work:

1. identify independent tasks;
2. when delegation is genuinely ambiguous, use the judge selected at task start or judge in the parent;
3. spawn `6-luna` high workers in parallel;
4. allow those workers to recursively delegate independent subtasks when useful;
5. continue only independent work in each parent;
6. avoid progress monitoring and polling; use only permitted lifecycle checks and limited corrections or cancellation;
7. let the user directly use `/subagent` for the limited permitted controls;
8. integrate results only after completion.
