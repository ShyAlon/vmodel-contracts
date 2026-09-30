import pytest
from vmodel_contracts.semantic_review import *

def fixture():
 return make_review('session','srs',{'items':[{'id':'1','text':'Click the button'},{'id':'2','text':'Other'}]},[{'finding_id':'f1','item_id':'1','path':['items',0],'rule':'solution_language','reason':'Names a UI widget rather than behavior','original':{'id':'1','text':'Click the button'}}])

def test_revision_and_original_are_bound():
 r=fixture();d=r.model_dump();d['candidate']['items'][0]['text']='changed'
 with pytest.raises(ValueError):SemanticReview.model_validate(d)

def test_unresolved_and_schema_invalid_never_pass():
 r=fixture()
 with pytest.raises(ValueError):r.resolved_candidate(lambda d:None)
 d=r.model_dump();d['decisions']=[{'item_id':'1','action':'accept','actor':'founder'}];r=SemanticReview.model_validate(d)
 def reject(d):raise ValueError('required field missing')
 with pytest.raises(ValueError):r.resolved_candidate(reject)
 assert r.resolved_candidate(lambda d:None)==r.candidate

def test_remove_replace_and_unknown_decision():
 d=fixture().model_dump();d['decisions']=[{'item_id':'1','action':'replace','replacement':{'id':'1','text':'Status is visible'},'actor':'founder'}]
 assert SemanticReview.model_validate(d).resolved_candidate(lambda d:None)['items'][0]['text']=='Status is visible'
 d['decisions'][0]={'item_id':'1','action':'remove','actor':'founder'}
 assert len(SemanticReview.model_validate(d).resolved_candidate(lambda d:None)['items'])==1
 d['decisions'][0]['item_id']='unrelated'
 with pytest.raises(ValueError):SemanticReview.model_validate(d)

def test_structural_accept_is_forbidden():
 d=fixture().model_dump();d['findings'][0]['kind']='structural';d['revision']=digest({k:d[k] for k in ('session_id','phase','candidate','findings')});d['decisions']=[{'item_id':'1','action':'accept','actor':'founder'}]
 with pytest.raises(ValueError):SemanticReview.model_validate(d)

def test_list_removal_order_and_overlapping_paths():
 r=make_review('s','intent',{'items':list(range(12))},[{'finding_id':str(i),'item_id':str(i),'path':['items',i],'rule':'test','reason':'Test','original':i} for i in (2,10)])
 d=r.model_dump();d['decisions']=[{'item_id':str(i),'action':'remove','actor':'founder'} for i in (2,10)]
 assert SemanticReview.model_validate(d).resolved_candidate(lambda d:None)['items']==[0,1,3,4,5,6,7,8,9,11]

def test_malformed_paths_fail_as_validation_errors():
 for path in (['missing'],['items',-1],['items','0'],['items',99],['items',True]):
  with pytest.raises(ValueError):make_review('s','srs',{'items':['x']},[{'finding_id':'f','item_id':'i','path':path,'rule':'test','reason':'Test','original':'x'}])
