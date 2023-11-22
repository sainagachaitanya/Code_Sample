
name='osmongo'
version='0.0.1'
build_command='rezbuild'

authors=['schaitanya']

requires = [
	"logger>=0.1.1",
	"rezbuild>=0.1.1",
	"preferences>=0.1.0",
	"pymongo>=4.4.1",
	"schema>=0.0.1"
]

description = "osmongo Rez Package"

def commands():
	global env
	env.PATH.append('{root}/bin')
	env.PYTHONPATH.append('{root}/python')
