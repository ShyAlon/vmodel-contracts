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
