import os
import shlex
import subprocess

from PyQt5 import QtCore, QtGui, QtWidgets


class TrjConvSettingsDialog(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):

        super(TrjConvSettingsDialog, self).__init__(*args, **kwargs)

        self.setGeometry(0, 0, 600, 300)

        self.init_ui()

    def init_ui(self):
        """Set the widgets of the dialog
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def build_events(self):
        """Build the signal/slot
        """

        self._topology_file_browse.clicked.connect(self.on_browse_topology_file)
        self._trajectory_file_browse.clicked.connect(self.on_browse_trajectory_file)
        self._output_file_browse.clicked.connect(self.on_browse_output_file)
        self._run_button.clicked.connect(self.on_convert_trajectory)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QGridLayout()

        main_layout.addWidget(self._topology_file_label, 0, 0)
        main_layout.addWidget(self._topology_file_lineedit, 0, 1)
        main_layout.addWidget(self._topology_file_browse, 0, 2)

        main_layout.addWidget(self._trajectory_file_label, 1, 0)
        main_layout.addWidget(self._trajectory_file_lineedit, 1, 1)
        main_layout.addWidget(self._trajectory_file_browse, 1, 2)

        main_layout.addWidget(self._trjconv_parameters_label, 2, 0)
        main_layout.addWidget(self._trjconv_parameters_lineedit, 2, 1, 1, 2)

        main_layout.addWidget(self._output_file_label, 3, 0)
        main_layout.addWidget(self._output_file_lineedit, 3, 1)
        main_layout.addWidget(self._output_file_browse, 3, 2)

        main_layout.addWidget(self._run_button, 4, 0, 1, 3)

        main_layout.addWidget(self._trjconv_output_textedit, 5, 0, 1, 3)

#        vspacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        # main_layout.addItem(vspacer, 6, 0, 1, -1)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets of the dialog
        """

        self._topology_file_label = QtWidgets.QLabel('Topology file')
        self._topology_file_lineedit = QtWidgets.QLineEdit()
        self._topology_file_browse = QtWidgets.QPushButton('Browse')

        self._trajectory_file_label = QtWidgets.QLabel('Trajectory file')
        self._trajectory_file_lineedit = QtWidgets.QLineEdit()
        self._trajectory_file_browse = QtWidgets.QPushButton('Browse')

        self._trjconv_parameters_label = QtWidgets.QLabel('Trjconv parameters')
        self._trjconv_parameters_lineedit = QtWidgets.QLineEdit()
        self._trjconv_parameters_lineedit.setText('-ur compact -fit progressive -center')

        self._output_file_label = QtWidgets.QLabel('Output trajectory file')
        self._output_file_lineedit = QtWidgets.QLineEdit()
        self._output_file_browse = QtWidgets.QPushButton('Browse')

        self._run_button = QtWidgets.QPushButton('Run trjconv')

        self._trjconv_output_textedit = QtWidgets.QTextEdit()

    def on_browse_topology_file(self):
        """Event handler which pops up a file selector for the input topology file.
        """

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open topology file', '', '(*.tpr);;(*.gro);;(*.pdb)', options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if not filename:
            return

        self._topology_file_lineedit.setText(filename)

    def on_browse_trajectory_file(self):
        """Event handler which pops up a file selector for the input trajectory file.
        """

        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open trajectory file', '', '(*.xtc);;(*.trr)', options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if not filename:
            return

        self._trajectory_file_lineedit.setText(filename)

        basename, ext = os.path.splitext(filename)

        output_file = basename + '_centered' + ext

        self._output_file_lineedit.setText(output_file)

    def on_browse_output_file(self):
        """Event handler which pops up a file selector for the output trajectory file.
        """

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption='Save output trajectory as ...', filter="(*.xtc *.gro *.trr)")
        if not filename:
            return

        self._output_file_lineedit.setText(filename)

    def on_convert_trajectory(self):
        """Event handler which performs the trajectory conversion using gmx trjconv program.
        """

        topology_file = self._topology_file_lineedit.text()
        if not os.path.exists(topology_file):
            return

        trajectory_file = self._trajectory_file_lineedit.text()
        if not os.path.exists(trajectory_file):
            return

        options = self._trjconv_parameters_lineedit.text()

        output_file = self._output_file_lineedit.text()
        if not output_file:
            return

        cmd = 'gmx trjconv {} -f {} -s {} -o {}'.format(options, trajectory_file, topology_file, output_file)

        proc = subprocess.Popen(shlex.split(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = proc.communicate(b'1\n1\n0')

        style_sheet = 'QTextEdit {color:black}' if proc.returncode == 0 else 'QTextEdit {color:red}'
        self._trjconv_output_textedit.setStyleSheet(style_sheet)

        self._trjconv_output_textedit.setText(''.join([v.decode('utf-8') for v in stdout]))
