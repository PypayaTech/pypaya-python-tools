from pypaya_python_tools.chains.base.context import ChainContext
from pypaya_python_tools.chains.base.operations import ChainOperationType


def test_context_initialization():
    context = ChainContext()
    assert len(context.operation_history) == 0
    assert len(context.modifications) == 0
    assert len(context.metadata) == 0


def test_record_operation():
    context = ChainContext()
    record = context.record_operation(
        ChainOperationType.IMPORT,
        "test_method",
        "arg1",
        kwarg1="value1"
    )

    assert len(context.operation_history) == 1
    assert context.operation_history[0] == ChainOperationType.IMPORT
    assert record.method_name == "test_method"
    assert record.args == ("arg1",)
    assert record.kwargs == {"kwarg1": "value1"}


def test_metadata():
    context = ChainContext()
    context.set_metadata("key1", "value1")
    assert context.get_metadata("key1") == "value1"
    assert context.get_metadata("nonexistent") is None
    assert context.get_metadata("nonexistent", "default") == "default"


def test_context_clone():
    context = ChainContext()
    context.set_metadata("key1", "value1")
    context.record_operation(ChainOperationType.IMPORT, "test")

    cloned = context.clone()
    assert cloned is not context
    assert cloned.metadata == context.metadata
    assert len(cloned.operation_history) == len(context.operation_history)
    assert len(cloned.modifications) == len(context.modifications)
