"""NuclearCraft: Overhauled turbine rotor blades."""

from .. import optimizer

import typing


class RotorBlade:
    """An object representing a NuclearCraft: Overhauled turbine rotor blade."""
    def __init__(self, name: str, efficiency: float, expansion: float) -> None:
        """Constructs a RotorBlade object.

        :param name: The name of the rotor blade.
        :param efficiency: The efficiency of the rotor blade.
        :param expansion: The expansion of the rotor blade.
        """
        self.name = name
        self.efficiency = efficiency
        self.expansion = expansion


STEEL = RotorBlade("steel", 1.0, 1.4)
EXTREME = RotorBlade("extreme", 1.1, 1.6)
SIC_SIC_CMC = RotorBlade("sic_sic_cmc", 1.2, 1.8)
STATOR = RotorBlade("stator", -1.0, 0.75)


class EfficiencyCalculator:
    """Calculates the efficiency of a sequence of turbine rotor blades."""
    def __init__(self, rotor_blade_types: list[RotorBlade]):
        """Constructs an EfficiencyCalculator object.

        :param rotor_blade_types: A list of rotor blade types.
        """
        self.rotor_blade_types = rotor_blade_types

    def id_to_blades(self, sequence: list[int]) -> list[RotorBlade]:
        """Converts a sequence of IDs to a sequence of rotor blades.

        :param sequence: A sequence of IDs.
        :return: A sequence of rotor blades.
        """
        return [self.rotor_blade_types[i] for i in sequence]

    def expansion_levels(self, sequence: list[RotorBlade] | list[int]) -> tuple[float, list[float]]:
        """Computes the expansion levels of the turbine.

        :param sequence: A sequence of rotor blades.
        :return: A tuple containing the total expansion level as well as the expansion level at every point.
        """
        if isinstance(sequence[0], int):
            sequence = self.id_to_blades(sequence)
        total_expansion_level = 1.0
        expansion_levels = []
        for rotor_blade in sequence:
            expansion_levels.append(total_expansion_level * rotor_blade.expansion ** (1 / 2))
            total_expansion_level *= rotor_blade.expansion
        return total_expansion_level, expansion_levels

    def efficiency(self, sequence: list[RotorBlade] | list[int], opt_expansion: float) -> float:
        """Calculates the total efficiency of the sequence.

        :param sequence: A sequence of rotor blades.
        :param opt_expansion: The optimal expansion.
        :return: The total efficiency of the sequence.
        """
        if isinstance(sequence[0], int):
            sequence = self.id_to_blades(sequence)
        total_expansion_level, expansion_levels = self.expansion_levels(sequence)
        efficiency = 0.0
        n_blades = 0
        for i, rotor_blade in enumerate(sequence):
            if rotor_blade.efficiency > 0:
                opt_expansion_ = opt_expansion ** ((i + 0.5) / len(sequence))
                expansion_ = expansion_levels[i]
                efficiency += rotor_blade.efficiency * (
                    ((opt_expansion_ / expansion_) if opt_expansion_ < expansion_ else (expansion_ / opt_expansion_))
                    if opt_expansion_ > 0 and expansion_ > 0 else 0
                )
                n_blades += 1
        return efficiency / n_blades if n_blades > 0 else 0


def optimal_rotor_blade_sequence(
        length: int,
        opt_expansion: float,
        rotor_blade_types: list[RotorBlade],
        type_limits: list[int]
) -> list[RotorBlade]:
    """Determines the optimal rotor blade sequence.

    :param length: The length of the rotor blade sequence.
    :param opt_expansion: The expansion level to optimize for.
    :param rotor_blade_types: A list of rotor blade types.
    :param type_limits: The maximum number of each type of rotor blades.
    :return: The optimal rotor blade sequence.
    """
    calc = EfficiencyCalculator(rotor_blade_types)
    return calc.id_to_blades(optimizer.optimal_sequence(
        optimizer.ConstrainedIntegerSequence(
            length,
            len(rotor_blade_types),
            [
                optimizer.max_appearances_constraint(i, type_limits[i])
                for i in range(len(type_limits)) if type_limits[i] >= 0
            ]
        ).generator(),
        lambda seq: calc.efficiency(seq, opt_expansion)
    ))
