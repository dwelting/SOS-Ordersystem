import configparser

VERSION = "2020.11.18"

Config__Admin_mode = "Admin mode"
Config__Window_width = "Window width"
Config__Window_height = "Window height"
Config__Added_by = "Added by"
Config__Column_size = "Column size"

Config_Version = "Version"
Config_Installed_From = 'Installed from'
Config_Regex = 'Regex filtering'
Config_Attachment = "Attachment"
Config_Misc = "Misc"
Config_Default = 'DEFAULT'


class _Config:
	Config_File = "config.txt"

	_Config_Last_Opened = "Last opened database"
	_Config_Attachment_Folder = ''

	_Config_values_misc = {	Config_Version : VERSION,
							Config_Installed_From : '',
	                        Config_Regex : '0',
							Config_Attachment : _Config_Attachment_Folder,
							_Config_Last_Opened : Config_Default}

	_Config_values_default = { 	Config__Admin_mode: '0',
								Config__Window_width: '1575',
								Config__Window_height: '580',
								Config__Added_by: '',
								Config__Column_size: '211,155,246,53,83,66,183,63,50,72,54,96,96,96'}

	def __init__(self, file=Config_File):
		self.Config_File = file
		self.config = configparser.ConfigParser()

		if not self._file_exists():
			self._file_create()

		self.config.read(self.Config_File)

		self.check_configs() #to remove errors

		import atexit
		atexit.register(self._write_to_file)  # destructor

	def _file_exists(self):
		exists = True
		try:
			file = open(self.Config_File, "r")
			file.close()
		except FileNotFoundError:
			exists = False
		finally:
			return exists

	def _file_create(self):
		self.config[Config_Misc] = self._Config_values_misc

		self.config[Config_Default] = self._Config_values_default

		self._write_to_file()

	def _write_to_file(self):
		with open(self.Config_File, 'w') as configfile:
			self.config.write(configfile)
		return True

	def check_configs(self):
		try:
			_ = self.config[self.get_last_opened()][Config__Admin_mode] #check random setting that should be in the settings
		except:
			try:
				self.config[Config_Misc][Config_Installed_From] = self.config[Config_Misc][Config_Installed_From]
			finally:
				self._file_create()

	def get_all_configs(self):
		return self.config.sections()

	def get_last_opened(self):
		return self.config[Config_Misc][self._Config_Last_Opened]

	def set_last_opened(self, db_name):
		self.config[Config_Misc][self._Config_Last_Opened] = db_name
		self.config[db_name] = {}

	def get_setting(self, setting, location=None):
		try:
			if location is None:
				location = self.get_last_opened()
				return self.config[location][setting]
			else:
				return self.config[location][setting]
		except:
			return False

	def set_setting(self, set_name, set_data, location=None):
		if location is None:
			self.config[self.get_last_opened()][set_name] = str(set_data)
		else:
			self.config[location][set_name] = str(set_data)

if __name__ == "__main__":

	config = _Config()


