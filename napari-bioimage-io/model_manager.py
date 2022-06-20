import os
import shutil
import json
import urllib.request
import urllib.error
import glob
import yaml

import bioimageio.core as bc
import bioimageio.spec as bs
import zipfile


MODELS_DIRECTORY_DEFAULT = os.path.join(os.getcwd(), "models")
RDF_URL_DEFAULT = 'https://raw.githubusercontent.com/bioimage-io/collection-bioimage-io/gh-pages/collection.json'
RDF_SOURCE_URL_DEFAULT = 'https://raw.githubusercontent.com/bioimage-io/collection-bioimage-io/gh-pages/rdfs'


def set_models_path(path):
    os.environ['BIOIMAGEIO_NAPARI_MODELS_PATH'] = path


def get_models_path():
    return os.environ.get('BIOIMAGEIO_NAPARI_MODELS_PATH', MODELS_DIRECTORY_DEFAULT)


def set_rdf_url(url):
    os.environ['BIOIMAGEIO_NAPARI_RDF_URL'] = url


def get_rdf_url():
    return os.environ.get('BIOIMAGEIO_NAPARI_RDF_URL', RDF_URL_DEFAULT)


def set_rdf_source_url(url):
    os.environ['BIOIMAGEIO_NAPARI_RDF_SOURCE_URL'] = url


def get_rdf_source_url():
    return os.environ.get('BIOIMAGEIO_NAPARI_RDF_SOURCE_URL', RDF_SOURCE_URL_DEFAULT)


def get_model_list():
    result = []
    try:
        rdf_url = get_rdf_url()
        with urllib.request.urlopen(rdf_url) as url:
            data = json.loads(url.read().decode())
            if isinstance(data, dict) and isinstance(data['collection'], list):
                for key in data['collection']:
                    if isinstance(key, dict) and key['type'] == 'model':
                        for version in key['versions']:
                            result.append({'name': key['name'],
                                           'description': key['description'],
                                           'id': key['id'],
                                           'version': version,
                                           'tags': ",".join(key['tags'] if 'tags' in key else ''),
                                           'nickname': key['nickname'] if 'nickname' in key else '',
                                           'nickname_icon': key['nickname_icon'] if 'nickname_icon' in key else ''})
            result = sorted(result, key=lambda d: d['name'])
    except urllib.error.URLError as e:
        print(e.reason)

    return result


def get_model_yaml(model_id, model_version):
    result = ''
    try:
        rdf_source_url = get_rdf_source_url()
        with urllib.request.urlopen(rdf_source_url + '/' + str(model_id) + '/' + str(model_version) + '/rdf.yaml') as url:
            result = url.read().decode()
    except urllib.error.URLError as e:
        print(e.reason)

    return result


def get_installed_models():
    result = []
    models_directory = get_models_path()
    for file in glob.glob(models_directory + '/**/rdf.yaml', recursive=True):
        model_info = bc.load_raw_resource_description(file)
        result.append({'name': model_info.name,
                       'description': model_info.description,
                       'id': model_info.id[:(model_info.id.rfind('/'))],
                       'version': model_info.id[(model_info.id.rfind('/') + 1):],
                       'tags': ",".join(model_info.tags),
                       'nickname': model_info.config['bioimageio']['nickname'] if 'nickname' in model_info.config['bioimageio'] else '',
                       'nickname_icon': model_info.config['bioimageio']['nickname_icon'] if 'nickname_icon' in model_info.config['bioimageio'] else ''})

    result = sorted(result, key=lambda d: d['name'])

    return result


def install_model(model_id, model_version, overwrite):
    models_directory = get_models_path()
    install_folder = os.path.join(models_directory, str(model_id), str(model_version) if model_version is not None else "latest")
    destination_file = os.path.join(install_folder, "model.zip")
    yaml_file = os.path.join(install_folder, "rdf.yaml")
    if os.path.exists(install_folder):
        if overwrite:
            shutil.rmtree(install_folder)
        else:
            return convert_model_to_yaml_string(yaml_file)

    os.makedirs(install_folder)
    resource_description = str(model_id)
    if model_version is not None and str(model_version) != '':
        resource_description = resource_description + '/' + str(model_version)
    bc.export_resource_package(resource_description, output_path=destination_file)
    with zipfile.ZipFile(destination_file, 'r') as zip_ref:
        zip_ref.extractall(install_folder)
    os.remove(destination_file)

    return convert_model_to_yaml_string(yaml_file)


def remove_model(model_id, model_version):
    models_directory = get_models_path()
    install_folder = os.path.join(models_directory, str(model_id), str(model_version) if model_version is not None else "latest")
    if os.path.exists(install_folder):
        shutil.rmtree(install_folder)
        if len(os.listdir(os.path.join(models_directory, str(model_id)))) == 0:
            os.rmdir(os.path.join(models_directory, str(model_id)))


def inspect_model(model_id, model_version):
    models_directory = get_models_path()
    install_folder = os.path.join(models_directory, str(model_id), str(model_version) if model_version is not None else "latest")
    destination_file = os.path.join(install_folder, "rdf.yaml")
    if os.path.exists(install_folder):
        return convert_model_to_yaml_string(destination_file)

    return None


def load_model(model_id, model_version):
    models_directory = get_models_path()
    install_folder = os.path.join(models_directory, str(model_id), str(model_version) if model_version is not None else "latest")
    destination_file = os.path.join(install_folder, "rdf.yaml")
    if os.path.exists(install_folder):
        return bc.load_resource_description(destination_file)

    return None


def convert_model_to_yaml_string(source_file):
    if os.path.exists(source_file):
        return yaml.dump(bs.serialize_raw_resource_description_to_dict(bc.load_raw_resource_description(source_file)))

    return ''

