# napari-plot-profile

[![License](https://img.shields.io/pypi/l/napari-plot-profile.svg?color=green)](https://github.com/haesleinhuepf/napari-plot-profile/raw/master/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-plot-profile.svg?color=green)](https://pypi.org/project/napari-plot-profile)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-plot-profile.svg?color=green)](https://python.org)
[![tests](https://github.com/haesleinhuepf/napari-plot-profile/workflows/tests/badge.svg)](https://github.com/haesleinhuepf/napari-plot-profile/actions)
[![codecov](https://codecov.io/gh/haesleinhuepf/napari-plot-profile/branch/master/graph/badge.svg)](https://codecov.io/gh/haesleinhuepf/napari-plot-profile)

Plot the intensities a long a line in napari.

## Usage

* Open some images and add a shapes layer.

![img.png](https://github.com/haesleinhuepf/napari-plot-profile/raw/main/docs/add_shapes_layer_screenshot.png)
  
* Activate the line drawing tool or the path tool and draw a line.

![img.png](https://github.com/haesleinhuepf/napari-plot-profile/raw/main/docs/draw_line_tool_screenshot.png)
  
* After drawing a line, click on the menu Plugins > Measurements (Plot Profile)
* If you modify the line, you may want to click the "Refresh" button to redraw the profile.

![img.png](https://github.com/haesleinhuepf/napari-plot-profile/raw/main/docs/redraw_screenshot.png)

To see how these steps can be done programmatically from python, check out the [demo notebook](https://github.com/haesleinhuepf/napari-plot-profile/blob/main/docs/demo.ipynb)

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using with [@napari]'s [cookiecutter-napari-plugin] template.

## Installation

You can install `napari-plot-profile` via [pip]:

    pip install napari-plot-profile

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-plot-profile" is free and open source software

## Issues

If you encounter any problems, please create a thread on [image.sc] along with a detailed description and tag [@haesleinhuepf].

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/haesleinhuepf/napari-plot-profile/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/

[@haesleinhuepf]: https://twitter.com/haesleinhuepf
