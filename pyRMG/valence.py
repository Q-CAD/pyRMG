class ONCVValences:
    def __init__(self):
        self.valence = {
            "Ag": 19, "Al": 11, "Ar": 8, "As": 5, "Au": 19,
            "Ba": 10, "Be": 4, "Bi": 15, "B": 3, "Br": 7,
            "Ca": 10, "Cd": 20, "Cl": 7, "C": 4, "Co": 17,
            "Cr": 14, "Cs": 9, "Cu": 19, "Fe": 16, "F": 7,
            "Ga": 13, "Ge": 14, "He": 2, "Hf": 26, "H": 1,
            "In": 13, "I": 17, "K": 9, "Kr": 8, "La": 11,
            "Li": 3, "Mg": 10, "Mn": 15, "Mo": 14, "Na": 9,
            "Nb": 13, "Ne": 8, "Ni": 18, "N": 5, "O": 6,
            "Pb": 14, "Pd": 18, "P": 5, "Po": 16, "Rb": 9,
            "Rh": 17, "Ru": 16, "Sb": 15, "Sc": 11, "Se": 6,
            "Si": 4, "Sn": 14, "S": 6, "Sr": 10, "Ta": 27,
            "Tc": 15, "Te": 16, "Ti": 12, "Tl": 13, "V": 13,
            "Xe": 18, "Y": 11, "Zn": 20, "Zr": 12
        }
    
    def get_valence(self, element):
        return self.valence.get(element, None)

