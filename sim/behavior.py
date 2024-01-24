from desym.timed_events_manager import CustomEventListener
import sim.behavior_functions

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import desym.objects.stopper
    import desym.core


class BaselineBehaviourController:
    input_pt01_at_rest_function = CustomEventListener(
        sim.behavior_functions.pt01_container_input, (), {}
    )
    external_container_input_function = CustomEventListener(
        sim.behavior_functions.external_container_input, (), {}
    )

    external_functions = {0: [external_container_input_function]}

    calculate_busyness_function = CustomEventListener(
        sim.behavior_functions.calculate_busyness
    )

    for i in range(10, 50000, 100):
        external_functions[i] = [calculate_busyness_function]

    stopper_external_functions: dict[
        desym.objects.stopper.StopperId, list[CustomEventListener]
    ] = {
        "DIR04": [
            CustomEventListener(sim.behavior_functions.delay, (), {"time": 10}),
            CustomEventListener(sim.behavior_functions.empty_tray),
        ],
        "PT06": [
            CustomEventListener(sim.behavior_functions.delay, (), {"time": 10}),
            CustomEventListener(
                sim.behavior_functions.fill_tray_three_products,
            ),
        ],
        "PT05": [
            CustomEventListener(sim.behavior_functions.bifurcation_pt05),
        ],
        "PT09": [
            CustomEventListener(sim.behavior_functions.bifurcation_pt09),
        ],
        "PT10": [CustomEventListener(sim.behavior_functions.bifurcation_pt10)],
        "PT16": [CustomEventListener(sim.behavior_functions.bifurcation_pt16)],
        "DIR17": [
            CustomEventListener(sim.behavior_functions.delay, (), {"time": 10}),
            CustomEventListener(sim.behavior_functions.process_01),
        ],
        "DIR13": [
            CustomEventListener(sim.behavior_functions.delay, (), {"time": 10}),
            CustomEventListener(sim.behavior_functions.process_02),
        ],
        "DIR19": [
            CustomEventListener(sim.behavior_functions.delay, (), {"time": 10}),
            CustomEventListener(sim.behavior_functions.process_03),
        ],
    }

    return_rest_functions = {"PT01": [input_pt01_at_rest_function]}
