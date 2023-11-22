name ='logger'
version ='1.0.0'
build_command='build'

description = """Otherside VFX Logger"""

authors = ['saichaitanya']

requires = [
    'rezbuild>=1.0.0'
]

def commands():
    global env
    env.PATH.append('{root}/bin')
    env.PYTHONPATH.append('{root}/python')
