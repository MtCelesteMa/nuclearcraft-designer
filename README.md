# NuclearCraft Designer
Generates multiblock designs for NuclearCraft.

## Installation
NuclearCraft Designer can be installed via pip using the following command:
```shell
pip install nuclearcraft-designer
```

## Usage
Design the best rotor blade sequence of length 10 optimized for 400% expansion using a maximum of 1 SiC-SiC-CMC blade.
```python
from nuclearcraft_designer.overhauled import turbine_rotor_blade

if __name__ == "__main__":
    gen = turbine_rotor_blade.designer.RotorBladeSequenceDesigner().design_generator(
        10,
        4.0,
        {
            "sic_sic_cmc": 1
        }
    )
    seq = []
    for seq in gen:
        pass
    
    # Print the best sequence.
    for blade in seq:
        print(blade.name, end=" ")
    print()
```
Design the best dynamo coil configuration with a side length of 3 and a shaft width of 1:
```python
from nuclearcraft_designer.overhauled import turbine_dynamo_coil

if __name__ == "__main__":
    gen = turbine_dynamo_coil.designer.DynamoCoilConfigurationDesigner().design_generator(
        3,
        1,
        {
            "connector": 0  # Enabling connectors can lead to invalid designs.
        }
    )
    seq = []
    for seq in gen:
        pass

    for y in range(seq.dims[0]):
        for x in range(seq.dims[1]):
            print(seq[y, x].name, end=" ")
        print()
```

### OR-Tools Powered Designers
Certain NuclearCraft Designer designers have OR-Tools powered alternatives. They are generally faster than the normal designers, but are less reliable and may have fewer features.

OR-Tools is not a required dependency. Use the following command to install it:
```shell
pip install ortools
```
The above usage examples can be done as follows (with missing features omitted):
```python
from nuclearcraft_designer.overhauled import turbine_rotor_blade

if __name__ == "__main__":
    status, sequence = turbine_rotor_blade.beta_designer.RotorBladeSequenceDesigner().design(
        10,
        4.0,
        {
            "sic_sic_cmc": 1
        }
    )
    print(status)
    for blade in sequence:
        print(blade.name, end=" ")
    print()
```
Note that the OR-Tools powered designer can design 7x7 turbines in a reasonable amount of time, while the normal designer can't do so for 5x5 turbines.
```python
from nuclearcraft_designer.overhauled import turbine_dynamo_coil

if __name__ == "__main__":
    status, configuration = turbine_dynamo_coil.beta_designer.DynamoCoilConfigurationDesigner().design(
        7,
        1,
        {
            "connector": 0  # Enabling connectors can lead to invalid designs.
        }
    )
    print(status)
    for y in range(configuration.dims[0]):
        for x in range(configuration.dims[1]):
            print(configuration[y, x].name, end=" ")
        print()
```
