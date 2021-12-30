import napari_plot_profile
import pytest

def test_something_with_viewer(make_napari_viewer):
    viewer = make_napari_viewer()

    import numpy as np
    image = np.random.random((256,256))
    viewer.add_image(image, colormap='green', blending='additive')

    viewer.add_shapes([[100, 80], [140, 150]], shape_type='path', edge_color='cyan', edge_width=3)

    num_dw = len(viewer.window._dock_widgets)
    from napari_plot_profile import PlotProfile
    plotter = PlotProfile(viewer)
    viewer.window.add_dock_widget(plotter)
    assert len(viewer.window._dock_widgets) == num_dw + 1

    plotter.to_table()
