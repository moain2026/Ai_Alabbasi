"""اختبارات آلة الحالات."""
import pytest
from state_machine import StateMachine, State, InvalidTransition


def test_initial_idle():
    sm = StateMachine()
    assert sm.state == State.IDLE


def test_valid_path():
    sm = StateMachine()
    sm.to(State.RUNNING)
    sm.to(State.INTERRUPTED)
    sm.to(State.RESUMING)
    sm.to(State.RUNNING)
    sm.to(State.DONE)
    assert sm.is_terminal()


def test_invalid_transition_raises():
    sm = StateMachine()
    with pytest.raises(InvalidTransition):
        sm.to(State.DONE)   # لا يمكن من IDLE مباشرة


def test_done_is_terminal():
    sm = StateMachine()
    sm.to(State.RUNNING)
    sm.to(State.DONE)
    assert sm.can(State.RUNNING) is False


def test_is_active():
    sm = StateMachine()
    assert sm.is_active() is False
    sm.to(State.RUNNING)
    assert sm.is_active() is True


def test_reset():
    sm = StateMachine()
    sm.to(State.RUNNING)
    sm.reset()
    assert sm.state == State.IDLE
    assert len(sm.history) == 1


def test_history_records():
    sm = StateMachine()
    sm.to(State.RUNNING)
    sm.to(State.FAILED)
    assert sm.history == [State.IDLE, State.RUNNING, State.FAILED]
