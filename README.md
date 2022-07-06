# napari-bioimage-io

napari plugin for managing AI models in the BioImage Model Zoo.

## Installation

```
pip install napari[pyqt5] napari-bioimageio
```

## Usage

This library is meant for helping developers to ease the handling of models in napari.

We provide a set of API functions for managing and selecting models.

### `show_model_manager()`
Show the model manager with a model list pulled from the BioImage Model Zoo, the user can explore all the available models, download or remove models.

### `show_model_selector(filter=None)`
Display a dialog for selecting models from the BioImage Model Zoo, the user can either select an existing model or download from the BioImage Model Zoo.

The selecte model information (a dictionary) will be returned if the user selected a model, otherwise it returns `None`.

Once the user selected the model, you can access the name, and also the file path to the model resource description file (via the `rdf_source` key). With the `bioimageio.core` library (installed via `pip install bioimageio.core` or `conda install -c conda-forge bioimageio.core`), you can run inference directly, the following examples shows how to implement it:

```python
# Popup a model selection dialog for choosing the model
model_info = show_model_selector(filter=nuclear_segmentation_model_filter)

if model_info:
  self.nucseg_model_source = model_info["rdf_source"]
  # Load model 
  model_description = bioimageio.core.load_resource_description(model_info["rdf_source"])
  input_image = imageio.imread("./my-image.tif")

  with bioimageio.core.create_prediction_pipeline(
      bioimageio_model=model_description
  ) as pipeline:
    output_image = bioimageio.core.prediction.predict_with_padding(
        pipeline, input_image, padding=padding
    )
```

For more examples, see [this example notebook](https://github.com/bioimage-io/core-bioimage-io-python/blob/main/example/bioimageio-core-usage.ipynb) for `bioimageio.core`.
### `show_model_uploader()`
Display a dialog to instruct the user to upload a model package to the BioImage Model Zoo.
Currently, it only shows a message, in the future, we will try to support direct uploading with user's credentials obtained from Zenodo (a public data repository used by the BioImage Model Zoo to store models).

To create a BioImageIO-compatible model package, you can use the `build_model` function as demonstrated in [this notebook]((https://github.com/bioimage-io/core-bioimage-io-python/blob/main/example/bioimageio-core-usage.ipynb)).

## Development

- Install and set up development environment.

  ```sh
  pip install -r requirements_dev.txt
  ```

  This will install all requirements.
It will also install this package in development mode, so that code changes are applied immediately without reinstall necessary.

- Here's a list of development tools we use.
  - [black](https://pypi.org/project/black/)
  - [flake8](https://pypi.org/project/flake8/)
  - [mypy](https://pypi.org/project/mypy/)
  - [pydocstyle](https://pypi.org/project/pydocstyle/)
  - [pylint](https://pypi.org/project/pylint/)
  - [pytest](https://pypi.org/project/pytest/)
  - [tox](https://pypi.org/project/tox/)
- It's recommended to use the corresponding code formatter and linters also in your code editor to get instant feedback. A popular editor that can do this is [`vscode`](https://code.visualstudio.com/).
- Run all tests, check formatting and linting.

  ```sh
  tox
  ```

- Run a single tox environment.

  ```sh
  tox -e lint
  ```

- Reinstall all tox environments.

  ```sh
  tox -r
  ```

- Run pytest and all tests.

  ```sh
  pytest
  ```

- Run pytest and calculate coverage for the package.

  ```sh
  pytest --cov-report term-missing --cov=napari-bioimageio
  ```

- Continuous integration is by default supported via [GitHub actions](https://help.github.com/en/actions). GitHub actions is free for public repositories and comes with 2000 free Ubuntu build minutes per month for private repositories.
