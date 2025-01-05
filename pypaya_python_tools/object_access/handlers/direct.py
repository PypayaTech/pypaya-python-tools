from typing import Any
from pypaya_python_tools.object_access.definitions import AccessType, ObjectAccess
from pypaya_python_tools.object_access.handlers.base import AccessHandler, AccessResult


class DirectHandler(AccessHandler):
    """Handles direct object access without modifications."""

    def can_handle(self, obj: Any, access: ObjectAccess) -> bool:
        return access.type == AccessType.DIRECT

    def handle(self, obj: Any, access: ObjectAccess) -> AccessResult:
        return AccessResult(
            obj,
            metadata={"type": type(obj).__name__}
        )
