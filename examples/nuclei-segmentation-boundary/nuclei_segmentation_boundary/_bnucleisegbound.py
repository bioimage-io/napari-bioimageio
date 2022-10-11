import bioimageio.core
import napari.resources
import numpy as np
from xarray import DataArray
from skimage.measure import label
from skimage.io import imread
from napari._qt.qt_resources import get_stylesheet
from napari.utils.notifications import show_error as notify_error
from napari_bioimageio import show_model_selector, load_model_by_id
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

cell_segmentation_model_filter = "10.5281/zenodo.5764892"

# TODO find a proper way to import style from napari
custom_style = get_stylesheet("dark")


class QTNucleiSegBound(QDialog):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._viewer = viewer
        self.setStyleSheet(custom_style)
        self.image_layer = ""
        self.cellseg_model_source = ""
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
            test_image = imread('https://zenodo.org/api/files/61da5c68-e09b-49a6-899b-94c22cdfc4d9/sample_input_0.tif')
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


        cellsegBox = QHBoxLayout()
        cellseg_label = QLabel("Model:")
        self.cellseg_value = QLabel(self.cellseg_id)
        cellseg_value_btn = QPushButton("Select")

        def select_model():
            model_info, selected_version = show_model_selector(filter_id=cell_segmentation_model_filter)
            if model_info:
                self.cellseg_model_source = model_info["rdf_source"]
                self.cellseg_id = model_info["id"]
                self.cellseg_version = selected_version
                self.cellseg_value.setText(model_info["config"]["bioimageio"]["nickname"])

        cellseg_value_btn.clicked.connect(select_model)
        cellsegBox.addWidget(cellseg_label)
        cellsegBox.addSpacing(10)
        cellsegBox.addWidget(self.cellseg_value)
        cellsegBox.addSpacing(10)
        cellsegBox.addWidget(cellseg_value_btn)
        cellsegBox.addStretch()
        cellsegBox.setContentsMargins(10, 0, 10, 0)
        self.layout.addLayout(cellsegBox)


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
        if self.cellseg_model_source == "":
            notify_error("Please select a valid model")
            return

        np_img = self._viewer.layers[self.cb.currentText()].data

        run_cell_model = load_model_by_id(
            self.cellseg_id + '/' + self.cellseg_version
        )

        axes = run_cell_model.inputs[0].axes
        padding = {"x": 16, "y": 16}
        input_img = DataArray(
            [[np_img]],
            dims=axes,
        )

        segmentation = bioimageio.core.prediction.predict_with_padding(
            bioimageio.core.create_prediction_pipeline(
                bioimageio_model=run_cell_model
            ), input_img, padding=padding)[0].values[0]

        threshold = 0.5
        fg = segmentation[0]
        nuclei = label(fg > threshold)

        fg = segmentation[1]
        boundaries = label(fg > threshold)

        v = self._viewer
        v.add_labels(nuclei, name="segmentation")
        v.add_labels(boundaries, name="bondaries")