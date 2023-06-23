"""NuclearCraft: Overhauled turbine rotor blade sequence designer."""

from . import RotorBlade, ROTOR_BLADE_TYPES
from ... import utils

import uuid

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None


class RotorBladeSequenceDesigner:
    """Designs NuclearCraft: Overhauled turbine rotor blade sequences."""
    def __init__(
            self,
            rotor_blade_types: list[RotorBlade] = ROTOR_BLADE_TYPES,
            scaling_factor: int = 2
    ) -> None:
        """Constructs a RotorBladeSequenceDesigner object.

        :param rotor_blade_types: A list of rotor blade types.
        :param scaling_factor: The number of digits to scale decimals by.
        """
        self.rotor_blade_types = rotor_blade_types
        self.scaling_factor = scaling_factor
        self.sc = utils.scaled_calculator.ScaledCalculator(self.scaling_factor)

    def ids_to_blades(self, sequence: list[int]) -> list[RotorBlade]:
        """Converts a sequence of IDs to a sequence of rotor blades.

        :param sequence: A sequence of IDs.
        :return: A sequence of rotor blades.
        """
        return [
            self.rotor_blade_types[i] if i >= 0 else None
            for i in sequence
        ]

    def blade_attributes(self, model: cp_model.CpModel, n_blades: int) -> tuple[
        list[cp_model.IntVar], list[cp_model.IntVar], list[cp_model.IntVar], list[cp_model.IntVar]
    ]:
        """Registers rotor blades as well as their attributes to the model.

        :param model: The model to register rotor blades to.
        :param n_blades: The number of blades to register.
        :return: Four lists of IntVars, representing the blades, the efficiencies, and the expansions and their
        square roots.
        """
        blades = [
            model.NewIntVar(0, len(self.rotor_blade_types) - 1, "blade_{0:d}".format(i))
            for i in range(n_blades)
        ]

        efficiencies = [
            model.NewIntVar(-2 ** 31, 2 ** 31 - 1, "efficiency_{0:d}".format(i))
            for i in range(n_blades)
        ]
        for blade, efficiency in zip(blades, efficiencies):
            model.AddElement(blade, [
                round(blade_type.efficiency * (10 ** self.scaling_factor))
                for blade_type in self.rotor_blade_types
            ], efficiency)

        expansions = [
            model.NewIntVar(1, 2 ** 31 - 1, "expansion_{0:d}".format(i))
            for i in range(n_blades)
        ]
        for blade, expansion in zip(blades, expansions):
            model.AddElement(blade, [
                round(blade_type.expansion * (10 ** self.scaling_factor))
                for blade_type in self.rotor_blade_types
            ], expansion)

        expansions_sqrt = [
            model.NewIntVar(1, 2 ** 31 - 1, "expansion_sqrt_{0:d}".format(i))
            for i in range(n_blades)
        ]
        for blade, expansion_sqrt in zip(blades, expansions_sqrt):
            model.AddElement(blade, [
                round(blade_type.expansion ** (1 / 2) * (10 ** self.scaling_factor))
                for blade_type in self.rotor_blade_types
            ], expansion_sqrt)

        return blades, efficiencies, expansions, expansions_sqrt

    def expansion_levels(
            self,
            model: cp_model.CpModel,
            expansions: list[cp_model.IntVar],
            expansions_sqrt: list[cp_model.IntVar]
    ) -> list[cp_model.IntVar]:
        """Calculates the expansion levels of a sequence of rotor blades.

        :param model: The optimization model.
        :param expansions: A list of IntVars representing each blade's expansion.
        :param expansions_sqrt: A list of IntVars representing the square root of each blade's expansion.
        :return: A list of IntVars representing the expansion levels.
        """
        expansion_levels = [
            model.NewIntVar(1, 2 ** 31 - 1, "expansion_level_{0:d}".format(i))
            for i in range(len(expansions))
        ]
        total_expansion_level = 100
        for expansion, expansion_sqrt, expansion_level in zip(expansions, expansions_sqrt, expansion_levels):
            self.sc.scaled_multiplication(model, expansion_level, total_expansion_level, expansion_sqrt)
            total_expansion_level_ = model.NewIntVar(1, 2 ** 31 - 1, str(uuid.uuid4()))
            self.sc.scaled_multiplication(model, total_expansion_level_, total_expansion_level, expansion)
            total_expansion_level = total_expansion_level_
        return expansion_levels

    def total_efficiency(
            self,
            model: cp_model.CpModel,
            efficiencies: list[cp_model.IntVar],
            expansion_levels: list[cp_model.IntVar],
            opt_expansion: float
    ) -> cp_model.IntVar:
        """Calculates the total efficiency of a sequence of rotor blades.

        :param model: The optimization model.
        :param efficiencies: A list of IntVars representing each blade's efficiency.
        :param expansion_levels: A list of IntVars representing the expansion levels.
        :param opt_expansion: The optimal expansion.
        :return: An IntVar representing the total efficiency.
        """
        total_efficiencies = [
            model.NewIntVar(0, 2 ** 31 - 1, "total_efficiency_{0:d}".format(i))
            for i in range(len(efficiencies))
        ]
        n_blades = [
            model.NewIntVar(0, len(efficiencies), "n_blades_{0:d}".format(i))
            for i in range(len(efficiencies))
        ]
        is_blade = [
            model.NewBoolVar("is_blade_{0:d}".format(i))
            for i in range(len(efficiencies))
        ]
        multipliers = [
            model.NewIntVar(0, 100, "multiplier_{0:d}".format(i))
            for i in range(len(efficiencies))
        ]
        effective_efficiencies = [
            model.NewIntVar(-2 ** 31, 2 ** 31 - 1, "effective_efficiency_{0:d}".format(i))
            for i in range(len(efficiencies))
        ]
        for i in range(len(efficiencies)):
            model.Add(efficiencies[i] >= 0).OnlyEnforceIf(is_blade[i])
            model.Add(efficiencies[i] < 0).OnlyEnforceIf(is_blade[i].Not())

            n_blades_prev = n_blades[i - 1] if i > 0 else 0
            model.Add(n_blades[i] == n_blades_prev + 1).OnlyEnforceIf(is_blade[i])
            model.Add(n_blades[i] == n_blades_prev).OnlyEnforceIf(is_blade[i].Not())

            opt_expansion_ = round((opt_expansion ** ((i + 0.5) / len(efficiencies))) * (10 ** self.scaling_factor))
            expansion_ = expansion_levels[i]
            multiplier_a = model.NewIntVar(0, 2 ** 31 - 1, str(uuid.uuid4()))
            self.sc.scaled_division(model, multiplier_a, opt_expansion_, expansion_)
            multiplier_b = model.NewIntVar(0, 2 ** 31 - 1, str(uuid.uuid4()))
            self.sc.scaled_division(model, multiplier_b, expansion_, opt_expansion_)
            model.AddMinEquality(multipliers[i], [multiplier_a, multiplier_b])

            self.sc.scaled_multiplication(model, effective_efficiencies[i], efficiencies[i], multipliers[i])

            total_efficiencies_prev = total_efficiencies[i - 1] if i > 0 else 0
            model.Add(total_efficiencies[i] == total_efficiencies_prev + effective_efficiencies[i])\
                .OnlyEnforceIf(is_blade[i])
            model.Add(total_efficiencies[i] == total_efficiencies_prev).OnlyEnforceIf(is_blade[i].Not())

        n_blades_ = model.NewIntVar(1, len(efficiencies), "n_blades")
        model.Add(n_blades_ == n_blades[-1])

        total_efficiency = model.NewIntVar(0, 2 ** 31 - 1, "total_efficiency")
        model.AddDivisionEquality(total_efficiency, total_efficiencies[-1], n_blades_)

        return total_efficiency

    def design(
            self,
            length: int,
            opt_expansion: float,
            type_limits: dict[str, int],
            time_limit: float = None
    ) -> tuple[int, list[RotorBlade]]:
        """Designs the optimal sequence of rotor blades if possible.

        :param length: The length of the rotor blade sequence.
        :param opt_expansion: The expansion level to optimize for.
        :param type_limits: The maximum number of each type of rotor blade.
        :param time_limit: The maximum time in seconds to run for.
        :return: The status as well as a sequence of rotor blades.
        """
        model = cp_model.CpModel()

        blades, efficiencies, expansions, expansions_sqrt = self.blade_attributes(model, length)

        expansion_levels = self.expansion_levels(model, expansions, expansions_sqrt)

        total_efficiency = self.total_efficiency(model, efficiencies, expansion_levels, opt_expansion)

        for target_name, quantity in type_limits.items():
            utils.constraints.MaxQuantityConstraint(target_name, quantity).apply_to_model(
                model,
                blades,
                self.rotor_blade_types
            )

        model.Maximize(total_efficiency)

        solver = cp_model.CpSolver()
        if time_limit:
            solver.parameters.max_time_in_seconds = time_limit
        status = solver.Solve(model)

        return status, self.ids_to_blades([
            solver.Value(blade) for blade in blades
            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE
        ])
