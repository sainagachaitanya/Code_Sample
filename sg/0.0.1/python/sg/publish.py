import getpass
import os
import re
import shutil
import time
import logging
import subprocess

from api import DDShotgun, DDShotgunAPIError

# from dd.runtime import api
#
# api.load("indiapipeline")
# api.load("sgtk_core")
#
# from indiapipeline.renamer import Renamer
# import sgtk

# Get Environment variables
SHOW = os.getenv("DD_SHOW")
SEQUENCE = os.getenv("DD_SEQ")
SHOT = os.getenv("DD_SHOT")
PATH_REGEX = re.compile(r"(\w+-\w+)\.([vV][0-9]{3})\.(\w+)")

logger = logging.getLogger("dd.{}".format(__name__))
logging.basicConfig(level=logging.INFO)


def copy_files_to_shared(input_path, version_number, task, output=""):
    version_number = str(version_number)

    shared_task_path = "/dd/shows/{0}/{1}/{2}/SHARED/IMG/{3}/{4}/v{5}".format(
    SHOW, SEQUENCE, SHOT, task, task, version_number.zfill(3)
    )

    save_path = shared_task_path
    if os.path.splitext(input_path)[1] == ".exr":
        save_path = os.path.join(shared_task_path, "images")
    elif os.path.splitext(input_path)[1] == ".psd":
        save_path = os.path.join(shared_task_path, "psd")
    elif os.path.splitext(input_path)[1] == ".nk":
        save_path = os.path.join(shared_task_path, "scripts")

    try:
        print("\nCopying to Shared Directory...")
        start_time = time.time()
        cmd = ["jsmk", save_path]
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            default_error_msg = "Process returned Non Zero Exit Code, Exit Code={}".format(process.returncode)
            return stderr if stderr.strip() else default_error_msg
        else:
            print("\nCopying {} -> {}".format(input_path, save_path))
            shutil.copy2(input_path, save_path)
            end_time = time.time()
            print("\nCopied to Shared Directory in {} seconds".format(end_time - start_time))

            try:
                old_file_name = os.path.basename(input_path) # Get input filename
                proper_file_name = "{0}_{1}_{2}_{3}-{4}.v{5}".format(
                SEQUENCE, SHOT, task, task, output, version_number.zfill(3))
                new_file_name = old_file_name.replace(old_file_name.split(".")[0], proper_file_name)
                old_name = os.path.join(save_path, old_file_name)
                new_name = os.path.join(save_path, new_file_name)
                os.rename(old_name, new_name) # Rename PSD to appropriate naming
                return new_name

            except Exception as e:
                logger.error(e)

    except Exception as e:
        logger.error(e)


class SgPublish(object):
    def __init__(self):
        # Initiate class variables
        self.sg_api = None
        self.show = None
        self.sequence = None
        self.shot = None
        self.user = None

        self.is_connected = False

    @staticmethod
    def validate_environment():
        env_vars = [SHOW, SEQUENCE, SHOT]
        for env in env_vars:
            if env == "":
                print("Please use 'go <show> <sequence> <shot> =<role>', then run this script")
                return False
            else:
                return True

    def connect(self):
        if not self.validate_environment():
            return
        else:
            # Get User Credentials
            username = getpass.getuser()
            password = getpass.getpass("Enter Your Password: ")

            # Initiate Shotgun API
            self.sg_api = DDShotgun(username, password)

            # Set Shotgun API Environment
            self.sg_api.set_show(SHOW)
            self.sg_api.set_sequence(SEQUENCE)
            self.sg_api.set_shot(SHOT)

            # update class variables
            self.show = self.sg_api.get_project()
            self.sequence = self.sg_api.get_sequence()
            self.shot = self.sg_api.get_shot()
            self.user = self.sg_api.get_user()

            self.is_connected = True

    def validate(self, publish_name):

        fields = ["code", "version_number"]
        published_files = self.sg_api.get_published_files(fields)

        published_names = [published_file["code"] for published_file in published_files]

        if publish_name in published_names:
            DDShotgunAPIError("Found Conflicting Publish for '{}', Please Version up!".format(publish_name))
        else:
            print("\nSuccessfully Validated {}, Publishing...".format(publish_name))

    def sg_version(self, source_path, version_number, task, description):
        # Only Make a Shotgun version if it's an Image File Type
        valid_version_extensions = [".exr", ".jpg", ".jpeg", ".tif", ".tiff"]

        if os.path.splitext(source_path)[1] in valid_version_extensions:
            print("\nCreating Version for {}".format(source_path))
            version_name = PATH_REGEX.search(source_path).group(1)
            version_code = "{}.{}".format(version_name, str(version_number).zfill(3))

            # Frame Calculation
            frames = os.listdir(os.path.dirname(source_path))
            frame_numbers = [frame.split(".")[2] for frame in frames]

            first_frame = min(frame_numbers)
            last_frame = max(frame_numbers)
            frame_range = "{}-{}".format(first_frame, last_frame)
            frame_count = len(frames)

            version_data = {
            "project": {"type": "Project", "id": self.show['id']},
            "entity": {"type": "Shot", "id": self.shot['id']},
            'code': version_code,
            'user': {'type': 'HumanUser', 'id': self.user["id"]},
            "frame_count": int(frame_count),
            "sg_first_frame": int(first_frame),
            "frame_range": frame_range,
            "sg_last_frame": int(last_frame),
            'sg_path_to_frames': source_path,
            'description': description,
            'sg_status_list': 'rev',
            'sg_task': {"type": "Task", "id": task["id"]}
            }

            sg_version = self.sg_api.create("Version", version_data)

            if sg_version:
                print("\nCreated Version on Shotgun for {}, Publishing...".format(sg_version["code"]))
                return sg_version

    def publish(self, source_path, version_number, task, description=""):

        self.sg_api.set_task(task)
        try:
            sg_task = self.sg_api.get_task()
        except Exception as e:
            print(e)
            return

        sg_version_entity = self.sg_version(source_path, version_number, sg_task, description)

        print("\nCreating PublishedFile for {}".format(source_path))
        name = PATH_REGEX.search(source_path).group(1)

        # renamer = Renamer()
        # tk = renamer.tk
        # context = tk.context_from_path(source_path)

        published_file_type = None
        if os.path.splitext(source_path)[1] == ".exr":
            published_file_type = "Rendered Image"
        elif os.path.splitext(source_path)[1] == ".nk":
            published_file_type = "Nuke Script"
        elif os.path.splitext(source_path)[1] == ".psd":
            published_file_type = "Photoshop Image"

        try:
            version_entity = {"type": "Version", "id": sg_version_entity['id']}
        except Exception as e:
            print("\nNo Need to create Version Entity for {} extension, skipping...".format(
            os.path.splitext(source_path)[1]))
            version_entity = None

        published_file = sgtk.util.register_publish(tk,
                                                    context,
                                                    source_path,
                                                    name,
                                                    version_number,
                                                    comment=description,
                                                    published_file_type=published_file_type,
                                                    thumbnail_path="",
                                                    update_task_thumbnail=True,
                                                    version_entity=version_entity,
                                                    task={"type": "Task", "id": sg_task["id"]})

        if published_file:
            data = {"sg_path_to_source": source_path,
                    'sg_status_list': 'ip',
                    'sg_output': 'main'}

            _id = published_file["id"]
            print("\nCreated Published File on Shotgun for {}".format(published_file["code"]))
            self.sg_api.update("PublishedFile", _id, data)
            return published_file
