import os
import re
import shutil


class DMPGatherData(object):
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def gather_layers(self):
        all_files = os.listdir(self.folder_path)

        layers = [layer for layer in all_files
                  if os.path.splitext(layer)[1] not in [".psd"] and layer not in ["NukeScript", "PSD", "NukeRender"]]
        return layers

    def gather_psd(self):
        all_files = os.listdir(self.folder_path)
        psd = [layer for layer in all_files if os.path.splitext(layer)[1] == ".psd"]
        return psd

    def get_version(self):
        if self.folder_path.endswith("/"):
            self.folder_path = self.folder_path[0:-1]
        version = int(os.path.basename(self.folder_path)[1:])

        return version

    def layers(self):
        dmp_files = self.gather_layers()
        regex = re.compile(r"_(\d+)\.")
        pos_numbers = sorted([regex.search(dmp_file).group(1) for dmp_file in dmp_files if not dmp_file.startswith(".")],
                             reverse=True)

        ordered_files = []

        for index, pos_number in enumerate(pos_numbers):
            for dmp_file in dmp_files:
                if pos_number in dmp_file:
                    ordered_files.insert(index, dmp_file)

        return ordered_files


if __name__ == "__main__":
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dmp", "v001/")
    b = DMPGatherData(path)
    print(b.gather_layers())