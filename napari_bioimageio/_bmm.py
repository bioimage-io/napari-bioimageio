import os
from pathlib import Path
from qtpy.QtCore import (
    QObject,
    QProcess,
    QSize,
    Qt,
    QThread,
    Signal,
)
from qtpy.QtGui import QFont, QMovie
from qtpy.QtWidgets import (
    QCheckBox,
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
)
from superqt import QElidingLabel
import napari.resources
from napari._qt.qt_resources import get_stylesheet, QColoredSVGIcon
from . import model_manager


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

QtBioimageIOModelManager QSplitter{
  padding-right: 2;
}

QtModelInfo > QTextEdit{
  margin: 0px;
  border: 0px;
  padding: 2px;
}
"""
)


class Installer(QObject):
    model_id = ""
    model_version = ""
    filter_text = ""
    inspect_data = ""
    already_installed = {}
    ready_to_install = {}
    exit_code = 0
    finished = Signal()

    def __init__(
        self,
    ):
        super().__init__()

    def install(
        self,
    ):
        try:
            model_manager.install_model(self.model_id, self.model_version, True)
        except Exception as e:
            print("Could not install model:", str(e))
            self.exit_code = -1

        self.refresh()

    def uninstall(
        self,
    ):
        try:
            model_manager.remove_model(self.model_id, self.model_version)
        except Exception as e:
            print("Could not remove model:", str(e))
            self.exit_code = -1

        self.refresh()

    def inspect(
        self,
    ):
        try:
            self.inspect_data = str(
                model_manager.inspect_model(self.model_id, self.model_version)
            )
        except Exception as e:
            print("Could not inspect model:", str(e))
            self.exit_code = -1

        self.finished.emit()

    def refresh(
        self,
    ):
        self.already_installed = {}
        self.ready_to_install = {}
        model_list = model_manager.get_installed_models()
        for curr_model in model_list:
            if self.filter_text == "":
                self.already_installed[
                    curr_model["id"] + "/" + curr_model["version"]
                ] = curr_model
            else:
                model_key = (
                    str(curr_model["id"]) + "/" + str(curr_model["version"]).lower()
                )
                for curr_filter in self.filter_text.split(";"):
                    if (
                        curr_filter.lower() in curr_model["name"].lower()
                        or curr_filter.lower() in curr_model["tags"].lower()
                        or curr_filter.lower() in curr_model["nickname"].lower()
                        or curr_filter.lower() in model_key
                    ):
                        self.already_installed[
                            curr_model["id"] + "/" + curr_model["version"]
                        ] = curr_model
                        break

        model_list = model_manager.get_model_list()
        for curr_model in model_list:
            if self.filter_text == "":
                self.ready_to_install[
                    curr_model["id"] + "/" + curr_model["version"]
                ] = curr_model
            else:
                model_key = (
                    str(curr_model["id"]) + "/" + str(curr_model["version"]).lower()
                )
                for curr_filter in self.filter_text.split(";"):
                    if (
                        curr_filter.lower() in curr_model["name"].lower()
                        or curr_filter.lower() in curr_model["tags"].lower()
                        or curr_filter.lower() in curr_model["nickname"].lower()
                        or curr_filter.lower() in model_key
                    ):
                        self.ready_to_install[
                            curr_model["id"] + "/" + curr_model["version"]
                        ] = curr_model
                        break

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
        model_id,
        model_version,
        model_name,
        model_description,
        model_nickname_icon,
        installed,
        parent: QWidget = None,
        selection=False,
    ):
        super().__init__(parent)
        self.model_id = model_id
        self.model_version = model_version
        self.model_name = model_name
        self.model_description = model_description
        self.model_nickname_icon = model_nickname_icon
        self.model_installed = installed
        self.selection = selection

        self.setup_ui()

        self.ui_name.setText(model_nickname_icon + " " + model_name)
        self.ui_description.setText(model_description)
        self.ui_version.setText(str(model_version))

        if self.model_installed == 2:
            self.action_button.setText("Uninstall")
            self.action_button.setObjectName("remove_button")
        elif self.model_installed == 1:
            self.action_button.setText("Re-install")
            self.action_button.setObjectName("install_button")
        else:
            self.action_button.setText("Install")
            self.action_button.setObjectName("install_button")

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

        if self.model_installed == 2:
            self.inspect_icon = QPushButton(self)
            icon = QColoredSVGIcon.from_resources("zoom")
            self.inspect_icon.setIcon(icon.colored(color="#33F0FF"))
            self.row1.addWidget(self.inspect_icon)
            if self.selection:
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

        self.ui_version = QLabel(self)
        self.ui_version.setAlignment(Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        self.row1.addWidget(self.ui_version)

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
    def __init__(self, parent, ui_parent, selection):
        super().__init__(parent)
        self.ui_parent = ui_parent
        self.selection = selection
        self.setSortingEnabled(True)

    def addItem(
        self,
        model_info,
        installed,
    ):
        item = QListWidgetItem(
            str(model_info["id"]) + str(model_info["version"]), parent=self
        )
        super().addItem(item)
        widg = QtModelListItem(
            model_id=model_info["id"],
            model_version=model_info["version"],
            model_name=model_info["name"],
            model_description=model_info["description"],
            model_nickname_icon=model_info["nickname_icon"],
            installed=installed,
            parent=self,
            selection=self.selection,
        )

        item.widget = widg
        action_name = "uninstall" if installed == 2 else "install"
        widg.action_button.clicked.connect(
            lambda: self.handle_action(
                item, model_info["id"], model_info["version"], action_name
            )
        )
        if installed == 2:
            widg.inspect_icon.clicked.connect(
                lambda: self.handle_action(
                    item, model_info["id"], model_info["version"], "inspect"
                )
            )
        if installed == 2 and self.selection:
            widg.selection_button.clicked.connect(
                lambda: self.handle_action(
                    item, model_info["id"], model_info["version"], "select"
                )
            )
        item.setSizeHint(widg.sizeHint())
        self.setItemWidget(item, widg)

    def handle_action(self, item, model_id, model_version, action_name):
        widget = item.widget

        if action_name == "install":
            self.ui_parent.run_thread("install", model_id, model_version)
        elif action_name == "uninstall":
            self.ui_parent.run_thread("uninstall", model_id, model_version)
        elif action_name == "inspect":
            self.ui_parent.run_thread("inspect", model_id, model_version)
        elif action_name == "select":
            self.ui_parent.run_thread("select", model_id, model_version)


class QtBioimageIOModelManager(QDialog):
    def __init__(self, parent=None, prefilter="", selection=False):
        super().__init__(parent)
        self.setStyleSheet(custom_style)
        self.models_folder = model_manager.get_models_path()
        if not os.path.exists(self.models_folder):
            self.models_folder = os.getcwd()
            model_manager.set_models_path(self.models_folder)
        self.RUNNING = False
        self.selection = selection
        self.setup_ui()
        if prefilter != "":
            self.filter.setText(prefilter)
            self.filter.setReadOnly(True)
            self.filter.setEnabled(False)
        else:
            self.run_thread("refresh", "", "")

    def run_thread(self, action_name, model_id, model_version):
        if self.RUNNING == False:
            if action_name == "select":
                self.parent().select_bioimageio_model(
                    str(model_id) + ("/" + str(model_version))
                    if str(model_version) != ""
                    else ""
                )
                self.close()
                return

            self.RUNNING = True
            self.working_indicator.show()
            self.thread = QThread()
            self.worker = Installer()
            self.worker.moveToThread(self.thread)

            self.worker.model_id = model_id
            self.worker.model_version = model_version
            self.worker.filter_text = self.filter.text()
            if action_name == "install":
                self.thread.started.connect(self.worker.install)
                self.run_status.setText("Installing...")
                self.worker.finished.connect(self.refresh)
            elif action_name == "uninstall":
                self.thread.started.connect(self.worker.uninstall)
                self.run_status.setText("Uninstalling...")
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
        previous_filter = self.worker.filter_text
        self.installed_list.clear()
        self.available_list.clear()

        for curr_model_key in self.worker.already_installed:
            self.installed_list.addItem(
                self.worker.already_installed[curr_model_key], installed=2
            )

        for curr_model_key in self.worker.ready_to_install:
            install_option = 1 if curr_model_key in self.worker.already_installed else 0
            self.available_list.addItem(
                self.worker.ready_to_install[curr_model_key], installed=install_option
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
        self.resize(1080, 525)

        vlay_1 = QVBoxLayout(self)

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
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("filter...")
        self.filter.setMaximumWidth(350)
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(lambda: self.run_thread("refresh", "", ""))
        filterBox.addWidget(self.filter)
        filterBox.addStretch()
        vlay_1.addLayout(filterBox)

        self.h_splitter = QSplitter(self)
        vlay_1.addWidget(self.h_splitter)
        self.h_splitter.setOrientation(Qt.Horizontal)
        self.v_splitter = QSplitter(self.h_splitter)
        self.v_splitter.setOrientation(Qt.Vertical)
        self.v_splitter.setMinimumWidth(500)

        installed = QWidget(self.v_splitter)
        lay = QVBoxLayout(installed)
        lay.setContentsMargins(0, 2, 0, 2)
        self.installed_label = QLabel("Installed models:")
        mid_layout = QHBoxLayout()
        mid_layout.addWidget(self.installed_label)
        mid_layout.addStretch()
        lay.addLayout(mid_layout)
        self.installed_list = QtModelList(installed, self, self.selection)
        lay.addWidget(self.installed_list)

        available = QWidget(self.v_splitter)
        lay = QVBoxLayout(available)
        lay.setContentsMargins(0, 2, 0, 2)
        self.avail_label = QLabel("Available models:")
        mid_layout = QHBoxLayout()
        mid_layout.addWidget(self.avail_label)
        mid_layout.addStretch()
        lay.addLayout(mid_layout)
        self.available_list = QtModelList(available, self, False)
        lay.addWidget(self.available_list)

        self.v_splitter.setStretchFactor(1, 2)
        self.h_splitter.setStretchFactor(0, 2)

    def getfiles(self):
        dlg = QFileDialog()
        dlg.setDirectory(self.models_folder)
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec_():
            filenames = dlg.selectedFiles()
            model_manager.set_models_path(filenames[0])
            self.models_folder = model_manager.get_models_path()
            self.modfol_value.setText(self.models_folder)
            self.run_thread("refresh", "", "")


def launcher(parent=None, model_filter="", static_filter=False):
    d = QtBioimageIOModelManager(parent, model_filter, static_filter)
    d.setObjectName("QtBioimageIOModelManager")
    d.setWindowTitle("Bioimage model manager")
    d.setWindowModality(Qt.ApplicationModal)
    d.exec_()
