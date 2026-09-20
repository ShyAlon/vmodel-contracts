"""Code-owned contracts for every blocking human decision across V-model CLIs."""
from __future__ import annotations
import json
from typing import Any,Iterable


def founder_decision(decision_id:str,title:str,prompt:str,options:Iterable[dict[str,Any]],*,
                     rationale_required:bool=False,rationale_label:str|None=None,
                     answer_format:str='<value>',context:dict[str,Any]|None=None)->dict[str,Any]:
    rows=[]
    for option in options:
        row={key:option[key] for key in ('value','label','summary','advantages','disadvantages') if key in option}
        if not str(row.get('value','')).strip() or not str(row.get('label','')).strip():raise ValueError('decision options require value and label')
        rows.append(row)
    if not rows:raise ValueError('founder decision requires options')
    result={'type':'founder_decision','decision_id':decision_id,'title':title,'prompt':prompt,'options':rows,
            'rationale_required':rationale_required,'answer_format':answer_format}
    if rationale_label:result['rationale_label']=rationale_label
    if context:result['context']=context
    return result


def binary_decision(decision_id:str,title:str,prompt:str,*,context:dict[str,Any]|None=None)->dict[str,Any]:
    return founder_decision(decision_id,title,prompt,[
        {'value':'y','label':'Approve','summary':'Accept this artifact and continue.'},
        {'value':'n','label':'Reject','summary':'Do not approve; stop before the next phase.'}],context=context)


def emit_decision(decision:dict[str,Any],*,stream=None)->None:
    import sys
    print('REQUIRE_EVENT '+json.dumps(decision,separators=(',',':')),file=stream or sys.stderr,flush=True)
