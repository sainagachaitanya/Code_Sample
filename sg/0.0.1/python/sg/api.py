#!/usr/bin/env python

# Import Built Modules
import os
from pprint import pprint
import getpass
import logging

# import dd runtime api
from dd.runtime import api

# load packages using api
api.load("pillow")
api.load("sgtk_core")

# import modules loaded by api
from PIL import Image

# import shotgun api
from tank_vendor import shotgun_api3

logger = logging.getLogger("dd.{}".format(__name__))
logging.basicConfig()


class DDShotgunAPIError(object):
    def __init__(self, msg):
        raise shotgun_api3.shotgun.ShotgunError(msg)


class DDShotgun(object):
    """
    DD Shotgun API is built on top of already existing shotgunAPI for easily accessing data from shotgun.

    USAGE:

    sg = DDShotgunAPI("<shotgun_username>", "<shotgun_password>")

    we have to set the Show, Sequence, Shot and Task using the set methods

    sg.set_show("BEETLE")
    sg.set_sequence("PIR")
    sg.set_shot("0780")
    sg.set_task("Vendor")

    NOTE: Show, Sequence, Shot, Task etc entities should be set first to access their respective data

    After using the set methods, we can retrieve data from shotgun using the get methods

    use dir(sg) for all the available methods

    """

    def __init__(self, username, password):
        """
        param username: user's shotgun username
        param password: user's shotgun password
        """

        self.url = "http://shotgun.d2-india.com"
        self.username = username
        self.password = password

        # Create Shotgun Object for Internal use inside the class, hence "_sg".
        self._sg = shotgun_api3.Shotgun(self.url, login=self.username, password=self.password)

        # Initiate Instance Variables
        self.show = ""
        self.sequence = ""
        self.shot = ""
        self.task = ""

    # CUSTOMIZING SHOTGUN API DEFAULT METHODS - START
    def _schema_entity_read(self):
        """
        override shotgun_api3.Shotgun.schema_entity_read method
        """
        entities = self._sg.schema_entity_read(self._project())
        return entities

    def _schema_field_read(self, entity, field_name=None):
        """
        override shotgun_api3.Shotgun.schema_field_read method
        """
        fields = self._sg.schema_field_read(entity, field_name=field_name, project_entity=self._project())
        return fields

    def _find_one(self, entity, data, fields=None):
        """
        override shotgun_api3.Shotgun.find_one method
        """
        if fields is None:
            fields = []
        result = self._sg.find_one(entity, data, fields)
        return result

    def _find(self, entity, data, fields=None):
        if fields is None:
            fields = []
        result = self._sg.find(entity, data, fields)
        return result

    def _get_attachment_download_url(self, attachment):
        if not attachment:
            raise shotgun_api3.shotgun.ShotgunError("<class-instance>._get_attachment_download_url.No Attachment Given")

        result = self._sg.get_attachment_download_url(attachment)
        return result

    def _download_attachment(self, attachment, download_path):
        if not attachment:
            raise shotgun_api3.shotgun.ShotgunError("<class-instance>._download_attachment.No Attachment Given")

        file_path = os.path.join(download_path, attachment["name"].replace(" ", "_"))
        result = self._sg.download_attachment(attachment, file_path)
        return result

    def _create(self, entity_type, data):
        assert isinstance(entity_type, str)
        assert isinstance(data, dict)
        result = self._sg.create(entity_type, data)
        return result

    def _delete(self, entity_type, _id):
        """
        Deletes an entity in shotgun, Eg Entities: Shot, Sequence, PublishedFile

        parm entity_type: str Type of entity to Delete
        parm _id: int Id of the Item to delete
        """
        assert isinstance(entity_type, str)
        assert isinstance(_id, int)
        result = self._sg.delete(entity_type, _id)
        return result

    def _update(self, entity_type, _id, data):
        assert isinstance(entity_type, str)
        assert isinstance(_id, int)
        assert isinstance(data, dict)
        result = self._sg.update(entity_type, _id, data)
        return result

    # DDShotgunAPI methods for accessing data from Shotgun
    def _project(self):

        show = self.show
        if show == "":
            DDShotgunAPIError("Project not set, Please use <class_instance>.set_show(name)")

        data = [['code', 'is', show]]
        fields = ["code", "name", "sg_status"]
        project = self._find_one("Project", data, fields)

        if project is not None:
            return project
        else:
            msg = "Couldn't Find any Project: {}".format(show)
            DDShotgunAPIError(msg)

    def _sequence(self, find_one=True, fields=None):
        if fields is None:
            fields = []
        show = self._project()
        sequence = self.sequence

        if sequence == "":
            DDShotgunAPIError("Sequence not set, Please use <class_instance>.set_sequence(name)")

        seq_fields = ["code", "sg_shots", "sg_status_list", "project"]
        seq_fields.extend(fields)

        data = [['project', 'is', {'type': 'Project', 'id': show['id']}]]

        if find_one:
            data.append(['code', 'is', sequence])
            result = self._find_one("Sequence", data, seq_fields)
        else:
            result = self._find("Sequence", data, seq_fields)

        if result is not None:
            return result
        else:
            msg = "Couldn't Find any Sequence: {}".format(sequence)
            DDShotgunAPIError(msg)

    def _shot(self, find_one=True, fields=None):
        if fields is None:
            fields = []
        show = self._project()
        sequence = self._sequence()
        shot = self.shot

        if shot == "":
            DDShotgunAPIError("Shot not set, Please use <class_instance>.set_shot(name)")

        shot_fields = ["code", "sg_status_list", "sg_sequence"]
        shot_fields.extend(fields)

        data = [
            ['project', 'is', {'type': 'Project', 'id': show['id']}],
            ['sg_sequence', 'is', {'type': 'Sequence', 'id': sequence['id']}]
        ]

        if find_one:
            data.append(['code', 'is', shot])
            result = self._find_one("Shot", data, shot_fields)
        else:
            result = self._find("Shot", data, shot_fields)

        if result is not None:
            return result
        else:
            msg = "Couldn't Find any Shot: {}".format(shot)
            DDShotgunAPIError(msg)

    def _task(self, find_one=True, fields=None):
        if fields is None:
            fields = []
        show = self._project()
        sequence = self._sequence()
        shot = self._shot()
        task = self.task

        if task == "":
            DDShotgunAPIError("Task not set, Please use <class_instance>.set_task(name)")

        task_fields = ["content", "sg_status_list", "step", "task_assignees"]
        task_fields.extend(fields)

        data = [['project', 'is', {'type': 'Project', 'id': show['id']}],
                ['entity', 'is', {'type': 'Shot', 'id': shot['id']}]]

        if find_one:
            data.append(["content", "is", task])
            result = self._find_one("Task", data, task_fields)
        else:
            result = self._find("Task", data, task_fields)

        if result is not None:
            return result
        else:
            DDShotgunAPIError("Couldn't Find any Task: {}".format(task))

    def _user(self):
        current_user = getpass.getuser()
        person_data = [["login", "is", current_user]]

        fields = ["name", "email", "login"]

        person = self._find_one("HumanUser", person_data, fields)

        if person is not None:
            return person
        else:
            DDShotgunAPIError("Couldn't Find any Person: {}".format(current_user))

    def _user_tasks(self, in_show=False, in_shot=False, fields=None):

        if fields is None:
            fields = []

        show = self._project()
        shot = self._shot()
        person = self._user()

        task_fields = ["id", "content", "project", "entity"]
        task_fields.extend(fields)
        filters = [["task_assignees", "is", {"type": "HumanUser", "id": person['id']}], ["sg_status_list", "is", "ip"]]

        if not in_show and not in_shot:
            tasks = self._find("Task", filters, task_fields)
        elif in_show and not in_shot:
            filters.append(['project', 'is', {'type': 'Project', 'id': show['id']}])
            tasks = self._find("Task", filters, task_fields)
        else:
            filters.append(['project', 'is', {'type': 'Project', 'id': show['id']}])
            filters.append(['entity', 'is', {'type': 'Shot', 'id': shot['id']}])
            tasks = self._find("Task", filters, task_fields)

        if tasks is not None:
            return tasks
        else:
            DDShotgunAPIError("Couldn't Find any Tasks for : {}".format(person["name"]))

    def _data(self):
        show = self._project()
        sequence = self._sequence()
        shot = self._shot()

        data = [
            ["project", "is", {"type": "Project", "id": show['id']}],
            ["entity", "is", {"type": "Shot", "id": shot['id']}]
        ]
        return data

    def _versions(self, fields=None):
        if fields is None:
            fields = []
        data = self._data()
        version_fields = ["code", "open_notes_count", "sg_task", "frame_range"]
        version_fields.extend(fields)
        versions = self._find("Version", data, fields=version_fields)

        if versions is not None:
            return versions
        else:
            DDShotgunAPIError("Couldn't Find any versions for : {}".format(self.shot))

    def _deliveries(self, fields=None):
        if fields is None:
            fields = []
        show = self._project()
        data = [
            ["project", "is", {"type": "Project", "id": show['id']}]
        ]

        delivery_fields = ["title", "ticket_sg_deliveries_tickets"]
        delivery_fields.extend(fields)

        deliveries = self._find("Delivery", data, fields=delivery_fields)
        if deliveries is not None:
            return deliveries
        else:
            DDShotgunAPIError("Couldn't Find any deliveries for : {}".format(self.shot))

    def _notes(self, fields=None):
        if fields is None:
            fields = []
        show = self._project()
        shot = self._shot()

        data = [
            ["project", "is", {"type": "Project", "id": show['id']}],
            ["note_links", "is", {"type": "Shot", "id": shot['id']}],
            ["attachments", "is_not", None]
        ]

        notes_fields = ["subject", "content", "sg_note_type", "note_links", "attachments", "tasks"]
        notes_fields.extend(fields)

        notes = self._find("Note", data, notes_fields)
        if notes is not None:
            return notes
        else:
            DDShotgunAPIError("Couldn't Find any notes for : {}".format(self.shot))

    def _attachments(self):
        notes = self._notes()
        all_attachments = []

        for note in notes:
            attachments = note["attachments"]
            all_attachments.extend(attachments)

        for attachment in all_attachments:
            attachment["url"] = self._get_attachment_download_url(attachment)

        if all_attachments is not None:
            return all_attachments
        else:
            DDShotgunAPIError("Couldn't Find any attachments for : {}".format(self.shot))

    def _attachment_download(self, attachment, download_path):

        downloaded_file = self._download_attachment(attachment, download_path)

        if not os.path.splitext(downloaded_file)[1]:
            # Query the type of file
            image = Image.open(downloaded_file)
            extension = image.format.lower()
            renamed_attachment = "{}.{}".format(downloaded_file, extension)
            # Add Extension to Attachment
            os.rename(downloaded_file, renamed_attachment)
            return renamed_attachment
        else:
            return downloaded_file

    def _published_files(self, fields=None):
        if fields is None:
            fields = []
        data = self._data()
        published_files = self._find("PublishedFile", data, fields=fields)
        if published_files is not None:
            return published_files
        else:
            DDShotgunAPIError("Couldn't Find any published_files for : {}".format(self.shot))

    def _published_file_by_id(self, _id, fields=None):
        if fields is None:
            fields = []
        data = self._data()
        data.append(["id", "is", _id])
        published_file = self._find_one("PublishedFile", data, fields=fields)
        if published_file is not None:
            return published_file
        else:
            DDShotgunAPIError("Couldn't Find any published_file of id : {}".format(_id))

    def _filter_by_published_file_type(self, filter_by=None):
        if filter_by is None:
            filter_by = []
        published_files = self._published_files(fields=["published_file_type", "version"])
        filtered_files = []
        for name in filter_by:
            files = [published_file for published_file in published_files if
                     published_file["published_file_type"]["name"] == name]
            filtered_files.extend(files)

        if filtered_files is not None:
            return filtered_files
        else:
            DDShotgunAPIError("Couldn't Find any published_file of type(s) : {}".format(filter_by))

    # Set Methods
    def set_show(self, show_name):
        self.show = show_name

    def set_sequence(self, sequence_name):
        self.sequence = sequence_name

    def set_shot(self, shot_number):
        self.shot = shot_number

    def set_task(self, task_name):
        self.task = task_name

    # Get Methods
    def get_project(self):
        return self._project()

    def get_sequence(self, fields=None):
        if fields is None:
            fields = []
        return self._sequence(find_one=True, fields=fields)

    def get_sequences(self, fields=None):
        if fields is None:
            fields = []
        return self._sequence(find_one=False, fields=fields)

    def get_shot(self, fields=None):
        if fields is None:
            fields = []
        return self._shot(find_one=True, fields=fields)

    def get_shots(self, fields=None):
        if fields is None:
            fields = []
        return self._shot(find_one=False, fields=fields)

    def get_task(self, fields=None):
        if fields is None:
            fields = []
        return self._task(find_one=True, fields=fields)

    def get_tasks(self, fields=None):
        if fields is None:
            fields = []
        return self._task(find_one=False, fields=fields)

    def get_all_user_tasks(self, in_show=False, in_shot=False, fields=None):
        if fields is None:
            fields = []
        return self._user_tasks(in_show=in_show, in_shot=in_shot, fields=fields)

    def get_versions(self, fields=None):
        if fields is None:
            fields = []
        return self._versions(fields)

    def get_published_files(self, fields=None):
        if fields is None:
            fields = []
        return self._published_files(fields)

    def get_published_file_by_id(self, _id, fields=None):
        if fields is None:
            fields = []
        return self._published_file_by_id(_id, fields)

    def get_filtered_published_files(self, filter_by=None):
        if filter_by is None:
            filter_by = []
        return self._filter_by_published_file_type(filter_by=filter_by)

    def get_entities(self):
        return self._schema_entity_read()

    def get_fields_for_entity(self, entity, field_name=None):
        return self._schema_field_read(entity, field_name=field_name)

    def get_notes(self):
        return self._notes()

    def get_attachments(self):
        return self._attachments()

    def get_user(self):
        return self._user()

    def create(self, entity_type, data):
        return self._create(entity_type, data)

    def find_one(self, entity, data, fields=None):
        if fields is None:
            fields = []
        return self._find_one(entity, data, fields)

    def update(self, entity_type, _id, data):
        return self._update(entity_type, _id, data)

    def delete(self, entity_type, _id):
        return self._delete(entity_type, _id)

    def download_attachment(self, attachment, download_path):
        return self._attachment_download(attachment, download_path)


def main():
    username = getpass.getuser()
    # password = getpass.getpass("Enter Your Password: ")
    password = "Demo@5678"

    sg_api = DDShotgun(username, password)
    # sg.set_show("DEV02")

    get_project = sg_api.get_project()
    # pprint(get_project)

    """
    # seq_data = {
    #     'project': {"type":"Project","id": get_project["id"]},
    #     'code': 'RND',
    #     'description': 'Creating RND Sequence using shotgun python api',
    #     'sg_status_list': 'ip'
    # }
    # 
    # seq = sg.create("Sequence", seq_data)
    # 
    # pprint(seq)
    """

    # sg.set_sequence("RND")
    # get_sequence = sg.get_sequence()
    # # pprint(get_sequence)

    """shot_data = {
        'project': {"type": "Project", "id": project["id"]},
        'sg_sequence': {'type': 'Sequence', 'id': get_sequence['id']},
        'code': '0010',
        'description': 'Creating 0010 shot using shotgun python api',
        'sg_status_list': 'ip'
    }

    shot = sg.create("Shot", shot_data)
    pprint(shot)"""

    # sg.set_shot("0010")
    # get_shot = sg.get_shot()
    # # pprint(get_shot)

    """pub_file_data = {
        "project": {"type": "Project", "id": get_project['id']},
        "entity": {"type": "Shot", "id": get_shot['id']},
        'code': 'RND_0010_comp_comp_dn-main.v001.%04d.exr',
        'description': 'Creating published file using shotgun python api',
        'sg_status_list': 'ip'
    }

    pub_file = sg.create("PublishedFile", pub_file_data)
    pprint(pub_file)"""

    # sg.set_task("comp")
    # get_task = sg.get_task()
    # pprint(get_task)

    # sg.delete("Version", 193092)
    # pprint(sg.get_user())


# main()