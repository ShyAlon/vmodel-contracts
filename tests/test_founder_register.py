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


def _item(item_id,stages=(),status='open',decision_required=False,**kw):
 return FounderDecision(item_id=item_id,data_class='other',question='Q?',owner='founder',scope='S',source='Interview',
  blocks=['x'],blocked_stages=list(stages),decision_required=decision_required,status=status,**kw)

def test_old_registers_without_stages_validate_and_never_stop_a_stage():
 old={'session_id':'s','items':[{'item_id':'a','data_class':'flows','question':'Q?','owner':'founder','scope':'S','source':'I','blocks':['user flows']}]}
 r=FounderRegister.model_validate(old)
 assert r.items[0].blocked_stages==[] and r.items[0].decision_required is False
 assert unresolved_before(r,'handoff')==[]

def test_unresolved_before_counts_items_blocking_this_or_an_earlier_stage():
 r=FounderRegister(session_id='s',items=[_item('srs-item',['srs']),_item('arch-item',['architecture']),_item('items-item',['items']),
  _item('done',['srs'],status='decided',decision='x'),_item('later',['tests'])])
 ids=lambda stage:[x.item_id for x in unresolved_before(r,stage)]
 assert ids('srs')==['srs-item']
 assert ids('architecture')==['srs-item','arch-item']
 assert ids('items')==['srs-item','arch-item','items-item']
 assert ids('tests')==['srs-item','arch-item','items-item','later']
 with pytest.raises(ValueError):unresolved_before(r,'prepare')

def test_deferral_resolves_an_ordinary_input_but_not_one_that_requires_a_decision():
 r=FounderRegister(session_id='s',items=[_item('plain',['items']),_item('must',['items'],decision_required=True)])
 deferred=apply_resolutions(r,[{'item_id':'plain','status':'deferred','reason':'Later'}],'founder')
 assert [x.item_id for x in unresolved_before(deferred,'items')]==['must']
 with pytest.raises(ValueError):apply_resolutions(r,[{'item_id':'must','status':'deferred','reason':'Later'}],'founder')
 decided=apply_resolutions(r,[{'item_id':'must','status':'decided','decision':'Postgres','reason':'Founder choice'}],'founder')
 assert [x.item_id for x in unresolved_before(decided,'items')]==['plain']
