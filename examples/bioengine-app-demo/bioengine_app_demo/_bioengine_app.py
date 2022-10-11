import napari.resources
from skimage.measure import label
from skimage.io import imread
from napari._qt.qt_resources import get_stylesheet
from napari.utils.notifications import show_error as notify_error
from .hypha_http_client import execute

from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

# TODO find a proper way to import style from napari
custom_style = get_stylesheet("dark")


class QTBioEngineApp(QDialog):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._viewer = viewer
        self.setStyleSheet(custom_style)
        self.image_layer = ""
        # self.cellseg_model_source = ""
        self.cellseg_id = "None"

        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout()

        imageBox = QHBoxLayout()
        image_label = QLabel("Image layer:")

        self.cb = QComboBox()
        for curr_layer in self._viewer.layers:
            self.cb.addItem(curr_layer.name)
        self.cb.addItem("None")

        test_image_btn = QPushButton("Load test image")

        def load_test_image():
            test_image = imread('https://zenodo.org/api/files/8e1dc6e7-bdc9-412c-b06c-e79ee375989f/sample_input_0.tif')
            v = self._viewer
            v.add_image(test_image)
            self.cb.addItem("test_image")
            self.cb.setCurrentText("test_image")

        test_image_btn.clicked.connect(load_test_image)

        imageBox.addWidget(image_label, 3)
        imageBox.addWidget(self.cb, 4)
        imageBox.addWidget(test_image_btn, 3)
        imageBox.addStretch()
        imageBox.setContentsMargins(10, 10, 10, 0)
        self.layout.addLayout(imageBox)

        runBox = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.setObjectName("install_button")
        self.run_btn.clicked.connect(self.run_model)
        runBox.addWidget(self.run_btn)
        runBox.setContentsMargins(10, 20, 10, 10)
        self.layout.addLayout(runBox)

        self.layout.addStretch()
        self.setLayout(self.layout)

    def run_model(self):
        if self.cb.currentText() == "None":
            notify_error("Please select a valid image layer")
            return

        np_img = self._viewer.layers[self.cb.currentText()].data

        if np_img.ndim == 2:
            np_img = np_img[None, None, : , :]
        elif np_img.ndim == 3:
            np_img = np_img[None, :, : , :]

        assert len(np_img.shape) == 4

        kwargs = {"inputs": [np_img], "model_id": "10.5281/zenodo.5869899"}
        ret = execute(
            inputs=[kwargs],
            server_url="https://ai.imjoy.io",
            model_name="bioengine-model-runner",
            serialization="imjoy",
        )
        
        result = ret["result"]
        assert result["success"] == True, result["error"]
        segmentation = result["outputs"][0]

        threshold = 0.5
        fg = segmentation[0, 0, :, :]
        nuclei = label(fg > threshold)

        fg = segmentation[0, 1, :, :]
        boundaries = label(fg > threshold)

        v = self._viewer
        v.add_labels(nuclei, name="segmentation")
        v.add_labels(boundaries, name="bondaries")