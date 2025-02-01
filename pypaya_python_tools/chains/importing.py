from typing import Optional, Any, Union
from pathlib import Path
from pypaya_python_tools.chains.base.chain import ObjectChain
from pypaya_python_tools.chains.base.operations import ChainOperationType
from pypaya_python_tools.chains.base.context import ChainContext
from pypaya_python_tools.chains.base.state import ChainState
from pypaya_python_tools.importing import (
    ImportManager,
    ImportSecurity,
    ImportingError
)


class ImportChain(ObjectChain[Any]):
    """Chain for import operations"""

    def __init__(
        self,
        value: Optional[Any] = None,
        context: Optional[ChainContext] = None,
        security: Optional[ImportSecurity] = None
    ):
        super().__init__(value=value, context=context)
        self._manager = ImportManager(security)

    def from_module(self, name: str, object_name: Optional[str] = None) -> "ImportChain":
        """Import from a module with optional object name"""
        self._ensure_state([ChainState.INITIAL])

        try:
            if object_name:
                self._value = self._manager.import_from_module(name, object_name)
            else:
                self._value = self._manager.import_module(name)

            self._state = ChainState.LOADED
            self._record_operation(
                ChainOperationType.IMPORT,
                "from_module",
                True,
                None,
                name,
                object_name
            )
        except ImportingError as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.IMPORT,
                "from_module",
                False,
                e,
                name,
                object_name
            )
            raise

        return self

    def from_file(self, path: Union[str, Path], object_name: Optional[str] = None) -> "ImportChain":
        """Import from a file with optional object name"""
        self._ensure_state([ChainState.INITIAL])

        try:
            self._value = self._manager.import_from_file(path, object_name)
            self._state = ChainState.LOADED
            self._record_operation(
                ChainOperationType.IMPORT,
                "from_file",
                True,
                None,
                str(path),
                object_name
            )
        except ImportingError as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.IMPORT,
                "from_file",
                False,
                e,
                str(path),
                object_name
            )
            raise

        return self

    def get_builtin(self, name: str) -> "ImportChain":
        """Import a builtin object"""
        self._ensure_state([ChainState.INITIAL])

        try:
            self._value = self._manager.import_builtin(name)
            self._state = ChainState.LOADED
            self._record_operation(
                ChainOperationType.IMPORT,
                "get_builtin",
                True,
                None,
                name
            )
        except ImportingError as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.IMPORT,
                "get_builtin",
                False,
                e,
                name
            )
            raise

        return self

    def get_class(self, name: str) -> "ImportChain":
        """Get a class from the imported module"""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            if not hasattr(self._value, name):
                raise ImportingError(f"No class named '{name}' in {self._value}")

            value = getattr(self._value, name)
            if not isinstance(value, type):
                raise ImportingError(f"'{name}' is not a class")

            self._value = value
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.IMPORT,
                "get_class",
                True,
                None,
                name
            )
        except Exception as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.IMPORT,
                "get_class",
                False,
                e,
                name
            )
            raise

        return self

    def get_object(self, name: str) -> "ImportChain":
        """Get any object from the imported module"""
        self._ensure_state([ChainState.LOADED, ChainState.MODIFIED])

        try:
            if not hasattr(self._value, name):
                raise ImportingError(f"No object named '{name}' in {self._value}")

            self._value = getattr(self._value, name)
            self._state = ChainState.MODIFIED
            self._record_operation(
                ChainOperationType.IMPORT,
                "get_object",
                True,
                None,
                name
            )
        except Exception as e:
            self._state = ChainState.FAILED
            self._last_error = e
            self._record_operation(
                ChainOperationType.IMPORT,
                "get_object",
                False,
                e,
                name
            )
            raise

        return self

    def to_import_chain(self) -> "ImportChain":
        return self

    def to_access_chain(self) -> "AccessChain":
        from pypaya_python_tools.chains.object_operation import OperationChain
        return OperationChain(value=self._value, context=self._context.clone())

    def to_execution_chain(self) -> "ExecutionChain":
        from pypaya_python_tools.chains.execution import ExecutionChain
        return ExecutionChain(value=self._value, context=self._context.clone())
