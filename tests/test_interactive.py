from uuid import uuid4
import pytest
from pydantic import ValidationError
from vmodel_contracts.interactive import (
    INTERACTIVE_PROTOCOL_VERSION, EngineSnapshot, EventType, InputKind, InputOption,
    InputRequest, InteractiveEvent, NextStep, ProcessStatus, ProtocolErrorCode,
)


def request(kind=InputKind.APPROVAL):
    return InputRequest(input_id=uuid4(),kind=kind,prompt="Approve intent?",options=[
        InputOption(value=1,label="Approve"),InputOption(value=0,label="Reject")])


def test_input_event_is_typed_and_versioned():
    pending=request()
    event=InteractiveEvent(event_id=uuid4(),session_id="s1",task_id="t1",phase_id=10,sequence=3,
        event_type=EventType.INPUT_REQUESTED,process_status=ProcessStatus.WAITING_INPUT,
        next_step=NextStep.WAIT_INPUT,input_request=pending)
    body=event.model_dump(mode="json")
    assert body["protocol_version"]==INTERACTIVE_PROTOCOL_VERSION
    assert body["event_type"]==EventType.INPUT_REQUESTED
    assert InteractiveEvent.model_validate(body)==event


def test_wrong_protocol_version_fails_before_control_flow():
    data={"protocol_version":2,"event_id":str(uuid4()),"session_id":"s","task_id":"t","phase_id":1,
          "sequence":1,"event_type":EventType.HEARTBEAT,"process_status":ProcessStatus.RUNNING,
          "next_step":NextStep.RUN}
    with pytest.raises(ValidationError):InteractiveEvent.model_validate(data)


def test_waiting_status_requires_numeric_wait_next_step():
    with pytest.raises(ValidationError):
        InteractiveEvent(event_id=uuid4(),session_id="s",task_id="t",phase_id=1,sequence=1,
            event_type=EventType.INPUT_REQUESTED,process_status=ProcessStatus.WAITING_INPUT,
            next_step=NextStep.RUN,input_request=request())


def test_text_input_cannot_smuggle_options():
    with pytest.raises(ValidationError):request(InputKind.TEXT)


def test_snapshot_has_no_prose_process_state():
    snapshot=EngineSnapshot(session_id="s",task_id="t",sequence=0,
        process_status=ProcessStatus.CREATED,next_step=NextStep.RUN)
    assert isinstance(snapshot.process_status,ProcessStatus)
    assert isinstance(snapshot.next_step,NextStep)


def test_choice_option_preserves_display_tradeoffs():
    option=InputOption(value='1',label='Progressive web app',summary='One installable web surface',
        advantages=['Fast deployment'],disadvantages=['Limited background behavior'])
    assert option.model_dump(mode='json')['advantages']==['Fast deployment']
    assert InputOption.model_validate(option.model_dump(mode='json'))==option


def test_route_change_payload_is_typed_and_usage_segment_kept():
    from vmodel_contracts.interactive import RouteChangePayload,ModelRouteSwitchRequest
    from vmodel_contracts.telemetry import StageTokenUsage
    payload=RouteChangePayload(actor_id='founder',from_route='ollama',to_route='deepseek',
        from_model_map={'probing':('ollama','phi4')},to_model_map={'probing':('deepseek','deepseek-flash')},route_version=1,session_sequence=3,idempotency_key=uuid4())
    event=InteractiveEvent(event_id=uuid4(),session_id='s',task_id='t',phase_id=0,sequence=3,
        event_type=EventType.ROUTE_CHANGED,process_status=ProcessStatus.WAITING_INPUT,next_step=NextStep.WAIT_INPUT,route_change=payload)
    assert InteractiveEvent.model_validate_json(event.model_dump_json()).route_change.route_version==1
    assert ModelRouteSwitchRequest(model_route='ollama',model='phi4',expected_sequence=3,expected_input_id=uuid4(),idempotency_key=uuid4(),actor_id='founder').model=='phi4'
    usage=StageTokenUsage(session_id='s',route_version=1,stage='probing',provider='deepseek',model='deepseek-flash',
        prompt_tokens=12,completion_tokens=5,price_per_mtok_prompt_usd=.3,price_per_mtok_completion_usd=1.2)
    assert StageTokenUsage.model_validate_json(usage.model_dump_json()).route_version==1
    with pytest.raises(ValidationError):
        InteractiveEvent(event_id=uuid4(),session_id='s',task_id='t',phase_id=0,sequence=3,
          event_type=EventType.ROUTE_CHANGED,process_status=ProcessStatus.WAITING_INPUT,next_step=NextStep.WAIT_INPUT)
