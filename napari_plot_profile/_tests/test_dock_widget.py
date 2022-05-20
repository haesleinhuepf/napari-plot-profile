import napari_plot_profile
import pytest
import numpy as np


def test_dock_plot_profile_widget(make_napari_viewer):
    """Test docking plot profile widget to viewer."""
    viewer = make_napari_viewer()

    import numpy as np
    image = np.random.random((256, 256))
    viewer.add_image(image, colormap='green', blending='additive')

    viewer.add_shapes([[100, 80], [140, 150]], shape_type='path',
                      edge_color='cyan', edge_width=3)

    num_dw = len(viewer.window._dock_widgets)
    from napari_plot_profile import PlotProfile
    plotter = PlotProfile(viewer)
    viewer.window.add_dock_widget(plotter)
    assert len(viewer.window._dock_widgets) == num_dw + 1

    plotter.to_table()


def test_dock_topographical_widget(make_napari_viewer):
    """Test docking topographical widget to viewer."""

    viewer = make_napari_viewer()
    num_dw = len(viewer.window._dock_widgets)
    dw = napari_plot_profile.topographical_view()
    viewer.window.add_dock_widget(dw)

    assert len(viewer.window._dock_widgets) == num_dw + 1


array_list = [np.arange(25).reshape(5, 5),
              np.arange(25).reshape(5, 5) - 5]
expected_types_list = [
    ['image', 'points', 'surface'],
    ['image', 'image', 'points', 'surface']
    ]


@pytest.mark.parametrize("array, expected_types",
                         zip(array_list, expected_types_list))
def test_run_topographical_widget(make_napari_viewer, array, expected_types):
    """Test running topographical widget on 2 images."""
    viewer = make_napari_viewer()
    viewer.add_image(array)
    widget = napari_plot_profile.topographical_view(
        return_points={'value': True},
        return_surface={'value': True})
    viewer.window.add_dock_widget(widget)
    widget()
    output_layer_types = [layer.as_layer_data_tuple()[-1]
                          for layer in viewer.layers[1:]]
    assert sorted(expected_types) == sorted(output_layer_types)
