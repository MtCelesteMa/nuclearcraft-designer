# NuclearCraft Designer
Generates multiblock designs for NuclearCraft.

## Installation
NuclearCraft Designer can be installed via pip using the following command:
```shell
pip install git+https://github.com/MtCelesteMa/nuclearcraft-designer.git@v0.1.0
```

## Usage
Generate the best rotor blade sequence of length 10 optimized for 400% expansion using a maximum of 1 SiC-SiC-CMC blade.
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
