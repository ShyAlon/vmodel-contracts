import hashlib,pytest
from vmodel_contracts.handoff import CodingHandoff

def test_versioned_handoff_checks_exact_files_and_checksums():
 payload={'session_id':'s','files':{'README.md':'hello'},'sha256':{'README.md':hashlib.sha256(b'hello').hexdigest()}}
 assert CodingHandoff.model_validate(payload).version==1
 for changes in ({'sha256':{}},{'files':{'README.md':'changed'}},{'version':2}):
  with pytest.raises(ValueError):CodingHandoff.model_validate({**payload,**changes})

def test_new_contracts_export_schemas():
 from vmodel_contracts.export_schema import all_models
 models=all_models()
 assert {'CodingHandoff','SemanticReview','FounderRegister','InputResponse'}.issubset(models)
 for name in ('CodingHandoff','SemanticReview','FounderRegister','InputResponse'):assert models[name].model_json_schema()['type']=='object'
