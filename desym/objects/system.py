from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Dict

if TYPE_CHECKING:
    import desym.objects.stopper.core

SystemDescription = Dict[desym.objects.stopper.core.StopperId, desym.objects.stopper.core.StopperDescription]

SimulationData = Dict[desym.objects.stopper.core.StopperId, desym.objects.stopper.core.Stopper]
