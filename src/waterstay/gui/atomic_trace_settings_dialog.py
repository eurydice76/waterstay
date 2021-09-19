from PyQt5 import QtCore, QtGui, QtWidgets


class AtomicTraceSettingsDialog(QtWidgets.QDialog):

    rendering_type_changed = QtCore.pyqtSignal(str)

    opacity_changed = QtCore.pyqtSignal(float)

    isocontour_level_changed = QtCore.pyqtSignal(float)

    def __init__(self, hist_min, hist_max, hist_mean, *args, **kwargs):

        super(AtomicTraceSettingsDialog, self).__init__(*args, **kwargs)

        self._hist_min = hist_min

        self._hist_max = hist_max

        self._hist_mean = hist_mean

        self.setGeometry(0, 0, 300, 100)

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

        self._rendering_type_combo.currentTextChanged.connect(self.on_change_rendering_type)
        self._opacity_spinbox.valueChanged.connect(self.on_change_opacity)
        self._isocontour_level_slider.valueChanged.connect(self.on_change_isocontour_level)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QGridLayout()

        main_layout.addWidget(self._rendering_type_label, 0, 0)
        main_layout.addWidget(self._rendering_type_combo, 0, 1)
        main_layout.addWidget(self._opacity_label, 1, 0)
        main_layout.addWidget(self._opacity_spinbox, 1, 1)
        main_layout.addWidget(self._isocontour_level_label, 2, 0)
        main_layout.addWidget(self._isocontour_level_slider, 2, 1)

        vspacer = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

        main_layout.addItem(vspacer, 3, 0, 1, -1)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets of the dialog
        """

        self._rendering_type_label = QtWidgets.QLabel('Rendering type')

        self._rendering_type_combo = QtWidgets.QComboBox()
        self._rendering_type_combo.addItems(['wireframe', 'surface', 'points'])

        self._opacity_label = QtWidgets.QLabel('Opacity')

        self._opacity_spinbox = QtWidgets.QDoubleSpinBox()
        self._opacity_spinbox.setSingleStep(0.1)
        self._opacity_spinbox.setMinimum(0.0)
        self._opacity_spinbox.setMaximum(1.0)
        self._opacity_spinbox.setValue(0.5)

        self._isocontour_level_label = QtWidgets.QLabel('Isocontour level')

        self._isocontour_level_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._isocontour_level_slider.setSingleStep(0.1)
        self._isocontour_level_slider.setMinimum(self._hist_min)
        self._isocontour_level_slider.setMaximum(self._hist_max)
        self._isocontour_level_slider.setValue(self._hist_mean)

    def on_change_rendering_type(self, rendering_type):
        """Event handler called when the rendering type is changed.
        """

        self.rendering_type_changed.emit(rendering_type)

    def on_change_opacity(self, opacity):
        """Event handler called when the opacity level is changed.
        """

        self.opacity_changed.emit(opacity)

    def on_change_isocontour_level(self, level):
        """Event handler called when the isocontour level is changed.
        """

        self.isocontour_level_changed.emit(level)
