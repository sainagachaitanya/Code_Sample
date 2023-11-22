"""
copy_share.py Sharing Nuke Setups between a team of nuke artists
"""

# Import nuke
import nuke

# import built-ins
import os
import getpass
import json
from datetime import datetime
from uuid import uuid1

class CopyShare():

    CS_ROOT = os.path.join(os.getenv("ASSETS"), "CopyShare").replace("\\", "/")
    SCRIPT_LOCATION = os.path.join(CS_ROOT, "nk_scripts").replace("\\", "/")
    DATA_LOCATION = os.path.join(CS_ROOT, "data").replace("\\", "/")

    dirs = [CS_ROOT, SCRIPT_LOCATION, DATA_LOCATION]
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

    USERNAME = getpass.getuser()

    @staticmethod
    def write_data(user=None, file_name=None, setup_name=None, script_location=None):
        """
        Write a json file to disk to DATA_LOCATION
        """
        data = dict()
        data["user"] = user
        data["setup_name"] = setup_name
        data["menu_name"] = user[0]
        data["script_location"] = script_location
        data["script_name"] = os.path.basename(script_location)
        data["save_time"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

        data_file = os.path.join(CopyShare.DATA_LOCATION, "{}.json".format(file_name))

        with open(data_file, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load_data(location=None):
        """
        Read all json files on disk from DATA_LOCATION, and return list of dicts, If no data is found, clears the menu items
        """
        if location is not None and os.path.exists(location):
            all_data = os.listdir(location)
            data_content = []

            if len(all_data) > 0:
                for data in all_data:
                    data_file = os.path.join(CopyShare.DATA_LOCATION, data)
                    with open(data_file, "r") as f:
                        contents = json.load(f)
                        data_content.append(contents)

                return data_content
            else:
                nuke.tprint("[INFO] No Data Found!, Clearing Menu")
                try:
                    nuke.menu("Nuke").findItem("Copy and Share/Paste Nodes").clearMenu()
                except AttributeError:
                    nuke.tprint("[WARNING] Couldn't find Paste Nodes sub-menus, Skipping clearing menus....")
        else:
            nuke.message("Data Location couldn't be found!")
            return None

    @staticmethod
    def refresh():
        """
        Reads the json data on disk and builds the menu items
        """
        nuke.tprint("[INFO] Refreshing....")
        paste_menu = CopyShare.build_paste_menu()
        all_data = CopyShare.load_data(CopyShare.DATA_LOCATION)

        all_setups = []
        if all_data:
            for data in all_data:
                # role = data["role"]
                sub_menu = data["menu_name"]
                user = data["user"]
                # script_name = data["script_name"]
                script_location = data["script_location"]
                setup_name = data["setup_name"]
                all_setups.append(setup_name)
                menu_item_name = "{} - {}".format(user, setup_name)

                data_menu = paste_menu.addMenu("{}".format(sub_menu))
                data_menu.addCommand(menu_item_name)

                # set script for the menu item
                CopyShare.set_script(sub_menu, menu_item_name, script_location)

            return all_setups

    @staticmethod
    def copy_nodes():
        """
        Copies the selected nodes to disk using nuke.nodeCopy(path) to SCRIPT_LOCATION, and builds the menu item for the copied item
        """
        sel = nuke.selectedNodes()
        if len(sel) > 0:
            setup_name = nuke.getInput("Enter a name for your setup...")
            if setup_name:
                setup_name = setup_name.replace(" ", "_")
                random_name = str(uuid1()).split("-")[0]
                script_name = "{}-{}-{}.nk".format(CopyShare.USERNAME, setup_name, random_name)
                setup_save_path = os.path.join(CopyShare.SCRIPT_LOCATION, script_name).replace("\\", "/")

                nuke.nodeCopy(setup_save_path)
                nuke.tprint("[INFO] copied nodes to {0}".format(setup_save_path))
                CopyShare.write_data(user=CopyShare.USERNAME, file_name=script_name, setup_name=setup_name,
                                     script_location=setup_save_path)
                CopyShare.set_selection_to_none(sel)
                CopyShare.refresh()

        else:
            nuke.message("No Node Selected")

    @staticmethod
    def set_selection_to_none(sel):
        """
        clear node selection in nuke
        """
        for node in sel:
            node.setSelected(False)

    @staticmethod
    def set_script(sub_menu, menu_item, script_location):
        """
        set the script for the menu item
        """
        script_item_menu = nuke.menu("Nuke").findItem("Copy and Share/Paste Nodes/{}/{}".format(sub_menu, menu_item))
        exec_script = "nuke.nodePaste(os.path.join('{}'))\nfor node in nuke.selectedNodes():\n node.setSelected(False)".format(script_location)
        script_item_menu.setScript(exec_script)

    @staticmethod
    def build_paste_menu():
        """
        Add Paste Nodes Menu to DD India/Copy and Share
        """
        menu = nuke.menu("Nuke")
        cs_menu = menu.findItem("Copy and Share")
        paste_menu = cs_menu.addMenu("Paste Nodes")
        return paste_menu

    @staticmethod
    def usage():
        message = "1) Refresh --> Updates the Paste Nodes Menu items\n\n2)Usage --> Get the usage of the tool\n\n3)Copy Nodes --> Copies the nodes with the setup name and creates a json data file\n\n4)Paste Nodes/(user - setup name) --> Pastes the setup into the current nuke session"
        nuke.message(message)
