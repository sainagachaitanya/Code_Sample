import os
import subprocess
import logging
from logger import Logger

class PkBuildLogger(Logger):
    LOGGER_NAME = "PK-BUILD"
    DEFAULT_LEVEL = logging.DEBUG
    PROPAGATE_DEFAULT = False

def get_package_path(name, context):
	return os.path.join(os.getenv(f"{context.upper()}_PACKAGES_PATH"), name)

def package_build(name, version, context):
    if context == "stage":
       package_dir = os.path.join(get_package_path(name, "dev"), version)
       build_package_dir = os.getenv("STAGE_PACKAGES_PATH")

    elif context == "show":
        package_dir = os.path.join(os.getenv("SHOWS"), name, "package", "dev", name, version)
        build_package_dir = os.path.join(os.getenv("SHOWS"), name, "package", "stage")

    try:
        os.chdir(package_dir)
    except FileNotFoundError as e:
        PkBuildLogger.warning("Traceback Message: ")
        PkBuildLogger.exception(e)
        PkBuildLogger.warning("Error Message: ")
        PkBuildLogger.critical(f"{name} package couldn't be found in {package_dir}, \nare you sure it exists in the repository, run 'pk read {name}' to check the details")
        
    command = ["rez-build", "--install", "--clean", "--prefix", build_package_dir]
    try:
        subprocess.run(command)
    except subprocess.CalledProcessError as e:
        PkBuildLogger.exception("Error occurred:", e)
        PkBuildLogger.exception("Command output (stderr):", e.stderr)