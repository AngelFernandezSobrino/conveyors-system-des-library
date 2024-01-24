from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict
    import desym.objects.stopper.core
    from desym.objects.stopper.core import Stopper

SystemDescription = Dict[
    desym.objects.stopper.TypeId, desym.objects.stopper.core.StopperDescription
]

SimulationData = Dict[desym.objects.stopper.TypeId, Stopper]
