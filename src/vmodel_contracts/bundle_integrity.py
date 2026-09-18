"""Canonical, deterministic integrity checks for a delivered V-model bundle."""
from __future__ import annotations
from dataclasses import dataclass
from .needs import StakeholderNeedsSet
from .requirements import RequirementSet
from .spec import ItemSpec, TraceabilityEntry
from .verification import AcceptanceTest

@dataclass(frozen=True)
class IntegrityDiagnostic:
    code: str
    path: str
    message: str


def validate_traceability_graph(needs: StakeholderNeedsSet, requirements: RequirementSet,
                                items: list[ItemSpec], tests: list[AcceptanceTest],
                                traceability: list[TraceabilityEntry] | None = None) -> list[IntegrityDiagnostic]:
    """Validate every N -> R -> SPEC/AC -> T edge and, when supplied, the materialized matrix."""
    out: list[IntegrityDiagnostic] = []
    need_ids={n.need_id for n in needs.needs}; req_ids=requirements.requirement_ids()
    specs={x.spec_id:x for x in items}; test_by_id={x.test_id:x for x in tests}
    ac_owner={a.criterion_id:r.requirement_id for r in requirements.requirements for a in r.acceptance}
    for n in needs.needs:
        if not n.intent_need_ids:
            out.append(IntegrityDiagnostic("orphan-need", f"needs/{n.need_id}", "traces to no interview stakeholder need"))
    for r in requirements.requirements:
        unknown=sorted(set(r.need_ids)-need_ids)
        if unknown: out.append(IntegrityDiagnostic("unknown-need",f"requirements/{r.requirement_id}",f"references unknown needs {unknown}"))
        if not r.need_ids: out.append(IntegrityDiagnostic("orphan-requirement",f"requirements/{r.requirement_id}","traces to no stakeholder need"))
    covered={rid for x in items for rid in x.requirement_ids}
    for rid in sorted(req_ids-covered): out.append(IntegrityDiagnostic("uncovered-requirement",f"requirements/{rid}","covered by no item spec"))
    for x in items:
        unknown=sorted(set(x.requirement_ids)-req_ids)
        if unknown: out.append(IntegrityDiagnostic("unknown-requirement",f"items/{x.spec_id}",f"references unknown requirements {unknown}"))
        deps=sorted(set(x.depends_on)-set(specs))
        if deps: out.append(IntegrityDiagnostic("unknown-spec-dependency",f"items/{x.spec_id}",f"depends on unknown specs {deps}"))
    for t in tests:
        if t.spec_id and t.spec_id not in specs: out.append(IntegrityDiagnostic("unknown-test-spec",f"tests/{t.test_id}",f"targets unknown spec {t.spec_id}"))
        if t.criterion_id and t.criterion_id not in ac_owner: out.append(IntegrityDiagnostic("unknown-test-criterion",f"tests/{t.test_id}",f"realizes unknown criterion {t.criterion_id}"))
    tested={t.criterion_id for t in tests if t.criterion_id}
    for acid,rid in ac_owner.items():
        if acid not in tested: out.append(IntegrityDiagnostic("untested-criterion",f"requirements/{rid}/{acid}","has no test"))
    if traceability is not None:
        rows={r.requirement_id:r for r in traceability}
        for rid in sorted(req_ids-set(rows)): out.append(IntegrityDiagnostic("missing-matrix-row",f"traceability/{rid}","requirement has no traceability row"))
        for rid in sorted(set(rows)-req_ids): out.append(IntegrityDiagnostic("unknown-matrix-row",f"traceability/{rid}","row names an unknown requirement"))
        for r in requirements.requirements:
            row=rows.get(r.requirement_id)
            if not row: continue
            expected_specs=sorted(x.spec_id for x in items if r.requirement_id in x.requirement_ids)
            expected_acs=sorted(a.criterion_id for a in r.acceptance)
            expected_tests=sorted(t.test_id for t in tests if t.criterion_id in expected_acs or t.spec_id in expected_specs)
            for name,actual,expected in (("spec_ids",row.spec_ids,expected_specs),("acceptance_criterion_ids",row.acceptance_criterion_ids,expected_acs),("test_ids",row.test_ids,expected_tests)):
                if sorted(actual)!=expected: out.append(IntegrityDiagnostic("matrix-mismatch",f"traceability/{r.requirement_id}/{name}",f"stored={sorted(actual)} recomputed={expected}"))
    return out
