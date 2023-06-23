"""NuclearCraft: Overhauled turbine rotor blades."""

from ... import utils


class RotorBlade(utils.component.Component):
    """An object representing a NuclearCraft: Overhauled turbine rotor blade."""
    def __init__(self, name: str, efficiency: float, expansion: float) -> None:
        """Constructs a RotorBlade object.

        :param name: The name of the rotor blade.
        :param efficiency: The efficiency of the rotor blade.
        :param expansion: The expansion of the rotor blade.
        """
        super().__init__(name, {
            "efficiency": efficiency,
            "expansion": expansion
        }, utils.placement_rule.PlacementRule())

    @property
    def efficiency(self) -> float:
        return self.stats["efficiency"]

    @property
    def expansion(self) -> float:
        return self.stats["expansion"]


STEEL = RotorBlade("steel", 1.0, 1.4)
EXTREME = RotorBlade("extreme", 1.1, 1.6)
SIC_SIC_CMC = RotorBlade("sic_sic_cmc", 1.2, 1.8)
STATOR = RotorBlade("stator", -1.0, 0.75)

ROTOR_BLADE_TYPES = [STEEL, EXTREME, SIC_SIC_CMC, STATOR]
