"""Revision-bound candidate review. Semantic acceptance never bypasses schemas."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator

def digest(value)->str:
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

class ReviewModel(BaseModel):
    model_config=ConfigDict(extra='forbid')

class SemanticFinding(ReviewModel):
    finding_id:str=Field(min_length=1,max_length=200)
    item_id:str=Field(min_length=1,max_length=200)
    path:list[str|int]=Field(min_length=1,max_length=20)
    rule:str=Field(min_length=1,max_length=200)
    reason:str=Field(min_length=1,max_length=2000)
    kind:Literal['semantic','structural']='semantic'
    original:object

class ItemReviewDecision(ReviewModel):
    item_id:str=Field(min_length=1,max_length=200)
    action:Literal['remove','replace','accept']
    replacement:object|None=None
    actor:str=Field(min_length=1,max_length=240)
    rationale:str=Field(default='',max_length=7000)
    @model_validator(mode='after')
    def replacement_required(self):
        if self.action=='replace' and self.replacement is None:raise ValueError('replacement is required')
        if self.action!='replace' and self.replacement is not None:raise ValueError('replacement applies only to replace')
        return self

class SemanticReview(ReviewModel):
    version:Literal[1]=1
    session_id:str=Field(min_length=1,max_length=240)
    phase:str=Field(min_length=1,max_length=40)
    revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    candidate:dict|list
    findings:list[SemanticFinding]=Field(max_length=1000)
    decisions:list[ItemReviewDecision]=Field(default_factory=list,max_length=1000)
    @model_validator(mode='after')
    def bound(self):
        basis={'session_id':self.session_id,'phase':self.phase,'candidate':self.candidate,'findings':[f.model_dump() for f in self.findings]}
        if digest(basis)!=self.revision:raise ValueError('semantic review revision does not match evidence')
        ids=[f.finding_id for f in self.findings]
        if len(set(ids))!=len(ids):raise ValueError('duplicate finding ids')
        decision_ids=[d.item_id for d in self.decisions]
        if len(set(decision_ids))!=len(decision_ids):raise ValueError('duplicate item decisions')
        for d in self.decisions:
            relevant=[f for f in self.findings if f.item_id==d.item_id]
            if not relevant:raise ValueError('decision item does not belong to review')
            if any(f.kind=='structural' for f in relevant) and d.action=='accept':raise ValueError('structural failures cannot be accepted')
        for f in self.findings:
            value=self.candidate
            try:
                for part in f.path:
                    if isinstance(part,bool) or isinstance(value,list) and (not isinstance(part,int) or part<0):raise ValueError('invalid candidate path')
                    value=value[part]
            except (KeyError,IndexError,TypeError) as exc:raise ValueError('finding path is not in candidate') from exc
            if value!=f.original:raise ValueError('finding original does not match candidate path')
        return self

    def resolved_candidate(self,validator):
        """Require all item decisions; validate the entire result after edits."""
        decisions={d.item_id:d for d in self.decisions}
        if set(decisions)!={f.item_id for f in self.findings}:raise ValueError('unresolved review items')
        result=deepcopy(self.candidate)
        paths={}
        for finding in self.findings:
            key=tuple(finding.path)
            if key in paths and paths[key]!=finding.item_id:raise ValueError('conflicting item paths')
            paths[key]=finding.item_id
        for path in paths:
            if any(path[:len(other)]==other for other in paths if len(other)<len(path)):
                raise ValueError('overlapping review item paths')
        # Descending indices keep removals from shifting sibling list paths.
        for path,item_id in sorted(paths.items(),key=lambda p:tuple((1,x) if isinstance(x,int) else (0,x) for x in p[0]),reverse=True):
            decision=decisions[item_id]
            if decision.action=='accept':continue
            parent=result
            for part in path[:-1]:parent=parent[part]
            if decision.action=='remove':del parent[path[-1]]
            else:parent[path[-1]]=deepcopy(decision.replacement)
        validator(result)
        return result

def make_review(session_id:str,phase:str,candidate:dict|list,findings:list[dict])->SemanticReview:
    basis={'session_id':session_id,'phase':phase,'candidate':deepcopy(candidate),
           'findings':[SemanticFinding.model_validate(f).model_dump() for f in findings]}
    return SemanticReview.model_validate({**basis,'revision':digest(basis)})
