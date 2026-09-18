

def test_srs_linter_names_exact_solution_classes_and_inventions():
    from vmodel_contracts.text_qa import srs_draft_findings
    draft={"functional":[{"requirement_id":"R-1","title":"API 47","statement":"POST /api/users returns 201 JSON using OAuth and AES-256",
      "acceptance":[{"criterion_id":"AC-1","statement":"Click the Submit button"}]}],"non_functional":[]}
    findings=srs_draft_findings(draft,"stakeholder needs secure user access")
    rules={f["rule"] for f in findings}
    assert {"named_technology","http_verb","http_status","url_path","json_shape","ui_widget","absent_from_interview"} <= rules
    assert any(f["span"]=="AES-256" and f["location"]=="R-1 field statement" for f in findings)
