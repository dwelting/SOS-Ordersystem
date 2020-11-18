from MyConfig import _Config
from MyConfig import *
from os import startfile, getenv, remove

EXE_NAME = r'Simple Order system.exe'
TARGET_FOLDER = r"/Simple Order System/"
config_text = 'config.txt'

def update(Installed_from, path):
	# delete current exe
	# copy exe from 'installed from'
	from shutil import copy2
	print('update')
	path = path + EXE_NAME
	new_path = Installed_from + ''+ EXE_NAME

	remove(path)
	copy2(new_path, path)

if __name__ == "__main__":

	TARGET_FOLDER = getenv('APPDATA') + TARGET_FOLDER


	config = _Config(TARGET_FOLDER + _Config.Config_File)
	version = config.get_setting(Config_Version, Config_Misc)
	Installed_from = config.get_setting(Config_Installed_From, Config_Misc)

	external_config = _Config(Installed_from + '\\' + config_text)
	external_version = external_config.get_setting(Config_Version, Config_Misc)

	path = TARGET_FOLDER #current working directory

	#print(version+', '+external_version)
	if version != external_version:
		update(Installed_from, path)
		config.set_setting(Config_Version, external_version, Config_Misc) #set new version number

	path += r"\\"
	# launch app
	startfile('"'+TARGET_FOLDER+EXE_NAME+'"')

