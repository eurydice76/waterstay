import os
import sys

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from waterstay.__pkginfo__ import __version__
from waterstay.readers.reader_registry import REGISTERED_READERS
from waterstay.gui.molecular_viewer import MolecularViewer


class MainWindow(QtWidgets.QMainWindow):

    selected_atom_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def init_ui(self):

        self.build_menu()

        self.statusBar().showMessage("waterstay version {}".format(__version__))

        self._main_frame = QtWidgets.QFrame(self)

        self.build_widgets()

        self.build_layout()

        self._molecular_viewer.renderer.ResetCamera()

        self._main_frame.setLayout(self._vl)
        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 800, 800)

        self.show()

        self._molecular_viewer.iren.Initialize()

        self._molecular_viewer.iren.Start()

        # Signals/slots
        self._atoms_table.verticalHeader().sectionClicked.connect(self.on_row_select)
        self._atoms_table.selectionModel().selectionChanged.connect(self.on_cell_select)
        self._frame_slider.valueChanged.connect(self.on_change_frame)
        self._frame_spinbox.valueChanged.connect(self.on_change_frame)
        self.selected_atom_changed.connect(self._molecular_viewer.on_pick_atom)
        self._molecular_viewer.picked_atom_changed.connect(self.on_pick_atom)

    def on_change_frame(self, frame):
        """Event handler when a new frame is selected from the frame slider of the frame spinbox

        Args:
            frame (int): the selected frame
        """

        self._frame_slider.setValue(frame)
        self._frame_spinbox.setValue(frame)

        self._molecular_viewer.set_coordinates(frame)

    def build_menu(self):
        """Build the menu of the main window.
        """

        file_action = QtWidgets.QAction(QtGui.QIcon('file.png'), '&File', self)
        file_action.setShortcut('Ctrl+O')
        file_action.setStatusTip('Open trajectory file')
        file_action.triggered.connect(self.on_open_trajectory_file)

        exit_action = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.on_quit_application)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        fileMenu.addAction(file_action)
        fileMenu.addAction(exit_action)

    def build_widgets(self):
        """Build the widgets of the main window.
        """

        self._atoms_table = QtWidgets.QTableWidget()
        self._atoms_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._atoms_table.setSelectionMode(QtWidgets.QTableView.SingleSelection)
        self._atoms_table.setColumnCount(7)
        self._atoms_table.setHorizontalHeaderLabels(
            ['residue name', 'residue id', 'atom name', 'atom id', 'x', 'y', 'z'])

        self._molecular_viewer = MolecularViewer(self._main_frame)

        self._frame_slider = QtWidgets.QSlider(Qt.Horizontal)
        self._frame_spinbox = QtWidgets.QSpinBox()

    def build_layout(self):
        """Build the layout of the main window.
        """

        self._vl = QtWidgets.QVBoxLayout()
        self._vl.addWidget(self._molecular_viewer.iren)

        hl = QtWidgets.QHBoxLayout()
        hl.addWidget(self._frame_slider)
        hl.addWidget(self._frame_spinbox)

        self._vl.addLayout(hl)
        self._vl.addWidget(self._atoms_table)

    def on_row_select(self, row_index):
        """Event handler called when an entire row of the atoms table is selected.

        Args:
            row_index(int): the select row
        """

        self.select_atom(row_index)

    def on_cell_select(self, item):
        """Event handler called when a cell of the atoms table is selected

        Args:
            item (PyQt5.QtCore.QItemSelection): the selected cell
        """

        selected_rows = item.indexes()

        if not selected_rows:
            return

        selected_atom = selected_rows[0].row()

        self.select_atom(selected_atom)

    def select_atom(self, selected_atom):
        """Select an atom.

        Args:
            selected_atom (int): the index of the selected atom
        """

        self.selected_atom_changed.emit(selected_atom)

    def on_open_trajectory_file(self):
        """Opens a trajectory file.
        """

        # Pop up a file browser
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        trajectory_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open trajectory file", "", "PDB Files (*.pdb);;Gromacs Files (*.gro)", options=options)

        # If not trajectory file was selected, exit
        if not trajectory_file:
            return

        # Take the trajectory reader corresponding to the selected trajectory based on the trajectory file extension
        _, ext = os.path.splitext(trajectory_file)
        reader = REGISTERED_READERS[ext](trajectory_file)

        # Update the atoms table
        self.fill_atoms_table(reader, 0)

        # Update the molecular viewer
        self._molecular_viewer.set_reader(reader)

        # Update the frame slider
        self._frame_slider.setMinimum(0)
        self._frame_slider.setMaximum(reader.n_frames-1)
        self._frame_slider.setValue(0)

        # Updathe the frame editor
        self._frame_spinbox.setMinimum(0)
        self._frame_spinbox.setMaximum(reader.n_frames-1)
        self._frame_spinbox.setValue(0)

        # Update the status bar
        self.statusBar().showMessage("Loaded {} trajectory file".format(trajectory_file))

    def fill_atoms_table(self, reader, frame):
        """Fill the atoms table with the atom contents of a trajectory.

        Args:
            reader (IReader): the trajectory object
            frame (int): the frame to read
        """

        residue_ids = reader.residue_ids
        residue_names = reader.residue_names
        atom_ids = reader.atom_ids
        atom_names = reader.atom_names

        coords = reader.read_frame(frame)

        n_atoms = reader.n_atoms

        self._atoms_table.setRowCount(n_atoms)

        for i in range(n_atoms):
            self._atoms_table.setItem(i, 0, QtWidgets.QTableWidgetItem(residue_names[i]))
            self._atoms_table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(residue_ids[i])))
            self._atoms_table.setItem(i, 2, QtWidgets.QTableWidgetItem(atom_names[i]))
            self._atoms_table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(atom_ids[i])))
            self._atoms_table.setItem(
                i, 4, QtWidgets.QTableWidgetItem("{:8.3f}".format(coords[i, 0])))
            self._atoms_table.setItem(
                i, 5, QtWidgets.QTableWidgetItem("{:8.3f}".format(coords[i, 1])))
            self._atoms_table.setItem(
                i, 6, QtWidgets.QTableWidgetItem("{:8.3f}".format(coords[i, 2])))

    def on_pick_atom(self, picked_atom):
        """Event handler when an atom is picked from the molecular viewer.

        Args:
            picked_atom (int): the index of the picked atom
        """

        self._atoms_table.selectRow(picked_atom)

    def on_quit_application(self):
        """Event handler when the application is exited.
        """

        choice = QtWidgets.QMessageBox.question(self, 'Quit',
                                                "Do you really want to quit?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec_())
