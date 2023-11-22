
name='filesave'
version='0.0.1'
build_command='build'

authors=['saichaitanya']

requires = [
	"logger>=1.0.0",
	"rezbuild>=1.0.0",
	"pypi>=1.0.0",
	"fileutils>=0.0.1",
	"preferences>=0.1.0"
]

description = "filesave Rez Package"

def commands():
	global env
	env.PATH.append('{this.root}/bin')
	env.PYTHONPATH.append('{this.root}/python')
