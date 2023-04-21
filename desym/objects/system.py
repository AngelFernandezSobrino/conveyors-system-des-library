from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Dict

if TYPE_CHECKING:
    import desym.objects.stopper.core
    from desym.objects.stopper.core import Stopper

SystemDescription = Dict[Stopper.StopperId, desym.objects.stopper.core.StopperDescription]

SimulationData = Dict[Stopper.StopperId, Stopper]
