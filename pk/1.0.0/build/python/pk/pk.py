# import built-in modules
from pathlib import Path
import shutil
import os
import getpass
import re
import ast
import subprocess

# MODULE CONSTANTS
COMMERCIAL_PACKAGES = ["aces", "cmake", "houdini", "maya", "mongocompass", "mongodb", "mongoshell", "neatvideo", "nodejs", "nuke", " painter", "photoshop", " pyblish", "pyblish_qml", "sidefxlabs"]
REGEX_VERSION_PATTERN = r"^(\d+)\.(\d+)\.(\d+)$"
ANSWERS = { 
	"accepting_answers": ["y", "Y", "yes", "Yes", "YES"], 
	"not_accepting_answers": ["n", "N", "no", "No", "NO"]
	}

def get_package(name, repo="dev"):
	return Path(os.getenv(f"{repo.upper()}_PACKAGES_PATH")) / name


def can_upgrade(version):
	return re.match(REGEX_VERSION_PATTERN, version) is not None

class PkError(Exception):
    """
    Custom exception raised for specific errors.
    """
    def __init__(self, message):
        """
        Initialize the custom exception with a specific error message.
        """
        self.message = message
        super().__init__(self.message)

def create_package(name, version, repo="dev", rez_package_data={"path": "{root}/bin", "pythonpath": "{root}/python"}):
	"""
	Create a Rez Package

	:param name: Name of the Package to Create
	:type name: str

	:param version: Version of the package to create
	:type version: str
	
	:return: Return the path of the package created
	:rtype: str

	:raises PkError: Exception takes a message to display

	Example:
		>>> package = create_package("nuke", "13.2v5")
		>>> print(package)
		Output: E:/SaiChaitanya/osvfx/tools/win10_64/package/dev/nuke/13.2v5
	"""
	pkg_dir = get_package(name, repo)
	pkg_ver_dir = pkg_dir / version
	pkgVerExists = os.path.exists(pkg_ver_dir)

	print(f"Checking for {name} package with version-{version} in {repo} repository")
	if not pkgVerExists:
		print(f"{name}-{version} does not exist, Proceeding to create...")
		pkg_ver_dir.mkdir(parents=True)
		
		sub_dirs = ["bin", "docs", "python", "tests"]
		for sub_dir in sub_dirs:
			_path = pkg_ver_dir / sub_dir
			_path.mkdir(parents=True)
			if sub_dir == "python":
				py_pk_dir = _path / name
				py_pk_dir.mkdir(parents=True)
				Path(py_pk_dir / "__init__.py").touch()
			if sub_dir == "tests":
				Path(_path / "__init__.py").touch()

		print(f"Package {name}-{version} created")
		with open(f"{pkg_ver_dir}/package.py", "w") as f:
			path = rez_package_data.get("path")
			pythonpath = rez_package_data.get("pythonpath")
			f.write(
f"""
name='{name}'
version='{version}'
build_command='build'

authors=['{getpass.getuser()}']

requires = [
	"rezbuild>=1.0.0"
]

description = "{name} Rez Package"

def commands():
	import os
	global getenv, env
	env.PATH.append('{path}')
	env.PYTHONPATH.append('{pythonpath}')
"""
)
		return pkg_ver_dir
	else:
		raise PkError(f"{name}-{version} already exists, consider upgrading or creating a new version")
			
def delete_package(name, version, repo="dev"):
	"""
	Delete a Package determined by type

	:param name: Name of the Package to Delete
	:type name: str

	:param repo: Package repo to delete from, options: "dev", "local", "release"
	:type repo: str

	:param version: Version of the package to create, defaults to None, if not provided, deletes the entire package
	:type version: str
	
	:return: Return the path of the package delete
	:rtype: str

	:raises PkError: Exception takes a message to display

	Example:
		>>> package = delete_package("nuke", "dev", version="13.2v5")
		>>>	print(package)
		>>> 'E:/SaiChaitanya/osvfx/tools/win10_64/package/dev/nuke/13.2v5

	"""
	try:
		package = get_package(name, repo)
		confirmation_text = f"[WARNING] You are trying to delete a package from {repo} repository.Are you sure? (y/n): "
		confirmation = input(confirmation_text)

		if confirmation in ANSWERS["accepting_answers"]:
			if version:
				package_dir = package / version
				print(f"Marking {name}-{version} for Deletion from {repo} repository")
			else:
				version_confirm_text = f"[WARNING] No version is provided, this will delete the entire package, Continue?(y or n): "
				version_confirm = input(version_confirm_text)
				if version_confirm in ANSWERS["accepting_answers"]:
					package_dir = package
					print(f"Marking {name} for Deletion from {repo} repository")
				elif confirmation in ANSWERS["not_accepting_answers"]:
					print("Exiting Delete Operation.")
			try:
				shutil.rmtree(package_dir) # Delete Operation
				print(f"Deleted {package_dir}")
				return package_dir
			except UnboundLocalError:
				pass

		elif confirmation in ANSWERS["not_accepting_answers"]:
			print("Exiting Delete Operation.")
		else:
			print(f"Invalid Input, Please Enter {ANSWERS['accepting_answers'].extend(ANSWERS['not_accepting_answers'])}")
	except Exception as e:
		print(e)

def upgrade_package(name, upgrade_type, repo="dev"):
	"""
	Attempts Upgrade a Development Package based on to_version options, else asks for version number to directly upgrade

	:param name: Name of the Package to Upgrade
	:type name: str

	:param upgrade_type: Option to upgrade a package, options: "major", "minor", "patch"
	:type upgrade_type: str
	
	:return: Return the path of the package upgraded
	:rtype: str

	:raises: None

	Example:
		>>> latest_version = "0.0.1"
		>>> package_major = upgrade_package("assetmanager", upgrade_type="major")
		>>> package_minor = upgrade_package("assetmanager", upgrade_type="minor")
		>>> package_patch = upgrade_package("assetmanager", upgrade_type="patch")

		>>> print(package_major)
		>>> 'E:/SaiChaitanya/osvfx/tools/win10_64/package/dev/assetmanager/1.0.0'

		>>> print(package_minor)
		>>> 'E:/SaiChaitanya/osvfx/tools/win10_64/package/dev/assetmanager/1.1.0'

		>>> print(package_patch)
		>>> 'E:/SaiChaitanya/osvfx/tools/win10_64/package/dev/assetmanager/1.1.1'
		
		>>> nuke_version = "13.2v5"
		>>> nuke_package = upgrade_package("nuke", upgrade_type="major")
		>>> [WARNING] Whoopsie!! looks like nuke is not upgradable by Pk
		>>> [INFO] Please Enter a version number to upgrade to: <enter-version-here> eg: 14.0v1 
		>>> print(nuke_package)
		>>> 'E:/SaiChaitanya/osvfx/tools/win10_64/package/dev/nuke/14.0v1'

	"""
	package_dir = get_package(name, repo)

	if not package_dir.is_dir():
		print(f"{name} package does not exist.")
	else:
		latest_version = os.listdir(package_dir)[-1]
		print(f"{latest_version} is the latest version, attemping to upgrade")

		if can_upgrade(latest_version) and name not in COMMERCIAL_PACKAGES:
			current_version = latest_version.split(".")
			if upgrade_type == "major":
				curr = int(current_version[0])
				new = curr + 1
				new_version = f"{new}.0.0"
			elif upgrade_type == "minor":
				curr = int(current_version[1])
				new = curr + 1
				new_version = f"{current_version[0]}.{new}.0"
			elif upgrade_type == "patch":
				curr = int(current_version[2])
				new = curr + 1
				new_version = f"{current_version[0]}.{current_version[1]}.{new}"
		else:
			print(f"Whoopsie!! looks like {name} is not upgradable by Pk.")
			
			upgrade_confirm = input("Do you want to upgrade to a custom version? (y/n)")
			if upgrade_confirm in ANSWERS["accepting_answers"]:
				new_version = input("\nPlease Enter a version number to upgrade to: ")
			else:
				return "Exiting Upgrade Operation...."

		if new_version:
			next_version_dir = Path(os.path.join(package_dir, new_version))
			shutil.copytree(package_dir / latest_version, next_version_dir, symlinks=True)

			# Update Version number in package.py
			filename = os.path.join(next_version_dir, "package.py")
			old_version = f"version='{latest_version}'"
			new_version = f"version='{new_version}'"

			print(f"old_version: {old_version}")
			print(f"new_version: {new_version}")

			with open(filename, "r") as file:
				file_content = file.read()
			
			new_content = file_content.replace(f"{old_version}", f"{new_version}")
			print(f"new_content: \n{new_content}")
			# Write the modified content back to the package.py
			with open(filename, 'w') as file:
				file.write(new_content)
		
			print(f"Versioned up Dev Package {name} from {old_version} to {new_version}.")

			return next_version_dir
		else:
			print("Enter a Version Number or upgrade option")
		
def read_package(name):
	"""
	Prints Basic information about the package

	:param name: Name of the Package to Upgrade
	:type name: str
	
	:return: None

	:raises: None

	Example:
		>>> read_package("logger")
		>>> versions in dev: 0.0.1, 0.0.22
		>>>	versions in local: 0.0.1
		>>>	Description:
				logger to provide for standard stream redirection
	"""

	all_package_repos = [
		"dev", "local", "release", "stage", 
		"show", "show_dev", "show_stage"
	]

	for package_repo in all_package_repos:
		package_path = get_package(name, package_repo)
		if os.path.exists(package_path):
			versions = os.listdir(package_path)
			print(f"versions in {package_repo}:", "white")
			message = f"\t{', '.join(versions)}", "yellow"
			print(message)
	
			# Grab package.py from latest version
			file_path = get_package(name, package_repo) / versions[-1] / "package.py"
			description = _extract_description(file_path)
			requires = _extract_requires(file_path)

			print(f"DESCRIPTION: ", "white")
			if description:
				message = f"{description}", "cyan"
				print(message)
			else:
				print("\tNo description found.")
			
			print("REQUIRES: ", "white")
			requires_message =f"\t{', '.join(requires)}", "green"
			print(requires_message)

def install_package(name, version):
	print(f"installing {name}-{version} package")
	install_location = os.path.join(os.getenv("STORE"), "Resources", "PythonPackages").replace("\\", "/")
	try:
		subprocess.check_call(['pip', 'install', f"{name}=={version}", '--target', install_location])
		print(f"{name} and its dependencies have been installed at {install_location}.")

		# data = {
		# 	"path": 'os.path.join(os.getenv("STORE"), "Resources", "PythonPackages", "bin")',
		# 	"pythonpath": 'os.path.join(os.getenv("STORE"), "Resources", "PythonPackages")'
		# }

		# create_package(name, version, rez_package_data=data)

	except subprocess.CalledProcessError as e:
		print(f"An error occurred during the installation: {e}")

def _extract_description(file_path):

	with open(file_path, 'r') as file:
		tree = ast.parse(file.read())

	description_node = next((node.value for node in ast.walk(tree) if isinstance(node, ast.Assign) and node.targets[0].id == 'description'), None)
	if description_node and isinstance(description_node, ast.Str):
		return description_node.s
	return None

def _extract_requires(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())

    requires_node = next((node.value for node in ast.walk(tree) if isinstance(node, ast.Assign) and node.targets[0].id == 'requires'), None)

    if requires_node and isinstance(requires_node, ast.List):
        requires = [elem.s for elem in requires_node.elts if isinstance(elem, ast.Str)]
        return requires

    return []

__all__ = ["create_package", "delete_package", "read_package", "upgrade_package", "install_package"]

if __name__ == "__main__":
	create_package("nuke", version="13.2v5")
	# upgrade_package("nuke", "patch")
	# delete_package("nuke", "dev", version="")
