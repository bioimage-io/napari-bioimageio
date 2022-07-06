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
### `show_model_uploader()`

Display a dialog to instruct the user to upload a model to the BioImage Model Zoo.
Currently, it only shows a message, in the future, we will try to support direct uploading with user's credentials obtained from Zenodo (a public data repository used by the BioImage Model Zoo to store models).
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
