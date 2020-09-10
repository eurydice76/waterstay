from PyQt5 import QtWidgets

import pandas as pd

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class ResidenceTimesDialog(QtWidgets.QDialog):

    def __init__(self, occupancies, *args, **kwargs):

        super(ResidenceTimesDialog, self).__init__(*args, **kwargs)

        self.setGeometry(0, 0, 1000, 400)

        self._occupancies = occupancies

        n_times = len(self._occupancies.columns)

        self._residence_times = pd.Series(100.0*self._occupancies.sum(axis=1)/n_times, index=self._occupancies.index)
        self._residence_times = self._residence_times.sort_values(ascending=False)

        self.init_ui()

    def init_ui(self):
        """Set the widgets of the dialog
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def build_events(self):
        """Build the signal/slots.
        """

        self._residence_times_table.verticalHeader().sectionClicked.connect(self.on_select_row)
        self._residence_times_table.selectionModel().selectionChanged.connect(self.on_select_cell)

    def on_select_row(self, row_index):
        """Event called when a full row of the residence time table is selected

        Args:
            row_index (int): the index of the selected row
        """

        residue_index = int(self._residence_times_table.item(row_index, 0).text())

        self.update_residence_time_plot(residue_index)

    def on_select_cell(self):
        """Event called when a cell of the residence time table is selected
        """

        residue_index = int(self._residence_times_table.item(self._residence_times_table.currentRow(), 0).text())

        self.update_residence_time_plot(residue_index)

    def update_residence_time_plot(self, residue_index):
        """Update the residence time plot for a given residue index

        Args:
            residue_index (int): the residue index
        """

        occupancy = self._occupancies.loc[residue_index, :]

        self._axes.clear()
        self._axes.set_xlabel('time')
        self._axes.set_ylabel('occupancy')

        # self._axes.set_xlim([0, len(self._occupancies.columns)-1])
        self._axes.set_ylim([-1, 2])

        times = self._occupancies.columns

        self._plot, = self._axes.plot(times, occupancy, '.')

        self._canvas.draw()

    def build_widgets(self):
        """Build the widgets of the dialog
        """

        # Build the matplotlib widget
        self._figure = Figure()
        self._axes = self._figure.add_subplot(111)

        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        # Build the table that will show the results
        self._residence_times_table = QtWidgets.QTableWidget()
        self._residence_times_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._residence_times_table.setSelectionMode(QtWidgets.QTableView.SingleSelection)

        n_residues = len(self._residence_times)
        self._residence_times_table.setRowCount(n_residues)
        self._residence_times_table.setColumnCount(2)
        self._residence_times_table.setHorizontalHeaderLabels(['residue id', 'residence time (%)'])
        self._residence_times_table.setSortingEnabled(True)

        # Fill the residence times table
        for i, v in enumerate(self._residence_times.index):
            time = self._residence_times.loc[v]
            self._residence_times_table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(v)))
            self._residence_times_table.setItem(i, 1, QtWidgets.QTableWidgetItem("{:8.3f}".format(time)))

        # Plot the first entry by default
        self.update_residence_time_plot(int(self._residence_times_table.item(0, 0).text()))

    def build_layout(self):
        """Set the layout for the dialog.
        """

        self._hl = QtWidgets.QHBoxLayout()
        self._hl.addWidget(self._residence_times_table)

        self._vl = QtWidgets.QVBoxLayout()

        self._vl.addWidget(self._canvas)
        self._vl.addWidget(self._toolbar)

        self._hl.addLayout(self._vl)

        self.setLayout(self._hl)
