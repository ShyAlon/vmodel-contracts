"""Source snapshots are evidence, never a semantic-support verdict."""
import copy
import pytest
from vmodel_contracts.architecture import FounderDecisionCitation, ArchitectureDecision
from vmodel_contracts.semantic_review import digest
from vmodel_contracts import check_compatible, ContractVersionMismatch

SOURCE={'item_id':'FD-empty','status':'decided','decision':'Do nothing on unexpected page data.', 'reason':'Avoid intrusion.'}

def citation(source=SOURCE):
    return {'source_ref':source['item_id'],'source_revision':digest(source),'source':copy.deepcopy(source)}

def test_snapshot_binds_exact_source_and_never_mutates():
    raw=citation(); before=copy.deepcopy(raw)
    assert FounderDecisionCitation.model_validate(raw).model_dump()==raw
    assert raw==before
    for key,value in [('decision','Do something.'),('reason','A new reason.'),('status','open')]:
        changed=copy.deepcopy(raw);changed['source'][key]=value
        with pytest.raises(ValueError):FounderDecisionCitation.model_validate(changed)
    changed=citation();changed['source_ref']='FD-other'
    with pytest.raises(ValueError):FounderDecisionCitation.model_validate(changed)

def test_old_records_stay_unquoted_and_read_as_is():
    raw={'contract_version':'0.28.0','decision_id':'ADR-1','title':'Old','decision':'Old', 'rationale':'Old', 'driver':'simplicity','options_considered':[],'founder_decision_refs':['FD-empty']}
    parsed=ArchitectureDecision.model_validate(raw)
    assert parsed.founder_citations==[] and parsed.contract_version=='0.28.0'
    check_compatible(raw)
    with pytest.raises(ContractVersionMismatch):check_compatible({'contract_version':'0.29.0'},expecting='0.28.0')

def test_snapshot_ids_must_match_links_without_duplicate_evidence():
    raw={'decision_id':'ADR-1','title':'System choice','decision':'Implement behavior','rationale':'Why','driver':'simplicity','options_considered':[], 'founder_citations':[citation()]}
    with pytest.raises(ValueError):ArchitectureDecision.model_validate(raw)
    raw['founder_decision_refs']=['FD-empty']
    ArchitectureDecision.model_validate(raw)
    raw['founder_citations'].append(citation())
    with pytest.raises(ValueError):ArchitectureDecision.model_validate(raw)
