# import built-ins
import os
import sys
import subprocess
import argparse
import traceback
import shutil

sys.path.append("/dd/home/schaitanya/PythonProjects")

# import shotgun publish
from sg.publish import SgPublish, copy_files_to_shared
from dmp_gather import DMPGatherData


def dmp_nuke_script(path, version):
    python_template = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "nuke_script_settings.py")

    cmd = ["nuke", "-t", python_template, "--version", version, "--path", path]

    process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        default_error_msg = "Process returned Non Zero Exit Code, Exit Code={}".format(
            process.returncode)
        return stderr if stderr.strip() else default_error_msg
    else:
        return True


def move_psd(folder_path, version, psd_files):
    psd_folder = os.path.join(folder_path, "PSD", "v{}".format(version))

    if not os.path.exists(psd_folder):
        os.makedirs(psd_folder)
    try:
        for psd in psd_files:
            print("Copying {} to {}".format(psd, psd_folder))
            shutil.copy2(os.path.join(folder_path, psd), os.path.join(psd_folder, psd))
            return psd_folder
    except Exception as e:
        print(traceback.format_exc())


def dmp_collect(dmp_files_path, version_number, psd_files):
    # Gather the files in 'dmp_files_path' and extract publish data into NukeRender, NukeScript and PSD folders
    build_nuke_script = dmp_nuke_script(dmp_files_path, version=str(version_number))

    if build_nuke_script:
        str_version = str(version_number).zfill(3)
        nuke_scripts_loc = os.path.join(dmp_files_path, "NukeScript", "v{}".format(str_version))
        nuke_renders_loc = os.path.join(dmp_files_path, "NukeRender", "v{}".format(str_version))
        psd_files_loc = move_psd(dmp_files_path, str_version, psd_files=psd_files)

        nuke_files = [os.path.join(nuke_scripts_loc, nuke_script) for nuke_script in
                      os.listdir(nuke_scripts_loc)]

        nuke_renders = [os.path.join(nuke_renders_loc, nuke_render) for nuke_render in
                        os.listdir(nuke_renders_loc)]

        psd_files = [os.path.join(psd_files_loc, psd_file) for psd_file in os.listdir(psd_files_loc)]

        cp_nk_files = [copy_files_to_shared(nuke_file, version_number, "dmp", output="nuke_script")
                       for nuke_file in nuke_files]

        cp_nk_renders = [copy_files_to_shared(nuke_render, version_number, "dmp", output="main")
                         for nuke_render in nuke_renders]

        cp_psd_files = [copy_files_to_shared(psd_file, version_number, "dmp", output="psd") for
                        psd_file in psd_files]

        return cp_nk_renders, cp_nk_files, cp_psd_files


def clean_up(folder_path):
    nuke_render_path = os.path.join(folder_path, "NukeRender")
    nuke_script_path = os.path.join(folder_path, "NukeScript")
    psd_path = os.path.join(folder_path, "PSD")

    clean_up_files = [nuke_script_path, nuke_render_path, psd_path]

    for clean_up_file in clean_up_files:
        try:
            print("\nDeleting auto-generated {}".format(clean_up_file))
            shutil.rmtree(clean_up_file)
        except Exception as e:
            print(traceback.format_exc())


def parse_arguments():
    parser = argparse.ArgumentParser(description='Publish to shotgun.')

    parser.add_argument('-p', "--path", help='Path to Files')
    parser.add_argument('-d', "--description", help='Short Description of the publish')
    parser.add_argument('-v', "--version", help='Version Number')

    parsed_args = parser.parse_args()
    return parsed_args


if __name__ == "__main__":

    args = parse_arguments()
    sg_pub = SgPublish()
    sg_pub.connect()

    if not sg_pub.is_connected:
        print("Not connected to shotgun!")
    else:
        dmp_data = DMPGatherData(args.path)
        dmp_version = dmp_data.get_version()
        dmp_psd = dmp_data.gather_psd()

        if not args.version:
            publish_version = int(dmp_version)
        else:
            publish_version = int(args.version)

        collected_dmp = dmp_collect(args.path, publish_version, dmp_psd)

        collected_exr_files = collected_dmp[0]
        collected_nk_files = collected_dmp[1]
        collected_psd_files = collected_dmp[2]

        try:
            for exr in collected_exr_files:
                publish_name = os.path.basename(exr)
                sg_pub.validate(publish_name)
                sg_pub.publish(exr, publish_version, "dmp", args.description)
        except Exception as e:
            print(traceback.format_exc())

        try:
            for nk in collected_nk_files:
                publish_name = os.path.basename(nk)
                sg_pub.validate(publish_name)
                sg_pub.publish(nk, publish_version, "dmp", args.description)
        except Exception as e:
            print(traceback.format_exc())

        try:
            for psd_file in collected_psd_files:
                publish_name = os.path.basename(psd_file)
                sg_pub.validate(publish_name)
                sg_pub.publish(psd_file, publish_version, "dmp", args.description)
        except Exception as e:
            print(traceback.format_exc())

        # clean_up_permission = raw_input("Clean up auto-generated files in {}?(Y/N): ".format(args.path))
        # if clean_up_permission == "y" or clean_up_permission == "Y":
        #     clean_up(args.path)
        clean_up(args.path)