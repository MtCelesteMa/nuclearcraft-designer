"""NuclearCraft: Overhauled turbine dynamo coil configuration designer."""

from . import DynamoCoil, DYNAMO_COIL_TYPES
from ... import utils

import typing


class DynamoCoilConfigurationDesigner:
    """Designs NuclearCraft: Overhauled turbine dynamo coil configurations."""
    def __init__(
            self,
            dynamo_coil_types: list[DynamoCoil] = DYNAMO_COIL_TYPES
    ) -> None:
        """Constructs a DynamoCoilConfigurationDesigner object.

        :param dynamo_coil_types: A list of dynamo coil types.
        """
        self.dynamo_coil_types = dynamo_coil_types

    def ids_to_coils(self, sequence: list[int]) -> utils.ndim_sequence.Sequence2D[DynamoCoil]:
        """Converts a sequence of IDs to a sequence of rotor blades.

        :param sequence: A sequence of IDs.
        :return: A sequence of rotor blades.
        """
        return utils.ndim_sequence.Sequence2D([
            self.dynamo_coil_types[i] if i >= 0 else None
            for i in sequence
        ], round(len(sequence) ** (1 / 2)))

    def total_efficiency(self, sequence: utils.ndim_sequence.Sequence2D[DynamoCoil]) -> float:
        """Calculates the total efficiency of a sequence of dynamo coils.

        :param sequence: A sequence of dynamo coils.
        :return: The total efficiency of the sequence.
        """
        total_efficiency = 0.0
        n_coils = 0
        for i, dynamo_coil in enumerate(sequence):
            if dynamo_coil.conductivity > 0:
                total_efficiency += dynamo_coil.conductivity
                n_coils += 1
        return total_efficiency / n_coils if n_coils > 0 else 0

    def design_generator(
            self,
            side_length: int,
            shaft_width: int,
            type_limits: dict[str, int]
    ) -> typing.Generator[utils.ndim_sequence.Sequence2D[DynamoCoil], None, None]:
        """Constructs a generator that iteratively generates better dynamo coil sequences.

        :param side_length: The side length of the turbine.
        :param shaft_width: The width of the rotor shaft.
        :param type_limits: The maximum number of each type of dynamo coil.
        :return: A generator object.
        """
        gen = utils.optimizer.SequenceOptimizer(
            utils.optimizer.ConstrainedIntegerSequence(
                side_length ** 2,
                len(self.dynamo_coil_types),
                [
                    lambda seq: utils.constraints.CenteredBearingsConstraint(shaft_width)(self.ids_to_coils(seq)),
                    lambda seq: utils.constraints.PlacementRuleConstraint()(self.ids_to_coils(seq))
                ] + [
                    lambda seq: utils.constraints.MaxQuantityConstraint(target_name, quantity)(self.ids_to_coils(seq))
                    for target_name, quantity in type_limits.items()
                ]
            ).generator(),
            lambda seq: self.total_efficiency(self.ids_to_coils(seq))
        ).generator()
        for sequence in gen:
            yield self.ids_to_coils(sequence)
