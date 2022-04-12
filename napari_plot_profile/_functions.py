import numpy as np
from skimage import measure


def topographic_view_positive(image, sample_factor):
    """Generate a 3D topographical image from a 2D positive image."""
    max_range = image.max()
    # Get (z, y, x) coordinates (z are image intensities)
    z_indices = image.ravel().astype(int)[::sample_factor]
    y_indices = np.indices(image.shape)[0].ravel()[::sample_factor]
    x_indices = np.indices(image.shape)[1].ravel()[::sample_factor]

    # For each position, gets all (z,y,x) coordinates smaller than z:
    # - for every z: arange an array from 0 to z
    filled_z_indices = np.concatenate([np.arange(z_indices[i]+1)
                                       for i in range(len(z_indices))])
    # - for every x/y: repeat x/y by z times
    filled_y_indices = np.repeat(y_indices,  z_indices+1)
    filled_x_indices = np.repeat(x_indices,  z_indices+1)

    # Create a 3D image and fills it
    topographic_image = np.zeros((max_range+1,
                                  image.shape[0],
                                  image.shape[1])).astype(int)
    topographic_image[filled_z_indices,
                      filled_y_indices,
                      filled_x_indices] = filled_z_indices

    return topographic_image


def topo_view(image, return_as='image', step_size=1):
    """Generate a topographical view from a 2D image."""
    if return_as != 'surface':
        sample_factor = step_size
    else:
        # if return is a surface, 3D image is not sub-sampled
        sample_factor = 1

    if return_as == 'points':
        z_indices = image.ravel().astype(int)[::sample_factor]
        y_indices = np.indices(image.shape)[0].ravel()[::sample_factor]
        x_indices = np.indices(image.shape)[1].ravel()[::sample_factor]
        points = np.stack((z_indices, y_indices, x_indices), axis=1)
        return(points)
    else:  # image or surface
        if (image < 0).any():  # if image has negatives pixels
            image_pos = np.clip(image, a_min=0, a_max=None)
            topographic_image_pos = topographic_view_positive(image_pos,
                                                              sample_factor)

            image_neg = -np.clip(image, a_min=None, a_max=0)
            topographic_image_neg = -topographic_view_positive(image_neg,
                                                               sample_factor)
            # if return is surface, concatenate to yield a single 3D array
            if return_as == 'surface':
                topographic_image = np.concatenate(
                    (topographic_image_neg[::-1],
                     topographic_image_pos[1:])
                    )
            # if return is not surface, return positive and negative arrays
            else:
                topographic_list = [
                    topographic_image_neg[::-1],
                    topographic_image_pos]
                return topographic_list
        else:  # if image has no negative pixels, get 3D array and proceed
            topographic_image = topographic_view_positive(image, sample_factor)

    if return_as == 'surface':
        # offsets image to positive values to get surface where level = 0
        offset = abs(topographic_image.min())
        topographic_image[topographic_image != 0] += offset
        verts, faces, norm, val = measure.marching_cubes(topographic_image,
                                                         level=0,
                                                         step_size=step_size)
        surface = (verts, faces, val)
        return surface
    else:
        # return positve array
        return topographic_image
