from MyConfig import _Config
from MyConfig import *
from os import getenv, system,getcwd

INSTALL_FOLDER_SHORT = 'bin'
INSTALL_FOLDER = INSTALL_FOLDER_SHORT+'\\'

EXE_NAME = 'Simple Order System'
LAUNCHER_NAME = 'Launcher'
ICON_FOLDER = 'icon'
CONFIG = _Config.Config_File

PROGRAM_EXE	= EXE_NAME + '.exe'
LAUNCHER_EXE = LAUNCHER_NAME + '.exe'

TARGET_FOLDER = "/Simple Order System/"

if __name__ == "__main__":
	TARGET_FOLDER_HARD = getenv('APPDATA') + TARGET_FOLDER
	installed_from_path = getcwd() #save working directory

	cmd = (
		'cd "'+ installed_from_path + '"' + "&" +
		'mkdir "' + TARGET_FOLDER_HARD + '"' + "&" +	#make folder
		#'robocopy /S "../'+INSTALL_FOLDER_SHORT+'" "'+TARGET_FOLDER_HARD + '"' + "&" +

		'copy "' + INSTALL_FOLDER + PROGRAM_EXE + '" "' + TARGET_FOLDER_HARD + PROGRAM_EXE + '" /Y' + "&" +	#copy files
		'copy "' + INSTALL_FOLDER + LAUNCHER_EXE + '" "' + TARGET_FOLDER_HARD + LAUNCHER_EXE + '" /Y' + "&" +
		'copy "' + INSTALL_FOLDER + CONFIG + '" "' + TARGET_FOLDER_HARD + CONFIG + '" /Y' + "&" +
		'xcopy /E /I "' + INSTALL_FOLDER + ICON_FOLDER + '" "' + TARGET_FOLDER_HARD + ICON_FOLDER + '" /Y' + "&" +

		"powershell \"" +	#make shortcuts
		   "$s=(New-Object -COM WScript.Shell).CreateShortcut('%userprofile%/desktop/" + EXE_NAME + ".lnk');" +
		   "$s.TargetPath='%AppData%" + TARGET_FOLDER + LAUNCHER_EXE + "';" +
		   "$s.WorkingDirectory ='%AppData%" + TARGET_FOLDER + "';" +
		   "$s.Save()\"" +

			r";$s=(New-Object -COM WScript.Shell).CreateShortcut('%AppData%/Microsoft/Windows/Start Menu/" + EXE_NAME + ".lnk');" +
		   "$s.TargetPath='%AppData%" + TARGET_FOLDER + LAUNCHER_EXE + "';" +
		   "$s.WorkingDirectory ='%AppData%" + TARGET_FOLDER + "';" +
		   "$s.Save()\""
	)
	system(cmd)


#make config in TARGET_FOLDER
	config_file = TARGET_FOLDER_HARD + CONFIG
	config = _Config(config_file)
	config.set_setting(Config_Installed_From, installed_from_path + '\\' + INSTALL_FOLDER, Config_Misc)
