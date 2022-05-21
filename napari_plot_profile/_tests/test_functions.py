from napari_plot_profile._functions import topographic_image, topographic_points, topographic_surface
import numpy as np
import pytest

def test_topographical_view_image_positive_only():
    result_layer_data_tuples = topographic_image(np.array([[0, 1], [2, 3]]))

    result_data = [layer_data_tuple[0] for layer_data_tuple in result_layer_data_tuples]

    reference_data = [np.array([
                        [[0, 0], [0, 3]],
                        [[0, 0], [2, 2]],
                        [[0, 1], [1, 1]],
                        [[0, 0], [0, 0]]
                        ])]

    print(result_data)

    assert str(result_data) == str(reference_data)

def test_topographical_view_image_positive_and_negative():
    result_layer_data_tuples = topographic_image(np.array([[-1.5, 1], [2, 3]]))

    result_data = [layer_data_tuple[0] for layer_data_tuple in result_layer_data_tuples]

    reference_data = [np.asarray([
                        [[0, 0], [0, 3]],
                        [[0, 0], [2, 2]],
                        [[0, 1], [1, 1]],
                        [[0, 0], [0, 0]]
                        ]),
                      np.asarray([
                        [[0, 0], [0, 0]],
                        [[-1, 0], [0, 0]],
                        [[0, 0], [0, 0]]
                        ])
                      ]

    print(result_data)

    assert str(result_data) ==  str(reference_data)


def test_topographical_view_points():
    result_layer_data_tuples = topographic_points(np.array([[-1.5, 1], [2, 3]]))

    result_data = [layer_data_tuple[0] for layer_data_tuple in result_layer_data_tuples]

    reference_data = [np.array([[1, 0, 0],
              [-1, 0, 1],
              [-2, 1, 0],
              [-3, 1, 1]])]

    print(result_data)

    assert np.array_equal(result_data, reference_data)


#  Input array to test
array_4_sample_factor = np.repeat(np.arange(3, -1, -1)[np.newaxis, :],
                                  4, axis=0)

#  List of expected output shapes
expected_output_shape_list = [
    [(32, 3), (42, 3), (32,)],
    [(4, 3), (2, 3), (4,)],
    ]


@pytest.mark.parametrize("sample_factor, expected_output_shapes",
                         zip([1, 2], expected_output_shape_list))
def test_surface_and_sample_factor(sample_factor, expected_output_shapes):
    """Test outputs from topographic surface and sample factor."""
    output = topographic_surface(array_4_sample_factor,
                                 step_size=sample_factor)[0][0]
    output_shapes = [out.shape for out in output]
    assert expected_output_shapes == output_shapes
