---
name: gwitg
description: Codex agent skill for Admin-led delegation to Workers fixed at 6-luna/high and advisory Authors, with recursive delegation, no progress polling, and optional decision-model advice.
---

# gwitg

This skill is designed specifically for **OpenAI Codex** and its subagent controls. It is not currently intended as a generic cross-agent skill for Claude Code, Cursor, Copilot, or other runtimes.

Use subagents for independent work that can be completed without frequent synchronization with the current agent.

## Roles and ownership

The current session's agent is the **Admin**: it owns the overall goal, scope, constraints, integration, and final response. It decides whether to work directly, delegate execution to a **Worker**, consult an **Author**, continue, stop, or return a decision to the user. A delegated agent does not inherit the overall Admin role merely because it is a parent of its own children.

- **Admin — overall owner and final decision-maker.** The Admin evaluates all delegated results, integrates useful parts, and remains accountable for the outcome. It may accept, adapt, or reject an Author's advice.
- **Worker — execution role.** A Worker performs a bounded assignment such as implementation, investigation, testing, or review, and reports results, evidence, blockers, uncertainties, and risks. It does not change the user's goal or take over overall task ownership.
- **Author — advisory role.** An Author helps the Admin reason about design, alternatives, assumptions, trade-offs, risks, and longer-term effects. Its output is advice for the Admin, not an instruction to execute. It does not own the task, decide for the Admin, or send advice directly to a Worker or the user.

These are roles, not model names. The Admin uses the model and reasoning effort of the current session. The default Author configuration is **6.1-sol with medium reasoning effort**. A task may use at most one Author agent; this is a role-level cap, not a requirement to consult an Author. Workers have no fixed count limit: launch as many as useful for independent bounded work, subject to the runtime's global concurrency limit. Every Worker uses **6-luna with high reasoning effort**; there are no alternative Worker profiles. Do not silently substitute a different model or effort if the Author or Worker configuration is unsupported. The Admin should handle the work directly or report the runtime limitation.

Use a Worker directly for clear, bounded execution. Consult an Author when the Admin cannot confidently choose among consequential options or when an independent design perspective is especially valuable; do not call one for every task. A request to an Author should ask for judgment material, not implementation. If an Author uses recursive delegation to research its advice, its final responsibility remains an advisory response to the Admin.

The normal route is Admin → Worker → Admin for execution, or Admin → Author → Admin → (optional) Worker for advice followed by execution. Author advice never flows automatically to a Worker: the Admin first decides whether to adopt, adapt, reject, or escalate it.

The Admin may return a question to the user even when an Author has made a recommendation. Return it when the choice depends on the user's values or intent, materially changes the goal or scope or an explicit constraint, weakens a security condition, has significant irreversible consequences, or remains too uncertain for the Admin to decide responsibly. When a safe improvement preserves the goal and constraints, the Admin may decide and proceed without asking.

An optional decision model is also advisory. When the next action is genuinely unclear, the Admin may ask the selected judge to consider continuing directly, consulting an Author, or returning a decision to the user. Its recommendation informs the Admin; it cannot override the Admin's judgment or make the final user-escalation decision. Do not call it for routine, clear choices.

The outer user request need not prescribe the number of agents or reproduce this internal workflow. The Admin chooses whether and how to delegate under the task's goal, scope, and constraints.

Worker model and reasoning effort are fixed to **6-luna / high** as described below.

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

Every Worker uses:

- model: `6-luna`;
- reasoning effort: `high`;
- `/fast`: environment default unless the user changes it.

This is fixed Worker configuration, not a selectable profile. No per-task preference, configuration file, or judge recommendation may change the Worker model or reasoning effort. If the runtime cannot launch `6-luna` with high reasoning effort, do not substitute another configuration; keep the work in the current agent.

## Launching a worker

Check the current spawn tool's accepted model identifiers, reasoning efforts, and context-inheritance options in its exposed schema and parameter documentation before launching. Use the runtime's established launch identifier for `6-luna`; do not infer aliases by adding a prefix or substitute another model when no supported identifier is established.

If the spawn tool requires `fork_turns="none"` to select a model or reasoning effort, set it and pass both settings explicitly. In that runtime, `fork_turns="all"` or its default inherits the parent's configuration and cannot enforce the Worker configuration. Follow the current tool contract rather than assuming these parameters exist in every environment. If the selected settings cannot be applied, keep the work in the current agent.

Without inherited history, the delegation prompt must be self-contained: include the objective and acceptance criteria, working directory and relevant files, current state and constraints, permitted changes and validation, and expected report. Also pass the selected judge, the fixed `6-luna` / `high` Worker configuration, established launch identifier, and applicable gwitg rules so descendants can reuse them without rereading configuration. Do not assume the Worker can see earlier user messages or the Admin's findings.

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

- `clef`: use the available Clef delegation-judgment tool or connection (called Clef-flash-q4 in v1.0).
- `jev`: use the available Jev delegation-judgment tool or connection.
- `none`: make the judgment in the current agent without an external decision model.

Selection does not provision an API connection, install a model, or choose the worker model. Check that the selected judge has an actual callable tool or connection. If it is unavailable or its call fails, report the limitation and judge in the current agent; do not silently substitute the other external judge. Do not invent tool names, API endpoints, or model identifiers.

The delegation judge is separate from the fixed Worker configuration. The judge cannot change a Worker's model or reasoning effort.

The judge may evaluate:

- whether the task is sufficiently independent;
- whether the necessary context can be packaged into one prompt;
- whether parallel execution is safe;
- whether file or state conflicts are likely;
- whether the task should remain in the current agent;
- when the Admin is genuinely uncertain, whether the next step should be direct continuation, Author consultation, or a user decision.

A judge may not choose or change a Worker model or reasoning effort.

The judge is advisory. The current agent remains responsible for the final delegation decision.

Do not invoke a judge when the delegation decision is already clear.

Do not use a judge to monitor a running subagent.

## Common judge result format

Interpret every delegation judge's recommendation through the same two-field result, regardless of the judge or its connection:

```yaml
delegate: true
reason: Independent repository search with bounded scope
```

- `delegate` is required and must be a boolean. `true` recommends delegation; `false` does not.
- `reason` is required and must be a non-empty short string.

A missing field, wrong value type, empty reason, or undefined field makes the result invalid. Treat it as unavailable and let the Admin decide. Do not use a judge result to select or override the fixed Worker model or reasoning effort.

The common result must not contain concrete model identifiers, reasoning effort, or `/fast` state. The Admin makes the final delegation decision; Worker configuration remains fixed and separate. This two-field schema applies to delegation recommendations; it does not constrain separate advisory input about whether the Admin should continue, consult an Author, or return a choice to the user. Such advice remains non-binding. Judge-specific invocation, connection details, and raw response formats are outside the common result; map Clef, Jev, or another judge's response to these fields in that judge's environment.

## Parallelism

Prefer parallel execution when two or more tasks are independent.

Launch independent work concurrently instead of serializing it.

Parallelize by dependency, not merely by task count.

Do not create subagents merely to maximize the number of active workers.

Respect the runtime's global concurrency limit across the entire agent tree.

Avoid concurrent edits to the same files or shared mutable state unless responsibilities are explicitly partitioned and conflicts are unlikely.

## Recursive delegation

A subagent may spawn its own subagents when its assigned work contains independent subtasks that materially benefit from delegation or parallel execution.

Recursive delegation follows the same gwitg policy and uses the fixed `6-luna` / `high` Worker configuration. It does not ask the judge to select Worker settings.

A subagent that spawns children must:

- use `6-luna` with high reasoning effort for Workers;
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

## Role examples

- **Simple execution:** Admin → Worker → Admin.
- **Design uncertainty:** Admin → Author → Admin → optional Worker.
- **Partial adoption:** Admin → Author → Admin adapts the proposal → Worker → Admin.
- **User decision needed:** Admin → Author → Admin → user.
- **Decision-model advice:** Admin → selected judge → Admin decides whether to continue, consult an Author, or ask the user.

## Normal flow

For suitable work:

1. identify independent work and decide whether the Admin can proceed, should consult an Author, or should return a decision to the user;
2. when delegation is ambiguous, use the judge selected at task start or judge in the parent; skip the judge when the decision is clear;
3. spawn each Worker with `6-luna` and high reasoning effort;
4. when consulting an Author, request analysis or advice and use the default **6.1-sol / medium** configuration, unless the user specifies another supported configuration;
5. let Workers and Authors recursively delegate independent subtasks when useful, while preserving each outer role and responsibility;
6. continue only independent work in each parent;
7. avoid progress monitoring and polling; use only permitted lifecycle checks and limited corrections or cancellation;
8. let the user directly use `/subagent` for the limited permitted controls;
9. evaluate and integrate completed results; the Admin decides what to adopt and whether user input is needed.
