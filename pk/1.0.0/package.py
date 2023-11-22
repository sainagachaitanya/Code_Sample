name='pk'
version='1.0.0'
build_command='build'

authors=['saichaitanya']

requires = [
	"rezbuild>=0.1.1"
]

description = """
Package manager to create, read, upgrade and delete otherside visual effects rez-packages

# Upgrade Notes
0.1.0: 
	\n[UPDATE] 
		Updating with New Logger Object
	\n[UPDATE]
		Change all required packages versions to exact version numbers eg:'>=' replaced with '==' in requires
			
	\n[BUG][STATUS: FIXED] 
		when using upgrade, the version number replaces every old version number in the file to 
		new version number, including those in requires list. 
		For example 'pk upgrade --name pk --upgrade_type minor" command searches for "0.0.1" in the file and
		upgrades it to "0.1.0", so requires = ["logger==0.0.1"] becomes requires = ["logger==0.1.0"].
		That is not the desired behaviour so, instead we are searching for 'version=<version-number>' and replace it.
		IMP: When using version in the package.py file, avoid using something that looks similar to version syntax.

0.1.1:
	\n[UPDATE]
		Made code clean and optimised, upgraded create_package function to check for package version instead of package itself 
		to allow for more flexible package creation, for eg: if package exists and version doesn't exist it does not ask you to
		upgrade like 0.1.0 did, it will go ahead and create a package with the mentioned version.

0.2.0:
	\n[UPDATE]
		Loading Package Directory Structure and rez package.py contents from pk_preferences.yaml.
		Support for installing Pip Packages directly as Rez Packages into PYPI_PACKAGES_PATH
	\n[UPDATE]
		Added Package building code from pkgutils
0.3.0:
	\n[UPDATE]
		Added Functionality to install python packages to STORE/Resources/PythonPackages.
1.0.0:
	\n[UPDATE]
		Removed package dependancies.
"""

def commands():
	global env, alias
	env.PATH.append('{root}/bin')
	env.PYTHONPATH.append('{root}/python')
