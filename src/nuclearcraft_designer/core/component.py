"""NuclearCraft reactor/turbine components."""

from . import placement_rule


class Component:
    """NuclearCraft reactor/turbine components."""
    def __init__(
            self,
            name: str,
            stats: dict[str, float],
            rule: placement_rule.PlacementRule
    ) -> None:
        """Constructs a Component object.

        :param name: The name of the component.
        """
        self.name = name
        self.stats = stats
        self.placement_rule = rule
