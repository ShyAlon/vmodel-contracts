import json
import pytest
from pydantic import ValidationError
from vmodel_contracts import (ArtifactState as S, LifecycleTransition as T, LifecycleEvent,
    TRANSITION_TABLE, append_lifecycle_event, dot_diagram, mermaid_diagram)

BASE={"artifact_id":"architecture:s","artifact_kind":"architecture","actor":"spec-generator","reason":"test"}
GUARDS={
 T.BEGIN:{"producer_owns_artifact":1,"inputs_recorded":1,"anchor_recorded":1},
 T.CHECKPOINT:{"monotonic_progress":1,"same_inputs":1,"same_anchor":1},
 T.FINALIZE:{"schema_valid":1,"complete":1,"hashes_sealed":1},
 T.DEPENDENCY_CHANGED:{"changed_dependency":"baseline"},
 T.INVALIDATE:{"named_boundary":"architecture","downstream_closure_computed":1},
 T.RESTART:{"producer_rerun_started":1,"current_inputs":1},
 T.MIGRATE:{"approved_migrator":"0.16","source_hash":"old","source_version":"0.15","target_schema_valid":1},
 T.ADOPT_MIGRATION:{"canonical_storage_updated":1,"checkpoint_updated":1,"atomic":1,"hashes_agree":1},
 T.RESUME:{"named_next_artifact":"items","legal_outgoing_arc":"architecture->items"},
 T.DELETE:{"explicit_destructive_operation":1},
}

def event(t):
 sources,dest=TRANSITION_TABLE[t]
 return {**BASE,"transition":t,"from_state":next(iter(sources)),"to_state":dest,
         "content_hash":"sha256:x" if t==T.FINALIZE else None,"guard_evidence":GUARDS[t]}

def test_all_ten_transitions_accept_only_with_guards():
 assert len(TRANSITION_TABLE)==10
 for t in T:
  assert LifecycleEvent.model_validate(event(t)).to_state==TRANSITION_TABLE[t][1]
  bad=event(t);bad["guard_evidence"]={}
  with pytest.raises(ValidationError,match="guard missing"):
   LifecycleEvent.model_validate(bad)

def test_explicit_illegal_arcs_are_rejected():
 for t,source,dest in ((T.FINALIZE,S.COMPLETE,S.COMPLETE),(T.ADOPT_MIGRATION,S.STALE,S.COMPLETE),(T.RESUME,S.INVALIDATED,S.PARTIAL)):
  bad=event(t);bad.update(from_state=source,to_state=dest)
  with pytest.raises(ValidationError,match="illegal"):
   LifecycleEvent.model_validate(bad)

def test_jsonl_is_append_only_and_diagrams_cover_every_arc(tmp_path):
 path=tmp_path/"lifecycle.jsonl"
 append_lifecycle_event(path,event(T.BEGIN)); first=path.read_bytes()
 append_lifecycle_event(path,event(T.CHECKPOINT)); assert path.read_bytes().startswith(first)
 assert len(path.read_text().splitlines())==2
 for t in T:
  assert t.value in mermaid_diagram() and t.value in dot_diagram()
