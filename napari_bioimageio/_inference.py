def run_inference(image: 'napari.types.ImageData',
                  rdf_path: str,
                  halo: int = 16) -> 'napari.types.LayerDataTuple':
    """Run inference on a napari image using a bioimage.io model.

    Parameters
    ----------
    image : napari.types.ImageData
        Image to run inference on.
    rdf_path : str
        Path to the model RDF file.

    Returns
    -------
    napari.types.LayerDataTuple
        Inference result.
    """
    from bioimageio.core import (load_resource_description,
                                 predict_with_tiling,
                                 create_prediction_pipeline)
    import xarray as xr

    model_resource = load_resource_description(rdf_path)

    prediction_pipeline = create_prediction_pipeline(
        model_resource, devices=None, weight_format=None
    )

    tiling = {"tile": {"x": model_resource.inputs[0].shape[-1],
                       "y": model_resource.inputs[0].shape[-2],
                       "z": model_resource.inputs[0].shape[-3]},
              "halo": {"x": halo, "y": halo}}

    input_array = xr.DataArray(
        image,
        dims=tuple(model_resource.inputs[0].axes))

    # run prediction and throw clear error message if dimensions don't match
    prediction = predict_with_tiling(prediction_pipeline,
                                        input_array,
                                        tiling=tiling,
                                        verbose=True)
    properties = {
        'name': 'prediction',
        'colormap': 'inferno',
        'blending': 'additive',
        'opacity': 0.5
        }

    return (prediction, properties, 'image')
