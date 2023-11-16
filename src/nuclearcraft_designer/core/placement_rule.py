"""Placement rules for NuclearCraft reactor/turbine components."""

import enum
import uuid

from ortools.sat.python import cp_model


class LogicMode(enum.Enum):
    AND = "AND"
    OR = "OR"


class PlacementRule:
    """NuclearCraft reactor/turbine component placement rule."""
    def __call__(self, comp_names: tuple[str, ...]) -> bool:
        """Determines if the rule is satisfied.

        :param comp_names: A list of adjacent component names. Must be in the order of (+x, -x, +y, -y, +z, -z).
        :return: True if the rule is satisfied, false otherwise.
        """
        return True

    def to_model(
            self,
            model: cp_model.CpModel,
            type_names: list[str],
            comp_ids: list[cp_model.IntVar]
    ) -> cp_model.IntVar:
        """Registers the placement rule to a CP-SAT model.

        :param model: The CP-SAT model to register the placement rule to.
        :param type_names: A list of component type names.
        :param comp_ids: A list IntVars representing adjacent components.
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

    def __call__(self, comp_names: tuple[str, ...]) -> bool:
        if "incomplete" in comp_names:
            return True

        quantity = 0
        for name in comp_names:
            if name == self.name:
                quantity += 1

        axial = False
        for i in range(len(comp_names) // 2):
            if comp_names[i * 2] == comp_names[i * 2 + 1] == self.name:
                axial = True
                break

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
            type_names: list[str],
            comp_ids: list[cp_model.IntVar]
    ) -> cp_model.IntVar:
        name_to_id = {comp: i for i, comp in enumerate(type_names)}

        quantity = [model.NewIntVar(0, len(comp_ids), str(uuid.uuid4())) for _ in range(len(comp_ids))]
        matches = [model.NewBoolVar(str(uuid.uuid4())) for _ in range(len(comp_ids))]
        for i in range(len(comp_ids)):
            model.Add(comp_ids[i] == name_to_id[self.name]).OnlyEnforceIf(matches[i])
            model.Add(comp_ids[i] != name_to_id[self.name]).OnlyEnforceIf(matches[i].Not())

            quantity_prev = quantity[i - 1] if i > 0 else 0
            model.Add(quantity[i] == quantity_prev + 1).OnlyEnforceIf(matches[i])
            model.Add(quantity[i] == quantity_prev).OnlyEnforceIf(matches[i].Not())

        axials = [model.NewBoolVar(str(uuid.uuid4())) for _ in range(len(comp_ids) // 2)]
        for i in range(len(comp_ids) // 2):
            model.AddBoolAnd([matches[i * 2], matches[i * 2 + 1]]).OnlyEnforceIf(axials[i])
            model.AddBoolOr([matches[i * 2].Not(), matches[i * 2 + 1].Not()]).OnlyEnforceIf(axials[i].Not())

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

    def __call__(self, comp_names: tuple[str, ...]) -> bool:
        if self.mode == LogicMode.AND:
            for rule in self.rules:
                if not rule(comp_names):
                    return False
            return True
        else:
            for rule in self.rules:
                if rule(comp_names):
                    return True
            return False

    def to_model(
            self,
            model: cp_model.CpModel,
            type_names: list[str],
            comp_ids: list[cp_model.IntVar]
    ) -> cp_model.IntVar:
        satisfied_vars = [
            rule.to_model(model, type_names, comp_ids)
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
