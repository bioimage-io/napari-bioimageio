import os
from pathlib import Path

import napari.resources
from napari._qt.qt_resources import QColoredSVGIcon, get_stylesheet
from qtpy.QtCore import QObject, QSize, Qt, QThread, Signal
from qtpy.QtGui import QFont, QMovie
from qtpy.QtWidgets import (
    QAction,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
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

#dot_menu {
  image: url(":/themes/dark/vertical_separator.svg");
  max-width: 18px;
  max-height: 18px;
  min-width: 18px;
  min-height: 18px;
  margin: 0px;
  margin-left: 1px;
  padding: 2px;
}
"""
)


class Downloader(QObject):
    model_info = {}
    selected_version = ""
    destination_file = ""
    filter_id_text = ""
    filter_tag_text = ""
    inspect_data = ""
    validate_data = ""
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
            _utils.download_model(self.model_info["id"] + '/' + self.selected_version, True)
        except Exception as e:
            print("Could not download model:", str(e))
            self.exit_code = -1

        self.refresh()

    def remove(
        self,
    ):
        try:
            _utils.remove_model(self.model_info["id"][:self.model_info["id"].rfind('/') + 1] + self.selected_version)
        except Exception as e:
            print("Could not remove model:", str(e))
            self.exit_code = -1

        self.refresh()

    def inspect(
        self,
    ):
        try:
            self.inspect_data = str(_utils.inspect_model(self.model_info["id"][:self.model_info["id"].rfind('/') + 1] + self.selected_version))
        except Exception as e:
            print("Could not inspect model:", str(e))
            self.exit_code = -1

        self.finished.emit()

    def validate(
            self,
    ):
        try:
            self.validate_data = str(_utils.validate_model(self.destination_file))
        except Exception as e:
            print("Could not validate model:", str(e))
            self.exit_code = -1

        self.finished.emit()

    def _filter(self, models, filter_id, filter_tag):
        filtered = {}
        filters_id = filter_id.split(";")
        filters_id = filters_id.remove('') if '' in filters_id else filters_id
        filters_tag = filter_tag.split(";")
        filters_tag = filters_tag.remove('') if '' in filters_tag else filters_tag
        for curr_model in models:
            if not filters_id and not filters_tag:
                filtered[curr_model["id"]] = curr_model
            else:
                model_key = str(curr_model["id"]).lower()
                if filters_id:
                    for curr_filter in filters_id:
                        if (
                            curr_filter.lower() in curr_model["name"].lower()
                            or "nickname" in curr_model and curr_filter.lower() in curr_model["nickname"].lower()
                            or curr_filter.lower() in model_key
                        ):
                            filtered[curr_model["id"]] = curr_model
                            break
                if filters_tag:
                    for curr_filter in filters_tag:
                        if curr_filter.lower() in (",".join(curr_model["tags"])).lower():
                            filtered[curr_model["id"]] = curr_model
                            break
        return filtered

    def refresh(
        self,
    ):
        model_list = _utils.get_downloaded_models()
        self.already_downloaded = self._filter(model_list, self.filter_id_text, self.filter_tag_text)

        model_list = _utils.get_model_list()
        self.ready_to_download = self._filter(model_list, self.filter_id_text, self.filter_tag_text)
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
        versions,
        downloaded,
        parent: QWidget = None,
        select_mode=False,
    ):
        super().__init__(parent)
        self.parent = parent
        self.model_info = model_info
        self.model_id = model_info["id"]
        self.model_versions = versions
        self.selected_version = versions[0]
        self.model_name = model_info["name"]
        self.model_description = model_info["description"]
        nickname_icon = ''
        if "nickname_icon" in model_info:
            nickname_icon = model_info["nickname_icon"]
        elif "config" in model_info and "bioimageio" in model_info["config"] and "nickname_icon" in model_info["config"]["bioimageio"]:
            nickname_icon = model_info["config"]["bioimageio"]["nickname_icon"]
        self.model_nickname_icon = nickname_icon
        nickname = ''
        if "nickname" in model_info:
            nickname = model_info["nickname"]
        elif "config" in model_info and "bioimageio" in model_info["config"] and "nickname" in model_info["config"]["bioimageio"]:
            nickname = model_info["config"]["bioimageio"]["nickname"]
        self.model_nickname = nickname
        self.model_downloaded = downloaded
        self.select_mode = select_mode

        self.setup_ui()

        self.ui_name.setText(self.model_nickname_icon + " " + self.model_name)
        self.ui_description.setText(self.model_description)
        self.ui_nickname.setText(self.model_nickname)

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

        self.ui_nickname = QLabel(self)
        self.ui_nickname.setAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter
        )
        self.row1.addWidget(self.ui_nickname)
        self.row1.addStretch()

        if self.model_versions:
            self.ui_versions = QComboBox()
            for curr_version in self.model_versions:
                self.ui_versions.addItem(curr_version)
            self.row1.addStretch()
            self.row1.addWidget(QLabel("Version:"))
            self.row1.addWidget(self.ui_versions)

            def change_version(index):
                self.selected_version = self.model_versions[index]

            self.ui_versions.currentIndexChanged.connect(change_version)

        self.action_button = QPushButton(self)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.action_button.sizePolicy().hasHeightForWidth()
        )
        self.action_button.setSizePolicy(sizePolicy)
        self.action_button.setObjectName("dot_menu")
        self.row1.addWidget(self.action_button)

        action_menu = QMenu(self)
        self.action_button.setMenu(action_menu)

        if self.model_downloaded == 1:
            inspectAction = QAction('Inspect', self)
            inspectAction.triggered.connect(lambda: self.handle_action(self.model_info, "inspect"))
            action_menu.addAction(inspectAction)

            if self.select_mode:
                selectAction = QAction('Select', self)
                selectAction.triggered.connect(lambda: self.handle_action(self.model_info, "select"))
                action_menu.addAction(selectAction)

            removeAction = QAction('Remove', self)
            removeAction.triggered.connect(lambda: self.handle_action(self.model_info, "remove"))
            action_menu.addAction(removeAction)

        else:
            installAction = QAction('Install', self)
            installAction.triggered.connect(lambda: self.handle_action(self.model_info, "download"))
            action_menu.addAction(installAction)


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

    def handle_action(self, model_info, action_name):
        if action_name == "download":
            self.parent.ui_parent.run_thread("download", model_info, self.selected_version)
        elif action_name == "remove":
            self.parent.ui_parent.run_thread("remove", model_info, self.selected_version)
        elif action_name == "inspect":
            self.parent.ui_parent.run_thread("inspect", model_info, self.selected_version)
        elif action_name == "select":
            self.parent.ui_parent.run_thread("select", model_info, self.selected_version)

class QtModelList(QListWidget):
    def __init__(self, parent, ui_parent, select_mode):
        super().__init__(parent)
        self.ui_parent = ui_parent
        self.select_mode = select_mode
        self.setSortingEnabled(True)

    def addItem(
        self,
        model_info,
        versions,
        downloaded,
    ):
        item = QListWidgetItem(str(model_info["id"][:model_info["id"].rfind("/")]), parent=self)
        super().addItem(item)
        widg = QtModelListItem(
            model_info,
            versions,
            downloaded=downloaded,
            parent=self,
            select_mode=self.select_mode,
        )

        item.widget = widg
        item.setSizeHint(widg.sizeHint())
        self.setItemWidget(item, widg)

class QtBioImageIOModelManager(QDialog):
    def __init__(self, parent=None, filter_id=None, filter_tag=None, select_mode=False):
        super().__init__(parent)
        self.setStyleSheet(custom_style)
        self.models_folder = _utils.get_models_path()
        self.validation_file = ""

        self.RUNNING = False
        self.select_mode = select_mode
        self.selected = None
        self.filter_id = filter_id
        self.filter_tag = filter_tag
        self.setup_ui()

    def run_thread(self, action_name, model_info=None, selected_version=""):
        if self.RUNNING == False:
            if action_name == "select":
                self.selected = model_info
                self.selected_version = selected_version
                self.close()
                return

            self.RUNNING = True
            self.working_indicator.show()
            self.thread = QThread()
            self.worker = Downloader()
            self.worker.moveToThread(self.thread)

            self.worker.model_info = model_info
            self.worker.selected_version = selected_version
            self.worker.filter_id_text = self.filter_id_text.text()
            self.worker.filter_tag_text = self.filter_tag_text.text()
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
            elif action_name == "validate":
                self.worker.destination_file = self.validation_file
                self.thread.started.connect(self.worker.validate)
                self.run_status.setText("Validating...")
                self.worker.finished.connect(self.validate_popup)
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

        downloaded_versions = {}
        for curr_model_key in self.worker.already_downloaded:
            pure_model_id = curr_model_key[:curr_model_key.rfind('/')]
            pure_model_version = curr_model_key[len(pure_model_id) + 1:]
            if pure_model_id not in downloaded_versions:
               downloaded_versions[pure_model_id] = []
            downloaded_versions[pure_model_id].append(pure_model_version)

        for curr_model_key in downloaded_versions:
            self.downloaded_list.addItem(
                self.worker.already_downloaded[curr_model_key + '/' + downloaded_versions[curr_model_key][0]],
                sorted(downloaded_versions[curr_model_key], reverse=True),
                downloaded=1
            )

        for curr_model_key in self.worker.ready_to_download:
            self.available_list.addItem(
                self.worker.ready_to_download[curr_model_key],
                sorted(self.worker.ready_to_download[curr_model_key]["versions"], reverse=True),
                downloaded=0,
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

    def validate_popup(self):
        self.RUNNING = False
        self.working_indicator.hide()
        if self.worker.exit_code == -1:
            self.run_status.setText("Failed, please check logs!")
        else:
            self.run_status.setText("")
            d = QtModelInfo(self, self.worker.validate_data)
            d.setWindowTitle("Model validation")
            d.setWindowModality(Qt.ApplicationModal)
            d.exec_()

    def setup_ui(self):
        self.resize(1080, 825)

        vlay_1 = QVBoxLayout(self)

        imageBox = QHBoxLayout()
        logo_file = os.path.join(
            os.path.dirname(__file__), "bioimage-io-logo-white.png"
        )
        # TODO: Deal with light theme
        logo_label = QLabel(f'<img src="{logo_file}">')
        imageBox.addWidget(logo_label)
        imageBox.addSpacing(10)
        imageBox.addStretch()
        vlay_1.addLayout(imageBox)

        validateBox = QHBoxLayout()
        modval_btn = QPushButton("Validate a model")
        modval_btn.clicked.connect(self.getvalidation)

        validateBox.addStretch()
        validateBox.addWidget(modval_btn)
        validateBox.setContentsMargins(0, 0, 4, 8)
        vlay_1.addLayout(validateBox)

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
        folderBox.addSpacing(10)
        folderBox.addWidget(self.run_status)
        folderBox.addWidget(self.working_indicator)
        folderBox.setContentsMargins(0, 0, 4, 0)
        vlay_1.addLayout(folderBox)

        filterBox = QHBoxLayout()
        filter_label = QLabel("Filters:")
        self.filter_id_text = QLineEdit()
        self.filter_id_text.setPlaceholderText("Filter by id...")
        self.filter_id_text.setMaximumWidth(200)
        self.filter_id_text.setClearButtonEnabled(True)
        self.filter_id_text.textChanged.connect(lambda: self.run_thread("refresh"))

        self.filter_tag_text = QLineEdit()
        self.filter_tag_text.setPlaceholderText("Filter by tag...")
        self.filter_tag_text.setMaximumWidth(200)
        self.filter_tag_text.setClearButtonEnabled(True)
        self.filter_tag_text.textChanged.connect(lambda: self.run_thread("refresh"))
        filterBox.addWidget(filter_label)
        filterBox.addSpacing(10)
        filterBox.addWidget(self.filter_id_text)
        filterBox.addSpacing(5)
        filterBox.addWidget(self.filter_tag_text)
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

        if self.filter_id or self.filter_tag:
            if self.filter_id:
                self.filter_id_text.setText(self.filter_id)
                self.filter_id_text.setReadOnly(True)
                self.filter_id_text.setEnabled(False)
            if self.filter_tag:
                self.filter_tag_text.setText(self.filter_tag)
                self.filter_tag_text.setReadOnly(True)
                self.filter_tag_text.setEnabled(False)
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

    def getvalidation(self):
        dlg = QFileDialog()
        dlg.setDirectory(self.models_folder)
        dlg.setFileMode(QFileDialog.ExistingFile)

        if dlg.exec_():
            filenames = dlg.selectedFiles()
            self.validation_file = filenames[0]
            self.run_thread("validate")


def show_model_selector(filter_id=None, filter_tag=None):
    d = QtBioImageIOModelManager(filter_id=filter_id, filter_tag=filter_tag, select_mode=True)
    d.setObjectName("QtBioImageIOModelManager")
    d.setWindowTitle("BioImageIO Model Selector")
    d.setWindowModality(Qt.ApplicationModal)
    d.exec_()
    return d.selected, d.selected_version


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

def load_model_by_id(model_id):
    return _utils.load_model(model_id)