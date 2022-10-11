# BioEngine App Demo plugin

This plugin demonstrate how to use the BioEngine to run models on remote servers.

BioEngine is built on top of [Hypha](https://github.com/amun-ai/hypha), it allows serving models in the [BioImage Model Zoo](https://bioimage.io), see [here](https://slides.imjoy.io/?slides=https://raw.githubusercontent.com/oeway/slides/master/2022/i2k-2022-hypha-introduction.md) for more information about Hypha.

The advantage of using the BioEngine is that users won't need to install the deep learning libraries, for performing inference and even training on the server side. This however does mean the data will be sent to the server for processing, please be careful if you are processing sensitive data.

## Installation

```
cd examples/bioengine-app-demo
pip install .
```