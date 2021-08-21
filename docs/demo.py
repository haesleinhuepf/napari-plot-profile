import napari
from skimage.io import imread
from skimage.morphology import disk, ball
from skimage.filters.rank import gradient

image = imread('blobs.tif')
image.shape

viewer = napari.Viewer()

viewer.add_image(image, colormap='green', blending='additive')

viewer.add_image(gradient(image, disk(5)), name='gradient', colormap='magenta', blending='additive')

viewer.add_shapes([[ 100,80], [140, 150]], shape_type='path', edge_color='cyan', edge_width=3)

from napari_plot_profile import PlotProfile
profiler = PlotProfile(viewer)
viewer.window.add_dock_widget(profiler, area='right')

napari.run()
