How to install and try napari and the plugins
---------------------------------------------

- Create virtual environment
- Install napari
  - `pip install napari`
  - `pip install PyQt5` (if needed)
- Install `bioimage.napari` library
  - If published:
     - `pip install bioimage.napari`
  - OR if builded locally
     - `pip install {location of your bioimageio.napari-0.1.0-py3-none-any.whl}`
- Go to the main folder of each of the napari plugins and install them:
  - `pip install .`
- Run napari
  - `napari`
