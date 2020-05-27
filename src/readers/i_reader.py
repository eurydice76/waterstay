import abc
import os

import numpy as np

from waterstay.database import CHEMICAL_ELEMENTS
from waterstay.extensions.connectivity import PyConnectivity
from waterstay.extensions.atoms_in_shell import atoms_in_shell

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

    def get_mol_indexes(self, target_mol, target_atoms):
        """Return the nested list of the indexes matching a molecule name and target atoms

        Args:
            target_mol (str): the target molecule
            target_atoms (list): the list of target atoms (str)
        """

        indexes = []

        current_mol_index = None
        for i, resname in enumerate(self._residue_names):
            if resname != target_mol:
                continue

            mol_index = self._residue_ids[i]
            if mol_index != current_mol_index:
                if current_mol_index is not None:
                    indexes.append(new_mol)
                if self._atom_names[i] in target_atoms:
                    new_mol = [i]
                current_mol_index = mol_index
            else:
                if self._atom_names[i] in target_atoms:
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
        """Build the connectivity for the whole system at a given frame.

        Args:
            frame (int): the selected frame
        """

        # Read the first frame to fetch the residue and atom names
        coords = self.read_frame(frame)

        # Compute the bounding box of the system
        lower_bound = coords.min(axis=0)
        upper_bound = coords.max(axis=0)

        # Enlarge it a bit to not miss any atom
        lower_bound -= 1.0e-6
        upper_bound += 1.0e-6

        # Fetch the covalent radii from the database
        cov_radii = [CHEMICAL_ELEMENTS['atoms'][at]['covalent_radius'] for at in self._atom_types]

        # Initializes the octree used to build the connectivity
        connectivity_builder = PyConnectivity(lower_bound, upper_bound, 0, 10, 18)

        # Add the points to the octree
        for index, xyz, radius in zip(range(self._n_atoms), coords, cov_radii):
            connectivity_builder.add_point(index, xyz, radius)

        # Compute the collisions
        bonds = connectivity_builder.find_collisions(1.0e-1)

        return bonds

    def mol_in_shell(self, mol_name, target_atoms, center, radius):
        """Compute the residence time of molecules of a given type which are within a shell around an atomic center.

        Args:
            mol_name (str): the type of the molecules to scan
            target_atoms (list): the list of atoms to scan
            center (int): the index of the atomic center
            radius (float): the radius to scan around the atomic center
        """

        # Retrieve the indexes of the atoms which belongs to each molecule of the selected type
        target_mol_indexes = self.get_mol_indexes(mol_name, target_atoms)

        # Initialize the output array
        mol_residence_times = np.zeros((len(target_mol_indexes), self._n_frames), dtype=np.int32)

        # Loop over the frame of the trajectory
        for frame in range(self._n_frames):

            # Read the frame at time=frame
            coords = self.read_frame(frame)

            # Read the direct cell at time=frame
            cell = self.read_pbc(frame)

            # Compute the reverse cell at time=frame
            rcell = np.linalg.inv(cell)

            # Scan for the molecules of the selected type which are found around the atomic center by the selected radius
            atoms_in_shell(coords, cell, rcell, target_mol_indexes,
                           center, radius, mol_residence_times[:, frame])

            mol_ids = [self._residue_ids[v[0]] for v in target_mol_indexes]

        return mol_ids, mol_residence_times
