"""Constraints for NuclearCraft Designer"""

from . import component


class Constraint:
    """Constraints for optimizers."""
    def __call__(self, sequence: list[component.Component], **kwargs) -> bool:
        """Determines whether the sequence satisfies the constraint.

        :param sequence: A sequence of components.
        :param kwargs: Other required parameters.
        :return: True if the constraint is satisfied, false otherwise.
        """
        return True


class MaxQuantityConstraint(Constraint):
    """Limits the quantity of a given component."""
    def __init__(self, target_name: str, max_quantity: int) -> None:
        """Constructs a MaxQuantityConstraint object.

        :param target: The name of the target component.
        :param max_quantity:
        """
        self.target_name = target_name
        self.max_quantity = max_quantity

    def __call__(self, sequence: list[component.Component], **kwargs) -> bool:
        n = 0
        for component in sequence:
            if isinstance(component, type(None)):
                continue
            if component.name == self.target_name:
                n += 1
        return n <= self.max_quantity
