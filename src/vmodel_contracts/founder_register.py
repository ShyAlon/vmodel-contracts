"""Open founder inputs and advisories survive every handoff as explicit data."""
from typing import Literal
from pydantic import Field,model_validator
from .semantic_review import ReviewModel

class FounderDecision(ReviewModel):
    item_id:str=Field(min_length=1,max_length=200)
    data_class:Literal['content','flows','styling','error_states','empty_states','accessibility','deployment','other']
    question:str=Field(min_length=1,max_length=2000)
    owner:str=Field(min_length=1,max_length=240)
    status:Literal['open','deferred','decided']='open'
    scope:str=Field(min_length=1,max_length=1000)
    source:str=Field(min_length=1,max_length=1000)
    source_turns:list[int]=Field(default_factory=list)
    blocks:list[str]=Field(default_factory=list)
    decision:str|None=None
    reason:str|None=None

    @model_validator(mode='after')
    def explicit_status(self):
        if self.status=='decided' and not (self.decision or '').strip():raise ValueError('decided register entry requires an answer')
        if self.status!='decided' and self.decision:raise ValueError('open or deferred entry cannot carry a decision')
        return self

class ConstraintAdvisory(ReviewModel):
    advisory_id:str=Field(min_length=1,max_length=200)
    advisory_class:Literal['rights','real_device','other']
    statement:str=Field(min_length=1,max_length=2000)
    owner:str=Field(min_length=1,max_length=240)
    status:Literal['open','verified','not_applicable']='open'
    source:str=Field(min_length=1,max_length=1000)
    affected_ids:list[str]=Field(default_factory=list)
    validation_expectation:str=Field(min_length=1,max_length=2000)

class FounderRegister(ReviewModel):
    version:Literal[1]=1
    session_id:str=Field(min_length=1,max_length=240)
    items:list[FounderDecision]=Field(default_factory=list,max_length=1000)
    advisories:list[ConstraintAdvisory]=Field(default_factory=list,max_length=1000)

    @model_validator(mode='after')
    def unique_ids(self):
        if len({x.item_id for x in self.items})!=len(self.items):raise ValueError('duplicate founder input IDs')
        if len({x.advisory_id for x in self.advisories})!=len(self.advisories):raise ValueError('duplicate advisory IDs')
        return self

class FounderInputResolution(ReviewModel):
    item_id:str=Field(min_length=1,max_length=200)
    status:Literal['decided','deferred']
    decision:str|None=None
    reason:str=Field(min_length=1,max_length=7000)
    @model_validator(mode='after')
    def explicit_decision(self):
        if self.status=='decided' and not (self.decision or '').strip():raise ValueError('a decided input requires the founder answer')
        if self.status=='deferred' and self.decision:raise ValueError('deferral is not a decision')
        return self

def apply_resolutions(register:FounderRegister,resolutions:list[dict],actor:str)->FounderRegister:
    values=register.model_dump();known={x['item_id']:x for x in values['items']};seen=set()
    for raw in resolutions:
        resolution=FounderInputResolution.model_validate(raw)
        if resolution.item_id in seen or resolution.item_id not in known:raise ValueError('unknown or repeated founder input')
        seen.add(resolution.item_id);item=known[resolution.item_id]
        item.update(status=resolution.status,decision=resolution.decision,reason=resolution.reason,owner=actor)
    return FounderRegister.model_validate(values)
