import nuclearcraft_designer

if __name__ == "__main__":
    s = nuclearcraft_designer.overhauled.turbine_rotor_blade.optimal_rotor_blade_sequence(
        10,
        4.0,
        [
            nuclearcraft_designer.overhauled.turbine_rotor_blade.STEEL,
            nuclearcraft_designer.overhauled.turbine_rotor_blade.EXTREME,
            nuclearcraft_designer.overhauled.turbine_rotor_blade.SIC_SIC_CMC,
            nuclearcraft_designer.overhauled.turbine_rotor_blade.STATOR
        ],
        [-1, -1, -1, 1]
    )
    for i in s:
        print(i.name)
