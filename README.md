# vmodel-contracts

The versioned contract bundle shared by every module of the V-model spec
generator. **This package is the architecture.** Modules never import each
other; they exchange these models and nothing else.

Consumers (each pins an exact release, e.g. `vmodel-contracts @ git+https://github.com/ShyAlon/vmodel-contracts@v0.1.0`):

- `interview-engine` produces `ScopeVerdict`, `InterviewTranscript`, `IntentModel`, `ConOpsDocument`
- `spec-generator` consumes `IntentModel` + `ConOpsDocument`, produces `StakeholderNeedsSet`,
  `RequirementSet`, `ArchitectureOverview`, `SpecBundle` (items + AGENTS.md +
  build plan + manifest + punch list + traceability)
- `verification-loop` consumes `SpecBundle` + a build artifact, produces
  `AcceptanceTest` packages and the `VerificationReport`
- `delivery-api` owns `RunLink`, `RunStatus`, `RunCostReport`, `DeliveryBundle`

## Rules

1. Every model derives from `ContractModel` and carries `contract_version`.
2. SemVer: MAJOR breaks consumers, MINOR is additive, PATCH is docs/validation.
3. `pip install -e .[dev] && vmodel-contracts-export` dumps JSON Schemas to
   `schemas/`; the schema diff between releases IS the compatibility review.
4. A field that crosses a boundary exists here first. No ad-hoc JSON.

## Artifact lifecycle

`vmodel_contracts.artifact_lifecycle` is the canonical vocabulary for durable
artifacts across interview, specification, verification, and delivery. It is a
small transition contract, not a second workflow engine.

States: `missing`, `partial`, `complete`, `stale`, `invalidated`, `migrated`.
Transitions: `begin`, `checkpoint`, `finalize`, `dependency_changed`,
`invalidate`, `restart`, `migrate`, `adopt_migration`, `resume`, `delete`.
Each transition carries guard evidence and appends a `LifecycleEvent` to JSONL.
`mermaid_diagram()` and `dot_diagram()` render the same transition table used
by validation, so documentation and code cannot list different arcs.

Guard summary:

| Transition | Guard evidence |
|---|---|
| begin | producer ownership; inputs and anchor recorded |
| checkpoint | monotonic progress; same inputs and anchor |
| finalize | schema valid; complete; hashes sealed; content hash present |
| dependency_changed | named changed dependency |
| invalidate | named boundary; downstream closure computed |
| restart | producer rerun started under current inputs |
| migrate | approved migrator; source hash/version; target schema valid |
| adopt_migration | canonical storage and checkpoint updated atomically; hashes agree |
| resume | named next artifact and legal outgoing arc |
| delete | explicit destructive operation |

Explicitly illegal: changing an anchor while claiming `complete`; consuming an
`invalidated` artifact; overwriting `migrated` canonical data from a stale
checkpoint; resuming a bounded terminal checkpoint without a named legal arc.
Phase 1 defines and audits this contract only. Orchestration adoption starts
with the architecture artifact and proceeds stage by stage after shadow logs
match existing behavior.

### Local CI test

Run `./scripts/test-local.sh` from any directory. It creates a reusable `.venv`, installs the development dependencies and runs the same tests as the PR workflow using Python 3.12. Install Python 3.12 first, and make sure your Git authentication can read private `ShyAlon/vmodel-contracts` where it is a dependency.
