from __future__ import annotations

from typing import Dict
from typing import TYPE_CHECKING

import sim.objects.stopper

SystemDescription = Dict[str, sim.objects.stopper.StopperInfo]

SimulationData = Dict[str, sim.objects.stopper.Stopper]
