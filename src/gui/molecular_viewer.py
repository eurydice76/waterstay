import numpy as np

from PyQt5 import QtCore, QtWidgets

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from waterstay.database import CHEMICAL_ELEMENTS

RGB_COLOURS = {}
RGB_COLOURS["selection"] = (0, (1.00, 0.20, 1.00))
RGB_COLOURS["default"] = (1, (1.00, 0.90, 0.90))


def color_string_to_rgb(s):

    if not s.strip():
        s = "1;1;1"

    return np.array(s.split(';')).astype(np.float32)/255.


def ndarray_to_vtkarray(colors, radius, n_atoms):
    # define the colours
    color_scalars = vtk.vtkFloatArray()
    color_scalars.SetNumberOfValues(len(colors))
    for i, c in enumerate(colors):
        color_scalars.SetValue(i, c)
    color_scalars.SetName("colors")

    # some radii
    radius_scalars = vtk.vtkFloatArray()
    radius_scalars.SetNumberOfValues(radius.shape[0])
    for i, r in enumerate(radius):
        radius_scalars.SetValue(i, r)
    radius_scalars.SetName("radius")

    # the original index
    index_scalars = vtk.vtkIntArray()
    index_scalars.SetNumberOfValues(n_atoms)
    for i in range(n_atoms):
        index_scalars.SetValue(i, i)
    index_scalars.SetName("index")

    scalars = vtk.vtkFloatArray()
    scalars.SetNumberOfComponents(3)
    scalars.SetNumberOfTuples(radius_scalars.GetNumberOfTuples())
    scalars.CopyComponent(0, radius_scalars, 0)
    scalars.CopyComponent(1, color_scalars, 0)
    scalars.CopyComponent(2, index_scalars, 0)
    scalars.SetName("scalars")
    return scalars


def ndarray_to_vtkcellarray(array):
    bonds = vtk.vtkCellArray()
    for data in array:
        line = vtk.vtkLine()
        line.GetPointIds().SetId(0, int(data[0]))
        line.GetPointIds().SetId(1, int(data[1]))
        bonds.InsertNextCell(line)

    return bonds


class MolecularViewer(QtWidgets.QWidget):

    picked_atom_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent):

        super(MolecularViewer, self).__init__(parent)

        self._iren = QVTKRenderWindowInteractor(self)

        self._renderer = vtk.vtkRenderer()

        self._iren.GetRenderWindow().AddRenderer(self._renderer)

        self._iren.GetRenderWindow().SetPosition((0, 0))

        self._iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self._iren.Enable()

        # create camera
        self._camera = vtk.vtkCamera()
        # associate camera to renderer
        self._renderer.SetActiveCamera(self._camera)
        self._camera.SetFocalPoint(0, 0, 0)
        self._camera.SetPosition(0, 0, 20)

        self._picker_observer_id = None
        self._picker = vtk.vtkCellPicker()
        self._picker.SetTolerance(0.005)

        self._n_atoms = 0
        self._n_frames = 0
        self._resolution = 0

        self._iren.Initialize()

        self._atoms = []

        self._polydata = None

        self._reader = None

        self._current_frame = 0

        self._lut = None

        self._previously_picked_atom = None

        self.enable_picking()

    @property
    def iren(self):
        return self._iren

    @property
    def renderer(self):
        return self._renderer

    def enable_picking(self):

        self._picker_observer_id = self._iren.AddObserver("LeftButtonPressEvent", self.on_pick)

    def get_atom_index(self, pid):

        _, _, idx = self.glyph.GetOutput().GetPointData().GetArray("scalars").GetTuple3(pid)

        return int(idx)

    def on_pick(self, obj, event=None):
        """Event handler when an atom is mouse-picked
        """

        if not self._reader:
            return

        # Get the picked position and retrieve the index of the atom that was picked from it
        pos = obj.GetEventPosition()
        self._picker.AddPickList(self._picking_domain)
        self._picker.PickFromListOn()
        self._picker.Pick(pos[0], pos[1], 0, self._renderer)
        pid = self._picker.GetPointId()
        if pid > 0:
            idx = self.get_atom_index(pid)
            self.on_pick_atom(idx)

    def on_pick_atom(self, picked_atom):
        """Change the color of a selected atom
        """

        if self._reader is None:
            return

        # If an atom was previously picked, restore its scale and color
        if self._previously_picked_atom is not None:
            index, scale, color = self._previously_picked_atom
            self._atom_scales[index] = scale
            self._atom_colours[index] = color
            self._polydata.GetPointData().GetArray("scalars").SetTuple3(
                index, self._atom_scales[index], self._atom_colours[index], index)

        # Save the scale and color of the picked atom
        self._previously_picked_atom = (
            picked_atom, self._atom_scales[picked_atom], self._atom_colours[picked_atom])

        # Set its colors with the default value for atom selection and increase its size
        self._atom_colours[picked_atom] = RGB_COLOURS['selection'][0]
        self._atom_scales[picked_atom] *= 2

        self._polydata.GetPointData().GetArray("scalars").SetTuple3(
            picked_atom, self._atom_scales[picked_atom], self._atom_colours[picked_atom], picked_atom)

        self._polydata.Modified()

        self._iren.Render()

        self.picked_atom_changed.emit(picked_atom)

    def set_coordinates(self, frame):
        '''
        Sets a new configuration

        @param frame: the configuration number
        @type frame: integer
        '''

        self._current_frame = frame % self._reader.n_frames

        coords = self._reader.read_frame(self._current_frame)

        points = vtk.vtkPoints()
        points.SetNumberOfPoints(self._n_atoms)
        for i in range(self._n_atoms):
            x, y, z = coords[i]
            points.SetPoint(i, x, y, z)

        self._polydata.SetPoints(points)

        # Update the view.
        self.update_renderer()

    def build_scene(self):
        '''
        build a vtkPolyData object for a given frame of the trajectory
        '''

        actor_list = []
        line_actor = None

        line_mapper = vtk.vtkPolyDataMapper()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            line_mapper.SetInput(self._polydata)
        else:
            line_mapper.SetInputData(self._polydata)

        line_mapper.SetLookupTable(self._lut)
        line_mapper.ScalarVisibilityOn()
        line_mapper.ColorByArrayComponent("scalars", 1)
        line_actor = vtk.vtkLODActor()
        line_actor.GetProperty().SetLineWidth(3)
        line_actor.SetMapper(line_mapper)
        actor_list.append(line_actor)

        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(0, 0, 0)
        sphere.SetRadius(0.2)
        sphere.SetThetaResolution(self._resolution)
        sphere.SetPhiResolution(self._resolution)
        glyph = vtk.vtkGlyph3D()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            glyph.SetInput(self._polydata)
        else:
            glyph.SetInputData(self._polydata)

        glyph.SetScaleModeToScaleByScalar()
        glyph.SetColorModeToColorByScalar()
        glyph.SetScaleFactor(1)
        glyph.SetSourceConnection(sphere.GetOutputPort())
        glyph.SetIndexModeToScalar()
        sphere_mapper = vtk.vtkPolyDataMapper()
        sphere_mapper.SetLookupTable(self._lut)
        sphere_mapper.SetScalarRange(self._polydata.GetScalarRange())
        sphere_mapper.SetInputConnection(glyph.GetOutputPort())
        sphere_mapper.ScalarVisibilityOn()
        sphere_mapper.ColorByArrayComponent("scalars", 1)
        ball_actor = vtk.vtkLODActor()
        ball_actor.SetMapper(sphere_mapper)
        ball_actor.GetProperty().SetAmbient(0.2)
        ball_actor.GetProperty().SetDiffuse(0.5)
        ball_actor.GetProperty().SetSpecular(0.3)
        ball_actor.SetNumberOfCloudPoints(30000)
        actor_list.append(ball_actor)
        self.glyph = glyph

        self._picking_domain = ball_actor

        assembly = vtk.vtkAssembly()
        for actor in actor_list:
            assembly.AddPart(actor)

        return assembly

    def update_renderer(self):
        '''
        Update the renderer
        '''
        # deleting old frame
        self.clear_trajectory()

        # creating new polydata
        self._actors = self.build_scene()

        # adding polydata to renderer
        self._renderer.AddActor(self._actors)

        # rendering
        self._iren.Render()

    def set_reader(self, reader, frame=0):

        if (self._reader is not None) and (reader.filename == self._reader.filename):
            return

        self._reader = reader

        self.clear_trajectory()

        self._n_atoms = self._reader.n_atoms
        self._n_frames = self._reader.n_frames

        self._atoms = self._reader.atom_types

        # Hack for reducing objects resolution when the system is big
        self._resolution = int(np.sqrt(3000000.0 / self._n_atoms))
        self._resolution = 10 if self._resolution > 10 else self._resolution
        self._resolution = 4 if self._resolution < 4 else self._resolution

        self._atom_colours, self._lut = self.build_color_transfer_function()

        self._atom_scales = np.array([CHEMICAL_ELEMENTS['atoms'][at]['vdw_radius']
                                      for at in self._atoms]).astype(np.float32)

        scalars = ndarray_to_vtkarray(self._atom_colours, self._atom_scales, self._n_atoms)

        self._polydata = vtk.vtkPolyData()
        self._polydata.GetPointData().SetScalars(scalars)

        self.set_coordinates(frame)
        chemical_bonds = self._reader.build_connectivity(0)

        vtk_bonds = vtk.vtkCellArray()
        for at, bonded_ats in chemical_bonds.items():

            for bonded_at in bonded_ats:
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, at)
                line.GetPointIds().SetId(1, bonded_at)
                vtk_bonds.InsertNextCell(line)

        self._polydata.SetLines(vtk_bonds)

    def build_color_transfer_function(self):

        lut = vtk.vtkColorTransferFunction()

        for (idx, color) in RGB_COLOURS.values():
            lut.AddRGBPoint(idx, *color)

        colours = []
        unic_colours = {}

        color_string_list = [color_string_to_rgb(
            CHEMICAL_ELEMENTS['atoms'][at]['color']) for at in self._atoms]

        col_ids = len(RGB_COLOURS)

        for col in color_string_list:
            tup_col = tuple(col)
            if not (tup_col in unic_colours.keys()):
                unic_colours[tup_col] = col_ids
                lut.AddRGBPoint(col_ids, *tup_col)
                colours.append(col_ids)
                col_ids += 1
            else:
                colours.append(unic_colours[tup_col])

        return colours, lut

    def get_render_window(self):
        return self._iren.GetRenderWindow()

    def clear_trajectory(self):

        if not hasattr(self, "_actors"):
            return

        self._actors.VisibilityOff()
        self._actors.ReleaseGraphicsResources(self.get_render_window())
        self._renderer.RemoveActor(self._actors)

        del self._actors
