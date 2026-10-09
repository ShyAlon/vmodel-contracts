import pytest
from vmodel_contracts.text_qa import srs_draft_findings,normalize_comparison_text,SRS_COMMON_TERMS

def findings(text,source):
    return srs_draft_findings({'functional':[{'requirement_id':'R-1','title':'Test','statement':'The system shall '+text,'acceptance':[]}],'non_functional':[]},source)

def test_word_normalization_and_explicit_dictionary():
    assert normalize_comparison_text('  Ear-training  LESSONS ')=='ear training lessons'
    assert not findings('offer Ear-training lessons at a URL.', 'ear   training lessons')
    assert set(SRS_COMMON_TERMS)=={'url'}
    assert any(f['span']=='FooBar' for f in findings('use FooBar.', 'unrelated'))
    assert any(f['span']=='PDF' for f in findings('export PDF.', 'unrelated'))

@pytest.mark.parametrize('source',['2000 ms','200.5 ms','1200 ms','0.2 s','200 seconds','200 milliseconds','200','-200 ms','200%','200 MB'])
def test_numeric_unit_inventions_remain_strict(source):
    assert any(f['span']=='200' for f in findings('respond within 200 ms.',source))

@pytest.mark.parametrize('source',['200 ms','200ms','200   MS'])
def test_only_spacing_and_unit_case_are_normalized(source):
    assert not findings('respond within 200 ms.',source)

@pytest.mark.parametrize('candidate,source',[('2.5 ms','2.50 ms'),('200%','200'),('200','200.5'),('200','2000')])
def test_decimal_and_percent_exact(candidate,source):
    assert any(f['rule']=='absent_from_interview' for f in findings('respond within '+candidate+'.',source))

def test_checker_does_not_repair_ears():
    assert any(f['rule']=='ears_pattern' for f in srs_draft_findings({'functional':[{'requirement_id':'R-1','statement':'The system shall, respond.'}]},'respond'))

@pytest.mark.parametrize('candidate',['200ms','200 ms','-200 ms','+200 ms'])
def test_compact_and_signed_quantities_are_checked(candidate):
    assert any(f['rule']=='absent_from_interview' for f in findings('respond within '+candidate+'.','qualitative lag tolerance'))
    assert not findings('respond within '+candidate+'.',candidate)

@pytest.mark.parametrize('candidate,source',[('200 feet','200 meters'),('200 bytes','200 bits'),('2.5 cm','2.5 mm')])
def test_distance_and_size_units_cannot_borrow_numbers(candidate,source):
    assert any(f['rule']=='absent_from_interview' for f in findings('remain within '+candidate+'.',source))
    assert not findings('remain within '+candidate+'.',candidate)
