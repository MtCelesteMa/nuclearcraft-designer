"""NuclearCraft: Overhauled turbine rotor blade sequence designer."""

from . import RotorBlade, ROTOR_BLADE_TYPES
from ... import utils, common

import typing


class RotorBladeSequenceDesigner:
    """Designs NuclearCraft: Overhauled turbine rotor blade sequences."""
    def __init__(
            self,
            rotor_blade_types: list[RotorBlade] = ROTOR_BLADE_TYPES
    ) -> None:
        """Constructs a RotorBladeSequenceDesigner object.

        :param rotor_blade_types: A list of rotor blade types.
        """
        self.rotor_blade_types = rotor_blade_types

    def ids_to_blades(self, sequence: list[int]) -> common.multi_sequence.MultiSequence[RotorBlade]:
        """Converts a sequence of IDs to a sequence of rotor blades.

        :param sequence: A sequence of IDs.
        :return: A sequence of rotor blades.
        """
        return common.multi_sequence.MultiSequence([
            self.rotor_blade_types[i] if i >= 0 else None
            for i in sequence
        ], (len(sequence),))

    def expansion_levels(self, sequence: common.multi_sequence.MultiSequence[RotorBlade]) -> list[float]:
        """Calculates the expansion levels of a sequence of rotor blades.

        :param sequence: A sequence of rotor blades.
        :return: A list of expansion levels.
        """
        total_expansion_level = 1.0
        expansion_levels = []
        for rotor_blade in sequence:
            expansion_levels.append(total_expansion_level * rotor_blade.expansion ** (1 / 2))
            total_expansion_level *= rotor_blade.expansion
        return expansion_levels

    def total_efficiency(
            self,
            sequence: common.multi_sequence.MultiSequence[RotorBlade],
            opt_expansion: float
    ) -> float:
        """Calculates the total efficiency of a sequence of rotor blades.

        :param sequence: A sequence of rotor blades.
        :param opt_expansion: The optimal expansion.
        :return: The total efficiency of the sequence.
        """
        expansion_levels = self.expansion_levels(sequence)
        total_efficiency = 0.0
        n_blades = 0
        for i, rotor_blade in enumerate(sequence):
            if rotor_blade.efficiency > 0:
                opt_expansion_ = opt_expansion ** ((i + 0.5) / len(sequence))
                expansion_ = expansion_levels[i]
                total_efficiency += rotor_blade.efficiency * (
                    ((opt_expansion_ / expansion_) if opt_expansion_ < expansion_ else (expansion_ / opt_expansion_))
                    if opt_expansion_ > 0 and expansion_ > 0 else 0
                )
                n_blades += 1
        return total_efficiency / n_blades if n_blades > 0 else 0

    def design_generator(
            self,
            length: int,
            opt_expansion: float,
            type_limits: dict[str, int]
    ) -> typing.Generator[list[RotorBlade], None, None]:
        """Constructs a generator that iteratively generates better rotor blade sequences.

        :param length: The length of the rotor blade sequence.
        :param opt_expansion: The expansion level to optimize for.
        :param type_limits: The maximum number of each type of rotor blade.
        :return: A generator object.
        """
        gen = utils.optimizer.SequenceOptimizer(
            utils.optimizer.ConstrainedIntegerSequence(
                length,
                len(self.rotor_blade_types),
                [
                    lambda seq: common.constraints.MaxQuantityConstraint(target_name, quantity)(self.ids_to_blades(seq))
                    for target_name, quantity in type_limits.items()
                ]
            ).generator(),
            lambda seq: self.total_efficiency(self.ids_to_blades(seq), opt_expansion)
        ).generator()
        for sequence in gen:
            yield self.ids_to_blades(sequence)
