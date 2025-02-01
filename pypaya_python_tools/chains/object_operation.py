from typing import Any, Optional
from pypaya_python_tools.chains.base.chain import ObjectChain
from pypaya_python_tools.chains.base.context import ChainContext
from pypaya_python_tools.chains.base.operations import ChainOperationType
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.object_operations.definitions import Operation, OperationType
from pypaya_python_tools.object_operations.manager import AccessManager
from pypaya_python_tools.object_operations.security import OperationSecurity
from pypaya_python_tools.object_operations.exceptions import OperationError


class OperationChain(ObjectChain[Any]):
    """Chain for object operations"""

    def __init__(
            self,
            value: Optional[Any] = None,
            context: Optional[ChainContext] = None,
            security: Optional[OperationSecurity] = None
    ):
        super().__init__(value=value, context=context)
        self._manager = AccessManager(security)

    def get_attribute(self, name: str, default: Any = None) -> "OperationChain":
        """Get an attribute from the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.GET_ATTRIBUTE,
                args=(name, default)
            )
            self._value = self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "get_attribute",
                True,
                None,
                name=name,
                default=default
            )
        except Exception as e:
            self._handle_error("get_attribute", e, name=name, default=default)

        return self

    def set_attribute(self, name: str, value: Any) -> "OperationChain":
        """Set an attribute value on the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.SET_ATTRIBUTE,
                args=(name, value)
            )
            self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "set_attribute",
                True,
                None,
                name=name,
                value=value
            )
        except Exception as e:
            self._handle_error("set_attribute", e, name=name, value=value)

        return self

    def del_attribute(self, name: str) -> "OperationChain":
        """Delete an attribute from the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.DEL_ATTRIBUTE,
                args=(name,)
            )
            self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "del_attribute",
                True,
                None,
                name=name
            )
        except Exception as e:
            self._handle_error("del_attribute", e, name=name)

        return self

    def call(self, *args: Any, **kwargs: Any) -> "OperationChain":
        """Call the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.CALL,
                args=args,
                kwargs=kwargs
            )
            self._value = self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "call",
                True,
                None,
                args=args,
                kwargs=kwargs
            )
        except Exception as e:
            self._handle_error("call", e, args=args, kwargs=kwargs)

        return self

    def instantiate(self, *args: Any, **kwargs: Any) -> "OperationChain":
        """Instantiate the current class."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.INSTANTIATE,
                args=args,
                kwargs=kwargs
            )
            self._value = self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "instantiate",
                True,
                None,
                args=args,
                kwargs=kwargs
            )
        except Exception as e:
            self._handle_error("instantiate", e, args=args, kwargs=kwargs)

        return self

    def get_item(self, key: Any) -> "OperationChain":
        """Get an item from the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.GET_ITEM,
                args=(key,)
            )
            self._value = self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "get_item",
                True,
                None,
                key=key
            )
        except Exception as e:
            self._handle_error("get_item", e, key=key)

        return self

    def set_item(self, key: Any, value: Any) -> "OperationChain":
        """Set an item in the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.SET_ITEM,
                args=(key, value)
            )
            self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "set_item",
                True,
                None,
                key=key,
                value=value
            )
        except Exception as e:
            self._handle_error("set_item", e, key=key, value=value)

        return self

    def del_item(self, key: Any) -> "OperationChain":
        """Delete an item from the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(
                type=OperationType.DEL_ITEM,
                args=(key,)
            )
            self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "del_item",
                True,
                None,
                key=key
            )
        except Exception as e:
            self._handle_error("del_item", e, key=key)

        return self

    def iterate(self) -> "OperationChain":
        """Get an iterator for the current object."""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            access = Operation(type=OperationType.ITERATE)
            self._value = self._manager.access_object(self._value, access)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.ACCESS,
                "iterate",
                True,
                None
            )
        except Exception as e:
            self._handle_error("iterate", e)

        return self

    def _handle_error(self, operation: str, error: Exception, **kwargs) -> None:
        """Handle operation errors consistently."""
        self._state = ChainState.FAILED
        self._last_error = error
        self._record_operation(
            ChainOperationType.ACCESS,
            operation,
            False,
            error,
            **kwargs
        )
        raise OperationError(f"{operation} failed: {str(error)}") from error

    def to_import_chain(self) -> "ImportChain":
        from pypaya_python_tools.chains.importing import ImportChain
        return ImportChain(value=self._value, context=self._context.clone())

    def to_access_chain(self) -> "OperationChain":
        return self

    def to_execution_chain(self) -> "ExecutionChain":
        from pypaya_python_tools.chains.execution import ExecutionChain
        return ExecutionChain(value=self._value, context=self._context.clone())
