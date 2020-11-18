import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui
import PySide2.QtCore as QtCore


try: #needed because otherwise it crashes the exe for some reason
	import requests
except:
	import requests

from bs4 import BeautifulSoup

from MySqlite3 import _Sqlite3
from MyConfig import _Config
from MyConfig import *
from MyTableView import CheckboxItemDelegate, CheckboxItemDelegate_noedit, MyFilterProxyModel, MyTableModel
from shutil import copy2


from MyDebug import *
DEBUG = True



gID = 'ID'
gAdded_by = 'Added by'
gProduct = 'Product'
gAmount = 'Amount'
gPrice_per_unit = 'Price per unit'
gStore_name = 'Store name'
gURL_Ordernumber = 'URL/Order number'
gCost_centre = 'Cost centre'
gComment = 'Comment'
gOrdered = 'Ordered'
gNot_ordered = 'Not ordered'
gReturned = 'Returned'
gDate_added = 'Date added'
gDate_ordered = 'Date ordered'
gDate_returned = 'Date returned'

gProduct_col = 1
gStore_name_col = 2
gURL_Ordernumber_col = 3
gAmount_col = 4
gPrice_per_unit_col = 5
gCostCentre_col = 6
gComment_col = 7
gAdded_by_col = 8
gOrdered_col = 9
gNot_ordered_col = 10
gReturned_col = 11
gDate_added_col = 12
gDate_ordered_col = 13
gDate_returned_col = 14




class MyQMainWindow(QtWidgets.QMainWindow):
	close_check = QtCore.Signal(bool)
	def __init__(self):
		QtWidgets.QMainWindow.__init__(self)

	def closeEvent(self, *args, **kwargs):
		self.close_check.emit(True)


class IntDelegate(QtWidgets.QItemDelegate):
	def createEditor(self, parent, option, index):
		return QtWidgets.QSpinBox(parent, minimum=0, maximum=10000000)

class FloatDelegate(QtWidgets.QItemDelegate):
	def createEditor(self, parent, option, index):
		self.box = QtWidgets.QDoubleSpinBox(parent, minimum=0, maximum=10000000, decimals=2, singleStep=1)

		data = index.data()
		data = data.split(" ")
		self.box.setPrefix(data[0]+" ")
		self.box.setValue(float(data[1]))

		act_eur = QtWidgets.QAction("Edit currency to €", self.box)
		act_eur.triggered.connect(self.f_eur)
		self.box.addAction(act_eur)
		act_dol = QtWidgets.QAction("Edit currency to $", self.box)
		act_dol.triggered.connect(self.f_dol)
		self.box.addAction(act_dol)
		act_pou = QtWidgets.QAction("Edit currency to £", self.box)
		act_pou.triggered.connect(self.f_pou)
		self.box.addAction(act_pou)
		act_custom = QtWidgets.QAction("Edit currency to custom", self.box)
		act_custom.triggered.connect(self.f_custom)
		self.box.addAction(act_custom)

		self.box.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		return self.box

	def f_eur(self):
		self.box.setPrefix("€ ")

	def f_dol(self):
		self.box.setPrefix("$ ")

	def f_pou(self):
		self.box.setPrefix("£ ")

	def f_custom(self):  # input a custom currency
		currency, ok = QtWidgets.QInputDialog.getText(self.box, 'Custom currency', 'Input custom currency name')
		self.box.setPrefix(currency + " ")

	def setModelData(self, editor, model, index):
		# messagebox save data?
		model.setData(index, editor.text())

class MultiLineDelegate(QtWidgets.QItemDelegate):
	def createEditor(self, parent, option, index):
		box = QtWidgets.QPlainTextEdit(parent)
		box.setFixedHeight(100)
		return box

class LineEditDelegate(QtWidgets.QItemDelegate):
	def createEditor(self, parent, option, index):
		box = QtWidgets.QLineEdit(parent)
		box.setReadOnly(True)
		return box

# noinspection PyUnresolvedReferences
class Ui_MainWindow(QtWidgets.QWidget):
	REFRESH_BUSY = 0
	VERSION = 'v' + VERSION
	COMMENT_MAX_LEN = 999
	CUSTOM_CURRENCY = 3
	ADMIN_MODE = False

	columns_to_filter = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
	columns_to_filter_query = [gOrdered_col, gNot_ordered_col, gReturned_col]

	palette_window = QtGui.QPalette()
	palette_whitetext = QtGui.QPalette()
	palette_statusbar = QtGui.QPalette()

	int_delegate = IntDelegate()
	float_delegate = FloatDelegate()
	multiline_delegate = MultiLineDelegate()
	lineedit_noedit_delegate = LineEditDelegate()
	#lineedit_delegate = QtWidgets.QLineEdit()
	checkbox_delegate_noedit = CheckboxItemDelegate_noedit()
	checkbox_delegate_edit = CheckboxItemDelegate()

	tables = str()
	db_path = str()
	row_data = int()
	db = str()
	config = str()
	cproduct_list = list()
	table_row_changed = set()

	def __init__(self, MainWindow, db, config):
		QtWidgets.QWidget.__init__(self)

		self._set_palette()
		self.db = db
		self.config = config
		self._ui_set_mainwindow(MainWindow)

		self._ui_set_menubar()
		self._ui_set_statusbar()
		self._ui_set_tabs()
		self._ui_set_tab_neworder()
		self._ui_set_tab_table()
		self._ui_set_tab_overview()
		self._set_signal_slots()

		self._slot_set_currency_prefix()
		self.tabWidget.setCurrentIndex(0)  # opens in this tab

		self._set_tab_order()
		self.cAddedBy.setFocus()

		#self._fill_combobox_inputs()

		import atexit
		atexit.register(self.__destructor__)  # destructor

	def __destructor__(self):
		if config.get_last_opened() == Config_Default:
			return
		regex_mode = int(self.actionRegex_filtering_mode.isChecked())
		admin_mode = int(self.actionAdmin_mode.isChecked())
		window_width = MainWindow.width()
		window_height = MainWindow.height()
		added_by = self.cAddedBy.currentText()

		column_count = self.tablemodel.columnCount()
		column_size = str()
		for i in range(column_count - 1):
			column_size += str(self.tableview.columnWidth(i + 1)) + ','
		column_size = column_size.rstrip(',')

		config.set_setting(Config_Regex, regex_mode, Config_Misc)

		config.set_setting(Config__Admin_mode, admin_mode)
		config.set_setting(Config__Window_width, window_width)
		config.set_setting(Config__Window_height, window_height)
		config.set_setting(Config__Added_by, added_by)
		config.set_setting(Config__Column_size, column_size)

	def config_set(self):
		self.CONFIG_BUSY = True

		db_name = config.get_last_opened()

		if self.open_db(db_name, False):
			if self.explorer_open_db():
				self.__destructor__()
				MainWindow.close()  # if cancel exit app
				sys.exit(0)

		db_name = config.get_last_opened()
		regex_mode = int(config.get_setting(Config_Regex, Config_Misc))
		admin_mode = int(config.get_setting(Config__Admin_mode))
		window_width = int(config.get_setting(Config__Window_width))  # test
		window_height = int(config.get_setting(Config__Window_height))  # test
		added_by = config.get_setting(Config__Added_by)
		column_size = config.get_setting(Config__Column_size)
		if (column_size[0:2] == '75') and (column_size[3:5] == '75') and (column_size[6:8] == '75'): #sometimes the columns reset after unexpected exit. this fixes that
			column_size = config.get_setting(Config__Column_size, Config_Default)

		db.set_db(db_name)
		self.statusbar_text.setText(db_name)
		MainWindow.resize(window_width, window_height)
		dt_center = QtWidgets.QDesktopWidget().availableGeometry().center() #place in center of screen
		MainWindow.move(int(dt_center.x() - window_width/2), int(dt_center.y() - window_height/2))

		self.cAddedBy.setCurrentText(added_by)

		self.actionAdmin_mode.setChecked(admin_mode)

		self.table_refresh()
		self.actionRegex_filtering_mode.setChecked(regex_mode)

		try:
			column_size = column_size.split(',')
			for i, size in enumerate(column_size):
				self.tableview.setColumnWidth(i + 1, int(size))
		except:
			pass

		self.CONFIG_BUSY = False

	def _set_tab_order(self):
		# tab order
		self.tab_neworder.setTabOrder(self.cAddedBy, self.cProduct)
		self.tab_neworder.setTabOrder(self.cProduct, self.cStorename)
		self.tab_neworder.setTabOrder(self.cStorename, self.tURL)
		self.tab_neworder.setTabOrder(self.tURL, self.sAmount)
		self.tab_neworder.setTabOrder(self.sAmount, self.sPriceUnit)
		self.tab_neworder.setTabOrder(self.sPriceUnit, self.tCostCentre)
		self.tab_neworder.setTabOrder(self.tCostCentre, self.pComment)
		self.tab_neworder.setTabOrder(self.pComment, self.bAttachment)
		self.tab_neworder.setTabOrder(self.bAttachment, self.bSave)
		self.tab_neworder.setTabOrder(self.bSave, self.bClear)
		self.tab_neworder.setTabOrder(self.bClear, self.cCurrency)
		self.tab_neworder.setTabOrder(self.cCurrency, self.bUrl)
		self.tab_neworder.setTabOrder(self.bUrl, self.tabWidget)

		MainWindow.setTabOrder(self.tabWidget, self.tableview)

	def _set_palette(self):
		brush = QtGui.QBrush(QtGui.QColor(0, 102, 153))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_window.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
		brush = QtGui.QBrush(QtGui.QColor(0, 102, 153))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_window.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
		brush = QtGui.QBrush(QtGui.QColor(0, 102, 153))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_window.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)

		brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_whitetext.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
		brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_whitetext.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
		brush = QtGui.QBrush(QtGui.QColor(0, 51, 76))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_whitetext.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)

		brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_statusbar.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
		brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_statusbar.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
		brush = QtGui.QBrush(QtGui.QColor(240, 240, 240))
		brush.setStyle(QtCore.Qt.SolidPattern)
		self.palette_statusbar.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Window, brush)

	def _ui_set_mainwindow(self, MainWindow):
		MainWindow.setMinimumSize(QtCore.QSize(600, 400))
		MainWindow.setPalette(self.palette_window)

		self.centralWidget = QtWidgets.QWidget(MainWindow)
		self.gridLayout_mainwindow = QtWidgets.QGridLayout(self.centralWidget)
		self.gridLayout_mainwindow.setContentsMargins(6, 6, 6, 4)
		MainWindow.setCentralWidget(self.centralWidget)

		MainWindow.setWindowTitle("SOS: Simple Order System " + self.VERSION)
		MainWindow.setWindowIcon(QtGui.QIcon("icon/icon_180.png"))

	def _ui_set_menubar(self):
		self.menuBar = QtWidgets.QMenuBar(MainWindow)
		self.menuBar.setGeometry(QtCore.QRect(0, 0, 780, 21))
		MainWindow.setMenuBar(self.menuBar)
		# ----
		self.menuFile = QtWidgets.QMenu(self.menuBar)
		self.menuFile.setTitle("File")

		self.actionOpen = QtWidgets.QAction(MainWindow)
		self.actionOpen.setText("Open")
		self.menuFile.addAction(self.actionOpen)

		self.actionReload = QtWidgets.QAction(MainWindow)
		self.actionReload.setText("Reload")
		self.menuFile.addAction(self.actionReload)

		self.menuFile.addSeparator()

		self.actionExit = QtWidgets.QAction(MainWindow)
		self.actionExit.setText("Exit")
		self.menuFile.addAction(self.actionExit)
		# ----
		self.menuOptions = QtWidgets.QMenu(self.menuBar)
		self.menuOptions.setTitle("Options")

		self.actionRegex_filtering_mode = QtWidgets.QAction(MainWindow)
		self.actionRegex_filtering_mode.setText("Regex Filtering")
		self.actionRegex_filtering_mode.setCheckable(True)
		self.menuOptions.addAction(self.actionRegex_filtering_mode)

		self.menuOptions.addSeparator()

		self.actionAdmin_mode = QtWidgets.QAction(MainWindow)
		self.actionAdmin_mode.setText("Admin mode")
		self.actionAdmin_mode.setCheckable(True)
		self.menuOptions.addAction(self.actionAdmin_mode)
		#----
		self.menuAdminTools = QtWidgets.QMenu(self.menuBar)
		self.menuAdminTools.setTitle("Admin Tools")
		
		self.actionFarnellOrderList = QtWidgets.QAction(MainWindow)
		self.actionFarnellOrderList.setText("Farnell order list")
		self.menuAdminTools.addAction(self.actionFarnellOrderList)
		
		self.menuAdminTools.addSeparator()
		
		self.actionOpenURL = QtWidgets.QAction(MainWindow)
		self.actionOpenURL.setText("Open all URL's")
		self.menuAdminTools.addAction(self.actionOpenURL)
		# ----
		self.menuHelp = QtWidgets.QMenu(self.menuBar)
		self.menuHelp.setTitle("Help")

		self.actionInfo = QtWidgets.QAction(MainWindow)
		self.actionInfo.setText("Info")
		self.menuHelp.addAction(self.actionInfo)

		self.actionAbout = QtWidgets.QAction(MainWindow)
		self.actionAbout.setText("About")
		self.menuHelp.addAction(self.actionAbout)

		self.menuBar.addAction(self.menuFile.menuAction())
		self.menuBar.addAction(self.menuOptions.menuAction())
		self.menuBar.addAction(self.menuAdminTools.menuAction())
		self.menuBar.addAction(self.menuHelp.menuAction())

	def _ui_set_statusbar(self):
		self.statusBar = QtWidgets.QStatusBar(MainWindow)
		self.statusBar.setMaximumSize(QtCore.QSize(16777215, 18))  # height

		self.statusBar.setPalette(self.palette_statusbar)
		self.statusBar.setAutoFillBackground(True)
		MainWindow.setStatusBar(self.statusBar)

		self.statusbar_text = QtWidgets.QLabel('')
		self.statusBar.addWidget(self.statusbar_text)

	def _ui_set_tabs(self):
		self.tabWidget = QtWidgets.QTabWidget(self.centralWidget)
		self.tabWidget.setPalette(self.palette_window)
		# self.tabWidget.setAutoFillBackground(False)
		self.tabWidget.setStyleSheet("QTabWidget::pane {\n"
		                             "border:0;\n"
		                             "border-bottom: 2px solid #C2C7CB\n"
		                             "}")
		self.tabWidget.setTabPosition(QtWidgets.QTabWidget.South)
		self.tabWidget.setTabShape(QtWidgets.QTabWidget.Rounded)

		self.gridLayout_mainwindow.addWidget(self.tabWidget)  # , 0, 1, 1, 1)

	def _ui_set_tab_neworder(self):

		font_label = QtGui.QFont()
		font_label.setBold(True)
		font_label.setPointSize(10)

		font_input = QtGui.QFont()
		# font_input.setFamily('Monotype Corsiva') #todo
		font_input.setPointSize(11)

		font_combobox = 'font: 11pt;'
		# font: 8 pt "Comic Sans MS";

		self.tab_neworder = QtWidgets.QWidget()
		self.tab_neworder.setPalette(self.palette_window)
		self.tab_neworder.setAutoFillBackground(True)
		self.tabWidget.addTab(self.tab_neworder, "New order")

		self.gridLayout_neworder = QtWidgets.QGridLayout()  # self.centralWidget_neworder)
		self.gridLayout_neworder.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
		self.gridLayout_neworder.setContentsMargins(0, 0, 0, 9)
		self.gridLayout_neworder.setSpacing(6)
		self.gridLayout_neworder.setColumnStretch(0, 0)
		self.gridLayout_neworder.setColumnStretch(1, 1)

		self.centralWidget_neworder = QtWidgets.QWidget()  # needed for maximum size gridlayout
		self.centralWidget_neworder.setLayout(self.gridLayout_neworder)
		self.centralWidget_neworder.setMaximumWidth(800)
		self.hview = QtWidgets.QHBoxLayout(self.tab_neworder)
		self.hview.setContentsMargins(0, 0, 0, 0)
		self.hview.insertStretch(0, 0)
		self.hview.insertWidget(1, self.centralWidget_neworder, 1)
		self.hview.insertStretch(2, 0)

		self.bSave = QtWidgets.QPushButton(self.tab_neworder)
		self.bSave.setText("Save")
		self.bSave.setFixedWidth(75)
		self.gridLayout_neworder.addWidget(self.bSave, 9, 7, 1, 1)

		self.bClear = QtWidgets.QPushButton(self.tab_neworder)
		self.bClear.setText("Clear")
		self.bClear.setFixedWidth(75)
		self.gridLayout_neworder.addWidget(self.bClear, 9, 8, 1, 1)


		self.lAddedBy = QtWidgets.QLabel(self.tab_neworder)
		self.lAddedBy.setPalette(self.palette_whitetext)
		self.lAddedBy.setFont(font_label)
		self.lAddedBy.setAlignment(QtCore.Qt.AlignRight)
		self.lAddedBy.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lAddedBy.setText("Added by*")
		self.gridLayout_neworder.addWidget(self.lAddedBy, 0, 0, 1, 1)

		self.cAddedBy = QtWidgets.QComboBox(self.tab_neworder)
		self.cAddedBy.setStyleSheet(font_combobox)
		self.cAddedBy.setFocusPolicy(QtCore.Qt.WheelFocus)
		self.cAddedBy.setEditable(True)
		self.cAddedBy.setMaxVisibleItems(25)
		self.cAddedBy.setMaximumWidth(250)
		self.cAddedBy.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.gridLayout_neworder.addWidget(self.cAddedBy, 0, 1, 1, 8)

		self.lProduct = QtWidgets.QLabel(self.tab_neworder)
		self.lProduct.setPalette(self.palette_whitetext)
		self.lProduct.setFont(font_label)
		self.lProduct.setAlignment(QtCore.Qt.AlignRight)
		self.lProduct.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lProduct.setText("Product name*")
		self.gridLayout_neworder.addWidget(self.lProduct, 1, 0, 1, 1)

		self.cProduct = QtWidgets.QComboBox(self.tab_neworder)
		self.cProduct.setStyleSheet(font_combobox)
		self.cProduct.setEditable(True)
		self.cProduct.setMaxVisibleItems(25)
		self.cProduct.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.cProduct.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)
		self.cProduct.setAutoCompletion(False)
		self.gridLayout_neworder.addWidget(self.cProduct, 1, 1, 1, 8)

		self.lAmount = QtWidgets.QLabel(self.tab_neworder)
		self.lAmount.setPalette(self.palette_whitetext)
		self.lAmount.setFont(font_label)
		self.lAmount.setLayoutDirection(QtCore.Qt.LeftToRight)
		self.lAmount.setAlignment(QtCore.Qt.AlignRight)
		self.lAmount.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lAmount.setText("Amount*")
		self.gridLayout_neworder.addWidget(self.lAmount, 4, 0, 1, 1)

		self.sAmount = QtWidgets.QSpinBox(self.tab_neworder)
		self.sAmount.setFont(font_input)
		self.sAmount.setMinimum(1)
		self.sAmount.setMaximum(100000000)
		self.sAmount.setMaximumWidth(150)
		self.gridLayout_neworder.addWidget(self.sAmount, 4, 1, 1, 1)

		self.bUrl = QtWidgets.QPushButton(self.tab_neworder)
		self.bUrl.setText("Get data from\nFarnell")
		#self.bUrl.setHidden(True)
		#self.bUrl.setEnabled(True)
		self.gridLayout_neworder.addWidget(self.bUrl, 4, 8, 1, 1)

		self.lPriceUnit = QtWidgets.QLabel(self.tab_neworder)
		self.lPriceUnit.setPalette(self.palette_whitetext)
		self.lPriceUnit.setFont(font_label)
		self.lPriceUnit.setLayoutDirection(QtCore.Qt.LeftToRight)
		self.lPriceUnit.setAlignment(QtCore.Qt.AlignRight)
		self.lPriceUnit.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lPriceUnit.setText("Price (per unit)")
		self.gridLayout_neworder.addWidget(self.lPriceUnit, 5, 0, 1, 1)

		self.cCurrency = QtWidgets.QComboBox(self.tab_neworder)
		self.cCurrency.setStyleSheet(font_combobox)
		self.cCurrency.setFixedWidth(60)
		self.gridLayout_neworder.addWidget(self.cCurrency, 5, 2, 1, 1)
		self.cCurrency.addItem("€")
		self.cCurrency.addItem("$")
		self.cCurrency.addItem("£")
		self.cCurrency.addItem("Custom")

		self.sPriceUnit = QtWidgets.QDoubleSpinBox(self.tab_neworder)
		self.sPriceUnit.setFont(font_input)
		self.sPriceUnit.setMaximum(9999999.0)
		self.sPriceUnit.setSingleStep(0.1)
		self.gridLayout_neworder.addWidget(self.sPriceUnit, 5, 1, 1, 1)

		self.lStorename = QtWidgets.QLabel(self.tab_neworder)
		self.lStorename.setPalette(self.palette_whitetext)
		self.lStorename.setFont(font_label)
		self.lStorename.setAlignment(QtCore.Qt.AlignRight)
		self.lStorename.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lStorename.setText("Store name*")
		self.gridLayout_neworder.addWidget(self.lStorename, 2, 0, 1, 1)

		self.cStorename = QtWidgets.QComboBox(self.tab_neworder)
		self.cStorename.setStyleSheet(font_combobox)
		self.cStorename.setEditable(True)
		self.cStorename.setMaxVisibleItems(25)
		self.cStorename.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
		self.cStorename.setAutoCompletion(True)
		self.gridLayout_neworder.addWidget(self.cStorename, 2, 1, 1, 8)

		self.lURL = QtWidgets.QLabel(self.tab_neworder)
		self.lURL.setPalette(self.palette_whitetext)
		self.lURL.setFont(font_label)
		self.lURL.setAlignment(QtCore.Qt.AlignRight)
		self.lURL.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lURL.setText("URL/Order number*")
		self.gridLayout_neworder.addWidget(self.lURL, 3, 0, 1, 1)

		self.tURL = QtWidgets.QLineEdit(self.tab_neworder)
		self.tURL.setFont(font_input)
		self.tURL.setMaxLength(10000)
		self.gridLayout_neworder.addWidget(self.tURL, 3, 1, 1, 8)

		self.lCostCentre = QtWidgets.QLabel(self.tab_neworder)
		self.lCostCentre.setPalette(self.palette_whitetext)
		self.lCostCentre.setFont(font_label)
		self.lCostCentre.setAlignment(QtCore.Qt.AlignRight)
		self.lCostCentre.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lCostCentre.setText("Cost centre*")
		self.gridLayout_neworder.addWidget(self.lCostCentre, 6, 0, 1, 1)

		self.tCostCentre = QtWidgets.QLineEdit(self.tab_neworder)
		self.tCostCentre.setFont(font_input)
		self.tCostCentre.setMaxLength(100)
		self.tCostCentre.setText("")
		self.gridLayout_neworder.addWidget(self.tCostCentre, 6, 1, 1, 8)

		self.lComment = QtWidgets.QLabel(self.tab_neworder)
		self.lComment.setPalette(self.palette_whitetext)
		self.lComment.setFont(font_label)
		self.lComment.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop)
		self.lComment.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lComment.setText("Comment")
		self.gridLayout_neworder.addWidget(self.lComment, 7, 0, 1, 1)

		self.pComment = QtWidgets.QPlainTextEdit(self.tab_neworder)
		self.pComment.setFont(font_input)
		self.pComment.setTabChangesFocus(True)
		self.pComment.setPlaceholderText("Extra information")
		self.gridLayout_neworder.addWidget(self.pComment, 7, 1, 2, 8)

		self.lAttachment = QtWidgets.QLabel(self.tab_neworder)
		self.lAttachment.setPalette(self.palette_whitetext)
		self.lAttachment.setFont(font_label)
		self.lAttachment.setAlignment(QtCore.Qt.AlignRight)
		self.lAttachment.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
		self.lAttachment.setText("Select attachment")
		self.gridLayout_neworder.addWidget(self.lAttachment, 9, 0, 1, 1)

		self.bAttachment = QtWidgets.QPushButton(self.tab_neworder)
		self.bAttachment.setMaximumSize(QtCore.QSize(30, 16777215))
		self.bAttachment.setText("...")
		self.bAttachment.setFixedWidth(35)
		self.gridLayout_neworder.addWidget(self.bAttachment, 9, 5, 1, 1)

		self.tAttachment = QtWidgets.QLineEdit(self.tab_neworder)
		self.tAttachment.setFont(font_input)
		self.tAttachment.setMaxLength(100)
		self.tAttachment.setReadOnly(True)
		self.gridLayout_neworder.addWidget(self.tAttachment, 9, 1, 1, 4)

		self.combo_proxy_storename = QtCore.QSortFilterProxyModel(self.tab_neworder)
		self.combo_proxy_storename.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.combo_proxy_addedby = QtCore.QSortFilterProxyModel(self.tab_neworder)
		self.combo_proxy_addedby.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.combo_proxy_product = QtCore.QSortFilterProxyModel(self.tab_neworder)
		self.combo_proxy_product.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

	def _ui_set_tab_table(self):
		self.tab_table = QtWidgets.QWidget()
		self.tab_table.setPalette(self.palette_window)
		self.tab_table.setAutoFillBackground(True)
		self.tab_table.setObjectName("tab_table")
		self.gridLayout_table = QtWidgets.QGridLayout(self.tab_table)
		self.gridLayout_table.setContentsMargins(0, 0, 0, 6)
		self.gridLayout_table.setSpacing(6)
		self.tabWidget.addTab(self.tab_table, "Orders")

		self.tableview = QtWidgets.QTableView(self)

		self.act_copy = QtWidgets.QAction("Reorder", self.tableview)
		self.tableview.addAction(self.act_copy)
		#self.tableview.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
		
		self.act_open_farnell = QtWidgets.QAction("Open in Farnell", self.tableview)
		self.tableview.addAction(self.act_open_farnell)
		self.tableview.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

		self.tablemodel = MyTableModel([[]], self.tableview)

		self.proxyModel_filter = MyFilterProxyModel(self.tablemodel)  # model for normal table sorting
		self.proxyModel_filter.setSourceModel(self.tablemodel)
		self.proxyModel_filter.setSortRole(QtCore.Qt.UserRole)  # fixes sorting with numbers in strings

		self.tableview.setModel(self.proxyModel_filter)

		font_table = QtGui.QFont()
		font_table.setPointSize(9)
		self.tableview.setFont(font_table) #or else during elide it has an ugly font

		sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
		sizePolicy.setHeightForWidth(self.tableview.sizePolicy().hasHeightForWidth())
		self.tableview.setSizePolicy(sizePolicy)
		self.tableview.setFrameShadow(QtWidgets.QFrame.Plain)
		self.tableview.setLineWidth(1)
		self.tableview.setMidLineWidth(0)
		self.tableview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.tableview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
		self.tableview.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
		self.tableview.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
		self.tableview.setTabKeyNavigation(False)
		self.tableview.setDragDropOverwriteMode(False)
		self.tableview.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		self.tableview.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		self.tableview.setTextElideMode(QtCore.Qt.ElideRight)
		self.tableview.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerItem)
		self.tableview.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
		self.tableview.setShowGrid(True)
		self.tableview.setAlternatingRowColors(True)
		self.tableview.setGridStyle(QtCore.Qt.DashLine)
		self.tableview.setCornerButtonEnabled(True)
		self.tableview.setWordWrap(False)
		self.tableview.setSortingEnabled(True)

		self.tableview.horizontalHeader().setCascadingSectionResizes(False)
		self.tableview.horizontalHeader().setDefaultSectionSize(75)
		self.tableview.horizontalHeader().setSortIndicatorShown(True)
		#self.tableview.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		self.tableview.horizontalHeader().setStretchLastSection(True)
		self.tableview.verticalHeader().setVisible(False)
		self.tableview.verticalHeader().setDefaultSectionSize(23)
		self.tableview.verticalHeader().setHighlightSections(True)

		self.gridLayout_table.addWidget(self.tableview, 2, 0, 1, 6) #y,x,h,w

		self.HBoxLayout_table_filters = QtWidgets.QHBoxLayout(self.tab_table) #layout for the filters
		self.HBoxLayout_table_filters.setSpacing(6)
		self.gridLayout_table.addLayout(self.HBoxLayout_table_filters, 1, 0, 1, 6)


		self.cTable_Query_select = QtWidgets.QComboBox(self.tab_table)
		self.cTable_Query_select.setMaximumWidth(200)
		self.cTable_Query_select.addItems(['To be ordered', 'Ordered', 'Not ordered', 'Returned', 'All records'])
		self.gridLayout_table.addWidget(self.cTable_Query_select, 0, 5, 1, 1)

		self.bTable_save = QtWidgets.QPushButton(self.tab_table)
		self.bTable_save.setText("Save")
		self.bTable_save.setMaximumWidth(100)
		self.gridLayout_table.addWidget(self.bTable_save, 0, 0, 1, 1)

		self.bTable_delete = QtWidgets.QPushButton(self.tab_table)
		self.bTable_delete.setText("Delete row")
		self.bTable_delete.setMaximumWidth(100)
		self.gridLayout_table.addWidget(self.bTable_delete, 0, 1, 1, 1)

	def _ui_set_tab_overview(self):
		self.tab_overview = QtWidgets.QWidget()
		self.tab_overview.setEnabled(True)
		self.tab_overview.setPalette(self.palette_window)
		self.tab_overview.setAutoFillBackground(True)

		self.tab_overview.setPalette(self.palette_window)
		# self.tabWidget.addTab(self.tab_overview, "Overview")
		# self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_overview), "Overview")

		# self.tab_overview.setStyleSheet("QTabBar::tab::disabled {width: 0; height: 0; margin: 0; padding: 0; border: none;}")
		self.gridLayout_overview = QtWidgets.QGridLayout(self.tab_overview)
		self.gridLayout_overview.setContentsMargins(11, 11, 11, 11)
		self.gridLayout_overview.setSpacing(6)

		self.checkBox = QtWidgets.QCheckBox(self.tab_overview)
		self.checkBox.setPalette(self.palette_whitetext)
		self.checkBox.setText("CheckBox")
		self.gridLayout_overview.addWidget(self.checkBox, 0, 0, 1, 1)

		self.label = QtWidgets.QLabel(self.tab_overview)
		self.label.setPalette(self.palette_whitetext)
		self.label.setText("Overview self.setTabEnabled(tabIndex,True/False) #enable/disable the tab")
		self.gridLayout_overview.addWidget(self.label, 1, 0, 1, 1)

	def _set_signal_slots(self):
		self.actionExit.triggered.connect(MainWindow.close)
		self.actionInfo.triggered.connect(self._slot_menu_info)  # popup msgbox at pressing "?"
		self.actionAbout.triggered.connect(self._slot_menu_about)  # popup msgbox at pressing "?"
		self.actionOpen.triggered.connect(self.explorer_open_db)
		self.actionAdmin_mode.toggled['bool'].connect(self._slot_admin_mode_toggle)
		self.actionReload.triggered.connect(self._slot_save_changed_items)
		self.actionRegex_filtering_mode.toggled['bool'].connect(self.regex_check_changed)
		self.actionFarnellOrderList.triggered.connect(self._slot_make_Farnell_order_list)
		self.actionOpenURL.triggered.connect(self._slot_open_URLs)

		self.pComment.textChanged.connect(self._slot_pcomment_max_len)  # check if <1000 char, or else delete the >1000 chars
		self.cCurrency.currentTextChanged.connect(self._slot_set_currency_prefix)  # set the selectable currency in front of the amount
		self.cProduct.lineEdit().textEdited.connect(self._filter_combobox_product)
		self.cStorename.lineEdit().textEdited.connect(self._filter_combobox_storename)
		self.cAddedBy.lineEdit().textEdited.connect(self._filter_combobox_addedby)
		self.cProduct.lineEdit().returnPressed.connect(self._update_items_from_combobox_product)
		#self.sPriceUnit.valueChanged.connect(self.priceunit_value_changed)

		self.bUrl.clicked.connect(self.get_data_from_url)
		self.bAttachment.clicked.connect(self._slot_find_attachment)
		self.bClear.clicked.connect(self._slot_clear_fields)
		self.bSave.clicked.connect(self._slot_save_button_new_order)

		self.checkbox_delegate_edit.checked_signal.connect(self.set_time_date_after_checkbox)


		self.tablemodel.dataChanged.connect(self._slot_table_cell_changed)
		self.cTable_Query_select.currentTextChanged.connect(self.cTable_Query_select_changed)
		self.act_copy.triggered.connect(self.save_selection_to_input)
		self.act_open_farnell.triggered.connect(self.open_number_in_farnell)


		self.bTable_save.clicked.connect(self._slot_save_changed_items)
		self.bTable_delete.clicked.connect(self._slot_delete_row_table)

		MainWindow.close_check.connect(self._slot_save_changed_items)

		QtCore.QMetaObject.connectSlotsByName(MainWindow)
		
	
	def _slot_make_Farnell_order_list(self):
		rowcount = self.proxyModel_filter.rowCount()
		indexes = list()
		selection_index = self.tableview.selectedIndexes()
		for i, index in reversed(list(enumerate(selection_index))): #remove all column that are not 0 (the ID column)
			if index.column() != 0:
				selection_index.pop(i)
				continue
		#for sel_index in selection_index:
		#	print(self.proxyModel_filter.mapToSource(sel_index).row())
		#print("")
		for row in range(rowcount):  #get all visible in tableview
			index = self.proxyModel_filter.mapToSource(self.proxyModel_filter.index(row, gStore_name_col))
			if self.tablemodel.data(index, QtCore.Qt.DisplayRole) == "Farnell":	#discard all that are not farnell
				#print(index.row())
				for sel_index in selection_index:
					if index.row() == self.proxyModel_filter.mapToSource(sel_index).row():
						indexes.append(index)
				
		
		order_string = str()
		for index in indexes:	#get order numbers, amount, added by (project)
			row = index.row()
			ordernumber = str(self.tablemodel.getData(row, gURL_Ordernumber_col))
			if ordernumber == "*": continue
			if "http" in ordernumber: continue
			if not ordernumber[:6].isdigit(): continue
			amount = str(self.tablemodel.getData(row, gAmount_col))
			addedby = str(self.tablemodel.getData(row, gAdded_by_col))
			costcentre = str(self.tablemodel.getData(row, gCostCentre_col))
			order_string += ordernumber + ", " + amount + ", " + addedby + " " + costcentre + "\n"
		
		# display in plaintextedit in popup
		display_dialog = QtWidgets.QDialog(self)
		display_dialog.setPalette(self.palette_window)
		#display_dialog.setWindowTitle("SOS: Simple Order System " + self.VERSION)
		display_dialog.setWindowTitle(MainWindow.windowTitle())
		display_dialog.setWindowIcon(MainWindow.windowIcon())
		label = QtWidgets.QLabel("Farnell Order list")
		label.setPalette(self.palette_whitetext)
		textbox = QtWidgets.QPlainTextEdit()
		textbox.setPlainText(order_string)
		vlayout = QtWidgets.QVBoxLayout()
		vlayout.addWidget(label)
		vlayout.addWidget(textbox)
		display_dialog.setLayout(vlayout)
		display_dialog.exec_()
	
	def _slot_open_URLs(self):
		rowcount = self.proxyModel_filter.rowCount()
		indexes = list()
		selection_index = self.tableview.selectedIndexes()
		for i, index in reversed(list(enumerate(selection_index))): #remove all column that are not 0 (the ID column)
			if index.column() != 0:
				selection_index.pop(i)
				continue
		for row in range(rowcount):  # get all visible in tableview
			index = self.proxyModel_filter.mapToSource(self.proxyModel_filter.index(row, gStore_name_col))
			for sel_index in selection_index:
				if index.row() == self.proxyModel_filter.mapToSource(sel_index).row():
					indexes.append(index)

		order_string = list()
		for index in indexes:  # get order numbers, amount, added by (project)
			row = index.row()
			url = str(self.tablemodel.getData(row, gURL_Ordernumber_col))
			comment = str(self.tablemodel.getData(row, gComment_col))
		
			#http until spatie or \n
			import re
			url = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", url)
			comment = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", comment)

			#if not "http" in url or comment: continue
			if len(comment) != 0:
				order_string.append(comment[0])
			if len(url) != 0:
				order_string.append(url[0])

		#open url's in browser
		for i, url in enumerate(order_string):
			#open url in browser
			import webbrowser
			webbrowser.open(url, new=0, autoraise=True)
			#wait(100)
			from time import sleep #sleep to give broswer some time
			if i == 0: sleep(2.5) # wait to startup if necessary
			else: sleep(0.2)

	def _slot_admin_mode_toggle(self, istoggled):
		self.ADMIN_MODE = istoggled
		if istoggled:
			if self.CONFIG_BUSY == False:
				msgbox = QtWidgets.QMessageBox(MainWindow)
				msgbox.setIcon(QtWidgets.QMessageBox.Warning)
				msgbox.setWindowTitle('Toggle admin mode')
				msgbox.setText('If you are not the database administrator please press "Cancel"')
				msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
				msgbox.addButton(QtWidgets.QMessageBox.Cancel)
				msgbox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
				if msgbox.exec() == QtWidgets.QMessageBox.Cancel:
					self.actionAdmin_mode.blockSignals(True)
					self.actionAdmin_mode.setChecked(False)
					self.ADMIN_MODE = False
					self.actionAdmin_mode.blockSignals(False)
					return
		#	self.tabWidget.addTab(self.tab_overview, "Overview") #todo overview tab
		#	pass
		#else:
		#	self.tabWidget.removeTab(self.tabWidget.indexOf(self.tab_overview))
		
			self.menuAdminTools.menuAction().setVisible(True)
		else:
			self.menuAdminTools.menuAction().setVisible(False)

		if not self.CONFIG_BUSY:
			self.cTable_Query_select_changed()
			
			#self.menuBar.removeAction(self.menuAdminTools.menuAction())

	def _slot_delete_row_table(self):
		selection_index = self.tableview.selectedIndexes()
		if len(selection_index) == 0: return

		for i, index in reversed(list(enumerate(selection_index))): #remove all column that are not 0 (the ID column)
			if index.column() != 0:
				selection_index.pop(i)
				continue
			ordered_checked = index.model().data(index.model().index(index.row(), gOrdered_col), QtCore.Qt.DisplayRole)
			if ordered_checked != 0: #makes sure the already ordered records are not deleted
				msgbox = QtWidgets.QMessageBox(MainWindow)
				msgbox.setIcon(QtWidgets.QMessageBox.Question)
				msgbox.setWindowTitle('Cannot delete order')
				msgbox.setText('This item is already ordered, you cannot delete it.')
				msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
				msgbox.exec()
				selection_index.pop(i)

		if len(selection_index) == 0: return

		ID=""
		if len(selection_index) == 1:
			ID = str(selection_index[0].model().data(selection_index[0].model().index(selection_index[0].row(), 0), QtCore.Qt.DisplayRole))
			row = "row"
		else:
			for index in selection_index:
				ID += str(index.model().data(index.model().index(index.row(), 0), QtCore.Qt.DisplayRole)) + ", "
			ID = ID.rstrip(', ')
			row = "rows"

		msgbox = QtWidgets.QMessageBox(MainWindow)
		msgbox.setIcon(QtWidgets.QMessageBox.Question)
		msgbox.setWindowTitle('Unsaved changes')
		msgbox.setText('Are you sure you want to delete ' + str(len(selection_index)) + ' ' + row + '? (ID ' + ID + ')')
		msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes)
		msgbox.addButton(QtWidgets.QMessageBox.No)
		msgbox.setDefaultButton(QtWidgets.QMessageBox.No)

		if msgbox.exec() == QtWidgets.QMessageBox.Yes:
			self._slot_save_changed_items(True)
			query = "DELETE from orders WHERE "+gID+" in ("+ID+")"
			self.db.exec('execute', query)
			# todo save current ordering
			#self.proxyModel_filter.blockSignals(True)
			self.cTable_Query_select_changed(full_refresh=True)
			# todo set current ordering
			#self.proxyModel_filter.blockSignals(False)

	def _slot_save_changed_items(self, exit=False):
		if len(self.table_row_changed) > 0:
			msgbox = QtWidgets.QMessageBox(MainWindow)
			msgbox.setIcon(QtWidgets.QMessageBox.Question)
			msgbox.setWindowTitle('Unsaved changes')
			msgbox.setText('Do you want to save your unsaved changes?')
			msgbox.setStandardButtons(QtWidgets.QMessageBox.Yes)
			msgbox.addButton(QtWidgets.QMessageBox.No)
			msgbox.setDefaultButton(QtWidgets.QMessageBox.No)

			if msgbox.exec() == QtWidgets.QMessageBox.Yes:
				self._slot_save_button_table()

			if exit is False:
				self.cTable_Query_select_changed(full_refresh=True)
		else:
			self.cTable_Query_select_changed(full_refresh=True)

	def _slot_table_cell_changed(self, index):
		if self.REFRESH_BUSY == 0:
			self.table_row_changed.add(index.row())  #add changed row to list for saving later

	def _slot_set_currency_prefix(self):
		if self.cCurrency.currentIndex() == self.CUSTOM_CURRENCY:
			currency, ok = QtWidgets.QInputDialog.getText(self.cCurrency, 'Custom currency', 'Input custom currency name')
			if not ok:
				self.cCurrency.setCurrentIndex(0)
				currency = "€"
		else:
			currency = self.cCurrency.currentText()

		self.sPriceUnit.setPrefix(currency + " ")

	def _slot_pcomment_max_len(self):
		txt = self.pComment.toPlainText()
		if len(txt) > self.COMMENT_MAX_LEN - 1:
			self.pComment.setPlainText(txt[:self.COMMENT_MAX_LEN - 1])
			self.pComment.moveCursor(QTextCursor.End)

	def _slot_menu_info(self):
		message = \
			"Submit your orders using this form.\n" \
			"Fields with asterisk (*) are obligated. If for some reason you don't know how to fill in one of the obligated fields, please enter an asterisk (*), for later filter purposes.\n" \
			"If you have a quotation, fill in the extra details in the comment section. The attachment can be selected in the file selector field at the bottom. There is no need to manually copy it to a specific location.\n" \
			"Press the 'Orders' button to see all (past) orders. In the dropdown box you can select which order status you want to see.\n" \
			"With the comboboxes above the table you can filter the results. Use regex in the filter boxes for enhanced filtering."
		msgbox = QtWidgets.QMessageBox(MainWindow)
		msgbox.setWindowTitle("Info")
		msgbox.setText(message)
		msgbox.exec_()

	def _slot_menu_about(self):
		message = 'SOS: simple order system ' + self.VERSION
		message += "\n\nCreated by Dimitri Welting for the UMC Utrecht (2019)\n"

		msgbox = QtWidgets.QMessageBox(MainWindow)
		msgbox.setIcon(QtWidgets.QMessageBox.Question)
		msgbox.setWindowTitle('About')
		msgbox.setText(message)
		msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
		icon = QtGui.QPixmap("icon/icon_48.png")
		msgbox.setIconPixmap(icon)
		msgbox.exec_()

	def _slot_clear_fields(self):
		self.pComment.clear()  # clear comment box

		for field in self.tab_neworder.findChildren(QtWidgets.QLineEdit):  # find all widgets and clear them
			field.clear()

		self.sAmount.setValue(1)
		self.sPriceUnit.setValue(0.00)
		self.cCurrency.setCurrentIndex(0)
		self.tCostCentre.setText('')

		self.cAddedBy.setCurrentText(config.get_setting(Config__Added_by))

	def _slot_find_attachment(self):
		filename = QtWidgets.QFileDialog.getOpenFileName(MainWindow,
		                                                 "Open File",
		                                                 "",  # "/" test
		                                                 "Documents (*.pdf *.doc *.docx *.odt *.txt *.rtf *.tex)")
		self.tAttachment.setText(filename[0])

	def _slot_save_button_new_order(self):

		# get time and date
		timedate = self.current_time_date()
		# append attachtment file to comment line
		commenttext = self.pComment.toPlainText()
		if self.tAttachment.text() != "":
			filename = self._copy_attachment()
			commenttext = commenttext + "\n" + filename #self.tAttachment.text()

		# copy input form texts to array
		saved_input_list = [[0] * 2 for _ in range(len(self.row_data))]
		saved_input_list[0] = [gAdded_by, self.cAddedBy.currentText()]
		saved_input_list[1] = [gProduct, self.cProduct.currentText()]
		saved_input_list[2] = [gAmount, self.sAmount.value()]
		saved_input_list[3] = [gStore_name, self.cStorename.currentText()]
		saved_input_list[4] = [gURL_Ordernumber, self.tURL.text()]
		saved_input_list[5] = [gCost_centre, self.tCostCentre.text()]
		saved_input_list[6] = [gPrice_per_unit, self.sPriceUnit.text()]
		saved_input_list[7] = [gComment, commenttext]
		saved_input_list[8] = [gOrdered, '0']
		saved_input_list[9] = [gNot_ordered, '0']
		saved_input_list[10] = [gReturned, '0']
		saved_input_list[11] = [gDate_added, timedate]
		# saved_input_list[11] = [gDate_ordered, self.cAddedBy.currentText()]
		# saved_input_list[12] = [gDate_returned, self.cAddedBy.currentText()]

		for item in saved_input_list[0:6]: #check required inputs not empty
			if (item[1] == "") or (item[1] == 0):
				print('error')
				QtWidgets.QMessageBox.warning(
						MainWindow,
						'Error',
						'Error: not all required fields filled in',
						QtWidgets.QMessageBox.Ok)
				return

		for j, [saved_input_column, saved_input_data] in enumerate(saved_input_list): #insert all the saved data to the row_data list
			for i, [_, column_name, _] in enumerate(self.row_data):
				if column_name == saved_input_column:
					if isinstance(saved_input_data, str):
						saved_input_data = saved_input_data.replace('\n', " ")
						saved_input_data = saved_input_data.replace('\r', "")
					self.row_data[i][2] = saved_input_data
					break

		# create INSERT Query and send data
		scolumns_to_add_to = str()
		svalues_to_add = str()
		for column_nr, column_name, column_data in self.row_data:
			if column_name != gID:
				scolumns_to_add_to += '"' + column_name + '"' + ", "
				svalues_to_add += '"' + str(column_data) + '"' + ", "

		scolumns_to_add_to = scolumns_to_add_to[:-2]  # remove the last comma
		svalues_to_add = svalues_to_add[:-2]  # remove the last comma

		query = "INSERT INTO orders(" + scolumns_to_add_to + ") VALUES(" + svalues_to_add + ")"
		self.db.exec('execute', query)

		config.set_setting(Config__Added_by, self.cAddedBy.lineEdit().text())
		store_name = self.cStorename.currentText()

		# refresh table
		self.cTable_Query_select.setCurrentIndex(0)
		self.table_refresh()
		self._fill_combobox_inputs('full')

		self._slot_clear_fields() #empty imputs
		self.cStorename.setCurrentText(store_name)


		QtWidgets.QMessageBox.information(
				MainWindow,
				'Saved',
				'Order saved')

	def _slot_save_button_table(self):
		if len(self.table_row_changed) == 0:
			return

		for row in self.table_row_changed:
			self.table_to_row_data(row)

			# create INSERT Query and send data
			query = "UPDATE orders SET "
			for _, column_name, column_data in self.row_data:
				if column_name == gID:
					continue
				column_data = column_data.replace("'", "''") # escape character filtering
				query += "'" + column_name + "'" + " = " + "'" + str(column_data) + "'" + ", "
			query = query.rstrip(", ")
			query += " WHERE ID = " + str(self.tablemodel.getData(row, 0))

			self.db.exec('execute', query)

		# refresh table
		self.cTable_Query_select_changed(full_refresh=True)

		QtWidgets.QMessageBox.information(
				MainWindow,
				'Saved',
				str(len(self.table_row_changed))+' Orders updated')

		self.table_row_changed.clear()

	def _copy_attachment(self):
		dst_loc = str()

		src_loc = self.tAttachment.text()
		if src_loc == "":
			return

		tmp = src_loc.split('/')
		filename = QtCore.QDate.currentDate().toString('yyyyMMdd')
		filename += "-" + self.cAddedBy.currentText()
		filename += "-" + self.cStorename.currentText()
		filename += "-" + tmp[len(tmp) - 1]
		filename = filename.replace("/", "_")
		filename = filename.replace("\\", "_")
		filename = filename.replace("*", "")

		
		dst_config = config.get_setting(Config_Attachment, Config_Misc)
		try:
			if not "7TCoillab" in dst_config:
				raise FileNotFoundError('Wrong')
			else:
				copy2(src_loc, dst_config + filename)
		
		except FileNotFoundError:
			message = 'Destination folder for copying attachment not found.\nPlease select the correct attachment folder.'
			QtWidgets.QMessageBox.warning(
				MainWindow,
				'Database not valid',
				message)
			dst_dir = QtWidgets.QFileDialog.getExistingDirectory(MainWindow,
			                                           "Open Directory",
			                                           "",
			                                           QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
			dst_dir += "/"
			copy2(src_loc, dst_dir + filename)
			config.set_setting(Config_Attachment, dst_dir, Config_Misc)
		return filename

	def table_to_row_data(self, row):
		saved_input_list = [[0] * 2 for _ in range(len(self.row_data))]
		saved_input_list[0] = [gID,                 str(self.tablemodel.getData(row,  0))]
		saved_input_list[1] = [gProduct,            str(self.tablemodel.getData(row,  1))]
		saved_input_list[2] = [gStore_name,         str(self.tablemodel.getData(row,  2))]
		saved_input_list[3] = [gURL_Ordernumber,    str(self.tablemodel.getData(row,  3))]
		saved_input_list[4] = [gAmount,             str(self.tablemodel.getData(row,  4))]
		saved_input_list[5] = [gPrice_per_unit,     str(self.tablemodel.getData(row,  5))]
		saved_input_list[6] = [gCost_centre,        str(self.tablemodel.getData(row,  6))]
		saved_input_list[7] = [gComment,            str(self.tablemodel.getData(row,  7))]
		saved_input_list[8] = [gAdded_by,           str(self.tablemodel.getData(row,  8))]
		saved_input_list[9] = [gOrdered,            str(self.tablemodel.getData(row,  9))]
		saved_input_list[10] = [gNot_ordered,       str(self.tablemodel.getData(row, 10))]
		saved_input_list[11] = [gReturned,          str(self.tablemodel.getData(row, 11))]
		saved_input_list[12] = [gDate_added,        str(self.tablemodel.getData(row, 12))]
		saved_input_list[13] = [gDate_ordered,      str(self.tablemodel.getData(row, 13))]
		saved_input_list[14] = [gDate_returned,     str(self.tablemodel.getData(row, 14))]

		for j, [saved_input_column, saved_input_data] in enumerate(saved_input_list, 1):  # insert all the saved data to the row_data list
			for i, [_, column_name, _] in enumerate(self.row_data):
				if column_name == saved_input_column:
					self.row_data[i][2] = saved_input_data
					break

	def explorer_open_db(self):
		while True:
			fileDlg = QtWidgets.QFileDialog(MainWindow)
			filename = fileDlg.getOpenFileName(MainWindow, "Open File", QtCore.QDir.homePath(), "Documents (*.db)")
			fileDlg.close()
			fileDlg.deleteLater()

			if filename[0] == "":
				return True

			if self.open_db(filename[0]) == False:
				config.set_last_opened(filename[0])
				self.cTable_Query_select_changed(full_refresh=True)
				return False

	def open_db(self, filename, refresh=True):
		if self.db.isSQLite3(filename):
			self.statusbar_text.setText(filename)
			self.db.set_db(filename)

			self.tabWidget.setEnabled(True)
			return False

		else:
			message = 'No database is loaded or the database you chose is not a valid sqlite3 database. \nPlease choose another database.\n\nThis database is usually located in a network location'
			QtWidgets.QMessageBox.warning(
					MainWindow,
					'Invalid database',
					message)
			return True

	def table_init(self, columns, types):
		# table make columns
		for i_column, column in enumerate(columns):
			self.tablemodel.setHeaderData(i_column, QtCore.Qt.Horizontal, column)

			if (column.startswith('Date')) or (column == gID):  # set no-edit mode
				if self.ADMIN_MODE:
					self.tableview.setItemDelegateForColumn(i_column, None)
				else:
					self.tableview.setItemDelegateForColumn(i_column, self.lineedit_noedit_delegate)
			elif column == gID:  # set no-edit mode
				self.tableview.setItemDelegateForColumn(i_column, self.lineedit_noedit_delegate)
			elif column == gComment:
				self.tableview.setItemDelegateForColumn(i_column, self.multiline_delegate)  # set multi-line mode
			elif (column == gOrdered) or (column == gReturned) or (column == gNot_ordered):
				if self.ADMIN_MODE:
					self.tableview.setItemDelegateForColumn(i_column, self.checkbox_delegate_edit)  # checkbox, centered
				else:
					self.tableview.setItemDelegateForColumn(i_column, self.checkbox_delegate_noedit)  # checkbox, centered
			elif types[i_column] == "INTEGER":  # set validator per column depending on type in sql
				self.tableview.setItemDelegateForColumn(i_column, self.int_delegate)
			elif column == gPrice_per_unit: #types[i_column] == "REAL":
				self.tableview.setItemDelegateForColumn(i_column, self.float_delegate)

	def filter_year(self):
		child = self.tab_table.findChild(QtWidgets.QLineEdit, str(gDate_added_col))  # .setText(Ordered)
		thisyear = self.current_time_date()[:4]
		string_regex = str(int(thisyear) - 1) + '|' + thisyear

		thisyear_short = thisyear[2:4]
		thisyear_short_last = str(int(thisyear_short)-1)
		string_wildcard = thisyear[0:2]
		if thisyear_short[0] == thisyear_short_last[0]:
			string_wildcard += thisyear[2]
		else:
			string_wildcard += '[' + thisyear_short_last[0] + thisyear_short[0] + ']'
		string_wildcard += '[' + thisyear_short_last[1] + thisyear_short[1] + ']'

		childtext = child.text()

		if self.CONFIG_BUSY:
			if self.actionRegex_filtering_mode.isChecked() == True:
				child.setText(string_regex)
			else:
				child.setText(string_wildcard)
		else:
			if self.actionRegex_filtering_mode.isChecked() == True:
				if childtext == string_wildcard:
					child.setText(string_regex)  # adding extra speed to filtering by pre-filtering the year
			else:
				if childtext == string_regex:
					child.setText(string_wildcard)  # adding extra speed to filtering by pre-filtering the year

	def regex_check_changed(self, checked):
		self.proxyModel_filter.changeSyntax(checked)

	def table_refresh(self, Ordered='0', Not_ordered='0', Returned='0', full_refresh=True):
		DebugTiming.start('table refresh')
		self.REFRESH_BUSY = True

		# get db info and data
		if full_refresh:
			self.tables = self.db.get_table_names()
			self.column_names, self.column_types = self.db.get_table_info(self.tables[0])

			# set data list to transfer data from input to table
			self.row_data = [[] * 3 for _ in range(1, len(self.column_names) + 1)]
			for i, column in enumerate(self.column_names):
				self.row_data[i] = [i + 1, column, ""]

			query = 'SELECT * FROM "{}"'.format(self.tables[0])  # make table name a variable
			db_data = self.db.exec('fetchall', query)  # make table name a variable

			# init table
			db_data = [list(i) for i in db_data]
			if len(db_data) == 0: #if there are no records, make sure it doesnt crash, so add at least one (empty) line
				db_data.append([])
				for _ in column_names: db_data[0].append("")

			self.tablemodel.setAllData(db_data)

		self.table_init(self.column_names, self.column_types)

		if full_refresh:
			if self.set_filter_box():
				#self.filter_year()
				pass

		child = self.tab_table.findChild(QtWidgets.QLineEdit, str(self.columns_to_filter_query[0]))#.setText(Ordered)
		child.setText(Ordered)
		child = self.tab_table.findChild(QtWidgets.QLineEdit, str(self.columns_to_filter_query[1]))#.setText(Not_ordered)
		child.setText(Not_ordered)
		child = self.tab_table.findChild(QtWidgets.QLineEdit, str(self.columns_to_filter_query[2]))#.setText(Returned)
		child.setText(Returned)
		self.proxyModel_filter.filter()

		self.tableview.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		self.tableview.sortByColumn(0, QtCore.Qt.DescendingOrder)

		self._fill_combobox_inputs()

		self.REFRESH_BUSY = False
		DebugTiming.finish('table refresh')

	def cTable_Query_select_changed(self, returned=None, full_refresh=False): #'returned' is from signal: ignore

		index = self.cTable_Query_select.currentIndex()
		if index == 0:
			self.table_refresh(Ordered='0', Not_ordered='0', Returned='0', full_refresh=full_refresh)

		elif index == 1:
			self.table_refresh(Ordered='1', Not_ordered='', Returned='', full_refresh=full_refresh)

		elif index == 2:
			self.table_refresh(Ordered='', Not_ordered='1', Returned='', full_refresh=full_refresh)

		elif index == 3:
			self.table_refresh(Ordered='', Not_ordered='', Returned='1', full_refresh=full_refresh)

		elif index == 4:
			self.table_refresh(Ordered='', Not_ordered='', Returned='', full_refresh=full_refresh)

	def current_time_date(self):
		timedate = QtCore.QDate.currentDate().toString('yyyy-MM-dd')
		timedate = timedate + " " + QtCore.QTime.currentTime().toString('hh:mm')
		return timedate

	def _fill_combobox_inputs(self, refresh='soft'):
		if (self.db_path == db.DB_PATH) and (refresh == 'soft'):
			return

		#todo make these functions dependend on tablemodel data instead of queries
		self._fill_combobox_addedby()
		self._fill_combobox_product()
		self._fill_combobox_storename()

		self.db_path = db.DB_PATH

	def _fill_combobox_storename(self):
		DebugTiming.start('_fill_combobox_storename')
		data = list(set(self.tablemodel.getAllData(gStore_name_col)))
		data.sort(key=str.casefold)
		data.insert(0, '')

		combo_model = QtCore.QStringListModel(data)
		self.combo_proxy_storename.setSourceModel(combo_model)
		self.combo_proxy_storename.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.cStorename.setModel(self.combo_proxy_storename)
		DebugTiming.finish('_fill_combobox_storename')

	def _fill_combobox_addedby(self):
		DebugTiming.start('_fill_combobox_addedby')
		data = list(set(self.tablemodel.getAllData(gAdded_by_col)))
		data.sort(key=str.casefold)
		data.insert(0, '')

		text = self.cAddedBy.currentText()
		combo_model = QtCore.QStringListModel(data)
		self.combo_proxy_addedby.setSourceModel(combo_model)
		self.combo_proxy_addedby.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.cAddedBy.setModel(self.combo_proxy_addedby)
		self.cAddedBy.setCurrentText(text)

		DebugTiming.finish('_fill_combobox_addedby')

	def _fill_combobox_product(self):
		data = list(set(self.tablemodel.getAllData(gProduct_col)))
		data.sort(key=str.casefold)
		data.insert(0, '')

		combo_model = QtCore.QStringListModel(data)
		self.combo_proxy_product.setSourceModel(combo_model)
		self.cProduct.setModel(self.combo_proxy_product)

	def _filter_combobox_product(self, inputtext):
		text = self.cProduct.currentText()
		pos = self.cProduct.lineEdit().cursorPosition()

		self.combo_proxy_product.setFilterRegExp(inputtext)

		self.cProduct.blockSignals(True)
		self.cProduct.setCurrentText(text)
		self.cProduct.lineEdit().setCursorPosition(pos)
		self.cProduct.blockSignals(False)

	def _filter_combobox_storename(self, inputtext):
		text = self.cStorename.currentText()
		pos = self.cStorename.lineEdit().cursorPosition()
		self.combo_proxy_storename.setFilterRegExp(inputtext)
		
		self.cStorename.blockSignals(True)
		#if self.combo_proxy_storename.rowCount() == 1 and pos == len(text):
		#	index = self.combo_proxy_storename.index(0,0)
		#	text = self.combo_proxy_storename.data(index)
		#	self.cStorename.setCurrentText(text)
		#	self.cStorename.lineEdit().setSelection(pos, len(self.cStorename.currentText())-pos)
		#else:
		self.cStorename.setCurrentText(text)
		self.cStorename.lineEdit().setCursorPosition(pos)
		self.cStorename.blockSignals(False)

	def _filter_combobox_addedby(self, inputtext):
		text = self.cAddedBy.currentText()
		pos = self.cAddedBy.lineEdit().cursorPosition()
		self.combo_proxy_addedby.setFilterRegExp(inputtext)
		self.cAddedBy.blockSignals(True)
		self.cAddedBy.setCurrentText(text)
		self.cAddedBy.lineEdit().setCursorPosition(pos)
		self.cAddedBy.blockSignals(False)

	def _update_items_from_combobox_product(self):
		product = self.cProduct.currentText()

		data = self.tablemodel.getAllData()
		for item in data:
			if product in item:
				break

		self.sAmount.setValue(item[gAmount_col])

		data = item[gPrice_per_unit_col]
		data = data.split(" ")
		self.sPriceUnit.setPrefix(data[0]+" ")
		self.sPriceUnit.setValue(float(data[1]))

		self.cStorename.setCurrentText(item[gStore_name_col])
		self.tURL.setText(item[gURL_Ordernumber_col])

	def set_filter_box(self):
		self.proxyModel_filter.setColumnsToFilter(self.columns_to_filter)

		children = self.tab_table.findChildren(QtWidgets.QLineEdit)
		if len(children) > 0: #== self.tablemodel.columnCount():
			return False

		i_filterbox = 0
		for i_column in range(self.tablemodel.columnCount()): # make filter boxes above tableview in correct place and size for the columns
			line_edit = QtWidgets.QLineEdit(self.tab_table)
			line_edit.setMaximumWidth(self.tableview.columnWidth(i_column)-5)
			self.HBoxLayout_table_filters.addWidget(line_edit)
			line_edit.setObjectName(str(i_column))

			if i_column not in self.columns_to_filter:
				line_edit.setMaximumHeight(0)
				line_edit.setEnabled(False)
				continue

			header = str(self.tablemodel.headerData(i_column, QtCore.Qt.Horizontal))
			line_edit.setPlaceholderText(header + " filter")
			line_edit.setProperty("column", i_filterbox)
			line_edit.textChanged.connect(self.proxyModel_filter.setFilter)
			i_filterbox += 1

			if i_column == self.tablemodel.columnCount()-1:
				line_edit.setProperty("last", True)

			if i_column in self.columns_to_filter_query: #set the checkbox as query filters, optimized
				line_edit.setMaximumHeight(0)
				line_edit.setEnabled(False)
				line_edit.textChanged.disconnect()
				line_edit.textChanged.connect(self.proxyModel_filter.setFilter_fast)

		self.tableview.horizontalHeader().sectionResized.connect(self.resize_size_change) # on size change change filterbox size
		return True

	def resize_size_change(self, logicalIndex, oldSize, newSize): #set new size of filter input box after resize
		child = self.tab_table.findChild(QtWidgets.QLineEdit, str(logicalIndex))
		child.setMaximumWidth(newSize-6)

		if child.property("last") == True:
			if self.tableview.verticalScrollBar().isVisible():
				child.setMaximumWidth(newSize + 12)

	def open_number_in_farnell(self):
		#todo only show this context menu when store is farnell
		import webbrowser
		view_index = self.tableview.currentIndex()
		model_index = self.proxyModel_filter.mapToSource(view_index)
		storename = self.tablemodel.getData(model_index.row(),  gStore_name_col)
		if "Farnell" in storename:
			ordernumber = self.tablemodel.getData(model_index.row(),  gURL_Ordernumber_col)
			url = "https://nl.farnell.com/" + ordernumber
			webbrowser.open(url, new=0, autoraise=True)

	
	def save_selection_to_input(self): #copies selection in tableview to the input new order tab
		view_index = self.tableview.currentIndex()
		model_index = self.proxyModel_filter.mapToSource(view_index)
		self.table_to_row_data(model_index.row())

		for _, name, data in self.row_data:
			if name == gProduct:
				self.cProduct.setCurrentText(data)
			elif name == gStore_name:
				self.cStorename.setCurrentText(data)
			elif name == gURL_Ordernumber:
				self.tURL.setText(data)
			elif name == gAmount:
				self.sAmount.setValue(int(data))
			elif name == gPrice_per_unit:
				data = data.split(" ")
				self.sPriceUnit.setPrefix(data[0] + " ")
				self.sPriceUnit.setValue(float(data[1]))
			elif name == gCost_centre:
				self.tCostCentre.setText(data)
			elif name == gComment:
				self.pComment.setPlainText(data)
			elif name == gDate_added:
				self.row_data[gDate_ordered_col][2] = ''


	def get_data_from_url(self):
		url = self.tURL.text()
		url = url.split('?')
		try:
			url = url[0]
		except:
			pass

		validator = QtGui.QRegExpValidator()
		validator.setRegExp(QtCore.QRegExp(r"^(?:(http(s)?:\/\/))?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"))
		v = validator.validate(url, 0)
		if (v[0] != QtGui.QValidator.Acceptable) and (self.cStorename.currentText().lower() != "farnell"):
			#print('invalid url')
			return

		if (v[0] != QtGui.QValidator.Acceptable) and (self.cStorename.currentText().lower() == "farnell"):
			url = "https://nl.farnell.com/"+self.tURL.text()

		self.bUrl.setEnabled(False)
		msgbox = QtWidgets.QMessageBox(MainWindow)
		msgbox.setIcon(QtWidgets.QMessageBox.Warning)
		msgbox.setWindowTitle('URL data loading')
		msgbox.setText('URL data loading')
		msgbox.show()

		headers = {'User-Agent'               : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
		           "Upgrade-Insecure-Requests": "1", "DNT": "1", "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
		           "Accept-Language"          : "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate"}

		if ('farnell' in url):
			try:
				page = requests.get(url, headers=headers, timeout=5)
			except:
				msgbox.close()
				self.bUrl.setEnabled(True)
				#self.get_data_from_url()
				return
			soup = BeautifulSoup(page.content, 'html.parser')

			#try:
			if ('farnell' in url):
				product, ordercode, currency, price, storename = self.soup_Farnell(soup)
			#except:
			#	msgbox.close()
			#	self.bUrl.setEnabled(True)
			#	return
		else:
			msgbox.close()
			self.bUrl.setEnabled(True)
			return

		self.cProduct.setCurrentText(product)
		self.tURL.setText(ordercode)
		self.sPriceUnit.setValue(float(price))
		self.sPriceUnit.setPrefix(currency)
		self.cStorename.setCurrentText(storename)
		comment = self.pComment.toPlainText()
		if comment != "":
			if not (url in comment):
				comment = comment + '\n' + url
		else:
			comment = url
		self.pComment.setPlainText(comment)

		msgbox.close()
		self.bUrl.setEnabled(True)

	def soup_Farnell(self, soup):
		pricebox = soup.find('span', attrs={'class': 'price'})
		price = pricebox.text
		#price = price.replace('&euro;', "€")
		price = price.replace('\r', "")
		price = price.replace('\n', "")
		price = price.replace('\t', "")
		price = price.replace(' ', "")
		price = price.replace(',', '.')

		if len(price.split('.')) > 2:
			price = price.split('.')
			price = price[0]+price[1]+'.'+price[2]

		import re
		currency = re.sub(r'\d', '', price)
		currency = currency.strip('.')
		currency += ' '

		price = price[1:]

		product = soup.find('meta', attrs={'property': 'og:title'})['content']
		ordercode = soup.find('input', attrs={'name': 'cpnPartNumber'})['value']

		return product, ordercode, currency, price, 'Farnell'


	def set_time_date_after_checkbox(self, index, checked):
		index = self.proxyModel_filter.mapToSource(index)
		column = index.column()
		row = index.row()
		
		if (column == gOrdered_col) or (column == gNot_ordered_col):
			ordered = self.tablemodel.getData(row, gOrdered_col)
			notordered = self.tablemodel.getData(row, gNot_ordered_col)
			
			if column == gOrdered_col:
				ordered = checked #get checked state of this index
			elif column == gNot_ordered_col:
				notordered = checked #get checked state of this index
			
			if (ordered == 1) and (notordered == 1):
				if column == gOrdered_col:
					index = self.tablemodel.index(row, gNot_ordered_col) #notordered = 0
				elif column == gNot_ordered_col:
					index = self.tablemodel.index(row, gOrdered_col) #ordered = 0
				self.tablemodel.setData(index, 0, QtCore.Qt.EditRole)

			index = self.tablemodel.index(row, gDate_ordered_col)

		elif column == gReturned_col:
			index = self.tablemodel.index(row, gDate_returned_col)
		else:
			return

		if checked:
			#print(str(index.column()) + "," + str(checked))
			timedate = self.current_time_date()
			self.tableview.model().sourceModel().setData(index, timedate, QtCore.Qt.EditRole)
		else:
			#print(str(index.column()) + "," + str(checked))
			self.tableview.model().sourceModel().setData(index, "", QtCore.Qt.EditRole)


if __name__ == "__main__":
	import sys

	# todo add project column
	# todo Farnell item price, depending on amount
	
	# todo knop toevoegen die bij orders de zichtbare lijst kopieerd, ordernummer, amount, added by, project
	#   of rechtermuisknop, copy
	
	# todo after deleting row, keep ordering

	#todo divide Ui_MainWindow class into multiple parts (setting up ui, table stuff, signal slots(?))
	# maybe one class per tab, so it's easy to make another tab in the future?

	DebugTiming.enable(DEBUG)
	DebugTiming.start('creating objects')
	# set global locale, for portability to different computers
	locale = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)
	locale.setNumberOptions(QtCore.QLocale.RejectGroupSeparator)
	QtCore.QLocale.setDefault(locale)

	# create db object
	db = _Sqlite3()

	# config
	config = _Config()

	# create window
	app = QtWidgets.QApplication(sys.argv)
	app.setQuitOnLastWindowClosed(True)
	MainWindow = MyQMainWindow()
	ui = Ui_MainWindow(MainWindow, db, config)
	DebugTiming.finish('creating objects')

	# show window
	DebugTiming.start('MainWindow.show')
	MainWindow.show()
	DebugTiming.finish('MainWindow.show')

	DebugTiming.start('config_set')
	ui.config_set()
	DebugTiming.finish('config_set')
	#DebugTiming.setEnable(False)

	sys.exit(app.exec_())

