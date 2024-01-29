from __future__ import annotations
from typing import TYPE_CHECKING

from desim.objects.conveyor.core import Conveyor

if TYPE_CHECKING:
    import desim.objects.stopper
    from desim.objects.stopper.core import Stopper
    import desim.objects.system
    import desim.events_manager


class ExternalFunctionController:
    def __init__(self):
        self.functions_repository: dict[
            str,
            list[desim.events_manager.CustomEventListener],
        ] = {}

    def register_event(
        self,
        id: str,
        event: desim.events_manager.CustomEventListener,
    ):
        if id not in self.functions_repository:
            self.functions_repository[id] = []
        self.functions_repository[id] += [event]

    def external_function(self, context: Stopper | Conveyor):
        if context.id not in self.functions_repository:
            return
        for function in self.functions_repository[context.id]:
            function(context)
