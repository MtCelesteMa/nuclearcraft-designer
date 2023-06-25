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
        for i in range(len(sequence)):
            coords = sequence.int_to_tuple(i)
            if isinstance(sequence[coords], type(None)):
                continue
            for d in range(len(sequence.dims)):
                coords_ = tuple([
                    sequence.dims[i] - coords[i] - 1 if i == d else coords[i]
                    for i in range(len(sequence.dims))
                ])
                if isinstance(sequence[coords_], type(None)):
                    continue
                if sequence[coords].name != sequence[coords_].name:
                    return False
        return True

    def apply_to_model(
            self,
            model: cp_model.CpModel,
            sequence: multi_sequence.MultiSequence[cp_model.IntVar],
            component_types: list[component.Component],
            **kwargs
    ) -> None:
        for i in range(len(sequence)):
            coords = sequence.int_to_tuple(i)
            if isinstance(sequence[coords], type(None)):
                continue
            for d in range(len(sequence.dims)):
                coords_ = tuple([
                    sequence.dims[i] - coords[i] - 1 if i == d else coords[i]
                    for i in range(len(sequence.dims))
                ])
                model.Add(sequence[coords] == sequence[coords_])


class PlacementRuleConstraint(Constraint):
    """Enforces component placement rules."""
    def component_name(self, comp: component.Component | None) -> str:
        """Returns the name of the component, or "incomplete" if None.

        :param comp: The component or None.
        :return: The name of the component or "incomplete"
        """
        return "incomplete" if isinstance(comp, type(None)) else comp.name

    def __call__(self, sequence: multi_sequence.MultiSequence[component.Component], **kwargs) -> bool:
        for i in range(len(sequence)):
            coords = sequence.int_to_tuple(i)
            if len(coords) == 2:
                x, y = coords[1], coords[0]
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
            elif len(coords) == 3:
                x, y, z = coords
                xp = self.component_name(sequence[x + 1, y, z]) if x < sequence.dims[0] - 1 else "wall"
                xn = self.component_name(sequence[x - 1, y, z]) if x > 0 else "wall"
                yp = self.component_name(sequence[x, y + 1, z]) if y < sequence.dims[1] - 1 else "wall"
                yn = self.component_name(sequence[x, y - 1, z]) if y > 0 else "wall"
                zp = self.component_name(sequence[x, y, z + 1]) if z < sequence.dims[2] - 1 else "wall"
                zn = self.component_name(sequence[x, y, z - 1]) if z > 0 else "wall"
                if not isinstance(sequence[x, y, z], type(None)) and not sequence[x, y, z].placement_rule(
                        yp,
                        xp,
                        yn,
                        xn,
                        zp,
                        zn
                ):
                    return False
            else:
                raise NotImplementedError("Placement rule constraint only supports 2 and 3 dimensions!")
        return True

    def apply_to_model(
            self,
            model: cp_model.CpModel,
            sequence: multi_sequence.MultiSequence[cp_model.IntVar],
            component_types: list[component.Component],
            **kwargs
    ) -> None:
        for i in range(len(sequence)):
            coords = sequence.int_to_tuple(i)
            if len(coords) == 2:
                x, y = coords[1], coords[0]
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
            elif len(coords) == 3:
                x, y, z = coords
                xp = sequence[x + 1, y, z] if x < sequence.dims[0] - 1 else -1
                xn = sequence[x - 1, y, z] if x > 0 else -1
                yp = sequence[x, y + 1, z] if y < sequence.dims[1] - 1 else -1
                yn = sequence[x, y - 1, z] if y > 0 else -1
                zp = sequence[x, y, z + 1] if z < sequence.dims[2] - 1 else -1
                zn = sequence[x, y, z - 1] if z > 0 else -1
                satisfied_vars = [
                    component_type.placement_rule.to_model(
                        model,
                        [comp.name for comp in component_types],
                        yp,
                        xp,
                        yn,
                        xn,
                        zp,
                        zn
                    )
                    for component_type in component_types
                ]
                satisfied = model.NewBoolVar(str(uuid.uuid4()))
                model.AddElement(sequence[y, x], satisfied_vars, satisfied)
                model.Add(satisfied == 1)
            else:
                raise NotImplementedError("Placement rule constraint only supports 2 and 3 dimensions!")


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
