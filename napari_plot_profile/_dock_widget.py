import time
import warnings

from qtpy.QtWidgets import QSpacerItem, QSizePolicy
from napari_plugin_engine import napari_hook_implementation
from qtpy.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSpinBox, QCheckBox
from qtpy.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QGridLayout, QPushButton, QFileDialog
from qtpy.QtCore import Qt
from magicgui.widgets import Table
from napari._qt.qthreading import thread_worker

import pyqtgraph as pg
import numpy as np
import napari

class PlotProfile(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer
        napari_viewer.layers.selection.events.changed.connect(self._on_selection)

        self.data = None
        self.former_line = None

        graph_container = QWidget()

        # histogram view
        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_widget.setBackground(None)

        #graph_container.setMaximumHeight(100)
        graph_container.setLayout(QHBoxLayout())
        graph_container.layout().addWidget(self.graphics_widget)

        # individual layers: legend
        self.labels = QWidget()
        self.labels.setLayout(QVBoxLayout())
        self.labels.layout().setSpacing(0)

        # setup layout
        self.setLayout(QVBoxLayout())

        self.layout().addWidget(graph_container)
        self.layout().addWidget(self.labels)

        num_points_container = QWidget()
        num_points_container.setLayout(QHBoxLayout())

        lbl = QLabel("Number of points")
        num_points_container.layout().addWidget(lbl)
        self.sp_num_points = QSpinBox()
        self.sp_num_points.setMinimum(2)
        self.sp_num_points.setMaximum(10000000)
        self.sp_num_points.setValue(100)
        num_points_container.layout().addWidget(self.sp_num_points)
        num_points_container.layout().setSpacing(0)
        self.layout().addWidget(num_points_container)


        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._on_selection)
        self.layout().addWidget(btn_refresh)

        self.cb_live_update = QCheckBox("Live update")
        self.cb_live_update.setChecked(True)
        self.layout().addWidget(self.cb_live_update)

        btn_list_values = QPushButton("List values")
        btn_list_values.clicked.connect(self._list_values)
        self.layout().addWidget(btn_list_values)

        verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout().addItem(verticalSpacer)
        # self.layout().setSpacing(0)

        # we're using a thread worker because layer.mouse_drag_callbacks doesn't work
        # as expected in napari 0.4.10.
        # Todo: check later if the thread_worker can be replaced with a mouse/move/drag event
        # https://napari.org/guides/stable/threading.html
        @thread_worker
        def loop_run():
            while True:  # endless loop
                time.sleep(0.5)
                yield True

        worker = loop_run()

        def update_layer(whatever):
            if self.cb_live_update.isChecked():
                self.redraw()
            if not self.isVisible():
                worker.quit()

        # Start the loop
        worker.yielded.connect(update_layer)
        worker.start()
        self.redraw()

    def _on_selection(self, event):
        # redraw when layer selection has changed
        self.redraw(force_redraw=True)

    def _list_values(self):
        table = {}
        for my_profile in self.data:
            positions = np.asarray(my_profile['positions'])
            for i, x in enumerate(positions[0]):
                table[my_profile['name'] + '_pos' + str(i)] = positions[:, i]

            table[my_profile['name'] + '_intensity'] = my_profile['intensities']
            table[my_profile['name'] + '_distance'] = my_profile['distances']

        # turn table into a widget
        dock_widget = table_to_widget(table)

        # add widget to napari
        self.viewer.window.add_dock_widget(dock_widget, area='right')

    def _get_current_line(self):
        line = None
        for layer in self.viewer.layers.selection:
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


        if not force_redraw:
            if self.former_line is not None and np.array_equal(line, self.former_line):
                return

        self._reset_plot()

        self.former_line = line + 0

        # clean up
        layout = self.labels.layout()
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)

        # visualize plots
        num_bins = self.sp_num_points.value()
        colors = []
        self.data = []
        for i, layer in enumerate(self.selected_image_layers()):
            # plot profile
            my_profile = profile(layer, line, num_points=num_bins)
            my_profile['name'] = layer.name
            self.data.append(my_profile)

            colormap = layer.colormap.colors
            color = np.asarray(colormap[-1, 0:3]) * 255
            colors.append(color)

            intensities = my_profile['intensities']

            self.p2.plot(my_profile['distances'], intensities, pen=color, name=layer.name)

            text = '[%0.2f .. %0.2f], %0.2f +- %0.2f' % (np.min(intensities),np.max(intensities),np.mean(intensities),np.std(intensities))

            row = LayerLabelWidget(layer, text, colors[i], self)
            layout.addWidget(row)


    def _reset_plot(self):
        if not hasattr(self, "p2"):
            self.p2 = self.graphics_widget.addPlot()
            axis = self.p2.getAxis('bottom')
            axis.setLabel("Distance")
            axis = self.p2.getAxis('left')
            axis.setLabel("Intensity")
        else:
            self.p2.clear()

    def selected_image_layers(self):
        return [layer for layer in self.viewer.layers if (isinstance(layer, napari.layers.Image) and layer.visible)]

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
        position = start * relative_position + end * (1.0 - relative_position)
        positions.append(position.astype(int))

    intensities = [layer.data[tuple(position)] for position in positions]

    return {
        'positions': positions,
        'distances': [i * step for i in range(num_points)],
        'intensities': intensities
    }

# copied from napari-skimage-regionprops
def table_to_widget(table: dict) -> QWidget:
    """
    Takes a table given as dictionary with strings as keys and numeric arrays as values and returns a QWidget which
    contains a QTableWidget with that data.
    """
    view = Table(value=table)

    copy_button = QPushButton("Copy to clipboard")

    @copy_button.clicked.connect
    def copy_trigger():
        view.to_dataframe().to_clipboard()

    save_button = QPushButton("Save as csv...")

    @save_button.clicked.connect
    def save_trigger():
        filename, _ = QFileDialog.getSaveFileName(save_button, "Save as csv...", ".", "*.csv")
        view.to_dataframe().to_csv(filename)

    widget = QWidget()
    widget.setWindowTitle("region properties")
    widget.setLayout(QGridLayout())
    widget.layout().addWidget(copy_button)
    widget.layout().addWidget(save_button)
    widget.layout().addWidget(view.native)

    return widget

def min_max(data):
    return data.min(), data.max()

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    # you can return either a single widget, or a sequence of widgets
    return [PlotProfile]
