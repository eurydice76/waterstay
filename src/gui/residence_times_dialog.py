from PyQt5 import QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class ResidenceTimesDialog(QtWidgets.QDialog):

    def __init__(self, occupancy, mol_ids, reader, *args, **kwargs):

        super(ResidenceTimesDialog, self).__init__(*args, **kwargs)

        self.setGeometry(0, 0, 1000, 400)

        self._occupancy = occupancy

        self._mol_ids = mol_ids

        self._reader = reader

        self._residence_times = occupancy.sum(axis=1)/self._reader.n_frames
        self._residence_times *= 100.0
        self._residence_times = list(zip(self._mol_ids, self._residence_times))
        self._residence_times.sort(key=lambda x: x[1], reverse=True)

        self.init_ui()

    def init_ui(self):
        """Set the the widgets of the dialog
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def build_events(self):

        self._residence_times_table.verticalHeader().sectionClicked.connect(self.on_select_row)
        self._residence_times_table.selectionModel().selectionChanged.connect(self.on_select_cell)

    def on_select_row(self, row_index):
        """Event called when a full row of the residence time table is selected

        Args:
            row_index (int): the index of the seletced row
        """

        mol_index = int(self._residence_times_table.item(row_index, 0).text())

        self.update_occupancy_plot(mol_index)

    def on_select_cell(self, event):
        """Event called when a cell of the residence time table is selected

        Args:
            event(PtQt5.QtWidgets.QTableItem): the event
        """

        mol_index = int(self._residence_times_table.item(
            self._residence_times_table.currentRow(), 0).text())

        self.update_occupancy_plot(mol_index)

    def update_occupancy_plot(self, mol_index):
        """Update the occupancy plot with a selected molecule

        Args:
            mol_index (int): the index of the selected molecule
        """

        try:
            idx = self._mol_ids.index(mol_index)
        except ValueError:
            return

        occ = self._occupancy[idx, :]

        # Case of the initial plot, plot the occupancy
        if not hasattr(self, '_plot'):
            self._plot, = self._axes.plot(occ)
        # If there is already a plot, just update the y data
        else:
            self._plot.set_ydata(occ)

        self._canvas.draw()

    def build_widgets(self):
        """Build the widgets of the dialog
        """

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('frame')
        self._axes.set_ylabel('occupancy')
        self._axes.set_xlim([0, self._reader.n_frames-1])
        self._axes.set_ylim([-1, 2])
        self._axes.set_xticks(range(self._reader.n_frames))
        self._axes.set_yticks(range(0, 2))
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        # Build the table that will show the results
        self._residence_times_table = QtWidgets.QTableWidget()
        self._residence_times_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._residence_times_table.setSelectionMode(QtWidgets.QTableView.SingleSelection)

        n_molecules = len(self._mol_ids)
        self._residence_times_table.setColumnCount(2)
        self._residence_times_table.setHorizontalHeaderLabels(['molecule id', 'residence time (%)'])
        self._residence_times_table.setRowCount(len(self._mol_ids))
        self._residence_times_table.setSortingEnabled(True)

        # Fill the residence times table
        for i in range(n_molecules):
            mol_id, time = self._residence_times[i]
            self._residence_times_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(mol_id)))
            self._residence_times_table.setItem(
                i, 1, QtWidgets.QTableWidgetItem("{:8.3f}".format(time)))

        # Plot the first entry by default
        self.update_occupancy_plot(int(self._residence_times_table.item(0, 0).text()))

    def build_layout(self):
        """Set the layout for the dialog
        """

        self._hl = QtWidgets.QHBoxLayout()
        self._hl.addWidget(self._residence_times_table)

        self._vl = QtWidgets.QVBoxLayout()

        self._vl.addWidget(self._canvas)
        self._vl.addWidget(self._toolbar)

        self._hl.addLayout(self._vl)

        self.setLayout(self._hl)
