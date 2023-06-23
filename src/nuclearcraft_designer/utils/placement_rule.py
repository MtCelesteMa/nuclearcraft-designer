"""Placement rules for NuclearCraft reactors and turbines."""

import enum
import uuid

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None


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

    def to_model(
            self,
            model: cp_model.CpModel,
            component_types: list[str],
            up: cp_model.IntVar,
            right: cp_model.IntVar,
            down: cp_model.IntVar,
            left: cp_model.IntVar,
            front: cp_model.IntVar = -1,
            back: cp_model.IntVar = -1
    ) -> cp_model.IntVar:
        """Registers the placement rule to a CP-SAT model.

        :param model: The CP-SAT model to register the placement rule to.
        :param component_types: A list of component type names.
        :param up: An IntVar representing the component above.
        :param right: An IntVar representing the component to the right.
        :param down: An IntVar representing the component below.
        :param left: An IntVar representing the component to the left.
        :param front: An IntVar representing the component to the right.
        :param back: An IntVar representing the component behind.
        :return: An IntVar representing whether the placement rule is satisfied.
        """
        satisfied = model.NewBoolVar(str(uuid.uuid4()))
        model.Add(satisfied == 1)
        return satisfied


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

    def to_model(
            self,
            model: cp_model.CpModel,
            component_types: list[str],
            up: cp_model.IntVar,
            right: cp_model.IntVar,
            down: cp_model.IntVar,
            left: cp_model.IntVar,
            front: cp_model.IntVar = -1,
            back: cp_model.IntVar = -1
    ) -> cp_model.IntVar:
        name_to_id = {comp: i for i, comp in enumerate(component_types)}
        components = (up, right, down, left, front, back)

        quantity = [model.NewIntVar(0, 6, str(uuid.uuid4())) for _ in range(6)]
        matches = [model.NewBoolVar(str(uuid.uuid4())) for _ in range(6)]
        for i in range(6):
            model.Add(components[i] == name_to_id[self.name]).OnlyEnforceIf(matches[i])
            model.Add(components[i] != name_to_id[self.name]).OnlyEnforceIf(matches[i].Not())

            quantity_prev = quantity[i - 1] if i > 0 else 0
            model.Add(quantity[i] == quantity_prev + 1).OnlyEnforceIf(matches[i])
            model.Add(quantity[i] == quantity_prev).OnlyEnforceIf(matches[i].Not())

        axials = [model.NewBoolVar(str(uuid.uuid4())) for _ in range(3)]
        model.AddBoolAnd([matches[0], matches[2]]).OnlyEnforceIf(axials[0])
        model.AddBoolOr([matches[0].Not(), matches[2].Not()]).OnlyEnforceIf(axials[0].Not())

        model.AddBoolAnd([matches[1], matches[3]]).OnlyEnforceIf(axials[1])
        model.AddBoolOr([matches[1].Not(), matches[3].Not()]).OnlyEnforceIf(axials[1].Not())

        model.AddBoolAnd([matches[4], matches[5]]).OnlyEnforceIf(axials[2])
        model.AddBoolOr([matches[4].Not(), matches[5].Not()]).OnlyEnforceIf(axials[2].Not())

        axial = model.NewBoolVar(str(uuid.uuid4()))
        model.AddBoolOr(axials).OnlyEnforceIf(axial)
        model.AddBoolAnd([axial_.Not() for axial_ in axials]).OnlyEnforceIf(axial.Not())

        satisfied = model.NewBoolVar(str(uuid.uuid4()))
        if self.axial:
            if self.exact:
                model.Add(axial and quantity[-1] == self.quantity).OnlyEnforceIf(satisfied)
                model.Add(axial.Not() or quantity[-1] != self.quantity).OnlyEnforceIf(satisfied.Not())
            else:
                model.Add(axial and quantity[-1] >= self.quantity).OnlyEnforceIf(satisfied)
                model.Add(axial.Not() or quantity[-1] < self.quantity).OnlyEnforceIf(satisfied.Not())
        else:
            if self.exact:
                model.Add(quantity[-1] == self.quantity).OnlyEnforceIf(satisfied)
                model.Add(quantity[-1] != self.quantity).OnlyEnforceIf(satisfied.Not())
            else:
                model.Add(quantity[-1] >= self.quantity).OnlyEnforceIf(satisfied)
                model.Add(quantity[-1] < self.quantity).OnlyEnforceIf(satisfied.Not())
        return satisfied


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

    def to_model(
            self,
            model: cp_model.CpModel,
            component_types: list[str],
            up: cp_model.IntVar,
            right: cp_model.IntVar,
            down: cp_model.IntVar,
            left: cp_model.IntVar,
            front: cp_model.IntVar = -1,
            back: cp_model.IntVar = -1
    ) -> cp_model.IntVar:
        satisfied_vars = [
            rule.to_model(model, component_types, up, right, down, left, front, back)
            for rule in self.rules
        ]
        satisfied = model.NewBoolVar(str(uuid.uuid4()))
        if self.mode == LogicMode.AND:
            model.Add(sum(satisfied_vars) >= len(satisfied_vars)).OnlyEnforceIf(satisfied)
            model.Add(sum(satisfied_vars) < len(satisfied_vars)).OnlyEnforceIf(satisfied.Not())
        else:
            model.Add(sum(satisfied_vars) > 0).OnlyEnforceIf(satisfied)
            model.Add(sum(satisfied_vars) == 0).OnlyEnforceIf(satisfied.Not())
        return satisfied
