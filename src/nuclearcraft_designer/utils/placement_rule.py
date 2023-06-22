"""Placement rules for NuclearCraft reactors and turbines."""

import enum


class LogicMode(enum.Enum):
    AND = "AND"
    OR = "OR"


class PlacementRule:
    """NuclearCraft reactor/turbine component placement rule."""
    def __call__(self, up: str, right: str, down: str, left: str, front: str = None, back: str = None) -> bool:
        """Determines if the rule is satisfied.

        :param up: The name of the component above.
        :param right: The name of the component to the right.
        :param down: The name of the component below.
        :param left: The name of the component to the left.
        :param front: The name of the component in front.
        :param back: The name of the component behind.
        :return: True if the rule is satisfied, false otherwise.
        """
        return True


class SimplePlacementRule(PlacementRule):
    """Placement rule requiring the presence of a certain component type."""
    def __init__(
            self,
            name: str,
            quantity: int,
            exact: bool = False,
            axial: bool = False
    ) -> None:
        """Constructs a SimplePlacementRule object.

        :param name: The name of the required component.
        :param quantity: The quantity of the required component.
        :param exact: Whether the quantity required is exact.
        :param axial: Whether the placement must be axial.
        """
        self.name = name
        self.quantity = quantity
        self.exact = exact
        self.axial = axial

    def __call__(self, up: str, right: str, down: str, left: str, front: str = None, back: str = None) -> bool:
        components = (up, right, down, left, front, back)
        if "incomplete" in components:
            return True

        quantity = 0
        axial = False
        for component in components:
            if component == self.name:
                quantity += 1
        if up == down == self.name or right == left == self.name or front == back == self.name:
            axial = True
        if self.exact:
            if quantity != self.quantity:
                return False
        else:
            if quantity < self.quantity:
                return False
        if self.axial and not axial:
            return False
        return True


class CompoundPlacementRule(PlacementRule):
    """Placement rule depending on the satisfaction of other placement rules."""
    def __init__(self, rules: list[PlacementRule], mode: LogicMode) -> None:
        """Constructs a CompoundPlacementRule object.

        :param rules: A list of placement rules.
        :param mode: Either LogicMode.OR or LogicMode.AND.
        """
        self.rules = rules
        self.mode = mode

    def __call__(self, up: str, right: str, down: str, left: str, front: str = None, back: str = None) -> bool:
        if self.mode == LogicMode.AND:
            for rule in self.rules:
                if not rule(up, right, down, left, front, back):
                    return False
            return True
        else:
            for rule in self.rules:
                if rule(up, right, down, left, front, back):
                    return True
            return False
