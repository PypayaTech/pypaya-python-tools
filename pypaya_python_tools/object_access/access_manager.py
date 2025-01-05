from typing import Dict, Any
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.importing.security import SecurityContext, DEFAULT_SECURITY
from pypaya_python_tools.object_access.exceptions import AccessError
from pypaya_python_tools.object_access.handlers.base import AccessHandler
from pypaya_python_tools.object_access.handlers.instantiate import InstantiateHandler
from pypaya_python_tools.object_access.handlers.call import CallHandler
from pypaya_python_tools.object_access.handlers.attribute import AttributeHandler
from pypaya_python_tools.object_access.handlers.direct import DirectHandler


class AccessManager:
    """Manages object access operations."""

    def __init__(self, security_context: SecurityContext = DEFAULT_SECURITY):
        self.security = security_context
        self.handlers: Dict[AccessType, AccessHandler] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default access handlers."""
        self.register_handler(AccessType.INSTANTIATE, InstantiateHandler(self.security))
        self.register_handler(AccessType.CALL, CallHandler(self.security))
        self.register_handler(AccessType.GET, AttributeHandler(self.security))
        self.register_handler(AccessType.SET, AttributeHandler(self.security))
        self.register_handler(AccessType.DIRECT, DirectHandler(self.security))

    def register_handler(self, access_type: AccessType, handler: AccessHandler) -> None:
        """Register a new access handler."""
        if not isinstance(handler, AccessHandler):
            raise TypeError(f"Expected AccessHandler, got {type(handler)}")
        self.handlers[access_type] = handler

    def access_object(self, obj: Any, access: ObjectAccess) -> Any:
        """Access object according to specification."""
        handler = self.handlers.get(access.type)
        if not handler:
            raise AccessError(f"No handler for access type: {access.type}")

        if not handler.can_handle(obj, access):
            raise AccessError(
                f"Handler for {access.type} cannot handle this object"
            )

        result = handler.handle(obj, access)
        return result.value
