import abc
import os
import yaml

import numpy as np

import waterstay

from waterstay.database import CHEMICAL_ELEMENTS
from waterstay.extensions.connectivity import PyConnectivity

STANDARD_RESIDUES = ['AIB', 'ALA', 'ARG', 'ARGN', 'ASN', 'ASP', 'ASPH', 'CYS', 'CYS2', 'CYSH', 'CYX',
                     'GLN', 'GLU', 'GLUH', 'GLY', 'HIS', 'HISD', 'HISE', 'HISH', 'ILE', 'LEU', 'LYS',
                     'LYSH', 'MET', 'PGLU', 'PHE', 'PRO', 'QLN', 'SER', 'THR', 'TYR', 'TRP', 'VAL']


class IReader(abc.ABC):

    def __init__(self, filename):

        if not os.path.exists(filename):
            raise IOError("The file {} does not exist.".format(filename))

        self._filename = filename

        self._fin = open(self._filename, "r")

        self._n_frames = 0

        self._n_atoms = 0

    def __del__(self):
        self._fin.close()

    @property
    def filename(self):
        return self._filename

    @property
    def n_atoms(self):
        return self._n_atoms

    @property
    def atom_ids(self):
        return self._atom_ids

    @property
    def atom_names(self):
        return self._atom_names

    @property
    def atom_types(self):
        return self._atom_types

    @property
    def residue_ids(self):
        return self._residue_ids

    @property
    def residue_names(self):
        return self._residue_names

    @property
    def n_frames(self):
        return self._n_frames

    @abc.abstractmethod
    def parse_first_frame(self):
        pass

    @abc.abstractmethod
    def read_frame(self, frame):
        pass

    @abc.abstractmethod
    def read_pbc(self, frame):
        pass

    def get_water_indexes(self, watername="SOL"):

        indexes = []

        resids, resnames, _, _, _ = self.read_frame(0)

        current_mol_index = None
        for i, resname in enumerate(resnames):
            if resname != watername:
                continue

            mol_index = resids[i]
            if mol_index != current_mol_index:
                if current_mol_index is not None:
                    indexes.append(new_mol)
                new_mol = [i]
                current_mol_index = mol_index
            else:
                new_mol.append(i)

        if new_mol:
            indexes.append(new_mol)

        return indexes

    def guess_atom_types(self):

        symbols = [at['symbol'].upper() for at in CHEMICAL_ELEMENTS['atoms'].values()]

        self._atom_types = []
        for i in range(self._n_atoms):

            atom_name = self._atom_names[i]
            residue_name = self._residue_names[i]

            # Remove the trailing and initial digits from the upperized atom names
            upper_atom_name = atom_name.upper()
            upper_atom_name = upper_atom_name.lstrip('0123456789').rstrip('0123456789')

            # Case of the an atom that belongs to a standard residue
            # Guess the atom type by the starting from the first alpha letter from the left,
            # increasing the word by one letter if there was no success in guessing the atom type
            if residue_name in STANDARD_RESIDUES:

                start = 1
                while True:
                    upper_atom_name = upper_atom_name[:start]
                    if upper_atom_name in symbols:
                        self._atom_types.append(upper_atom_name.capitalize())
                        break
                    if start > len(atom_name):
                        raise ValueError('Unknown atom type: {}'.format(atom_name))
                    start += 1
            # Case of the an atom that does not belong to a standard residue
            # Guess the atom type by the starting from whole atom name,
            # decreasing the word by one letter from the right if there was no success in guessing the atom type
            else:
                start = len(upper_atom_name)
                while True:
                    upper_atom_name = upper_atom_name[:start]
                    if upper_atom_name in symbols:
                        self._atom_types.append(upper_atom_name.capitalize())
                        break
                    # print(upper_atom_name)
                    if start == 0:
                        raise ValueError('Unknown atom type: {}'.format(atom_name))
                    start -= 1

    def build_connectivity(self, frame):

        # Read the first frame to fetch the residue and atom names
        coords = self.read_frame(frame)

        lower_bound = coords.min(axis=0)
        lower_bound -= 1.0e-6

        upper_bound = coords.max(axis=0)
        upper_bound += 1.0e-6

        cov_radii = [CHEMICAL_ELEMENTS['atoms'][at]['covalent_radius']
                     for at in self._atom_types]

        connectivity_builder = PyConnectivity(lower_bound, upper_bound, 0, 10, 18)

        for index, xyz, radius in zip(range(self._n_atoms), coords, cov_radii):
            connectivity_builder.add_point(index, xyz, radius)

        bonds = connectivity_builder.find_collisions()

        return bonds
