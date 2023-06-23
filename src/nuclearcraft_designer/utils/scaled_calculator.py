"""Computational utilities for NuclearCraft Designer"""

import uuid

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None


class ScaledCalculator:
    """An ortools calculator with a scaling factor."""
    def __init__(self, scaling_factor: int) -> None:
        """Constructs a ScaledCalculator object.

        :param scaling_factor: The number of digits to scale decimals by.
        """
        self.scaling_factor = scaling_factor

    def scaled_multiplication(
            self,
            model: cp_model.CpModel,
            target: cp_model.IntVar,
            a: cp_model.IntVar,
            b: cp_model.IntVar
    ) -> None:
        """Scaled multiplication constraint.

        :param model: The model to apply the constraint to.
        :param target: The target variable.
        :param a:
        :param b:
        """
        c = model.NewIntVar(-2 ** 31, 2 ** 31 - 1, str(uuid.uuid4()))
        model.AddMultiplicationEquality(c, [a, b])
        model.AddDivisionEquality(target, c, 10 ** self.scaling_factor)

    def scaled_division(
            self,
            model: cp_model.CpModel,
            target: cp_model.IntVar,
            num: cp_model.IntVar,
            denom: cp_model.IntVar
    ) -> None:
        """Scaled division constraint.

        :param model: The model to apply the constraint to.
        :param target: The target variable.
        :param num: The numerator variable.
        :param denom: The denominator variable.
        """
        num_scaled = model.NewIntVar(-2 ** 31, 2 ** 31 - 1, str(uuid.uuid4()))
        model.AddMultiplicationEquality(num_scaled, [num, 10 ** self.scaling_factor])
        model.AddDivisionEquality(target, num_scaled, denom)
