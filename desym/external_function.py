from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import desym.objects.stopper
    from desym.objects.stopper.core import Stopper
    import desym.objects.system
    import desym.timed_events_manager


class StopperExternalFunctionController:
    def __init__(self):
        self.functions_repository: dict[
            desym.objects.stopper.TypeId,
            list[desym.timed_events_manager.CustomEventListener],
        ] = {}

    def register_event(
        self,
        stopper_id: desym.objects.stopper.TypeId,
        event: desym.timed_events_manager.CustomEventListener,
    ):
        if stopper_id not in self.functions_repository:
            self.functions_repository[stopper_id] = []
        self.functions_repository[stopper_id] += [event]

    def external_function(self, stopper: Stopper):
        for function in self.functions_repository[stopper.id]:
            function(stopper)
