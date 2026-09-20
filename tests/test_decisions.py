import json
from vmodel_contracts.decisions import founder_decision,binary_decision,emit_decision

def test_shared_decision_contract_and_wire_event(capsys):
    d=founder_decision('srs-review','Review SRS','What next?',[{'value':'a','label':'Accept','summary':'Continue'},{'value':'f','label':'Feedback'}])
    emit_decision(d);line=capsys.readouterr().err.strip()
    assert json.loads(line.removeprefix('REQUIRE_EVENT '))==d and d['type']=='founder_decision'

def test_binary_decision_uses_machine_values():
    d=binary_decision('intent','Approve','Approve?')
    assert [(o['value'],o['label']) for o in d['options']]==[('y','Approve'),('n','Reject')]
