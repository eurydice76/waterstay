import sys

import numpy as np

from .i_reader import IReader
from .reader_registry import register_reader


@register_reader('.gro')
class GromacsReader(IReader):

    def __init__(self, filename):

        IReader.__init__(self, filename)

        # Read the title line and store its length
        first_title = self._fin.readline()
        first_title_size = len(first_title)

        # Read the number of atoms. Must be an integer.
        try:
            n_atoms = self._fin.readline()
            self._n_atoms_size = len(n_atoms)
            self._n_atoms = int(n_atoms)
        except ValueError:
            print("Invalid type for number of atoms: must be an int")
            sys.exit(1)

        # coords = self._fin.readline()
        # self._coords_size = len(coords)

        # self._frame_size = self._n_atoms*self._coords_size

        # # Restart from the beginning of the file
        # self._fin.seek(0)

        # # Go the end of the coordinates block
        # self._fin.read(first_title_size + self._n_atoms_size + self._frame_size)

        # # Read the PBC line
        # pbc = self._fin.readline()
        # self._pbc_size = len(pbc)

        # self._fin.seek(0)

        # # Loop over the file to get the length of all title lines (:-( they change over the file)
        # # Compute also the number of frames
        # self._title_sizes = []
        # self._n_frames = 0
        # eof = False
        # while True:
        #     for i in range(self._n_atoms + 3):
        #         line = self._fin.readline()
        #         if not line:
        #             eof = True
        #             break
        #         if i == 0:
        #             self._title_sizes.append(len(line))

        #     if eof:
        #         break

        #     self._n_frames += 1

        self._fin.seek(0)

        # Loop over the file to get the length of all title lines (:-( they change over the file)
        # Compute also the number of frames
        self._pbc_starts = []
        self._frame_starts = []
        self._n_frames = 0
        eof = False
        while True:
            for i in range(self._n_atoms + 3):
                line = self._fin.readline()
                if not line:
                    eof = True
                    break
                if i == 1:
                    self._frame_starts.append(self._fin.tell())
                elif i == self._n_atoms + 1:
                    self._pbc_starts.append(self._fin.tell())
            if eof:
                break

            self._n_frames += 1

        self._fin.seek(self._frame_starts[0])

        self._coords_size = 45

        self._frame_size = self._n_atoms*self._coords_size

        self.parse_first_frame()

    def parse_first_frame(self):

        # Rewind the file to the beginning of the first frame
        self._fin.seek(self._frame_starts[0])
        data = self._fin.read(self._frame_size)

        self._atom_names = []
        self._atom_ids = []
        self._atom_types = []
        self._residue_names = []
        self._residue_ids = []

        for i in range(self._n_atoms):
            start = i*self._coords_size
            end = start + self._coords_size
            line = data[start:end]
            self._residue_ids.append(int(line[0:5]))
            self._residue_names.append(line[5:10].strip())
            self._atom_names.append(line[10:15].strip())
            self._atom_ids.append(int(line[15:20]))

        self.guess_atom_types()

    def read_frame(self, frame):

        # Rewind the file to the beginning of the frame
        self._fin.seek(self._frame_starts[frame])

        data = self._fin.read(self._frame_size)

        coords = np.empty((self._n_atoms, 3), dtype=np.float)

        for i in range(self._n_atoms):
            start = i*self._coords_size
            end = start + self._coords_size
            line = data[start:end]
            x = float(line[20:28])
            y = float(line[28:36])
            z = float(line[36:44])
            coords[i, :] = [x, y, z]

        coords *= 10.0

        return coords

    def read_pbc(self, frame):

        # Fold the frame
        frame %= self._n_frames

        # Rewind the file to the beginning
        self._fin.seek(0)

        pbc = np.zeros((3, 3), dtype=np.float)

        title_sizes = sum(self._title_sizes[:frame+1])

        # Go to the beginning of the frame-th pbc block
        self._fin.seek(title_sizes + frame*(self._n_atoms_size + self._frame_size +
                                            self._pbc_size) + self._n_atoms_size + self._frame_size)

        data = [float(v) for v in self._fin.read(self._pbc_size).split()]

        n_data = len(data)
        if n_data == 3:
            np.fill_diagonal(pbc, data[0:3])
        elif n_data == 9:
            np.fill_diagonal(pbc, data[0:3])
            pbc[0, 1] = data[3]
            pbc[0, 2] = data[4]
            pbc[1, 0] = data[5]
            pbc[1, 2] = data[6]
            pbc[2, 0] = data[7]
            pbc[2, 1] = data[7]
        else:
            raise ValueError("Invalid PBC line")

        return pbc
