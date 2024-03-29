from typing import List

import numpy as np
from napari.types import LayerDataTuple, ImageData
from skimage import measure
from napari.utils.colormaps import colormap_utils
import napari
def _get_3D_indices(image, sample_factor):
    # Get (z, y, x) coordinates (z are image intensities)
    z_indices = image.ravel().astype(int)[::sample_factor]
    y_indices = np.indices(image.shape)[0].ravel()[::sample_factor]
    x_indices = np.indices(image.shape)[1].ravel()[::sample_factor]
    return z_indices, y_indices, x_indices


def _topographic_image_positive(image, sample_factor):
    """Generate a 3D topographical image from a 2D positive image."""
    max_range = np.ceil(image.max()).astype(int)
    z_indices, y_indices, x_indices = _get_3D_indices(image, sample_factor)

    # For each position, gets all (z,y,x) coordinates smaller than z:
    # - for every z: arange an array from 0 to z
    filled_z_indices = np.concatenate([np.arange(z_indices[i]+1)
                                       for i in range(len(z_indices))])
    # - for every x/y: repeat x/y by z times
    filled_y_indices = np.repeat(y_indices,  z_indices+1)
    filled_x_indices = np.repeat(x_indices,  z_indices+1)

    # Create a 3D image and fills it
    output_image = np.zeros((max_range+1,
                             image.shape[0],
                             image.shape[1])).astype(int)
    output_image[filled_z_indices,
                 filled_y_indices,
                 filled_x_indices] = filled_z_indices

    return output_image


def topographic_image(image: ImageData, step_size: int = 1, viewer: napari.Viewer = None) -> List[LayerDataTuple]:
    """Generate 3D topographical image layers from a 2D image."""

    output_layer_data_tuple_list = []

    positive_image = np.clip(image, a_min=0, a_max=None)

    # assemble LayerDataTuple
    layer_data = _topographic_image_positive(positive_image, step_size)[::-1]
    layer_properties = {'name': 'topographical image',
                        'translate': (-int(image.max()), 0, 0),
                        'blending': 'additive',
                        'rendering': 'mip',
                        'colormap': 'gist_earth'}
    layer_type = 'image'

    output_layer_data_tuple_list.append((layer_data, layer_properties, layer_type))

    # if image has negatives pixels, process positive and negative separately
    if (image < 0).any():
        negative_image = -np.clip(image, a_min=None, a_max=0)

        # assemble LayerDataTuple
        layer_data = -_topographic_image_positive(negative_image, step_size)
        layer_properties = {'name': 'topographical image negative',
                            'translate': (0, 0, 0),
                            'blending': 'additive',
                            'rendering': 'minip',
                            'colormap': get_inferno_rev_cmap()}

        output_layer_data_tuple_list.append((layer_data, layer_properties, layer_type))
        
    for layer in output_layer_data_tuple_list:
        if viewer is not None:
            if layer[1]['name'] not in viewer.layers:
                viewer.add_image(layer[0], **layer[1])
            else:
                _layer = viewer.layers[layer[1]]['name']
                _layer.data = layer[0]
                _layer.properties = layer[1]
    return output_layer_data_tuple_list


def topographic_points(image: ImageData, step_size: int = 1) -> List[LayerDataTuple]:
    """Generate points in 3D from a 2D image."""
    z_indices, y_indices, x_indices = _get_3D_indices(image, step_size)
    points = np.stack((z_indices, y_indices, x_indices), axis=1)

    points[:, 0] = -points[:, 0]

    # assemble LayerDataTuple
    magic_number = 30000
    layer_data = points
    layer_properties = {'name': 'topographical points',
                        'size': max(int(round(image.size / magic_number)), 1)}
    layer_type = 'points'

    return [(layer_data, layer_properties, layer_type)]


def topographic_surface(image: ImageData, step_size: int = 1) -> List[LayerDataTuple]:
    """Generate a surface from a 2D image."""
    # Get topographic image(s)
    layerDataTuples = topographic_image(image, step_size=1)
    output_list = [layer[0] for layer in layerDataTuples]

    # If list has 2 images, concatenate them
    if len(output_list) > 1:
        output_image = np.concatenate(
            (output_list[0][1:],
             output_list[1])
            )
    else:
        output_image = output_list[0]
    # offsets image to positive values to get surface where level = 0
    offset = abs(output_image.min())
    output_image[output_image != 0] += offset
    vertices, faces, normals, values = measure.marching_cubes(output_image,
                                                              level=0,
                                                              step_size=step_size)
    surface = (vertices, faces, values)

    # assemble LayerDataTuple
    layer_data = surface
    layer_properties = {'name': 'topographical surface',
                        'colormap': 'gist_earth',
                        'scale': (1, 1, 1),
                        'translate': (-int(image.max()), 0, 0)}
    layer_type = 'surface'

    return [(layer_data, layer_properties, layer_type)]


def get_inferno_rev_cmap():
    """Revert inferno colormap and make last value transparent."""
    inferno_colormap = colormap_utils.ensure_colormap('inferno')
    inferno_rev_colormap = {
      'colors': np.copy(inferno_colormap.colors)[::-1],
      'name': 'inferno_inv',
      'interpolation': 'linear'
    }
    inferno_rev_colormap['colors'][-1, -1] = 0
    return inferno_rev_colormap

