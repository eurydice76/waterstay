import logging
import os
import shutil
import sys

import yaml

from PyQt5 import QtCore, QtGui, QtWidgets

import waterstay
from waterstay.__pkginfo__ import __version__
from waterstay.database import STANDARD_RESIDUES
from waterstay.readers.i_reader import InvalidFileError
from waterstay.readers.reader_registry import REGISTERED_READERS
from waterstay.gui.logger_widget import QTextEditLogger
from waterstay.gui.molecular_viewer import MolecularViewer
from waterstay.gui.residence_times_dialog import ResidenceTimesDialog
from waterstay.gui.trjconv_settings_dialog import TrjConvSettingsDialog
from waterstay.utils.progress_bar import progress_bar


class MainWindow(QtWidgets.QMainWindow):
    """This class implements the main window of the application.
    """

    selected_atom_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):
        """Set the signal:slots of the main window
        """

        # Signals/slots
        self._atoms_table.verticalHeader().sectionClicked.connect(self.on_row_select)
        self._atoms_table.selectionModel().selectionChanged.connect(self.on_cell_select)
        self._frame_spinbox.valueChanged.connect(self.on_change_frame)
        self._target_residues.selectionModel().selectionChanged.connect(self.on_select_target_residues)
        self.selected_atom_changed.connect(self._molecular_viewer.on_pick_atom)
        self._molecular_viewer.picked_atom_changed.connect(self.on_pick_atom)
        self._molecular_viewer.show_atom_info.connect(self.on_show_atom_info)
        self._run.clicked.connect(self.run)

    def build_layout(self):
        """Build the layout of the main window.
        """

        main_layout = QtWidgets.QHBoxLayout()

        left_layout = QtWidgets.QVBoxLayout()

        left_layout.addWidget(self._atoms_table)

        parameters_layout = QtWidgets.QVBoxLayout()

        target_hlayout = QtWidgets.QHBoxLayout()
        target_hlayout.addWidget(self._target_residues)
        target_hlayout.addWidget(self._target_atoms)
        target_hlayout.addWidget(self._target_times)

        shell_radius_hlayout = QtWidgets.QHBoxLayout()
        shell_radius_hlayout.addWidget(self._shell_radius_label)
        shell_radius_hlayout.addWidget(self._shell_radius)

        parameters_layout.addLayout(target_hlayout)
        parameters_layout.addLayout(shell_radius_hlayout)

        left_layout.addLayout(parameters_layout)

        left_layout.addWidget(self._run)

        left_layout.addWidget(self._logger.widget)

        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self._molecular_viewer.iren)
        right_layout.addWidget(self._frame_spinbox)

        main_layout.addLayout(left_layout, stretch=1)
        main_layout.addLayout(right_layout, stretch=2)

        self._main_frame.setLayout(main_layout)

    def build_menu(self):
        """Build the menu of the main window.
        """

        file_action = QtWidgets.QAction('&File', self)
        file_action.setShortcut('Ctrl+O')
        file_action.setStatusTip('Open trajectory file')
        file_action.triggered.connect(self.on_open_trajectory_file)

        exit_action = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.on_quit_application)

        process_trajectory_action = QtWidgets.QAction('&Process trajectory', self)
        process_trajectory_action.setShortcut('Ctrl+P')
        process_trajectory_action.setStatusTip('Process trajectory using trjconv external program')
        process_trajectory_action.triggered.connect(self.on_process_trajectory)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')

        file_menu.addAction(file_action)
        file_menu.addAction(process_trajectory_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        database_menu = menubar.addMenu('&Database')

        add_standard_residue_action = QtWidgets.QAction('&Add standard residue', self)
        add_standard_residue_action.setShortcut('Ctrl+R')
        add_standard_residue_action.setStatusTip('Add a new standard residues to database')
        add_standard_residue_action.triggered.connect(self.on_add_standard_residue)

        database_menu.addAction(add_standard_residue_action)

        atomic_trace_menu = menubar.addMenu('&Atomic trace')

        clear_atomic_trace_action = QtWidgets.QAction('Clear', self)
        clear_atomic_trace_action.triggered.connect(self._molecular_viewer.on_clear_atomic_trace)

        open_atomic_trace_settings_action = QtWidgets.QAction('Settings', self)
        open_atomic_trace_settings_action.triggered.connect(self._molecular_viewer.on_open_atomic_trace_settings_dialog)

        show_atomic_trace_action = QtWidgets.QAction('Show', self)
        show_atomic_trace_action.triggered.connect(self._molecular_viewer.on_show_atomic_trace)

        atomic_trace_menu.addAction(clear_atomic_trace_action)
        atomic_trace_menu.addSeparator()
        atomic_trace_menu.addAction(show_atomic_trace_action)
        atomic_trace_menu.addAction(open_atomic_trace_settings_action)

    def build_widgets(self):
        """Build the widgets of the main window.
        """

        self._main_frame = QtWidgets.QFrame(self)

        self._atoms_table = QtWidgets.QTableWidget()
        self._atoms_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._atoms_table.setSelectionMode(QtWidgets.QTableView.SingleSelection)
        self._atoms_table.setColumnCount(7)
        self._atoms_table.setHorizontalHeaderLabels(['residue name', 'residue id', 'atom name', 'atom id', 'x', 'y', 'z'])

        self._molecular_viewer = MolecularViewer(self._main_frame)
        self._molecular_viewer.renderer.ResetCamera()
        self._molecular_viewer.iren.Initialize()
        self._molecular_viewer.iren.Start()

        self._frame_spinbox = QtWidgets.QSpinBox()

        self._target_residues = QtWidgets.QListWidget()
        self._target_residues.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._target_atoms = QtWidgets.QListWidget()
        self._target_atoms.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._target_times = QtWidgets.QListWidget()
        self._target_times.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._shell_radius_label = QtWidgets.QLabel()
        self._shell_radius_label.setText('Shell radius (A)')
        self._shell_radius = QtWidgets.QDoubleSpinBox()
        self._shell_radius.setMinimum(0.0)
        self._shell_radius.setValue(5)

        self._run = QtWidgets.QPushButton()
        self._run.setText('Run')

        self._logger = QTextEditLogger(self)
        self._logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self._logger)
        logging.getLogger().setLevel(logging.INFO)

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 1200, 800)

        self.statusBar().showMessage("waterstay version {}".format(__version__))
        self._progress_label = QtWidgets.QLabel('Progress')
        self._progress_bar = QtWidgets.QProgressBar()
        progress_bar.set_progress_widget(self._progress_bar)
        self.statusBar().showMessage("inspigtor {}".format(__version__))
        self.statusBar().addPermanentWidget(self._progress_label)
        self.statusBar().addPermanentWidget(self._progress_bar)

        icon_path = os.path.join(waterstay.__path__[0], "icons", "icon.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.show()

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

    def init_ui(self):
        """Set the widgets of the main window
        """

        self._reader = None

        self.build_widgets()

        self.build_layout()

        self.build_menu()

        self.build_events()

    def on_add_standard_residue(self):
        """Add a new residue to the database
        """

        residue, ok = QtWidgets.QInputDialog.getText(
            self, 'Enter residue name', 'Add standard residue name', QtWidgets.QLineEdit.Normal, '')

        if not ok or not residue:
            return

        if residue in STANDARD_RESIDUES:
            return

        STANDARD_RESIDUES.append(residue)

        homedir = os.path.expanduser('~')

        database_path = os.path.join(homedir, '.waterstay', 'residues.yml')

        with open(database_path, 'w') as file:
            yaml.dump(STANDARD_RESIDUES, file)

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

    def on_change_frame(self, frame):
        """Event handler when a new frame is selected from the frame slider of the frame spinbox

        Args:
            frame (int): the selected frame
        """

        self._frame_spinbox.setValue(frame)

        self._molecular_viewer.set_coordinates(frame)

    def on_open_trajectory_file(self):
        """Opens a trajectory file.
        """

        # Pop up a file browser
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        supported_files = ['(*{})'.format(ext) for ext in REGISTERED_READERS]
        supported_files = ';;'.join(supported_files)
        trajectory_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open trajectory file', '', supported_files, options=options)

        # If not trajectory file was selected, exit
        if not trajectory_file:
            return

        # Take the trajectory reader corresponding to the selected trajectory based on the trajectory file extension
        _, ext = os.path.splitext(trajectory_file)
        try:
            self._reader = REGISTERED_READERS[ext](trajectory_file)
        except InvalidFileError as error:
            logging.error(str(error))
            return

        # Update the atoms table
        self.fill_atoms_table(self._reader, 0)

        # Update the molecular viewer
        self._molecular_viewer.set_reader(self._reader)

        # Update the frame editor
        self._frame_spinbox.setMinimum(0)
        self._frame_spinbox.setMaximum(self._reader.n_frames-1)
        self._frame_spinbox.setValue(0)

        # Update the target residues combo box
        self._target_residues.clear()
        self._target_residues.addItems(sorted(set(self._reader.residue_names)))

        # Update the target times listview
        self._target_times.clear()
        self._target_times.addItems([str(v) for v in self._reader.times])

        # Update the status bar
        self.statusBar().showMessage("Loaded {} trajectory file".format(trajectory_file))

    def on_pick_atom(self, picked_atom):
        """Event handler when an atom is picked from the molecular viewer.

        Args:
            picked_atom (int): the index of the picked atom
        """

        self._atoms_table.selectRow(picked_atom)

    def on_process_trajectory(self):
        """Event handler called when the File -> Process trajectory menu item is fired.
        """

        if shutil.which('gmx') is None:
            logging.error('gmx program could not be found in the PATH')
            return

        dlg = TrjConvSettingsDialog()

        dlg.exec_()

    def on_quit_application(self):
        """Event handler when the application is exited.
        """

        choice = QtWidgets.QMessageBox.question(self, 'Quit',
                                                "Do you really want to quit?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()

    def on_row_select(self, row_index):
        """Event handler called when an entire row of the atoms table is selected.

        Args:
            row_index(int): the select row
        """

        self.select_atom(row_index)

    def on_select_target_residues(self):
        """Event handler called when the target molecule is changed
        """

        selected_target_residues = [item.text() for item in self._target_residues.selectedItems()]
        if not selected_target_residues:
            return

        atom_names = self._reader.atom_names

        target_atoms = set()
        for i, res_name in enumerate(self._reader.residue_names):
            if res_name in selected_target_residues:
                target_atoms.add(atom_names[i])

        target_atoms = sorted(target_atoms)

        self._target_atoms.clear()
        self._target_atoms.addItems(target_atoms)

    def on_show_atom_info(self, picked_atom):
        """Display information about the picked atom in the logger

        Args:
            picked_atom (int): the index of the picked atom
        """

        residue_name = self._atoms_table.item(picked_atom, 0).text()
        residue_id = self._atoms_table.item(picked_atom, 1).text()
        atom_name = self._atoms_table.item(picked_atom, 2).text()
        atom_id = self._atoms_table.item(picked_atom, 3).text()
        x = self._atoms_table.item(picked_atom, 4).text()
        y = self._atoms_table.item(picked_atom, 5).text()
        z = self._atoms_table.item(picked_atom, 6).text()

        info_string = "atom {}({}) of molecule {}({}) @ {},{},{}".format(atom_name,
                                                                         atom_id, residue_name, residue_id, x, y, z)

        logging.info(info_string)

    def run(self):
        """Run the application
        """

        if self._reader is None:
            return

        selected_target_residues = [item.text() for item in self._target_residues.selectedItems()]
        if not selected_target_residues:
            return

        selected_target_atoms = [item.text() for item in self._target_atoms.selectedItems()]
        if not selected_target_atoms:
            return

        selected_frames = [index.row() for index in self._target_times.selectedIndexes()]
        if not selected_frames:
            return

        shell_radius = self._shell_radius.value()
        if shell_radius <= 0.0:
            logging.error('The shell radius must be strictly positive')
            return

        center_atom_index = self._atoms_table.currentRow()
        if center_atom_index == -1:
            logging.error('No atomic center selected')
            return

        occupancies = self._reader.residues_in_shell(selected_target_residues, selected_target_atoms, center_atom_index, shell_radius, selected_frames=selected_frames)

        if occupancies is None:
            logging.error('No residue found in shell')
            return

        dlg = ResidenceTimesDialog(occupancies, self)
        dlg.show()

    def select_atom(self, selected_atom):
        """Select an atom.

        Args:
            selected_atom (int): the index of the selected atom
        """

        self.selected_atom_changed.emit(selected_atom)


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec_())
