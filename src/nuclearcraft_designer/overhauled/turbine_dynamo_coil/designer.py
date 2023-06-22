"""NuclearCraft: Overhauled turbine dynamo coil configuration designer."""

from . import DynamoCoil, DYNAMO_COIL_TYPES
from ...utils import ndim_sequence, optimizer

import typing


class DynamoCoilConfigurationDesigner:
    """Designs NuclearCraft: Overhauled turbine dynamo coil configurations."""
    def __init__(
            self,
            dynamo_coil_types: list[DynamoCoil] = DYNAMO_COIL_TYPES
    ) -> None:
        """Constructs a RotorBladeSequenceDesigner object.

        :param dynamo_coil_types: A list of dynamo coil types.
        """
        self.dynamo_coil_types = dynamo_coil_types

    def ids_to_blades(self, sequence: list[int]) -> ndim_sequence.Sequence2D[DynamoCoil]:
        """Converts a sequence of IDs to a sequence of rotor blades.

        :param sequence: A sequence of IDs.
        :return: A sequence of rotor blades.
        """
        return ndim_sequence.Sequence2D([
            self.dynamo_coil_types[i] if i >= 0 else None
            for i in sequence
        ], round(len(sequence) ** (1 / 2)))

    def centered_bearings_constraint(self, sequence: list[int], shaft_width: int) -> bool:
        """Determines whether the bearings are centered.

        :param sequence: A sequence of IDs.
        :param shaft_width: The width of the shaft.
        :return: True if the bearings are centered, false otherwise.
        """
        configuration = self.ids_to_blades(sequence)
        for x in range(configuration.cols):
            for y in range(configuration.cols):
                if configuration.cols % 2:
                    mid = (configuration.cols - 1) // 2
                    r = (shaft_width - 1) // 2
                    if mid - r <= x <= mid + r and mid - r <= y <= mid + r:
                        if not isinstance(configuration[x, y], type(None)) and configuration[x, y].name != "bearing":
                            return False
                    else:
                        if not isinstance(configuration[x, y], type(None)):
                            if configuration[x, y].name == "bearing":
                                return False
                else:
                    mid = configuration.cols // 2 - 1
                    r_left = shaft_width // 2 - 1
                    r_right = shaft_width // 2
                    if mid - r_left <= x <= mid + r_right and mid - r_left <= y <= mid + r_right:
                        if not isinstance(configuration[x, y], type(None)) and configuration[x, y].name != "bearing":
                            return False
                    else:
                        if not isinstance(configuration[x, y], type(None)):
                            if configuration[x, y].name == "bearing":
                                return False
        return True

    def coil_name(self, coil: DynamoCoil | None) -> str:
        return "incomplete" if isinstance(coil, type(None)) else coil.name

    def placement_rule_constraint(self, sequence: list[int]) -> bool:
        """Determines whether all dynamo coils follow placement rules.

        :param sequence: A sequence of IDs.
        :return: True if all dynamo coils follow placement rules, false otherwise.
        """
        configuration = self.ids_to_blades(sequence)
        for x in range(configuration.cols):
            for y in range(configuration.cols):
                up = self.coil_name(configuration[x, y - 1]) if y > 0 else "wall"
                right = self.coil_name(configuration[x + 1, y]) if x < configuration.cols - 1 else "wall"
                down = self.coil_name(configuration[x, y + 1]) if y < configuration.cols - 1 else "wall"
                left = self.coil_name(configuration[x - 1, y]) if x > 0 else "wall"
                if not isinstance(configuration[x, y], type(None)) and not configuration[x, y].placement_rule(up, right, down, left):
                    return False
        return True

    def total_efficiency(self, sequence: ndim_sequence.Sequence2D[DynamoCoil]) -> float:
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
    ) -> typing.Generator[ndim_sequence.Sequence2D[DynamoCoil], None, None]:
        """Constructs a generator that iteratively generates better dynamo coil sequences.

        :param side_length: The side length of the turbine.
        :param shaft_width: The width of the rotor shaft.
        :param type_limits: The maximum number of each type of dynamo coil.
        :return: A generator object.
        """
        type_limits_ = [-1 for _ in self.dynamo_coil_types]
        for name, limit in type_limits.items():
            for i, blade_type in enumerate(self.dynamo_coil_types):
                if name == blade_type.name:
                    type_limits_[i] = limit

        gen = optimizer.SequenceOptimizer(
            optimizer.ConstrainedIntegerSequence(
                side_length ** 2,
                len(self.dynamo_coil_types),
                [
                    lambda seq: self.centered_bearings_constraint(seq, shaft_width),
                    self.placement_rule_constraint
                ] + [
                    optimizer.max_appearances_constraint(i, limit)
                    for i, limit in enumerate(type_limits_) if limit >= 0
                ]
            ).generator(),
            lambda seq: self.total_efficiency(self.ids_to_blades(seq))
        ).generator()
        for sequence in gen:
            yield self.ids_to_blades(sequence)
