from vmodel_contracts import (AcceptanceCriterion, AcceptanceTest, ItemSpec, Requirement, RequirementSet, StakeholderNeed, StakeholderNeedsSet, TraceabilityEntry, validate_traceability_graph)

def fixture():
 n=StakeholderNeedsSet(session_id="s",needs=[StakeholderNeed(need_id="N-1",stakeholder="u",statement="x",kind="functional",intent_fields=[],intent_need_ids=["SN-1"])])
 r=Requirement(requirement_id="R-1",title="x",statement="System shall x",priority="must",kind="functional",acceptance=[AcceptanceCriterion(criterion_id="AC-1",statement="x")],need_ids=["N-1"],intent_fields=[])
 rs=RequirementSet(session_id="s",requirements=[r]); i=ItemSpec(spec_id="SPEC-1",slug="x",kind="api_surface",title="x",body_markdown="x",requirement_ids=["R-1"])
 t=AcceptanceTest(test_id="T-1",level="acceptance",criterion_id="AC-1",description="x",runner="http",definition={"preconditions":[],"steps":[],"expected_outcomes":[],"cleanup":[],"cases":[],"execution":{}})
 tr=TraceabilityEntry(requirement_id="R-1",spec_ids=["SPEC-1"],acceptance_criterion_ids=["AC-1"],test_ids=["T-1"])
 return n,rs,[i],[t],[tr]

def test_complete_graph_is_clean(): assert validate_traceability_graph(*fixture()) == []
def test_mutated_matrix_edge_is_named():
 x=fixture(); x[-1][0].test_ids=[]
 d=validate_traceability_graph(*x)
 assert [(e.code,e.path) for e in d]==[("matrix-mismatch","traceability/R-1/test_ids")]
def test_each_broken_layer_is_diagnosed():
 n,rs,items,tests,tr=fixture(); rs.requirements[0].need_ids=["N-X"];items[0].requirement_ids=[];tests[0].criterion_id="AC-X"
 codes={x.code for x in validate_traceability_graph(n,rs,items,tests,tr)}
 assert {"unknown-need","uncovered-requirement","unknown-test-criterion","untested-criterion","matrix-mismatch"} <= codes
