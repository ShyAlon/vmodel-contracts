import pytest
from vmodel_contracts.founder_register import *

def test_explicit_decision_and_deferral_do_not_invent_answers():
 r=FounderRegister(session_id='s',items=[FounderDecision(item_id='style',data_class='styling',question='Style?',owner='founder',scope='UI',source='Interview',blocks=['UI'])])
 with pytest.raises(ValueError):apply_resolutions(r,[{'item_id':'style','status':'decided','reason':'Need a style'}],'founder')
 deferred=apply_resolutions(r,[{'item_id':'style','status':'deferred','reason':'Later'}],'founder')
 assert deferred.items[0].decision is None;assert deferred.items[0].blocks==['UI']
 decided=apply_resolutions(r,[{'item_id':'style','status':'decided','decision':'Blue and white','reason':'Calm'}],'founder')
 assert decided.items[0].decision=='Blue and white'
