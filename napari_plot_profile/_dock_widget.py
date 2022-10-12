import time
import warnings
from enum import Enum
from functools import partial

from qtpy.QtWidgets import QSpacerItem, QSizePolicy
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSpinBox, QCheckBox, QListWidget, QListWidgetItem
from qtpy.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QGridLayout, QPushButton, QFileDialog
from qtpy.QtCore import Qt
from magicgui.widgets import Table
from napari._qt.qthreading import thread_worker
from qtpy.QtCore import QTimer

from magicgui import magic_factory
from ._functions import topographic_image, topographic_points, topographic_surface
from napari.types import ImageData, LayerDataTuple
from typing import List


import pyqtgraph as pg
import pandas as pd
import numpy as np
import napari
from napari_tools_menu import register_dock_widget

@register_dock_widget(menu="Measurement > Plot profile")
class PlotProfile(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self._viewer = napari_viewer
        napari_viewer.layers.selection.events.changed.connect(self._on_selection)

        self._data = None
        self._former_line = None
        shapes_layer = self._selected_shapes_layers()[0]
        self.shapes_metadata = shapes_layer.metadata

        graph_container = QWidget()

        # histogram view
        self._graphics_widget = pg.GraphicsLayoutWidget()
        self._graphics_widget.setBackground(None)
        
        # List of lines Widget
        self._list_of_lines_widget = QListWidget()
        self._list_of_lines_widget.itemClicked.connect(self._on_item_clicked)
        

        #graph_container.setMaximumHeight(100)
        graph_container.setLayout(QHBoxLayout())
        graph_container.layout().addWidget(self._graphics_widget)

        # individual layers: legend
        self._labels = QWidget()
        self._labels.setLayout(QVBoxLayout())
        self._labels.layout().setSpacing(0)

        # setup layout
        self.setLayout(QVBoxLayout())

        self.layout().addWidget(graph_container)
        self.layout().addWidget(self._labels)

        num_points_container = QWidget()
        num_points_container.setLayout(QHBoxLayout())

        lbl = QLabel("Number of points")
        num_points_container.layout().addWidget(lbl)
        self._sp_num_points = QSpinBox()
        self._sp_num_points.setMinimum(2)
        self._sp_num_points.setMaximum(10000000)
        self._sp_num_points.setValue(100)
        num_points_container.layout().addWidget(self._sp_num_points)
        num_points_container.layout().setSpacing(0)
        self.layout().addWidget(num_points_container)


        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._on_selection)
        self.layout().addWidget(btn_refresh)

        self._cb_live_update = QCheckBox("Live update")
        self._cb_live_update.setChecked(True)
        self.layout().addWidget(self._cb_live_update)

        btn_list_values = QPushButton("List values")
        btn_list_values.clicked.connect(self._list_values)
        self.layout().addWidget(btn_list_values)
        
        self.btn_activate_3d_drawing = QPushButton("Activate 3D Drawing")
        self.btn_activate_3d_drawing.setCheckable(True)
        self.btn_activate_3d_drawing.clicked.connect(self._activate_3d_drawing)
        self.layout().addWidget(self.btn_activate_3d_drawing)
        
        self.layout().addWidget(self._list_of_lines_widget)

        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout().addItem(verticalSpacer)
        # self.layout().setSpacing(0)

        # we're using a thread worker because layer.mouse_drag_callbacks doesn't work
        # as expected in napari 0.4.10.
        # Todo: check later if the thread_worker can be replaced with a mouse/move/drag event
        # https://napari.org/guides/stable/threading.html
        #@thread_worker
        #def loop_run():
        #    while True:  # endless loop
        #        time.sleep(0.5)
        #        yield True

        #worker = loop_run()

        #def update_layer(whatever):
        #    if self.cb_live_update.isChecked():
        #        self.redraw()
        #    if not self.isVisible():
        #        worker.quit()

        # Start the loop
        #worker.yielded.connect(update_layer)
        #worker.start()

        self._timer = QTimer()
        self._timer.setInterval(500)

        @self._timer.timeout.connect
        def update_layer(*_):
            if self._cb_live_update.isChecked():
                self.redraw()
            if not self.isVisible():
                self._timer.stop()

        self._timer.start()

        self.redraw()

    @property
    def data(self):
        warnings.warn("PlotProfile().data is deprecated. Use PlotProfile().to_table() instead.", DeprecationWarning)
        return self._data

    def _on_selection(self, event):
        # redraw when layer selection has changed
        self.redraw(force_redraw=True)


    def to_table(self):
        table = {}
        for my_profile in self._data:
            positions = np.asarray(my_profile['positions'])
            for i, x in enumerate(positions[0]):
                table[my_profile['name'] + '_pos' + str(i)] = positions[:, i]

            table[my_profile['name'] + '_intensity'] = my_profile['intensities']
            table[my_profile['name'] + '_distance'] = my_profile['distances']
        return table

    def _list_values(self):
        table = self.to_table()

        # turn table into a widget
        first_selected_layer = self.selected_image_layers()[0]
        first_selected_layer.properties = table
        from napari_skimage_regionprops import add_table
        add_table(first_selected_layer, self._viewer)
        
    def _activate_3d_drawing(self, event):
        if event:
            self._viewer.mouse_drag_callbacks.append(
                self._on_3d_click)
        else:
            if self._on_3d_click in self._viewer.mouse_drag_callbacks:
                self._viewer.mouse_drag_callbacks.remove(self._on_3d_click)
        
    def _on_3d_click(self, viewer, event):
        image_layer = self.selected_image_layers()[0]
        shapes_layer = self._selected_shapes_layers()[0]
        near_point, far_point = image_layer.get_ray_intersections(
            event.position,
            event.view_direction,
            event.dims_displayed
        )
        if (near_point is not None) and (far_point is not None):
            line_data = [np.array([near_point, far_point])]
            shapes_layer.add_lines(line_data, edge_color = '#777777ff')
            line_name = shapes_layer.shape_type[-1] + f" {len(shapes_layer.data)}"
            self._add_new_line_to_metadata(len(shapes_layer.data), line_name)
            self._update_list_widget_with_metadata()
            
    def _add_new_line_to_metadata(self, i, line_name):
        shapes_layer = self._selected_shapes_layers()[0]
        # Gives item new text name
        shapes_layer.metadata[i] = line_name
    
    def _get_list_widget_items(self):
        items = [self._list_of_lines_widget.item(x)
                 for x in range(self._list_of_lines_widget.count())]
        return items
    
    def _update_list_widget_with_metadata(self):
        shapes_layer = self._selected_shapes_layers()[0]
        items = self._get_list_widget_items()
        items_texts = [item.text() for item in items]
        # Iterate over line names in metadata values
        for name in list(shapes_layer.metadata.values()):
            if name not in items_texts:
                new_item = QListWidgetItem()
                new_item.setText(name)
                self._list_of_lines_widget.addItem(new_item)

    def _on_item_clicked(self, item):
        shapes_layer = self._selected_shapes_layers()[0]
        index = self._list_of_lines_widget.currentRow()
        shapes_layer.selected_data = {index}
        edge_color = np.array(['#777777ff'] * len(shapes_layer.data))
        edge_color[index] = 'red'
        self.redraw(force_redraw=True)
        shapes_layer.edge_color = edge_color

    def _get_current_line(self):
        line = None
        for layer in self._viewer.layers.selection:
            if isinstance(layer, napari.layers.Shapes):
                selection = list(layer.selected_data)
                if len(selection) > 0:
                    line = layer.data[selection[0]]
                    break
                try:
                    line = layer.data[-1]
                    break
                except IndexError:
                    pass
        return line

    def redraw(self, force_redraw : bool = False):

        line = self._get_current_line()
        
        if line is None:
            #self._reset_plot()
            return
        shapes_layer = self._selected_shapes_layers()[0]
        shapes_layer_length = len(shapes_layer.data)
        for i, shape_type in enumerate(shapes_layer.shape_type):
            # to do: guarantee unique shape_type + number
            # when deleting path and adding line for example, extra wrong names
            # may be added to metadata
            line_name = shape_type + f" {i+1}"
            if line_name not in list(shapes_layer.metadata.values()):
                self._add_new_line_to_metadata(i+1, line_name)
        self._update_list_widget_with_metadata()

        if not force_redraw:
            if self._former_line is not None and np.array_equal(line, self._former_line):
                return

        self._reset_plot()

        self._former_line = line + 0

        # clean up
        layout = self._labels.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

        # visualize plots
        num_bins = self._sp_num_points.value()
        colors = []
        self._data = []
        for i, layer in enumerate(self.selected_image_layers()):
            # plot profile
            my_profile = profile(layer, line, num_points=num_bins)
            my_profile['name'] = layer.name
            self._data.append(my_profile)

            colormap = layer.colormap.colors
            color = np.asarray(colormap[-1, 0:3]) * 255
            colors.append(color)

            intensities = my_profile['intensities']
            if len(intensities) > 0:
                self.p2.plot(my_profile['distances'], intensities, pen=color, name=layer.name)

                text = '[%0.2f .. %0.2f], %0.2f +- %0.2f' % (np.min(intensities),np.max(intensities),np.mean(intensities),np.std(intensities))

                row = LayerLabelWidget(layer, text, colors[i], self)
                layout.addWidget(row)


    def _reset_plot(self):
        if not hasattr(self, "p2"):
            self.p2 = self._graphics_widget.addPlot()
            axis = self.p2.getAxis('bottom')
            axis.setLabel("Distance")
            axis = self.p2.getAxis('left')
            axis.setLabel("Intensity")
        else:
            self.p2.clear()

    def selected_image_layers(self):
        return [layer for layer in self._viewer.layers if (isinstance(layer, napari.layers.Image) and layer.visible)]
    def _selected_shapes_layers(self):
        output =  [layer for layer in self._viewer.layers if (isinstance(layer, napari.layers.Shapes) and layer.visible)]
        if len(output) == 0:
            shapes_layer = self._viewer.add_shapes(ndim = 3)
            output = [shapes_layer]
        return output
    
    def hideEvent(self, event):
        super().hideEvent(event)
        if self._on_3d_click in self._viewer.mouse_drag_callbacks:
            self._viewer.mouse_drag_callbacks.remove(self._on_3d_click)

class LayerLabelWidget(QWidget):
    def __init__(self, layer, text, color, gui):
        super().__init__()

        self.setLayout(QHBoxLayout())

        lbl = QLabel(layer.name + text)
        lbl.setStyleSheet('color: #%02x%02x%02x' % tuple(color.astype(int)))
        self.layout().addWidget(lbl)

def profile(layer, line, num_points : int = 256):
    distance = 0
    former_point = None
    intermediate_distances = [0]
    for point in line:
        if former_point is not None:
            distance = distance + np.linalg.norm(point - former_point)
            intermediate_distances.append(distance)
        former_point = point
    intermediate_distances.append(intermediate_distances[-1])

    step = distance / (num_points - 1)

    positions = []
    distances = []

    current_line = 0
    for i in range(num_points):
        distance = i * step
        while current_line < len(intermediate_distances) - 1 and distance > intermediate_distances[current_line + 1]:
            current_line += 1
        start = line[min(current_line, len(line) - 1)] / layer.scale
        end = line[min(current_line + 1, len(line) - 1)] / layer.scale


        position_on_line = distance - intermediate_distances[current_line]
        if current_line == len(intermediate_distances)-1:
            relative_position = 0
        else:
            line_length = intermediate_distances[current_line + 1] - intermediate_distances[current_line]
            relative_position = position_on_line / line_length
        position = end * relative_position + start * (1.0 - relative_position)

        # check if point still within image
        position_clipped = np.maximum(position, np.zeros(position.shape))
        position_clipped = np.minimum(position_clipped, layer.data.shape - np.ones(position.shape))
        if np.array_equal(position, position_clipped):
            position = position.astype(int)
            positions.append(position)
            distances.append(i * step)

    data = layer.data
    if "dask" in str(type(data)):
        data = np.asarray(data)

    intensities = [data[tuple(position)] for position in positions]

    return {
        'positions': positions,
        'distances': distances,
        'intensities': intensities
    }

def min_max(data):
    return data.min(), data.max()

class TopographicalVisualization(Enum):
    Image = partial(topographic_image)
    Points = partial(topographic_points)
    Surface = partial(topographic_surface)

@register_dock_widget(menu="Visualization > Topographical view (npp)")
@magic_factory(step_size={"visible": True})
def topographical_view(image: ImageData, visualize_as:TopographicalVisualization = TopographicalVisualization.Image,
                       step_size: int = 1) -> List[LayerDataTuple]:
    """Return a 3D topographical view from a 2D image.

    This function warps pixels intensities to heights and returns a 3D visualization as specified.

    Parameters
    ----------
    image : 2D-array
        Grayscale 2D input image; will be converted to int internally
    visualize_as: TopographicalVisualization
        Type of visualization: Image(s), Points or Surfaces
    step_size : uint
        Grid-size for the visualization

    Returns
    -------
    napari layers : list of LayerDataTuple
        napari layers displaying pixel intensities as heights.
    """
    image = np.asarray(image)
    if not isinstance(image.dtype, int):
        image = image.astype(int)

    return visualize_as.value(image, step_size)


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [PlotProfile, topographical_view]
