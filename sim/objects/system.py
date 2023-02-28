from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Dict

if TYPE_CHECKING:
    import sim.objects.stopper.core

SystemDescription = Dict[sim.objects.stopper.core.StopperId, sim.objects.stopper.core.StopperDescription]

SimulationData = Dict[sim.objects.stopper.core.StopperId, sim.objects.stopper.core.Stopper]
