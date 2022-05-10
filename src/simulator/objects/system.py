from __future__ import annotations

from typing import Dict
from typing import TYPE_CHECKING

import simulator.objects.stopper

SystemDescription = Dict[str, simulator.objects.stopper.StopperInfo]

SimulationData = Dict[str, simulator.objects.stopper.Stopper]
