"""Helping library to ease interaction between napari and bioimageio.core."""

import glob
import json
import os
import shutil
import typing
import urllib.error
import urllib.request
import zipfile

import bioimageio.core
import bioimageio.spec
import yaml
from bioimageio.core.resource_io.nodes import ResourceDescription

MODELS_DIRECTORY_DEFAULT = os.path.join(os.getcwd(), "bioimageio-models")
RDF_URL_DEFAULT = "https://raw.githubusercontent.com/bioimage-io/collection-bioimage-io/gh-pages/collection.json"


def set_models_path(path: str) -> None:
    """Sets the models' directory.

    Args:
        path: string, location of the desired models directory
    """
    os.environ["BIOIMAGEIO_NAPARI_MODELS_PATH"] = path


def get_models_path() -> str:
    """Gets the models directory."""
    return os.environ.get("BIOIMAGEIO_NAPARI_MODELS_PATH", MODELS_DIRECTORY_DEFAULT)


def set_rdf_url(url: str) -> None:
    """Sets the main RDF collection JSON url.

    Args:
        url: string, url of the main RDF JSON collection
    """
    os.environ["BIOIMAGEIO_NAPARI_RDF_URL"] = url


def get_rdf_url() -> str:
    """Gets the main RDF collection JSON url."""
    return os.environ.get("BIOIMAGEIO_NAPARI_RDF_URL", RDF_URL_DEFAULT)


def get_model_list() -> typing.List[typing.Dict[str, str]]:
    """Produces a convenient python dictionary with all the available models in BioimageIO collection.

    For each item in the collection it creates an entry per version available with the following fields:
    id, version, name, description, tags, nickname, nickname_icon
    Returns:
        Python dictionary with all available models information
    """
    result: typing.List[typing.Dict[str, str]] = []
    try:
        rdf_url = get_rdf_url()
        with urllib.request.urlopen(rdf_url) as url:
            data = json.loads(url.read().decode())
            if isinstance(data, dict) and isinstance(data["collection"], list):
                for key in data["collection"]:
                    if isinstance(key, dict) and key["type"] == "model":
                        for version in key["versions"]:
                            result.append(
                                {
                                    "name": key["name"],
                                    "description": key["description"],
                                    "id": key["id"] + "/" + version,
                                    # "version": version,
                                    "tags": ",".join(
                                        key["tags"] if "tags" in key else ""
                                    ),
                                    "nickname": key["nickname"]
                                    if "nickname" in key
                                    else "",
                                    "nickname_icon": key["nickname_icon"]
                                    if "nickname_icon" in key
                                    else "",
                                }
                            )
            result = sorted(result, key=lambda d: d["name"])
    except urllib.error.URLError as excep:
        print(excep.reason)

    return result


def get_installed_models() -> typing.List[typing.Dict[str, str]]:
    """Produces a convenient python dictionary with all the currently installed models.

    For each item in the collection it creates an entry per version available with the following fields:
    id, version, name, description, tags, nickname, nickname_icon
    Returns:
        Python dictionary with all available models information
    """
    result: typing.List[typing.Dict[str, str]] = []
    models_directory = get_models_path()
    for file in glob.glob(models_directory + "/**/rdf.yaml", recursive=True):
        model_info = bioimageio.core.load_raw_resource_description(file)
        result.append(
            {
                "name": model_info.name,
                "description": model_info.description,
                "id": model_info.id,
                # "version": model_info.id[(model_info.id.rfind("/") + 1) :],
                "tags": ",".join(model_info.tags),
                "nickname": model_info.config["bioimageio"]["nickname"]
                if "nickname" in model_info.config["bioimageio"]
                else "",
                "nickname_icon": model_info.config["bioimageio"]["nickname_icon"]
                if "nickname_icon" in model_info.config["bioimageio"]
                else "",
            }
        )

    result = sorted(result, key=lambda d: d["name"])

    return result


def install_model(model_id: str, overwrite: bool) -> typing.Any:
    """Installs an existing BioimageIO model in the local model folder.

    The model contents will be decompressed in the
        [base model folder + model_id] directory
    Args:
        model_id: string, id of the model
        overwrite: bool, true to force re-install
    Returns:
        String in YAML format with the full model information
    """
    models_directory = get_models_path()
    install_folder = os.path.join(
        models_directory,
        str(model_id)
    )
    destination_file = os.path.join(install_folder, "model.zip")
    yaml_file = os.path.join(install_folder, "rdf.yaml")
    if os.path.exists(install_folder):
        if overwrite:
            shutil.rmtree(install_folder)
        else:
            return convert_model_to_yaml_string(yaml_file)

    os.makedirs(install_folder)
    resource_description = str(model_id)
    bioimageio.core.export_resource_package(resource_description, output_path=destination_file)
    with zipfile.ZipFile(destination_file, "r") as zip_ref:
        zip_ref.extractall(install_folder)
    os.remove(destination_file)

    return convert_model_to_yaml_string(yaml_file)


def remove_model(model_id: str) -> None:
    """Removes an existing locally installed model from the local model folder.

    The [base model folder + model_id] directory
        and all its contents will be removed
    Args:
        model_id: string, id of the model
    """
    models_directory = get_models_path()
    install_folder = os.path.join(
        models_directory,
        str(model_id),
    )
    if os.path.exists(install_folder):
        shutil.rmtree(install_folder)
        if len(os.listdir(os.path.join(models_directory, str(model_id)))) == 0:
            os.rmdir(os.path.join(models_directory, str(model_id)))


def inspect_model(model_id: str) -> typing.Any:
    """Gets the information an existing BioimageIO model in the local model folder.

    Args:
        model_id: string, id of the model
    Returns:
        String in YAML format with the full model information
    """
    models_directory = get_models_path()
    install_folder = os.path.join(
        models_directory,
        str(model_id),
    )
    destination_file = os.path.join(install_folder, "rdf.yaml")
    if os.path.exists(install_folder):
        return convert_model_to_yaml_string(destination_file)

    return None


def load_model(model_id: str) -> ResourceDescription:
    """Load an existing BioimageIO model in the local model folder as a BioimageIO resource.

    Args:
        model_id: string, id of the model
    Returns:
        BioImage.IO resource
    """
    models_directory = get_models_path()
    install_folder = os.path.join(
        models_directory,
        str(model_id),
    )
    destination_file = os.path.join(install_folder, "rdf.yaml")
    if os.path.exists(install_folder):
        return bioimageio.core.load_resource_description(destination_file)

    return None


def convert_model_to_yaml_string(source_file: str) -> typing.Any:
    """Convenient alternative to get the info an existing model in the local model folder from a rdf.yaml file.

    Args:
        source_file: path to the source file (normally "rdf.yaml")
    Returns:
        String in YAML format with the full model information
    """
    if os.path.exists(source_file):
        return yaml.dump(
            bioimageio.spec.serialize_raw_resource_description_to_dict(
                bioimageio.core.load_raw_resource_description(source_file)
            )
        )

    return None
