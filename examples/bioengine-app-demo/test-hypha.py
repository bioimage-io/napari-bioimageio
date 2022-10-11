"""Test the triton server proxy."""
import msgpack
import numpy as np
import requests
import gzip
import json

def get_config(server_url, model_name):
    response = requests.get(
        f"{server_url}/public/services/triton-client/get_config?model_name="+model_name,
    )
    return json.loads(response.content)

def encode_data(inputs):
    if isinstance(inputs, (np.ndarray, np.generic)):
        return {
            "_rtype": "ndarray",
            "_rvalue": inputs.tobytes(),
            "_rshape": inputs.shape,
            "_rdtype": str(inputs.dtype),
        }
    elif isinstance(inputs, (tuple, list)):
        ret = []
        for input_data in inputs:
            ret.append(encode_data(input_data))
        return ret
    elif isinstance(inputs, dict):
        ret = {}
        for k in list(inputs.keys()):
            ret[k] = encode_data(inputs[k])
        return ret
    else:
        return inputs

def decode_data(outputs):
    if isinstance(outputs, dict):
        if (
            outputs.get("_rtype") == "ndarray"
            and outputs["_rdtype"] != "object"
        ):
            return np.frombuffer(
                outputs["_rvalue"], dtype=outputs["_rdtype"]
            ).reshape(outputs["_rshape"])
        else:
            ret = {}
            for k in list(outputs.keys()):
                ret[k] = decode_data(outputs[k])
            return ret
    elif isinstance(outputs, (tuple, list)):
        ret = []
        for output in outputs:
            ret.append(decode_data(output))
        return ret
    else:
        return outputs   

def execute(inputs, server_url, model_name, **kwargs):
    """
    Execute a model on the trition server.
    The supported kwargs are consistent with pyotritonclient
    https://github.com/oeway/pyotritonclient/blob/bc655a20fabc4611bbf3c12fb15439c8fc8ee9f5/pyotritonclient/__init__.py#L40-L50
    """
    # Represent the numpy array with imjoy_rpc encoding
    # See: https://github.com/imjoy-team/imjoy-rpc#data-type-representation
    inputs = encode_data(inputs)

    kwargs.update(
        {
            "inputs": inputs,
            "model_name": model_name,
        }
    )
    # Encode the arguments as msgpack
    data = msgpack.dumps(kwargs)

    # Compress the data and send it via a post request to the server
    compressed_data = gzip.compress(data)
    response = requests.post(
        f"{server_url}/public/services/triton-client/execute",
        data=compressed_data,
        headers={
            "Content-Type": "application/msgpack",
            "Content-Encoding": "gzip",
        },
    )

    if response.ok:
        # Decode the results form the response
        results = msgpack.loads(response.content)
        # Convert the ndarray objects into numpy arrays
        results = decode_data(results)
        return results
    else:
        raise Exception(f"Failed to execute {model_name}: {response.reason or response.text}")


if __name__ == "__main__":
    # Get the model config with information about inputs/outputs etc.
    config = get_config("https://ai.imjoy.io", "cellpose-python")
    print(config)
    
    # Run inference with cellpose-python model
    image_array = np.random.randint(0, 255, [3, 256, 256]).astype("float32")
    params = {"diameter": 30}
    results = execute(
        inputs=[image_array, params],
        server_url="https://ai.imjoy.io",
        model_name="cellpose-python",
        decode_json=True,
    )
    mask = results["mask"]
    print("Mask predicted: ", mask.shape)
    assert mask.shape == (1, 256, 256)
    print("Test passed for cellpose-python")

    # Get the model config with information about inputs/outputs etc.
    config = get_config("https://ai.imjoy.io", "bioengine-model-runner")
    # print(config)
    
    # Run inference with bioengine-model-runner
    # With this runner you can pass any model_id that are available at https://bioimage.io to the model runner
    image_array = np.random.randint(0, 255, size=(1, 3, 128, 128), dtype=np.uint8)
    kwargs = {"inputs": [image_array], "model_id": "10.5281/zenodo.6200999"}
    ret = execute(
        inputs=[kwargs],
        server_url="https://ai.imjoy.io",
        model_name="bioengine-model-runner",
        serialization="imjoy",
    )
    result = ret["result"]
    assert result["success"] == True, result["error"]
    mask = result["outputs"][0]
    print("Mask predicted: ", mask.shape)
    assert mask.shape == (1, 3, 128, 128), str(
        mask.shape
    )
    print("Test passed for bioengine-model-runner")