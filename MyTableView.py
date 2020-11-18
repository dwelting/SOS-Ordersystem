from PySide2.QtCore import *
#from PySide2.QtGui import *
#from PySide2.QtWidgets import *

from PySide2 import QtWidgets


# https://www.saltycrane.com/blog/2007/06/pyqt-42-qabstracttablemodelqtableview/

class CheckboxItemDelegate(QtWidgets.QStyledItemDelegate): # makes centered chackboxes
	checked_signal = Signal(QModelIndex, bool)

	def createEditor(self, parent, option, index):
		box = QtWidgets.QLineEdit(parent)
		box.setMaximumWidth(0)
		box.setEnabled(False)
		return box

	def paint(self, painter, option, index):
		if option.state & QtWidgets.QStyle.State_Selected:
			# White pen while selection
			painter.setPen(Qt.white)
			painter.setBrush(option.palette.highlightedText())
			# This call will take care to draw, dashed line while selecting
			QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_ItemViewItem, option, painter, option.widget)

		try:
			data = int(index.data())
		except:
			data = 0

		if data:
			QtWidgets.QItemDelegate().drawCheck(painter, option, option.rect, Qt.Checked)
		else:
			QtWidgets.QItemDelegate().drawCheck(painter, option, option.rect, Qt.Unchecked)
			QtWidgets.QItemDelegate().drawFocus(painter, option, option.rect)

		return True


	def editorEvent(self, event, model, option, index):
		if event.type() == QEvent.MouseButtonRelease:
			data = int(model.data(index))
			if data > 1: data = 1
			data = abs(data - 1)
			self.checked_signal.emit(index, bool(data))
			model.setData(index, data, Qt.CheckStateRole)
			event.accept()
		return QtWidgets.QItemDelegate().editorEvent(event, model, option, index)


class CheckboxItemDelegate_noedit(CheckboxItemDelegate): # makes centered chackboxes
	def editorEvent(self, event, model, option, index):
		return QtWidgets.QItemDelegate().editorEvent(event, model, option, index)


class MyFilterProxyModel(QSortFilterProxyModel): # makes external filterboxes possible

	TemplateRegExp = QRegExp()
	FilterRegExp = list()
	columns_to_filter = list()

	def __init__(self, parent): #https://stackoverflow.com/questions/39488901/change-qsortfilterproxymodel-behaviour-for-multiple-column-filtering/39491243#39491243
		QSortFilterProxyModel.__init__(self)
		self.setParent(parent)
		self.TemplateRegExp.setCaseSensitivity(Qt.CaseInsensitive)
		#self.TemplateRegExp.setPatternSyntax(QRegExp.RegExp)
		self.TemplateRegExp.setPatternSyntax(QRegExp.Wildcard)

	def filterAcceptsRow(self, sourceRow, sourceParent):
		for i, column_number in enumerate(self.columns_to_filter):
			if self.FilterRegExp[i].isEmpty(): continue
			#source_index = self.sourceModel().index(sourceRow, column_number, sourceParent)
			#source_data = str(self.sourceModel().data(source_index))
			source_data = str(self.sourceModel().data_filter(sourceRow, column_number))
			if self.FilterRegExp[i].indexIn(source_data) == -1:
				return False #if regex string doesnt find a match then don't show this row
		return True

	def setFilter_fast(self, regExp):
		column = self.sender().property("column")  # check which filter is being typed
		self.FilterRegExp[column].setPattern(regExp)

	def setFilter(self, regExp):
		if len(self.columns_to_filter) > 0:
			column = self.sender().property("column")  # check which filter is being typed
			self.FilterRegExp[column].setPattern(regExp)
			self.invalidateFilter()

	def filter(self):
		self.invalidateFilter()

	def setColumnsToFilter(self, columns):
		self.columns_to_filter = columns
		import copy
		for _ in self.columns_to_filter:
			self.FilterRegExp.append(copy.copy(self.TemplateRegExp))

	def lessThan(self, source_left, source_right): # sorting corrected with mixed types (str, int, float, other)
		data_left = self.sourceModel().data(source_left, Qt.UserRole)
		data_right = self.sourceModel().data(source_right, Qt.UserRole)

		left_str = isinstance(data_left, str)
		right_str = isinstance(data_right, str)
		if left_str & right_str: #both strings
			if data_left.lower() < data_right.lower(): return True #compare everything in lowercase
			else: return False
		elif left_str: #if only one is string, then the other should be before it
			return False
		elif right_str:
			return True

		left_int_float = isinstance(data_left, int) | isinstance(data_left, float)
		right_int_float = isinstance(data_right, int) | isinstance(data_right, float)
		if left_int_float & right_int_float: #both int or float
			if data_left < data_right: return True
			else: return False
		elif left_int_float: #if only one is int or float, then the other should be before it
			return False
		elif right_int_float:
			return True

		# if any other type convert to str and sort
		data_left = str(data_left)
		data_right = str(data_right)
		if data_left < data_right: return True
		else: return False

	def changeSyntax(self, Regex = True):
		if len(self.FilterRegExp) > 0:
			for filter in self.FilterRegExp:
				if Regex:
					filter.setPatternSyntax(QRegExp.RegExp)
				else:
					filter.setPatternSyntax(QRegExp.Wildcard)

class MyTableModel(QAbstractTableModel):

	def __init__(self, data_in, parent=None, *args):
		QAbstractTableModel.__init__(self, parent, *args)
		self.model_data = list()
		self.model_data = data_in
		#self.checks = dict()
		self.header_labels = ["" for _ in range(1, len(data_in[0]) + 1)]
		#print(1)


	def rowCount(self, parent=""):
		return len(self.model_data)

	def columnCount(self, parent=""):
		return len(self.model_data[0])

	#def checkState(self, index):  # checks checkstate # https://stackoverflow.com/questions/50124556/pyqt-qabstracttablemodel-checkbox-not-checkable
	#	if index in self.checks.keys():  # if the index (like x,y coords) are in the dictionary, then return value, else unchecked
	#		return self.checks[index]
	#	else:
	#		return Qt.Unchecked

	def data_filter(self, row, column): #for super fast filtering
		return self.model_data[row][column]


	def data(self, index, role=Qt.DisplayRole):
		if (role == Qt.DisplayRole) or (role == Qt.EditRole):  # for speed optimisation
			return self.model_data[index.row()][index.column()]

		elif role == Qt.UserRole:  # makes sorting work properly with numbers in strings
			data = self.model_data[index.row()][index.column()]
			#return data

			if index.column() == gPrice_per_unit_col:
				data = data.split(" ")
				data = (float(data[1]))

			if isinstance(data, str):
				if not (data.replace('.', '', 1).isdigit()):  # https://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-float
					return data #normal string
				elif data.isdigit():
					return int(data)
				else:
					return float(data)
				
			else:
				return data
			
		elif role == Qt.ToolTipRole:
			if (index.column() == gComment_col) or (index.column() == gProduct_col) or (index.column() == gURL_Ordernumber_col) or (index.column() == gStore_name_col):
				return self.model_data[index.row()][index.column()]  # tooltip text
	
	#if (role == Qt.CheckStateRole) and index.column() == 0:
		#	return self.checkState(QPersistentModelIndex(index))

	def setData(self, index, value, role=Qt.EditRole):
		if (role == Qt.EditRole) or (role == Qt.CheckStateRole):
			row = index.row()
			column = index.column()

			if value == self.model_data[row][column]:
				return True #same data: return

			self.model_data[row][column] = value
			self.dataChanged.emit(index, index, role)
			return True

		#elif role == Qt.CheckStateRole:
			#self.checks[QPersistentModelIndex(index)] = value
			# self.model_data[index.row()][index.column()] = str(bool(value))
		#	self.parent().selectRow(index.row())  # tableview set row when click checkbox
		#	self.dataChanged.emit(index, index, role)
		#	return True
		return False

	# self.dataChanged.emit(index, index, role)
	# return QAbstractTableModel.setData(self, index, value, role)

	def setAllData(self, data_in):
		self.beginResetModel()
		self.model_data = data_in
		self.header_labels = ["" for _ in range(1, len(data_in[0]) + 1)]
		self.endResetModel()

	def getData(self, row, column):
		return self.model_data[row][column]

	def getAllData(self, column=None):
		if column is not None:
			return [row[column] for row in self.model_data]
		else:
			return self.model_data

	def flags(self, index):
		original_flags = super(MyTableModel, self).flags(index)
		return original_flags | Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

	def headerData(self, column, orientation, role=Qt.DisplayRole):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			return self.header_labels[column]
		return QAbstractTableModel.headerData(self, column, orientation, role)

	def setHeaderData(self, column, orientation, value, role=Qt.EditRole):
		if orientation==Qt.Horizontal:
			self.header_labels[column] = value

	def insertRows(self, row, count, index=QModelIndex()):
		if (count < 1) or (row < 0):  # or (row >verticalHeaderItems.count())
			return False

		self.beginInsertRows(index, row, row + count - 1)
		for i in range(count):
			self.model_data.insert(row, [''] * self.columnCount())
		self.endInsertRows()
		return True

	def removeRows(self, row, count, index=QModelIndex()):
		if (count < 1) or (row < 0):  # or (row >verticalHeaderItems.count())
			return False

		self.beginRemoveRows(index, row, row + count - 1)
		for i in range(count):
			self.model_data.pop(row)
		self.endRemoveRows()
		return True




from MyGui import gPrice_per_unit_col, gComment_col, gURL_Ordernumber_col, gProduct_col, gStore_name_col

