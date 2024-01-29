from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict
    import desim.objects.stopper.core
    from desim.objects.stopper.core import Stopper

SystemDescription = Dict[
    desim.objects.stopper.StopperId, desim.objects.stopper.core.StopperDescription
]

SimulationData = Dict[desim.objects.stopper.StopperId, Stopper]
