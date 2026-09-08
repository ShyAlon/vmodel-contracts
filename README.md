# vmodel-contracts

The versioned contract bundle shared by every module of the V-model spec
generator. **This package is the architecture.** Modules never import each
other; they exchange these models and nothing else.

Consumers (each pins an exact release, e.g. `vmodel-contracts @ git+https://github.com/ShyAlon/vmodel-contracts@v0.1.0`):

- `interview-engine` produces `ScopeVerdict`, `InterviewTranscript`, `IntentModel`
- `spec-generator` consumes `IntentModel`, produces `StakeholderNeedsSet`,
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
