"""Constraints for NuclearCraft Designer"""

from . import multi_sequence
from . import component

import uuid

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None


class Constraint:
    """Constraints for optimizers."""
    def __call__(
            self,
            sequence: multi_sequence.MultiSequence[component.Component],
            **kwargs
    ) -> bool:
        """Determines whether the sequence satisfies the constraint.

        :param sequence: A sequence of components.
        :param kwargs: Other required parameters.
        :return: True if the constraint is satisfied, false otherwise.
        """
        return True

    def apply_to_model(
            self,
            model: cp_model.CpModel,
            sequence: multi_sequence.MultiSequence[cp_model.IntVar],
            component_types: list[component.Component],
            **kwargs
    ) -> None:
        """Applies constraint to a CP-SAT model.

        :param model: The CP-SAT model to apply the constraint to.
        :param sequence: A list of IntVars representing rotor blade IDs.
        :param component_types: A list of component types.
        :param kwargs: Other required parameters.
        """
        raise NotImplementedError("This constraint does not support CP-SAT models!")


class MaxQuantityConstraint(Constraint):
    """Limits the quantity of a given component."""
    def __init__(self, target_name: str, max_quantity: int) -> None:
        """Constructs a MaxQuantityConstraint object.

        :param target_name: The name of the target component.
        :param max_quantity: The maximum quantity of the given component.
        """
        self.target_name = target_name
        self.max_quantity = max_quantity

    def __call__(
            self,
            sequence: multi_sequence.MultiSequence[component.Component],
            **kwargs
    ) -> bool:
        n = 0
        for comp in sequence:
            if isinstance(comp, type(None)):
                continue
            if comp.name == self.target_name:
                n += 1
        return n <= self.max_quantity

    def apply_to_model(
            self,
            model: cp_model.CpModel,
            sequence: multi_sequence.MultiSequence[cp_model.IntVar],
            component_types: list[component.Component],
            **kwargs
    ) -> None:
        target_id = -1
        for i, component_type in enumerate(component_types):
            if component_type.name == self.target_name:
                target_id = i
                break

        quantity = [model.NewIntVar(0, len(sequence), str(uuid.uuid4())) for _ in range(len(sequence))]
        for i in range(len(sequence)):
            match = model.NewBoolVar(str(uuid.uuid4()))
            model.Add(sequence[i] == target_id).OnlyEnforceIf(match)
            model.Add(sequence[i] != target_id).OnlyEnforceIf(match.Not())

            quantity_prev = quantity[i - 1] if i > 0 else 0
            model.Add(quantity[i] == quantity_prev + 1).OnlyEnforceIf(match)
            model.Add(quantity[i] == quantity_prev).OnlyEnforceIf(match.Not())
        model.Add(quantity[-1] <= self.max_quantity)


class SymmetryConstraint(Constraint):
    """Forces the sequence to be symmetric on all dimensions."""
    def __call__(self, sequence: multi_sequence.MultiSequence[component.Component], **kwargs) -> bool:
        if len(sequence.dims) == 2:
            for y in range(sequence.dims[0]):
                for x in range(sequence.dims[1]):
                    if (
                        isinstance(sequence[y, x], type(None))
                        or isinstance(sequence[sequence.dims[0] - y - 1, x], type(None))
                        or isinstance(sequence[y, sequence.dims[1] - x - 1], type(None))
                    ):
                        continue
                    if (
                        sequence[y, x].name != sequence[sequence.dims[0] - y - 1, x].name
                        or sequence[y, x].name != sequence[y, sequence.dims[1] - x - 1].name
                    ):
                        return False
            return True
        elif len(sequence.dims) == 3:
            for x in range(sequence.dims[0]):
                for y in range(sequence.dims[1]):
                    for z in range(sequence.dims[2]):
                        if (
                            isinstance(sequence[x, y, z], type(None))
                            or isinstance(sequence[sequence.dims[0] - x - 1, y, z], type(None))
                            or isinstance(sequence[x, sequence.dims[1] - y - 1, z], type(None))
                            or isinstance(sequence[x, y, sequence.dims[2] - z - 1], type(None))
                        ):
                            continue
                        if (
                            sequence[x, y, z].name != sequence[sequence.dims[0] - x - 1, y, z].name
                            or sequence[x, y, z].name != sequence[x, sequence.dims[1] - y - 1, z].name
                            or sequence[x, y, z].name != sequence[x, y, sequence.dims[2] - z - 1].name
                        ):
                            return False
            return True
        raise NotImplementedError("Symmetry constraint only available for 2 or 3 dimensions!")

    def apply_to_model(
            self,
            model: cp_model.CpModel,
            sequence: multi_sequence.MultiSequence[cp_model.IntVar],
            component_types: list[component.Component],
            **kwargs
    ) -> None:
        if len(sequence.dims) == 2:
            for y in range(sequence.dims[0]):
                for x in range(sequence.dims[1]):
                    model.Add(sequence[y, x] == sequence[sequence.dims[0] - y - 1, x])
                    model.Add(sequence[y, x] == sequence[y, sequence.dims[1] - x - 1])
        elif len(sequence.dims) == 3:
            for x in range(sequence.dims[0]):
                for y in range(sequence.dims[1]):
                    for z in range(sequence.dims[2]):
                        model.Add(sequence[x, y, z] == sequence[sequence.dims[0] - x - 1, y, z])
                        model.Add(sequence[x, y, z] == sequence[x, sequence.dims[1] - y - 1, z])
                        model.Add(sequence[x, y, z] == sequence[x, y, sequence.dims[2] - z - 1])
        else:
            raise NotImplementedError("Symmetry constraint only available for 2 or 3 dimensions!")


class PlacementRuleConstraint(Constraint):
    """Enforces component placement rules."""
    def component_name(self, comp: component.Component | None) -> str:
        """Returns the name of the component, or "incomplete" if None.

        :param comp: The component or None.
        :return: The name of the component or "incomplete"
        """
        return "incomplete" if isinstance(comp, type(None)) else comp.name

    def __call__(self, sequence: multi_sequence.MultiSequence[component.Component], **kwargs) -> bool:
        for y in range(sequence.dims[0]):
            for x in range(sequence.dims[1]):
                up = self.component_name(sequence[y - 1, x]) if y > 0 else "wall"
                right = self.component_name(sequence[y, x + 1]) if x < sequence.dims[1] - 1 else "wall"
                down = self.component_name(sequence[y + 1, x]) if y < sequence.dims[0] - 1 else "wall"
                left = self.component_name(sequence[y, x - 1]) if x > 0 else "wall"
                if not isinstance(sequence[y, x], type(None)) and not sequence[y, x].placement_rule(
                        up,
                        right,
                        down,
                        left
                ):
                    return False
        return True

    def apply_to_model(
            self,
            model: cp_model.CpModel,
            sequence: multi_sequence.MultiSequence[cp_model.IntVar],
            component_types: list[component.Component],
            **kwargs
    ) -> None:
        for y in range(sequence.dims[0]):
            for x in range(sequence.dims[1]):
                up = sequence[y - 1, x] if y > 0 else -1
                right = sequence[y, x + 1] if x < sequence.dims[0] - 1 else -1
                down = sequence[y + 1, x] if y < sequence.dims[0] - 1 else -1
                left = sequence[y, x - 1] if x > 0 else -1
                satisfied_vars = [
                    component_type.placement_rule.to_model(
                        model,
                        [comp.name for comp in component_types],
                        up,
                        right,
                        down,
                        left
                    )
                    for component_type in component_types
                ]
                satisfied = model.NewBoolVar(str(uuid.uuid4()))
                model.AddElement(sequence[y, x], satisfied_vars, satisfied)
                model.Add(satisfied == 1)


class CenteredBearingsConstraint(Constraint):
    """Ensures rotor bearings are centered."""
    def __init__(self, shaft_width: int) -> None:
        """Constructs a CenteredBearingsConstraint object.

        :param shaft_width: The width of the rotor shaft.
        """
        self.shaft_width = shaft_width

    def __call__(self, sequence: multi_sequence.MultiSequence[component.Component], **kwargs) -> bool:
        for y in range(sequence.dims[0]):
            for x in range(sequence.dims[1]):
                if sequence.dims[0] % 2:
                    mid = (sequence.dims[0] - 1) // 2
                    r = (self.shaft_width - 1) // 2
                    if mid - r <= x <= mid + r and mid - r <= y <= mid + r:
                        if not isinstance(sequence[y, x], type(None)) and sequence[y, x].name != "bearing":
                            return False
                    else:
                        if not isinstance(sequence[y, x], type(None)):
                            if sequence[y, x].name == "bearing":
                                return False
                else:
                    mid = sequence.dims[0] // 2 - 1
                    r_left = self.shaft_width // 2 - 1
                    r_right = self.shaft_width // 2
                    if mid - r_left <= x <= mid + r_right and mid - r_left <= y <= mid + r_right:
                        if not isinstance(sequence[y, x], type(None)) and sequence[y, x].name != "bearing":
                            return False
                    else:
                        if not isinstance(sequence[y, x], type(None)):
                            if sequence[y, x].name == "bearing":
                                return False
        return True

    def apply_to_model(
            self,
            model: cp_model.CpModel,
            sequence: multi_sequence.MultiSequence[cp_model.IntVar],
            component_types: list[component.Component],
            **kwargs
    ) -> None:
        name_to_id = {comp.name: i for i, comp in enumerate(component_types)}
        for y in range(sequence.dims[0]):
            for x in range(sequence.dims[1]):
                if sequence.dims[0] % 2:
                    mid = (sequence.dims[0] - 1) // 2
                    r = (self.shaft_width - 1) // 2
                    if mid - r <= x <= mid + r and mid - r <= y <= mid + r:
                        model.Add(sequence[y, x] == name_to_id["bearing"])
                    else:
                        model.Add(sequence[y, x] != name_to_id["bearing"])
                else:
                    mid = sequence.dims[0] // 2 - 1
                    r_left = self.shaft_width // 2 - 1
                    r_right = self.shaft_width // 2
                    if mid - r_left <= x <= mid + r_right and mid - r_left <= y <= mid + r_right:
                        model.Add(sequence[y, x] == name_to_id["bearing"])
                    else:
                        model.Add(sequence[y, x] != name_to_id["bearing"])
