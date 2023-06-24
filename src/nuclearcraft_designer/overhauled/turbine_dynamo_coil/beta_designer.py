"""NuclearCraft: Overhauled turbine dynamo coil configuration designer."""

from . import DynamoCoil, DYNAMO_COIL_TYPES
from ... import utils, common

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None


class DynamoCoilConfigurationDesigner:
    """Designs NuclearCraft: Overhauled turbine dynamo coil configurations."""
    def __init__(
            self,
            dynamo_coil_types: list[DynamoCoil] = DYNAMO_COIL_TYPES,
            scaling_factor: int = 2
    ) -> None:
        """Constructs a DynamoCoilConfigurationDesigner object.

        :param dynamo_coil_types: A list of dynamo coil types.
        :param scaling_factor: The number of digits to scale decimals by.
        """
        self.dynamo_coil_types = dynamo_coil_types
        self.scaling_factor = scaling_factor
        self.sc = utils.scaled_calculator.ScaledCalculator(self.scaling_factor)

    def ids_to_coils(self, sequence: list[int]) -> common.multi_sequence.MultiSequence[DynamoCoil]:
        """Converts a sequence of IDs to a sequence of rotor blades.

        :param sequence: A sequence of IDs.
        :return: A sequence of rotor blades.
        """
        side_length = round(len(sequence) ** (1 / 2))
        return common.multi_sequence.MultiSequence([
            self.dynamo_coil_types[i] if i >= 0 else None
            for i in sequence
        ], (side_length, side_length))

    def coil_attributes(self, model: cp_model.CpModel, n_coils: int) -> tuple[
        common.multi_sequence.MultiSequence[cp_model.IntVar], list[cp_model.IntVar]
    ]:
        """Registers dynamo coils as well as their attributes to the model.

        :param model: The model to register dynamo coils to.
        :param n_coils: The number of coils to register.
        :return: Two lists of IntVars, representing the coils and their conductivities.
        """
        coils = [
            model.NewIntVar(0, len(self.dynamo_coil_types) - 1, "coil_{0:d}".format(i))
            for i in range(n_coils)
        ]

        conductivities = [
            model.NewIntVar(-2 ** 31, 2 ** 31 - 1, "conductivity_{0:d}".format(i))
            for i in range(n_coils)
        ]
        for coil, conductivity in zip(coils, conductivities):
            model.AddElement(coil, [
                round(coil_type.conductivity * (10 ** self.scaling_factor))
                for coil_type in self.dynamo_coil_types
            ], conductivity)

        side_length = round(n_coils ** (1 / 2))
        return common.multi_sequence.MultiSequence(coils, (side_length, side_length)), conductivities

    def total_efficiency(self, model: cp_model.CpModel, conductivities: list[cp_model.IntVar]) -> cp_model.IntVar:
        """Calculates the total efficiency of a dynamo coil configuration.

        :param model: The optimization model.
        :param conductivities: A list of IntVars representing each coil's conductivity.
        :return: An IntVar representing the total efficiency.
        """
        total_efficiencies = [
            model.NewIntVar(0, 2 ** 31 - 1, "total_efficiency_{0:d}".format(i))
            for i in range(len(conductivities))
        ]
        n_coils = [
            model.NewIntVar(0, len(conductivities), "n_coils_{0:d}".format(i))
            for i in range(len(conductivities))
        ]
        is_coil = [
            model.NewBoolVar("is_coil_{0:d}".format(i))
            for i in range(len(conductivities))
        ]
        for i in range(len(conductivities)):
            model.Add(conductivities[i] >= 0).OnlyEnforceIf(is_coil[i])
            model.Add(conductivities[i] < 0).OnlyEnforceIf(is_coil[i].Not())

            n_coils_prev = n_coils[i - 1] if i > 0 else 0
            model.Add(n_coils[i] == n_coils_prev + 1).OnlyEnforceIf(is_coil[i])
            model.Add(n_coils[i] == n_coils_prev).OnlyEnforceIf(is_coil[i].Not())

            total_efficiencies_prev = total_efficiencies[i - 1] if i > 0 else 0
            model.Add(total_efficiencies[i] == total_efficiencies_prev + conductivities[i]).OnlyEnforceIf(is_coil[i])
            model.Add(total_efficiencies[i] == total_efficiencies_prev).OnlyEnforceIf(is_coil[i].Not())

        n_coils_ = model.NewIntVar(1, len(conductivities), "n_coils")
        model.Add(n_coils_ == n_coils[-1])

        total_efficiency = model.NewIntVar(0, 2 ** 31 - 1, "total_efficiency")
        model.AddDivisionEquality(total_efficiency, total_efficiencies[-1], n_coils_)

        return total_efficiency

    def design(
            self,
            side_length: int,
            shaft_width: int,
            type_limits: dict[str, int],
            symmetric: bool = False,
            time_limit: float = None
    ) -> tuple[int, common.multi_sequence.MultiSequence[DynamoCoil]]:
        """Designs the optimal dynamo coil configuration if possible.

        :param side_length: The side length of the turbine.
        :param shaft_width: The width of the rotor shaft.
        :param type_limits: The maximum number of each type of dynamo coil.
        :param symmetric: Whether to force the result to be symmetric.
        :param time_limit: The maximum time in seconds to run for.
        :return: The status as well as a dynamo coil configuration.
        """
        model = cp_model.CpModel()

        coils, conductivities = self.coil_attributes(model, side_length ** 2)

        total_efficiency = self.total_efficiency(model, conductivities)

        for target_name, quantity in type_limits.items():
            common.constraints.MaxQuantityConstraint(target_name, quantity).apply_to_model(
                model,
                coils,
                self.dynamo_coil_types
            )

        if symmetric:
            common.constraints.SymmetryConstraint().apply_to_model(
                model,
                coils,
                self.dynamo_coil_types
            )

        common.constraints.CenteredBearingsConstraint(shaft_width).apply_to_model(
            model,
            coils,
            self.dynamo_coil_types
        )

        common.constraints.PlacementRuleConstraint().apply_to_model(
            model,
            coils,
            self.dynamo_coil_types
        )

        model.Maximize(total_efficiency)

        solver = cp_model.CpSolver()
        if time_limit:
            solver.parameters.max_time_in_seconds = time_limit
        status = solver.Solve(model)

        return status, self.ids_to_coils([
            solver.Value(coil) for coil in coils
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
        ])
