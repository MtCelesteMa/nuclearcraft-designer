"""NuclearCraft reactor/turbine components."""


class Component:
    """NuclearCraft reactor/turbine components."""
    def __init__(self, name: str) -> None:
        """Constructs a Component object.

        :param name: The name of the component.
        """
        self.name = name
