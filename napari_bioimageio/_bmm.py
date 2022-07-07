import os
from pathlib import Path

import napari.resources
from napari._qt.qt_resources import QColoredSVGIcon, get_stylesheet
from qtpy.QtCore import QObject, QSize, Qt, QThread, Signal
from qtpy.QtGui import QFont, QMovie
from qtpy.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QMessageBox,
)
from superqt import QElidingLabel

from . import _utils

# TODO find a proper way to import style from napari
custom_style = (
    get_stylesheet("dark")
    + """
QtModelList {
  background: rgb(0, 0, 0);
}

QtModelListItem {
  background: rgb(52, 57, 64);
  padding: 0;
  margin: 2px 4px;
  border-radius: 3px;
}

QtModelListItem#unavailable {
  background: rgb(103, 108, 115);
  padding: 0;
  margin: 2px 4px;
  border-radius: 3px;
}

QtModelListItem QCheckBox::indicator:disabled {
  background-color: rgba(65, 72, 81, 127);
  image: url(":/themes/dark/check_50.svg");
}

QtBioImageIOModelManager QSplitter{
  padding-right: 2;
}

QtModelInfo > QTextEdit{
  margin: 0px;
  border: 0px;
  padding: 2px;
}
"""
)


class Downloader(QObject):
    model_info = {}
    filter_text = ""
    inspect_data = ""
    already_downloaded = {}
    ready_to_download = {}
    exit_code = 0
    finished = Signal()

    def __init__(
        self,
    ):
        super().__init__()

    def download(
        self,
    ):
        try:
            _utils.download_model(self.model_info["id"], True)
        except Exception as e:
            print("Could not download model:", str(e))
            self.exit_code = -1

        self.refresh()

    def remove(
        self,
    ):
        try:
            _utils.remove_model(self.model_info["rdf_source"])
        except Exception as e:
            print("Could not remove model:", str(e))
            self.exit_code = -1

        self.refresh()

    def inspect(
        self,
    ):
        try:
            self.inspect_data = str(_utils.inspect_model(self.model_info["rdf_source"]))
        except Exception as e:
            print("Could not inspect model:", str(e))
            self.exit_code = -1

        self.finished.emit()

    def _filter(self, models, filter):
        filtered = {}
        if isinstance(filter, str):
            filters = filter.split(";")
        else:
            filters = filter
        for curr_model in models:
            if filter == "":
                filtered[curr_model["id"]] = curr_model
            else:
                model_key = str(curr_model["id"]).lower()
                for curr_filter in filters:
                    if (
                        curr_filter.lower() in curr_model["name"].lower()
                        or curr_filter.lower() in curr_model["tags"].lower()
                        or curr_filter.lower() in curr_model["nickname"].lower()
                        or curr_filter.lower() in model_key
                    ):
                        filtered[curr_model["id"]] = curr_model
                        break
        return filtered

    def refresh(
        self,
    ):
        model_list = _utils.get_downloaded_models()
        self.already_downloaded = self._filter(model_list, self.filter_text)

        model_list = _utils.get_model_list()
        self.ready_to_download = self._filter(model_list, self.filter_text)
        self.finished.emit()


class QtModelInfo(QDialog):
    def __init__(self, parent=None, text=""):
        super().__init__(parent)

        self.layout = QVBoxLayout()

        self.infoTextBox = QTextEdit()
        self.infoTextBox.setLineWrapMode(QTextEdit.NoWrap)
        self.infoTextBox.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_layout = QHBoxLayout()
        self.info_layout.addWidget(self.infoTextBox, 1)
        self.info_layout.setAlignment(Qt.AlignTop)
        self.layout.addLayout(self.info_layout)

        self.infoTextBox.setText(text)
        self.infoTextBox.setMinimumSize(500, 500)

        self.setLayout(self.layout)


class QtModelListItem(QFrame):
    def __init__(
        self,
        model_info,
        downloaded,
        parent: QWidget = None,
        select_mode=False,
    ):
        super().__init__(parent)
        self.model_info = model_info
        self.model_id = model_info["id"]
        self.model_name = model_info["name"]
        self.model_description = model_info["description"]
        self.model_nickname_icon = model_info["nickname_icon"]
        self.model_nickname = model_info["nickname"]
        self.model_versions = model_info.get("versions", None)
        self.model_downloaded = downloaded
        self.select_mode = select_mode

        self.setup_ui()

        self.ui_name.setText(self.model_nickname_icon + " " + self.model_name)
        self.ui_description.setText(self.model_description)
        self.ui_nickname.setText(self.model_nickname)

        if self.model_downloaded == 2:
            self.action_button.setText("remove")
            self.action_button.setObjectName("remove_button")
        elif self.model_downloaded == 1:
            self.action_button.setText("Re-download")
            self.action_button.setObjectName("download_button")
        else:
            self.action_button.setText("Download")
            self.action_button.setObjectName("download_button")

    def _get_dialog(self) -> QDialog:
        p = self.parent()
        while not isinstance(p, QDialog) and p.parent():
            p = p.parent()
        return p

    def setup_ui(self):
        self.v_lay = QVBoxLayout(self)
        self.v_lay.setContentsMargins(-1, 6, -1, 6)
        self.v_lay.setSpacing(0)
        self.row1 = QHBoxLayout()
        self.row1.setSpacing(6)
        self.ui_name = QLabel(self)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ui_name.sizePolicy().hasHeightForWidth())
        self.ui_name.setSizePolicy(sizePolicy)
        font15 = QFont()
        font15.setPointSize(15)
        self.ui_name.setFont(font15)
        self.row1.addWidget(self.ui_name)

        if self.model_downloaded == 2:
            self.inspect_icon = QPushButton(self)
            icon = QColoredSVGIcon.from_resources("zoom")
            self.inspect_icon.setIcon(icon.colored(color="#33F0FF"))
            self.row1.addWidget(self.inspect_icon)
            if self.select_mode:
                self.selection_button = QPushButton(self)
                sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(
                    self.selection_button.sizePolicy().hasHeightForWidth()
                )
                self.selection_button.setSizePolicy(sizePolicy)
                self.selection_button.setText("Select")
                self.selection_button.setObjectName("help_button")
                self.row1.addWidget(self.selection_button)
            self.row1.addStretch()

        self.ui_nickname = QLabel(self)
        self.ui_nickname.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )
        self.row1.addWidget(self.ui_nickname)

        if self.model_versions:
            self.ui_versions = QComboBox()
            for version in self.model_versions:
                self.ui_versions.addItem(version)
            self.row1.addStretch()
            self.row1.addWidget(QLabel("version:"))
            self.row1.addWidget(self.ui_versions)

            def change_version(index):
                # Replace the active version id
                self.model_info["id"] = "/".join(
                    self.model_info["id"].split("/")[:2]
                    + [
                        self.model_versions[index],
                    ]
                )
                print("Switched to model version: " + self.model_info["id"])

            self.ui_versions.currentIndexChanged.connect(change_version)

        self.action_button = QPushButton(self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.action_button.sizePolicy().hasHeightForWidth()
        )
        self.action_button.setSizePolicy(sizePolicy)
        self.row1.addWidget(self.action_button)
        self.v_lay.addLayout(self.row1)
        self.row2 = QHBoxLayout()
        self.row2.setContentsMargins(-1, 4, 0, -1)
        self.ui_description = QElidingLabel(parent=self)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.ui_description.sizePolicy().hasHeightForWidth()
        )
        self.ui_description.setSizePolicy(sizePolicy)
        self.ui_description.setObjectName("small_text")
        self.row2.addWidget(self.ui_description)
        self.v_lay.addLayout(self.row2)


class QtModelList(QListWidget):
    def __init__(self, parent, ui_parent, select_mode):
        super().__init__(parent)
        self.ui_parent = ui_parent
        self.select_mode = select_mode
        self.setSortingEnabled(True)

    def addItem(
        self,
        model_info,
        downloaded,
    ):
        item = QListWidgetItem(str(model_info["id"]), parent=self)
        super().addItem(item)
        widg = QtModelListItem(
            model_info,
            downloaded=downloaded,
            parent=self,
            select_mode=self.select_mode,
        )

        item.widget = widg
        action_name = "remove" if downloaded == 2 else "download"
        widg.action_button.clicked.connect(
            lambda: self.handle_action(item, model_info, action_name)
        )
        if downloaded == 2:
            widg.inspect_icon.clicked.connect(
                lambda: self.handle_action(item, model_info, "inspect")
            )
        if downloaded == 2 and self.select_mode:
            widg.selection_button.clicked.connect(
                lambda: self.handle_action(item, model_info, "select")
            )
        item.setSizeHint(widg.sizeHint())
        self.setItemWidget(item, widg)

    def handle_action(self, item, model_info, action_name):
        if action_name == "download":
            self.ui_parent.run_thread("download", model_info)
        elif action_name == "remove":
            self.ui_parent.run_thread("remove", model_info)
        elif action_name == "inspect":
            self.ui_parent.run_thread("inspect", model_info)
        elif action_name == "select":
            self.ui_parent.run_thread("select", model_info)


class QtBioImageIOModelManager(QDialog):
    def __init__(self, parent=None, filter=None, select_mode=False):
        super().__init__(parent)
        self.setStyleSheet(custom_style)
        self.models_folder = _utils.get_models_path()

        self.RUNNING = False
        self.select_mode = select_mode
        self.selected = None
        self.filter = filter
        self.setup_ui()

    def run_thread(self, action_name, model_info=None):
        if self.RUNNING == False:
            if action_name == "select":
                self.selected = model_info
                self.close()
                return

            self.RUNNING = True
            self.working_indicator.show()
            self.thread = QThread()
            self.worker = Downloader()
            self.worker.moveToThread(self.thread)

            self.worker.model_info = model_info
            self.worker.filter_text = self.filterText.text()
            if action_name == "download":
                self.thread.started.connect(self.worker.download)
                self.run_status.setText("Downloading...")
                self.worker.finished.connect(self.refresh)
            elif action_name == "remove":
                self.thread.started.connect(self.worker.remove)
                self.run_status.setText("removing...")
                self.worker.finished.connect(self.refresh)
            elif action_name == "inspect":
                self.thread.started.connect(self.worker.inspect)
                self.run_status.setText("Inspecting...")
                self.worker.finished.connect(self.inspect_popup)
            else:
                self.thread.started.connect(self.worker.refresh)
                self.run_status.setText("Refreshing...")
                self.worker.finished.connect(self.refresh)

            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.start()

    def refresh(self):
        self.downloaded_list.clear()
        self.available_list.clear()

        for curr_model_key in self.worker.already_downloaded:
            self.downloaded_list.addItem(
                self.worker.already_downloaded[curr_model_key], downloaded=2
            )

        for curr_model_key in self.worker.ready_to_download:
            download_option = (
                1 if curr_model_key in self.worker.already_downloaded else 0
            )
            self.available_list.addItem(
                self.worker.ready_to_download[curr_model_key],
                downloaded=download_option,
            )
        self.working_indicator.hide()
        if self.worker.exit_code == -1:
            self.run_status.setText("Failed, please check logs!")
        else:
            self.run_status.setText("")
        self.RUNNING = False

    def inspect_popup(self):
        self.RUNNING = False
        self.working_indicator.hide()
        if self.worker.exit_code == -1:
            self.run_status.setText("Failed, please check logs!")
        else:
            self.run_status.setText("")
            d = QtModelInfo(self, self.worker.inspect_data)
            d.setWindowTitle("Model information")
            d.setWindowModality(Qt.ApplicationModal)
            d.exec_()

    def setup_ui(self):
        self.resize(1080, 825)

        vlay_1 = QVBoxLayout(self)

        folderBox = QHBoxLayout()
        logo_file = os.path.join(
            os.path.dirname(__file__), "bioimage-io-logo-white.png"
        )
        # TODO: Deal with light theme
        logo_label = QLabel(f'<img src="{logo_file}">')
        folderBox.addWidget(logo_label)
        folderBox.addSpacing(10)
        folderBox.addStretch()
        vlay_1.addLayout(folderBox)

        folderBox = QHBoxLayout()

        modfol_label = QLabel("Models folder:")
        self.modfol_value = QLabel(self.models_folder)
        modfol_folder_btn = QPushButton("Change")
        modfol_folder_btn.clicked.connect(self.getfiles)
        self.run_status = QLabel(self)
        self.run_status.setObjectName("small_italic_text")
        self.run_status.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self.working_indicator = QLabel("updating...", self)
        sp = self.working_indicator.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.working_indicator.setSizePolicy(sp)
        load_gif = str(Path(napari.resources.__file__).parent / "loading.gif")
        mov = QMovie(load_gif)
        mov.setScaledSize(QSize(18, 18))
        self.working_indicator.setMovie(mov)
        mov.start()

        folderBox.addWidget(modfol_label)
        folderBox.addSpacing(10)
        folderBox.addWidget(self.modfol_value)
        folderBox.addSpacing(10)
        folderBox.addWidget(modfol_folder_btn)
        folderBox.addStretch()
        folderBox.addWidget(self.run_status)
        folderBox.addWidget(self.working_indicator)
        folderBox.setContentsMargins(0, 0, 4, 0)
        vlay_1.addLayout(folderBox)

        filterBox = QHBoxLayout()
        self.filterText = QLineEdit()
        self.filterText.setPlaceholderText("filter...")
        self.filterText.setMaximumWidth(350)
        self.filterText.setClearButtonEnabled(True)
        self.filterText.textChanged.connect(lambda: self.run_thread("refresh"))
        filterBox.addWidget(self.filterText)
        filterBox.addStretch()
        vlay_1.addLayout(filterBox)

        self.h_splitter = QSplitter(self)
        vlay_1.addWidget(self.h_splitter)
        self.h_splitter.setOrientation(Qt.Horizontal)
        self.v_splitter = QSplitter(self.h_splitter)
        self.v_splitter.setOrientation(Qt.Vertical)
        self.v_splitter.setMinimumWidth(500)

        downloaded = QWidget(self.v_splitter)
        lay = QVBoxLayout(downloaded)
        lay.setContentsMargins(0, 2, 0, 2)
        self.downloaded_label = QLabel("Downloaded models:")
        mid_layout = QHBoxLayout()
        mid_layout.addWidget(self.downloaded_label)
        mid_layout.addStretch()
        lay.addLayout(mid_layout)
        self.downloaded_list = QtModelList(downloaded, self, self.select_mode)
        self.downloaded_list.setFixedHeight(250)
        lay.addWidget(self.downloaded_list)

        available = QWidget(self.v_splitter)
        lay = QVBoxLayout(available)
        lay.setContentsMargins(0, 2, 0, 2)
        self.avail_label = QLabel("Available models:")
        mid_layout = QHBoxLayout()
        mid_layout.addWidget(self.avail_label)
        mid_layout.addStretch()
        lay.addLayout(mid_layout)
        self.available_list = QtModelList(available, self, False)
        self.available_list.setFixedHeight(250)
        lay.addWidget(self.available_list)

        self.v_splitter.setStretchFactor(1, 2)
        self.h_splitter.setStretchFactor(0, 2)

        if self.filter:
            self.filterText.setText(self.filter)
            self.filterText.setReadOnly(True)
            self.filterText.setEnabled(False)
        else:
            self.run_thread("refresh", None)

    def getfiles(self):
        dlg = QFileDialog()
        dlg.setDirectory(self.models_folder)
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec_():
            filenames = dlg.selectedFiles()
            _utils.set_models_path(filenames[0])
            self.models_folder = _utils.get_models_path()
            self.modfol_value.setText(self.models_folder)
            self.run_thread("refresh")


def show_model_selector(filter=None):
    d = QtBioImageIOModelManager(filter=filter, select_mode=True)
    d.setObjectName("QtBioImageIOModelManager")
    d.setWindowTitle("BioImageIO Model Selector")
    d.setWindowModality(Qt.ApplicationModal)
    d.exec_()
    return d.selected


def show_model_manager():
    d = QtBioImageIOModelManager(select_mode=False)
    d.setObjectName("QtBioImageIOModelManager")
    d.setWindowTitle("BioImageIO Model Manager")
    d.setWindowModality(Qt.ApplicationModal)
    d.exec_()


def show_model_uploader():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setText("To upload the model, please go to https://bioimage.io/#/upload")
    msg.setWindowTitle("Uploading models...")
    # msg.setDetailedText("The details are as follows:")
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()
