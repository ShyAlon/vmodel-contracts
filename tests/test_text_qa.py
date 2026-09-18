

def test_srs_linter_names_exact_solution_classes_and_inventions():
    from vmodel_contracts.text_qa import srs_draft_findings
    draft={"functional":[{"requirement_id":"R-1","title":"API 47","statement":"POST /api/users returns 201 JSON using OAuth and AES-256",
      "acceptance":[{"criterion_id":"AC-1","statement":"Click the Submit button"}]}],"non_functional":[]}
    findings=srs_draft_findings(draft,"stakeholder needs secure user access")
    rules={f["rule"] for f in findings}
    assert {"named_technology","http_verb","http_status","url_path","json_shape","ui_widget","absent_from_interview"} <= rules
    assert any(f["span"]=="AES-256" and f["location"]=="R-1 field statement" for f in findings)


def test_linter_precision_algorithms_examples_and_ears():
    from vmodel_contracts.text_qa import srs_draft_findings
    clean={"functional":[{"requirement_id":"R-1","title":"Resolution Management",
      "statement":"When a user requests deletion, the system shall remove the record using an algorithm such as AES-256, Argon2, bcrypt, or SHA-256.","acceptance":[]}],"non_functional":[]}
    findings=srs_draft_findings(clean,"Each user needs Management Resolution deletion encryption")
    assert not [f for f in findings if f["rule"] in {"named_technology","http_verb","ears_pattern"}]
    assert not any(f["span"] in {"Each","Upon","Management","Resolution"} for f in findings)
    dirty={"functional":[{"requirement_id":"R-2","title":"Auth","statement":"the system should maybe handle users using OAuth","acceptance":[]}],"non_functional":[]}
    rules={f["rule"] for f in srs_draft_findings(dirty,"users need authentication")}
    assert "ears_pattern" in rules and "named_technology" in rules
    api={"functional":[{"requirement_id":"R-3","title":"Delete","statement":"The system shall expose DELETE /api/users","acceptance":[]}],"non_functional":[]}
    assert "http_verb" in {f["rule"] for f in srs_draft_findings(api,"delete users")}
