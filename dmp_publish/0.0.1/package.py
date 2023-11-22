
name='dmp_publish'
version='0.0.1'
build_command='build'

authors=['schaitanya']

requires = [
	"rezbuild>=1.0.0",
	"sg>=0.0.1"
]

description = "dmp_publish Rez Package"

def commands():
	import os
	global getenv, env
	env.PATH.append('{root}/bin')
	env.PYTHONPATH.append('{root}/python')
