from __future__ import annotations
from typing import TYPE_CHECKING, TypedDict


if TYPE_CHECKING:
    from desim.objects.stopper import StopperId, Stopper, StopperStateModel
    from desim.core import Simulation


class Cycle:
    ForeignStopper = TypedDict(
        "ForeignStopper", {"stopper": Stopper, "destiny_id": StopperId}
    )

    def __init__(self, stoppers: list[Stopper], core: Simulation) -> None:
        self.locked = False
        self.foreign_input_stoppers: list[Cycle.ForeignStopper] = []
        self.stoppers = stoppers
        self.core = core
        self.get_foreig_input_stoppers(core)
        pass

    def __repr__(self) -> str:
        return f"Cycle: {self.stoppers}"

    def __str__(self) -> str:
        return f"Cycle: {self.stoppers}"

    def max_population(cycle):
        return len(cycle.stoppers) - 1

    def population(cycle):
        population = 0
        for i in range(len(cycle.stoppers)):
            if (
                cycle.core.stoppers[cycle.stoppers[i].id].s.state.node
                != StopperStateModel.Node.REST
            ):
                population += 1

        return population

    def get_foreig_input_stoppers(self, core: Simulation):
        for stopper in self.stoppers:
            for system_stopper in core.stoppers.values():
                if (
                    system_stopper in stopper.input_conveyors
                    and system_stopper not in core.stoppers
                ):
                    self.foreign_input_stoppers.append(
                        {"stopper": system_stopper, "destiny_id": stopper.id}
                    )

    # def lock_cycle_stoppers(self):
    #     self.locker = True
    #     for foreign_stopper in self.foreign_input_stoppers:
    #         foreign_stopper["stopper"].input_events.graph_lock(
    #             [foreign_stopper["destiny_id"]]
    #         )

    # def unlock_cycle_stoppers(self):
    #     self.locked = False
    #     for foreign_stopper in self.foreign_input_stoppers:
    #         foreign_stopper["stopper"].input_events.graph_unlock(
    #             [foreign_stopper["destiny_id"]]
    #         )


class GraphAnalizer:
    def __init__(
        self,
        core: Simulation,
    ):
        # Dictionary with the output stoppers of each stopper that colide with a foreign cycle
        self.inputs_cycles_to_check: dict[
            Stopper.StopperId,
            dict[
                Stopper.StopperId,
                list[Cycle],
            ],
        ] = {}

        # Dictionary with the output stoppers of each stopper that colide with a foreign cycle
        self.outputs_cycles_to_check: dict[
            Stopper.StopperId,
            dict[
                Stopper.StopperId,
                list[Cycle],
            ],
        ] = {}

        self.stoppers = core.stoppers
        self.core = core

        self.visited: dict[Stopper.StopperId, bool] = {}
        self.stack: list[Stopper.StopperId] = []
        self.cycles: list[Cycle] = []
        self.path: list[Stopper] = []

        self.__find_cycles()
        self.__calculate_consideration_list_for_inputs()

    def __find_cycles(self):
        for stopper in self.stoppers.values():
            self.visited[stopper.id] = False

        self.__dfs(self.stoppers["PT01"])

    def __dfs(self, stopper: Stopper):
        self.visited[stopper.id] = True
        self.path.append(stopper)

        for output_stopper in stopper.output_conveyors.values():
            if output_stopper in self.path:
                cycle_start = self.path.index(output_stopper)
                self.cycles.append(Cycle(self.path[cycle_start:], self.core))
            else:
                if not self.visited[output_stopper.id]:
                    self.__dfs(output_stopper)
            # No else clause is needed since we don't need to do anything if we have already visited the node.

        self.path.pop()
        self.visited[stopper.id] = False

    # Calculate the consideration list. It has, for each stopper of the simulation, a dict for each input stopper with list of cycles where the stopper is present but the input stopper is not.
    def __calculate_consideration_list_for_inputs(self):
        for stopper in self.stoppers.values():
            for input_stopper in stopper.input_conveyors:
                for cycle in self.cycles:
                    if (
                        input_stopper not in cycle.stoppers
                        and stopper in cycle.stoppers
                    ):
                        if stopper.id not in self.inputs_cycles_to_check:
                            self.inputs_cycles_to_check[stopper.id] = {}
                        if (
                            input_stopper.id
                            not in self.inputs_cycles_to_check[stopper.id]
                        ):
                            self.inputs_cycles_to_check[stopper.id][
                                input_stopper.id
                            ] = [cycle]
                        elif (
                            cycle
                            not in self.inputs_cycles_to_check[stopper.id][
                                input_stopper.id
                            ]
                        ):
                            self.inputs_cycles_to_check[stopper.id][
                                input_stopper.id
                            ].append(cycle)

    # Calculate the consideration list. It has, for each stopper of the simulation, a dict for each output stopper with list of cycles where the output stopper is present but the stopper under consideration no.
    def __calculate_consideration_list_for_outputs(self):
        for stopper in self.stoppers.values():
            for output_stopper in stopper.output_conveyors:
                for cycle in self.cycles:
                    if (
                        stopper not in cycle.stoppers
                        and output_stopper in cycle.stoppers
                    ):
                        if stopper.id not in self.outputs_cycles_to_check:
                            self.outputs_cycles_to_check[stopper.id] = {}
                        if (
                            output_stopper.id
                            not in self.outputs_cycles_to_check[stopper.id]
                        ):
                            self.outputs_cycles_to_check[stopper.id][
                                output_stopper.id
                            ] = [cycle]
                        elif (
                            cycle
                            not in self.outputs_cycles_to_check[stopper.id][
                                output_stopper.id
                            ]
                        ):
                            self.outputs_cycles_to_check[stopper.id][
                                output_stopper.id
                            ].append(cycle)

    # It checks the population of the different cycles present in the graph representation of the simulation
    # If the population of a cycle is equal to the number of stoppers in the cycle less one, it locks all the stoppers that enter the cycle
    # That function is executed when requested by the stopper, different implementations can be considered.
    # In that case, the function is designed to be executed only by stopper present on input consideration list. It will check, for the requester stopper, if the population of the cycles where it is present is close to the limit of n-1 trays.

    def check_cycles_saturation(self):
        for cycle in self.cycles:
            if cycle.population() <= cycle.max_population():
                if cycle.locked:
                    cycle.unlock_cycle_stoppers()
            else:
                if not cycle.locked:
                    cycle.lock_cycle_stoppers()
