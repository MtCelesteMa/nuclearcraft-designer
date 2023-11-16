"""Scaled multiplication and division for OR-Tools."""

import uuid

from ortools.sat.python import cp_model


class ScaledOps:
    """Scaled multiplication and division for OR-Tools."""
    def __init__(self, scaling_factor: int) -> None:
        """Constructs a ScaledOps object.

        :param scaling_factor: The number of digits to scale decimals by.
        """
        self.scaling_factor = scaling_factor

    def scaled_mul(
            self,
            model: cp_model.CpModel,
            target: cp_model.IntVar,
            a: cp_model.IntVar,
            b: cp_model.IntVar
    ) -> None:
        """Scaled multiplication constraint.

        :param model: The model to apply the constraint to.
        :param target: The target variable.
        :param a: A factor variable.
        :param b: Another factor variable.
        """
        c = model.NewIntVar(-2 ** 31, 2 ** 31 - 1, str(uuid.uuid4()))
        model.AddMultiplicationEquality(c, [a, b])
        model.AddDivisionEquality(target, c, 10 ** self.scaling_factor)

    def scaled_div(
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
