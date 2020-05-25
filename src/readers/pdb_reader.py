import numpy as np

from .i_reader import IReader
from .reader_registry import register_reader


@register_reader('.pdb')
class PDBReader(IReader):

    def __init__(self, filename):

        IReader.__init__(self, filename)

        # Compute the number of atoms
        self._n_atoms = 0
        while True:
            line = self._fin.readline()
            if line[:3] == "TER":
                break
            self._n_atoms += 1

        # Substract the first lines of the files
        self._n_atoms -= 5

        self._fin.seek(0)

        # Loop over the file to get the length of all title lines (:-( they change over the file)
        # Compute also the number of frames
        self._pbc_starts = []
        self._frame_starts = []
        self._n_frames = 0
        eof = False
        while True:
            for i in range(self._n_atoms + 7):
                line = self._fin.readline()
                if not line:
                    eof = True
                    break
                if i == 2:
                    self._pbc_starts.append(self._fin.tell())
                elif i == 4:
                    self._frame_starts.append(self._fin.tell())
            if eof:
                break

            self._n_frames += 1

        self._fin.seek(self._frame_starts[0])

        self._coords_size = 79

        self._frame_size = self._n_atoms*self._coords_size

    def read_frame(self, frame):

        # Rewind the file to the beginning of the frame
        self._fin.seek(self._frame_starts[frame])

        data = self._fin.read(self._frame_size)

        residue_ids = []
        residue_names = []
        atom_names = []
        atom_ids = []
        coords = np.empty((self._n_atoms, 3), dtype=np.float)

        for i in range(self._n_atoms):
            start = i*self._coords_size
            end = start + self._coords_size
            line = data[start:end]
            atom_ids.append(int(line[6:11]))
            atom_names.append(line[12:16].strip())
            residue_names.append(line[17:20].strip())
            residue_ids.append(int(line[22:26]))
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            coords[i, :] = [x, y, z]

        return residue_ids, residue_names, atom_ids, atom_names, coords

    def read_pbc(self, frame):

        # Fold the frame
        frame %= self._n_frames

        # Rewind the file to the beginning of the frame
        self._fin.seek(self._pbc_starts[frame])

        data = self._fin.readline().split()

        a, b, c, alpha, beta, gamma = [float(v) for v in data[1:7]]

        alpha = np.deg2rad(alpha)
        beta = np.deg2rad(beta)
        gamma = np.deg2rad(gamma)

        cos_alpha = np.cos(alpha)
        cos_beta = np.cos(beta)
        cos_gamma = np.cos(gamma)
        sin_gamma = np.sin(gamma)

        pbc = np.zeros((3, 3), dtype=np.float)

        fact = (cos_alpha - cos_beta*cos_gamma)/sin_gamma

        # The a vector
        pbc[0, 0] = a

        # The b vector
        pbc[1, 0] = b*cos_gamma
        pbc[1, 1] = b*sin_gamma

        # The c vector
        pbc[2, 0] = c*cos_beta
        pbc[2, 1] = c*fact
        pbc[2, 2] = c*np.sqrt(1.0 - cos_beta*cos_beta - fact*fact)

        # Convert from angstroms to nanometers
        pbc *= 0.1

        return pbc