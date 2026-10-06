"""Open founder inputs and advisories survive every handoff as explicit data."""
from datetime import datetime,timezone
from typing import Literal
from pydantic import Field,model_validator
from .semantic_review import ReviewModel

STAGE_ORDER=('srs','architecture','items','tests','validation','handoff')
Stage=Literal['srs','architecture','items','tests','validation','handoff']

class FounderResolutionEntry(ReviewModel):
    """One resolution of an open input. Entries are only ever appended; the item's own
    status/decision/reason always mirror the latest entry."""
    at:str=Field(min_length=1,max_length=64)
    actor:str=Field(min_length=1,max_length=240)
    status:Literal['decided','deferred']
    decision:str|None=None
    reason:str|None=Field(default=None,max_length=7000)
    owner_before:str|None=Field(default=None,max_length=240)

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
    blocked_stages:list[Stage]=Field(default_factory=list,description="ADDED 0.25.0: pipeline stages that may not start while this input is unresolved. Empty keeps the older behavior: only the final handoff is blocked by `blocks`.")
    decision_required:bool=Field(default=False,description="ADDED 0.25.0: true when a deferral does not resolve this input; the founder must decide it.")
    decision:str|None=None
    reason:str|None=None
    history:list[FounderResolutionEntry]=Field(default_factory=list,max_length=1000)

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
    reason:str|None=Field(default=None,max_length=7000)
    @model_validator(mode='after')
    def explicit_decision(self):
        self.reason=(self.reason or '').strip() or None
        if self.status=='decided' and not (self.decision or '').strip():raise ValueError('a decided input requires the founder answer')
        if self.status=='deferred' and self.decision:raise ValueError('deferral is not a decision')
        return self

def apply_resolutions(register:FounderRegister,resolutions:list[dict],actor:str,now:str|None=None)->FounderRegister:
    at=now or datetime.now(timezone.utc).isoformat(timespec='seconds')
    values=register.model_dump();known={x['item_id']:x for x in values['items']};seen=set()
    for raw in resolutions:
        resolution=FounderInputResolution.model_validate(raw)
        if resolution.item_id in seen or resolution.item_id not in known:raise ValueError('unknown or repeated founder input')
        seen.add(resolution.item_id);item=known[resolution.item_id]
        if item.get('decision_required') and resolution.status=='deferred':raise ValueError('this input must be decided; deferring it does not resolve it')
        if item.get('blocks') and not resolution.reason:raise ValueError('a reason is required when the input blocks later work')
        entry={'at':at,'actor':actor,'status':resolution.status,'decision':resolution.decision,'reason':resolution.reason,'owner_before':item['owner']}
        item.update(status=resolution.status,decision=resolution.decision,reason=resolution.reason,owner=actor,history=[*item.get('history',[]),entry])
    return FounderRegister.model_validate(values)


def unresolved_before(register:FounderRegister,stage:str)->list[FounderDecision]:
    """Inputs that must be resolved before `stage` may start.

    An input counts when it blocks `stage` or any earlier stage and is still open,
    or deferred while a decision is required. Inputs with no blocked_stages never
    stop a stage (they only block the final handoff).
    """
    if stage not in STAGE_ORDER:raise ValueError(f'unknown stage {stage!r}')
    limit=STAGE_ORDER.index(stage)
    def pending(x:FounderDecision)->bool:
        return x.status=='open' or (x.status=='deferred' and x.decision_required)
    return [x for x in register.items if pending(x) and any(STAGE_ORDER.index(s)<=limit for s in x.blocked_stages)]
