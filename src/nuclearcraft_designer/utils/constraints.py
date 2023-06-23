"""Constraints for NuclearCraft Designer"""

from . import component, ndim_sequence


class Constraint:
    """Constraints for optimizers."""
    def __call__(
            self,
            sequence: list[component.Component] | ndim_sequence.Sequence2D[component.Component],
            **kwargs
    ) -> bool:
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

        :param target_name: The name of the target component.
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


class PlacementRuleConstraint(Constraint):
    """Enforces component placement rules."""
    def component_name(self, comp: component.Component | None) -> str:
        """Returns the name of the component, or "incomplete" if None.

        :param comp: The component or None.
        :return: The name of the component or "incomplete"
        """
        return "incomplete" if isinstance(comp, type(None)) else comp.name

    def __call__(self, sequence: ndim_sequence.Sequence2D[component.Component], **kwargs) -> bool:
        for x in range(sequence.cols):
            for y in range(sequence.rows):
                up = self.component_name(sequence[x, y - 1]) if y > 0 else "wall"
                right = self.component_name(sequence[x + 1, y]) if x < sequence.cols - 1 else "wall"
                down = self.component_name(sequence[x, y + 1]) if y < sequence.cols - 1 else "wall"
                left = self.component_name(sequence[x - 1, y]) if x > 0 else "wall"
                if not isinstance(sequence[x, y], type(None)) and not sequence[x, y].placement_rule(
                        up,
                        right,
                        down,
                        left
                ):
                    return False
        return True


class CenteredBearingsConstraint(Constraint):
    """Ensures rotor bearings are centered."""
    def __init__(self, shaft_width: int) -> None:
        """Constructs a CenteredBearingsConstraint object.

        :param shaft_width: The width of the rotor shaft.
        """
        self.shaft_width = shaft_width

    def __call__(self, sequence: ndim_sequence.Sequence2D[component.Component], **kwargs) -> bool:
        for x in range(sequence.cols):
            for y in range(sequence.rows):
                if sequence.cols % 2:
                    mid = (sequence.cols - 1) // 2
                    r = (self.shaft_width - 1) // 2
                    if mid - r <= x <= mid + r and mid - r <= y <= mid + r:
                        if not isinstance(sequence[x, y], type(None)) and sequence[x, y].name != "bearing":
                            return False
                    else:
                        if not isinstance(sequence[x, y], type(None)):
                            if sequence[x, y].name == "bearing":
                                return False
                else:
                    mid = sequence.cols // 2 - 1
                    r_left = self.shaft_width // 2 - 1
                    r_right = self.shaft_width // 2
                    if mid - r_left <= x <= mid + r_right and mid - r_left <= y <= mid + r_right:
                        if not isinstance(sequence[x, y], type(None)) and sequence[x, y].name != "bearing":
                            return False
                    else:
                        if not isinstance(sequence[x, y], type(None)):
                            if sequence[x, y].name == "bearing":
                                return False
        return True
