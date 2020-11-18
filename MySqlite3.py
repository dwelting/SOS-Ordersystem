import sqlite3


class _Sqlite3:
	DB_PATH = 'database.db'

	def __init__(self, db=DB_PATH):
		self.DB_PATH = db  # update DB_PATH


	@staticmethod
	def isSQLite3(db):  # https://stackoverflow.com/questions/12932607/how-to-check-if-a-sqlite3-database-exists-in-python
		from os.path import isfile, getsize

		if not isfile(db):
			return False
		if getsize(db) < 100:  # SQLite database file header is 100 bytes
			return False

		with open(db, 'rb') as fd:
			header = fd.read(100)

		return header[:16] == b'SQLite format 3\x00'


	def set_db(self, db=DB_PATH):
		self.DB_PATH = db  # update DB_PATH
#		if not self.isSQLite3(db):  # if not file exists and is sqlite3 database
#			raise ValueError("Error: file is not sqlite3 database")
			# msgbox error
			# open file explorer naar goede db

	def get_table_names(self):
		# select right table name in popup
		tables = self.exec('fetchall', "SELECT name FROM sqlite_master WHERE type = 'table'")
		tables = list(map(lambda x: x[0], tables))
		tables = [item for item in tables if not item.startswith('sqlite_')]
		#if len(tables) > 1:
		#	print(tables)
		#	print("select right table, to be implemented")
		return tables

	def get_table_info(self, table):
		# get table information (name, type)
		query = "PRAGMA table_info('{}')".format(table)  # make table name a variable
		result = self.exec('fetchall', query)
		result_name = list(map(lambda x: x[1], result))
		result_type = list(map(lambda x: x[2], result))
		return result_name, result_type

	def exec(self, function, query):
		self.set_db(self.DB_PATH)
		if function == 'execute':
			return self._execute(query)
		elif function == 'insert':
			self._insert(query)
		elif function == 'fetchone':
			return self._fetch_one(query)
		elif function == 'fetchall':
			return self._fetch_all(query)
		else:
			raise NameError

	def _execute(self, query, ):
		try:
			db = sqlite3.connect(self.DB_PATH)  # Creates or opens a file called mydb with a SQLite3 DB
			cursor = db.cursor()  # Get a cursor object
			cursor.execute(query)  # Check if table users does not exist and create it
			db.commit()  # Commit the change
		except Exception as error:  # Catch the exception
			db.rollback()  # Roll back any change if something goes wrong
			raise error
		finally:
			#data = cursor
			db.close()  # Close the db connection
			return cursor

	def _insert(self, query, ):
		try:
			db = sqlite3.connect(self.DB_PATH)  # Creates or opens a file called mydb with a SQLite3 DB
			cursor = db.cursor()  # Get a cursor object
			cursor.execute(query)  # Check if table users does not exist and create it
			db.commit()  # Commit the change
		except Exception as error:  # Catch the exception
			db.rollback()  # Roll back any change if something goes wrong
			raise error
		finally:
			db.close()  # Close the db connection

	def _fetch_one(self, query, ):
		try:
			db = sqlite3.connect(self.DB_PATH)  # Creates or opens a file called mydb with a SQLite3 DB
			cursor = db.cursor()  # Get a cursor object
			cursor.execute(query)  # select
			db.commit()  # Commit the change
		except Exception as error:  # Catch the exception
			db.rollback()  # Roll back any change if something goes wrong
			raise error
		finally:
			data = cursor.fetchone()
			db.close()  # Close the db connection
			return data

	def _fetch_all(self, query, ): #check SELECT in query
		try:
			db = sqlite3.connect(self.DB_PATH)  # Creates or opens a file called mydb with a SQLite3 DB
			cursor = db.cursor()  # Get a cursor object
			cursor.execute(query)  # select
			db.commit()  # Commit the change
		except Exception as error:  # Catch the exception
			db.rollback()  # Roll back any change if something goes wrong
			raise error
		finally:
			data = cursor.fetchall()
			db.close()  # Close the db connection
			return data