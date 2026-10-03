import pytest
from vmodel_contracts.founder_register import *

def test_explicit_decision_and_deferral_do_not_invent_answers():
 r=FounderRegister(session_id='s',items=[FounderDecision(item_id='style',data_class='styling',question='Style?',owner='founder',scope='UI',source='Interview',blocks=['UI'])])
 with pytest.raises(ValueError):apply_resolutions(r,[{'item_id':'style','status':'decided','reason':'Need a style'}],'founder')
 deferred=apply_resolutions(r,[{'item_id':'style','status':'deferred','reason':'Later'}],'founder')
 assert deferred.items[0].decision is None;assert deferred.items[0].blocks==['UI']
 decided=apply_resolutions(r,[{'item_id':'style','status':'decided','decision':'Blue and white','reason':'Calm'}],'founder')
 assert decided.items[0].decision=='Blue and white'

def _reg(**kw):
 return FounderRegister(session_id='s',items=[FounderDecision(item_id='style',data_class='styling',question='Style?',owner='founder',scope='UI',source='Interview',blocks=['UI'],**kw)])

def test_resolutions_append_history_and_current_state_is_the_latest_entry():
 r=_reg()
 assert r.items[0].history==[]
 d=apply_resolutions(r,[{'item_id':'style','status':'decided','decision':'Blue','reason':'Calm'}],'ann',now='2026-10-03T10:00:00+00:00')
 d2=apply_resolutions(d,[{'item_id':'style','status':'decided','decision':'Green','reason':'Changed my mind'}],'ben',now='2026-10-03T11:00:00+00:00')
 item=d2.items[0]
 assert [(h.actor,h.decision,h.at) for h in item.history]==[('ann','Blue','2026-10-03T10:00:00+00:00'),('ben','Green','2026-10-03T11:00:00+00:00')]
 assert (item.status,item.decision,item.reason)==('decided','Green','Changed my mind')
 assert d.items[0].decision=='Blue' and len(d.items[0].history)==1
 assert [h.owner_before for h in item.history]==['founder','ann']

def test_defer_after_decision_is_recorded_and_register_without_history_still_loads():
 d=apply_resolutions(_reg(),[{'item_id':'style','status':'decided','decision':'Blue','reason':'Calm'}],'ann')
 later=apply_resolutions(d,[{'item_id':'style','status':'deferred','reason':'Ask the designer'}],'ann')
 assert later.items[0].decision is None and [h.status for h in later.items[0].history]==['decided','deferred']
 legacy=d.model_dump(mode='json');[i.pop('history') for i in legacy['items']]
 assert FounderRegister.model_validate(legacy).items[0].history==[]

def _free():
 return FounderRegister(session_id='s',items=[FounderDecision(item_id='free',data_class='content',question='Tone?',owner='founder',scope='UI',source='Interview',blocks=[])])

def test_reason_is_optional_when_the_input_blocks_nothing_and_required_when_it_does():
 ok=apply_resolutions(_free(),[{'item_id':'free','status':'decided','decision':'Friendly'}],'ann')
 assert ok.items[0].decision=='Friendly' and ok.items[0].reason is None and ok.items[0].history[0].reason is None
 assert apply_resolutions(_free(),[{'item_id':'free','status':'deferred','reason':'  '}],'ann').items[0].reason is None
 with pytest.raises(ValueError,match='blocks later work'):apply_resolutions(_reg(),[{'item_id':'style','status':'decided','decision':'Blue'}],'ann')
 with pytest.raises(ValueError,match='blocks later work'):apply_resolutions(_reg(),[{'item_id':'style','status':'deferred','reason':' '}],'ann')
 with pytest.raises(ValueError):apply_resolutions(_free(),[{'item_id':'free','status':'decided','reason':'x'}],'ann')
