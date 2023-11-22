#!/usr/bin/env python

# Python Built-in Modules
import sys
import os
import re
import getpass

# Third-Party Modules
from PySide2 import QtWidgets as Qtw
from PySide2 import QtCore as Qtc
from PySide2 import QtGui as Qtg

# import osvfx packages
from fileutils import search_work_files, rename_slash
from preferences import Preference

PREFS = Preference("osvfx_preferences.yaml")

OSVFX_LOGO = os.path.join(os.getenv("ICONS_PATH"), "osvfx-dark.png").replace("\\", "/")
DEFAULT_LOGO = os.path.join(os.getenv("ICONS_PATH"), "no-file-small.jpg").replace("\\", "/")
SHOWS = os.getenv("SHOWS")
SHOW = os.getenv("SHOW")
SEQUENCE = os.getenv("SEQUENCE")
SHOT = os.getenv("SHOT")
ROLE = os.getenv("ROLE")
USER = getpass.getuser()

def version_up(val):
    number = val.group(2)
    new_version = str(int(number) + 1).zfill(len(number))
    return val.group(1) + new_version

class FilesaveDialog(Qtw.QDialog):
    def __init__(self, host):
        super(FilesaveDialog, self).__init__()

        # Instance Variables
        self.host = host
        self.latest_file = None

        # Window Properties
        self.setWindowTitle(f"{self.host.title()} - File Save")
        self.setWindowFlags(self.windowFlags() ^ Qtc.Qt.WindowContextHelpButtonHint)
        self.resize(1000, 400)

        # Methods
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

        # Set Path Input
        self.set_path()
        self.auto_version_update()

    def create_widgets(self):
        self.logo_group = Qtw.QGroupBox("Otherside Visual Effects Private Limited")
        self.osvfx_icon = Qtw.QLabel()
        self.separator = Qtw.QFrame()
        self.show_icon = Qtw.QLabel()

        self.show_label = Qtw.QLineEdit()
        self.scene_label = Qtw.QLineEdit()
        self.shot_label = Qtw.QLineEdit()
        self.role_label = Qtw.QLineEdit()
        self.user_label = Qtw.QLineEdit()
        self.task_input = Qtw.QLineEdit()
        self.version_input = Qtw.QSpinBox()
        self.auto_version = Qtw.QCheckBox("Auto Version")
        self.path_input = Qtw.QLineEdit()
        self.save_button = Qtw.QPushButton("Save")
        self.close_button = Qtw.QPushButton("Close")
        self.status_label = Qtw.QLabel()

        self._default_properties()

    def create_layouts(self):
        button_layout = Qtw.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)

        logo_layout = Qtw.QHBoxLayout()
        self.osvfx_icon.setAlignment(Qtc.Qt.AlignHCenter)
        self.show_icon.setAlignment(Qtc.Qt.AlignHCenter)
        logo_layout.addWidget(self.osvfx_icon)
        logo_layout.addWidget(self.separator)
        logo_layout.addWidget(self.show_icon)
        self.logo_group.setLayout(logo_layout)

        version_layout = Qtw.QHBoxLayout()
        version_layout.addWidget(self.version_input)
        version_layout.addWidget(self.auto_version)

        form_layout = Qtw.QFormLayout()
        form_layout.addRow("Show: ", self.show_label)
        form_layout.addRow("Scene: ", self.scene_label)
        form_layout.addRow("Shot: ", self.shot_label)
        form_layout.addRow("Role: ", self.role_label)
        form_layout.addRow("User: ", self.user_label)
        form_layout.addRow("Task: ", self.task_input)
        form_layout.addRow("Version", version_layout)
        form_layout.addRow("Path: ", self.path_input)
        form_layout.addRow("Status: ", self.status_label)

        main_layout = Qtw.QVBoxLayout(self)
        main_layout.addWidget(self.logo_group)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)

    def _default_properties(self):

        self.osvfx_icon.setPixmap(Qtg.QPixmap(OSVFX_LOGO))
        self.separator.setFrameShape(Qtw.QFrame.VLine)
        self.show_icon.setPixmap(Qtg.QPixmap(DEFAULT_LOGO))

        self.show_label.setText(SHOW)
        self.show_label.setDisabled(True)
        self.scene_label.setText(SEQUENCE)
        self.scene_label.setDisabled(True)

        self.shot_label.setText(SHOT)
        self.shot_label.setDisabled(True)

        self.role_label.setText(ROLE)
        self.role_label.setDisabled(True)

        self.user_label.setText(USER)
        self.user_label.setDisabled(True)

        self.task_input.setText(ROLE)

        self.version_input.setValue(1)
        self.version_input.setDisabled(True)
        self.auto_version.setChecked(True)

        self.path_input.setDisabled(True)
        
    def set_path(self):
        task = self.task_input.text()
        version = str(self.version_input.value()).zfill(3)

        # Template Path : "{shows}/{show}/{scene}/{shot}/nuke/scenes/{role}/{user}"
        # Template Filename : "{shot}_{role}_{task}_v{version}_t001.nk"
        user_path = PREFS[self.host]["filesave"]["path"].format(shows=SHOWS, show=SHOW, scene=SEQUENCE, shot=SHOT, role=ROLE, user=USER)
        file_name = PREFS[self.host]["filesave"]["filename"].format(shot=SHOT, role=ROLE, task=task, version=version)

        files, self.latest_file = search_work_files(os.path.dirname(user_path), task)
        if file_name in files:
            path = rename_slash(os.path.join(user_path, file_name))
            self.path_input.setStyleSheet("color: red; font-weight: bold")
            self.save_button.setEnabled(False)
            self.status_label.setText(f"[ERROR] '{self.latest_file}' exists, Cannot Save!")
        elif int(float(version)) == 0:
            self.path_input.setStyleSheet("color: red; font-weight: bold")
            self.status_label.setText("[Critical] Major/Minor Version Cannot be 0, Cannot Save!")
            self.save_button.setEnabled(False)
        else:
            path = rename_slash(os.path.join(user_path, file_name))
            self.path_input.setStyleSheet("color: white; font-weight: bold")
            self.save_button.setEnabled(True)
            self.status_label.setText("[Info] Press Save!")

        # Create directories if not exist
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        self.path_input.setText(path)

    def create_connections(self):
        self.task_input.textChanged.connect(self.set_path)
        self.task_input.textChanged.connect(self.auto_version_update)
        self.version_input.valueChanged.connect(self.set_path)
        self.auto_version.clicked.connect(self.auto_version_update)
        self.auto_version.clicked.connect(self.set_path)
        self.close_button.clicked.connect(self.close)

    def auto_version_update(self):
        if self.auto_version.isChecked():
            self.version_input.setDisabled(True)
            try:
                regex = re.search(r"_[vV](\d+)_", self.latest_file)
                version = regex.group(1)
                new_version = int(version) + 1
                self.version_input.setValue(new_version)
            except Exception as e:
                self.version_input.setValue(1)
        else:
            self.version_input.setDisabled(False)

def main():
    app = Qtw.QApplication(sys.argv)
    file_save = FilesaveDialog("nuke")
    file_save.show()
    app.exec_()

def show():
    file_save = FilesaveDialog()
    file_save.show()

if __name__ == "__main__":
    main()
