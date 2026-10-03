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

def test_defer_after_decision_is_recorded_and_register_without_history_still_loads():
 d=apply_resolutions(_reg(),[{'item_id':'style','status':'decided','decision':'Blue','reason':'Calm'}],'ann')
 later=apply_resolutions(d,[{'item_id':'style','status':'deferred','reason':'Ask the designer'}],'ann')
 assert later.items[0].decision is None and [h.status for h in later.items[0].history]==['decided','deferred']
 legacy=d.model_dump(mode='json');[i.pop('history') for i in legacy['items']]
 assert FounderRegister.model_validate(legacy).items[0].history==[]
