import bioimageio.core
import napari.resources
import numpy as np
from napari._qt.qt_resources import get_stylesheet
from napari.utils.notifications import show_error as notify_error
from napari_bioimageio import show_model_selector, show_model_manager, load_model_by_id
from qtpy.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from skimage.measure import label
from skimage.segmentation import watershed
from skimage.transform import rescale
from xarray import DataArray

nuclear_segmentation_model_filter = "10.5281/zenodo.6200999"
cell_segmentation_model_filter = "10.5281/zenodo.6200635"

# TODO find a proper way to import style from napari
custom_style = get_stylesheet("dark")


class QTHPASegmentation(QDialog):
    def __init__(self, viewer: "napari.viewer.Viewer"):
        super().__init__()
        self._viewer = viewer
        self.setStyleSheet(custom_style)
        self.image1_layer = ""
        self.image2_layer = ""
        self.image3_layer = ""
        self.nucseg_model_source = ""
        self.nucseg_id = "None"
        self.celseg_model_source = ""
        self.celseg_id = "None"

        self.setup_ui()

    def setup_ui(self):
        self.layout = QVBoxLayout()

        imageTitleBox = QHBoxLayout()
        imageTitle_label = QLabel("Layers selected:")
        imageTitle_label.setMinimumWidth(500)
        imageTitleBox.addWidget(imageTitle_label)
        imageTitleBox.addStretch()
        imageTitleBox.setContentsMargins(10, 10, 10, 0)
        self.layout.addLayout(imageTitleBox)

        image1Box = QHBoxLayout()
        image1_label = QLabel("- Nucleus:")
        self.cb_1 = QComboBox()
        for curr_layer in self._viewer.layers:
            self.cb_1.addItem(curr_layer.name)
        self.cb_1.addItem("None")
        image1Box.addWidget(image1_label, 3)
        image1Box.addWidget(self.cb_1, 7)
        image1Box.addStretch()
        image1Box.setContentsMargins(10, 0, 10, 0)
        self.layout.addLayout(image1Box)

        image2Box = QHBoxLayout()
        image2_label = QLabel("- Microtubules:")
        self.cb_2 = QComboBox()
        for curr_layer in self._viewer.layers:
            self.cb_2.addItem(curr_layer.name)
        self.cb_2.addItem("None")
        image2Box.addWidget(image2_label, 3)
        image2Box.addWidget(self.cb_2, 7)
        image2Box.addStretch()
        image2Box.setContentsMargins(10, 0, 10, 0)
        self.layout.addLayout(image2Box)

        image3Box = QHBoxLayout()
        image3_label = QLabel("- ER:")
        self.cb_3 = QComboBox()
        for curr_layer in self._viewer.layers:
            self.cb_3.addItem(curr_layer.name)
        self.cb_3.addItem("None")
        image3Box.addWidget(image3_label, 3)
        image3Box.addWidget(self.cb_3, 7)
        image3Box.addStretch()
        image3Box.setContentsMargins(10, 0, 10, 0)
        self.layout.addLayout(image3Box)

        modelsTitleBox = QHBoxLayout()
        modelsTitle_label = QLabel("Models:")
        modelsTitleBox.addWidget(modelsTitle_label)
        modelsTitleBox.addStretch()

        manager_btn = QPushButton("Show Models")

        def show_models():
            show_model_manager()

        manager_btn.clicked.connect(show_models)
        modelsTitleBox.addWidget(manager_btn)

        modelsTitleBox.setContentsMargins(10, 15, 10, 0)
        self.layout.addLayout(modelsTitleBox)

        nucsegBox = QHBoxLayout()
        nucseg_label = QLabel("Nucleus segmentation:")
        self.nucseg_value = QLabel(self.nucseg_id)
        nucseg_value_btn = QPushButton("Select")

        def select_model():
            model_info, selected_version = show_model_selector(filter_id=nuclear_segmentation_model_filter)
            if model_info:
                self.nucseg_model_source = model_info["rdf_source"]
                self.nucseg_id = model_info["id"]
                self.nucseg_version = selected_version
                self.nucseg_value.setText(model_info["config"]["bioimageio"]["nickname"])

        nucseg_value_btn.clicked.connect(select_model)
        nucsegBox.addWidget(nucseg_label)
        nucsegBox.addSpacing(10)
        nucsegBox.addWidget(self.nucseg_value)
        nucsegBox.addSpacing(10)
        nucsegBox.addWidget(nucseg_value_btn)
        nucsegBox.addStretch()
        nucsegBox.setContentsMargins(10, 0, 10, 0)
        self.layout.addLayout(nucsegBox)

        celsegBox = QHBoxLayout()
        celseg_label = QLabel("Cell segmentation:")
        self.celseg_value = QLabel(self.celseg_id)
        celseg_value_btn = QPushButton("Select")

        def select_model():
            model_info, selected_version = show_model_selector(filter_id=cell_segmentation_model_filter)
            if model_info:
                self.celseg_model_source = model_info["rdf_source"]
                self.celseg_id = model_info["id"]
                self.celseg_version = selected_version
                self.celseg_value.setText(model_info["config"]["bioimageio"]["nickname"])

        celseg_value_btn.clicked.connect(select_model)
        celsegBox.addWidget(celseg_label)
        celsegBox.addSpacing(10)
        celsegBox.addWidget(self.celseg_value)
        celsegBox.addSpacing(10)
        celsegBox.addWidget(celseg_value_btn)
        celsegBox.addStretch()
        celsegBox.setContentsMargins(10, 0, 10, 0)
        self.layout.addLayout(celsegBox)

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
        if self.cb_1.currentText() == "None":
            notify_error("Please select a valid Nucleus image layer")
            return
        if self.cb_2.currentText() == "None":
            notify_error("Please select a valid Microtubules image layer")
            return
        if self.cb_3.currentText() == "None":
            notify_error("Please select a valid ER image layer")
            return
        if self.nucseg_model_source == "":
            notify_error("Please select a valid nucleus segmentation model")
            return
        if self.celseg_model_source == "":
            notify_error("Please select a valid cell segmentation model")
            return

        image_paths = {}
        image_paths["plugin_cls"] = [
            [
                self.cb_2.currentText(),
                self.cb_1.currentText(),
                self.cb_3.currentText(),
            ]
        ]

        cell_segmentation = None

        run_nucleus_model = load_model_by_id(
            self.nucseg_id + '/' + self.nucseg_version
        )
        run_cell_model = load_model_by_id(
            self.celseg_id + '/' + self.celseg_version
        )

        axes = run_cell_model.inputs[0].axes
        channels = ["red", "blue", "green"]
        padding = {"x": 32, "y": 32}
        scale_factor = 1

        def load_image(channels, scale_factor=None):
            image = []
            for chan in channels:
                np_img_chan = []
                if chan == "red":
                    np_img_chan = self._viewer.layers[self.cb_2.currentText()].data
                elif chan == "blue":
                    np_img_chan = self._viewer.layers[self.cb_1.currentText()].data
                if chan == "green":
                    np_img_chan = self._viewer.layers[self.cb_3.currentText()].data
                if scale_factor is not None:
                    np_img_chan = rescale(np_img_chan, scale_factor)
                image.append(np_img_chan[None])
            image = np.concatenate(image, axis=0)

            return image

        def _segment(pp_cell, pp_nucleus):
            image = load_image(channels, scale_factor=scale_factor)
            print(np.shape(image))
            print(np.shape(image[1:2]))
            # run prediction with the nucleus model
            input_nucleus = DataArray(
                np.concatenate([image[1:2], image[1:2], image[1:2]], axis=0)[None],
                dims=axes,
            )
            nuclei_pred = bioimageio.core.prediction.predict_with_padding(
                pp_nucleus, input_nucleus, padding=padding
            )[0].values[0]

            # segment the nuclei in order to use them as seeds for the cell segmentation
            threshold = 0.5
            min_size = 250
            fg = nuclei_pred[-1]
            nuclei = label(fg > threshold)
            ids, sizes = np.unique(nuclei, return_counts=True)
            # don't apply size filter on the border
            border = np.ones_like(nuclei).astype("bool")
            border[1:-1, 1:-1] = 0
            filter_ids = ids[sizes < min_size]
            border_ids = nuclei[border]
            filter_ids = np.setdiff1d(filter_ids, border_ids)
            nuclei[np.isin(nuclei, filter_ids)] = 0

            # run prediction with the cell segmentation model
            input_cells = DataArray(image[None], dims=axes)
            cell_pred = bioimageio.core.prediction.predict_with_padding(
                pp_cell, input_cells, padding=padding
            )[0].values[0]
            # segment the cells
            threshold = 0.5
            fg, bd = cell_pred[2], cell_pred[1]
            cell_seg = watershed(bd, markers=nuclei, mask=fg > threshold)

            # bring back to the orignial scale
            cell_seg = rescale(
                cell_seg,
                1.0 / scale_factor,
                order=0,
                preserve_range=True,
                anti_aliasing=False,
            ).astype(cell_seg.dtype)
            return cell_seg

        with bioimageio.core.create_prediction_pipeline(
            bioimageio_model=run_cell_model
        ) as pp_cell:
            with bioimageio.core.create_prediction_pipeline(
                bioimageio_model=run_nucleus_model
            ) as pp_nucleus:
                cell_segmentation = _segment(pp_cell, pp_nucleus)


        def visualize(segmentation):
            v = self._viewer
            v.add_labels(segmentation)

        visualize(cell_segmentation)
