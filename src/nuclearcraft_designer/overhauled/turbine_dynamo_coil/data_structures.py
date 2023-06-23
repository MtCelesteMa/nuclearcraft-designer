"""NuclearCraft: Overhauled turbine dynamo coil data structures."""

from ... import utils


class DynamoCoil(utils.component.Component):
    """An object representing a NuclearCraft: Overhauled turbine dynamo coil."""
    def __init__(
            self,
            name: str,
            conductivity: float,
            placement_rule: utils.placement_rule.PlacementRule
    ) -> None:
        """Constructs a DynamoCoil object.

        :param name: The name of the dynamo coil.
        :param conductivity: The conductivity of the dynamo coil.
        :param placement_rule: The placement rule of the dynamo coil.
        """
        super().__init__(name, {"conductivity": conductivity}, placement_rule)

    @property
    def conductivity(self) -> float:
        return self.stats["conductivity"]


CASING = DynamoCoil("casing", -1.0, utils.placement_rule.PlacementRule())
BEARING = DynamoCoil("bearing", -1.0, utils.placement_rule.PlacementRule())
CONNECTOR = DynamoCoil("connector", -1.0, utils.placement_rule.CompoundPlacementRule([
    utils.placement_rule.SimplePlacementRule("magnesium", 1),
    utils.placement_rule.SimplePlacementRule("beryllium", 1),
    utils.placement_rule.SimplePlacementRule("aluminum", 1),
    utils.placement_rule.SimplePlacementRule("gold", 1),
    utils.placement_rule.SimplePlacementRule("copper", 1),
    utils.placement_rule.SimplePlacementRule("silver", 1)
], utils.placement_rule.LogicMode.OR))
MAGNESIUM = DynamoCoil("magnesium", 0.88, utils.placement_rule.CompoundPlacementRule([
    utils.placement_rule.SimplePlacementRule("bearing", 1),
    utils.placement_rule.SimplePlacementRule("connector", 1)
], utils.placement_rule.LogicMode.OR))
BERYLLIUM = DynamoCoil("beryllium", 0.9, utils.placement_rule.SimplePlacementRule("magnesium", 1))
ALUMINUM = DynamoCoil("aluminum", 1.0, utils.placement_rule.SimplePlacementRule("magnesium", 2))
GOLD = DynamoCoil("gold", 1.04, utils.placement_rule.SimplePlacementRule("aluminum", 1))
COPPER = DynamoCoil("copper", 1.06, utils.placement_rule.SimplePlacementRule("beryllium", 1))
SILVER = DynamoCoil("silver", 1.12, utils.placement_rule.CompoundPlacementRule([
    utils.placement_rule.SimplePlacementRule("gold", 1),
    utils.placement_rule.SimplePlacementRule("copper", 1)
], utils.placement_rule.LogicMode.AND))

DYNAMO_COIL_TYPES = [
    CASING,
    BEARING,
    CONNECTOR,
    MAGNESIUM,
    BERYLLIUM,
    ALUMINUM,
    GOLD,
    COPPER,
    SILVER
]
