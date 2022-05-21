from napari_plot_profile._functions import topographic_image, topographic_points, topographic_surface
import numpy as np
import pytest
#  List of input arrays to test
array_input_list = [
    np.array([[0, 1], [2, 3]]),
    np.array([[-1.5, 1], [2, 3]]),
    np.array([[0, 1], [2, 3]])
    ]
#  List of functions to test
func_list = [topographic_image,
             topographic_image,
             topographic_points]
#  List of expected outputs
expected_output_list = [
    [  # first output (1 array)
      np.array([
        [[0, 0], [0, 0]],  # height 0
        [[0, 1], [1, 1]],  # height 1
        [[0, 0], [2, 2]],  # height 2
        [[0, 0], [0, 3]]   # height 3
        ])
    ],
    [  # second output (2 arrays)
      np.array([
        [[0, 0], [0, 0]],  # height 0
        [[0, 1], [1, 1]],  # height 1
        [[0, 0], [2, 2]],  # height 2
        [[0, 0], [0, 3]]   # height 3
        ]),
      np.array([
        [[0, 0], [0, 0]],   # height 0
        [[-1, 0], [0, 0]],  # height -1
        [[0, 0], [0, 0]]    # height -2
        ])
      ],
    [  # third output (point coordinates)
     np.array([[0, 0, 0],
               [1, 0, 1],
               [2, 1, 0],
               [3, 1, 1]])
     ]
]


@pytest.mark.parametrize("function, array_input, expected_output",
                         zip(func_list, array_input_list,
                             expected_output_list))
def test_function_output(function, array_input, expected_output):
    """Test outputs from topographic image and points."""
    output = function(array_input)
    output_stack = np.vstack(output)
    expected_output_stack = np.vstack(expected_output)
    assert np.array_equal(expected_output_stack, output_stack)


#  Input array to test
array_4_sample_factor = np.repeat(np.arange(3, -1, -1)[np.newaxis, :],
                                  4, axis=0)
# array_4_sample_factor = array([[3 2 1 0]
#                                [3 2 1 0]
#                                [3 2 1 0]
#                                [3 2 1 0]])

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
                                 step_size=sample_factor)[0]
    output_shapes = [out.shape for out in output]
    assert expected_output_shapes == output_shapes
