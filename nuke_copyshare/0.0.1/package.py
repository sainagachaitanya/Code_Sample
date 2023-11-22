
name='nuke_copyshare'
version='0.0.1'
build_command='build'

authors=['saichaitanya']

requires = [
	"rezbuild>=1.0.0"
]


description = "nuke_copyshare Rez Package"

def commands():
	global env
	env.PATH.append('{root}/bin')
	env.PYTHONPATH.append('{root}/python')

	env.NUKE_PATH.append("{root}/python/nuke_copyshare")
