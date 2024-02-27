import sys
import os
import traceback
import winreg as reg
import jedi
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QTabWidget, QInputDialog, QMenuBar, QLabel, QLineEdit, QPushButton, QDialog, \
    QMenu, QTextBrowser
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QRunnable, QThreadPool, QObject, pyqtSlot, QTimer
from PyQt6.QtGui import QAction, QShortcut, QKeySequence, QPixmap
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PyQt6.Qsci import QsciScintilla

from pyeasyedit.LexersCustom import *

GLOBAL_COLOR_SCHEME = {
    "Keyword": "#FFC66D",
    "Comment": "#367d36",
    "ClassName": "#FFEEAD",
    "FunctionMethodName": "#be6ff2",
    "TripleSingleQuotedString": "#7bd9db",
    "TripleDoubleQuotedString": "#7bd9db",
    "SingleQuotedString": "#7bd9db",
    "DoubleQuotedString": "#7bd9db",
}

class SignalEmitter(QObject):
    completionsFetched = pyqtSignal(object)  # Use the correct data type for your completions
    errorOccurred = pyqtSignal(str)

class CompletionWorker(QRunnable, QObject):
    finished = pyqtSignal()


    def __init__(self, code, cursor_pos, environment, signalEmitter):
        super().__init__()  # Initialize base classes correctly
        self.code = code
        self.cursor_pos = cursor_pos  # cursor_pos is a tuple (line, column)
        self.environment = environment
        self.signalEmitter = signalEmitter
        # self.editor = editor

    def run(self):
        print("Running CompletionWorker")
        try:
            print(f"Code: {self.code[:50]}...")  # Print the first 50 chars of code for reference
            print(f"Cursor position: {self.cursor_pos}")
            line, column = self.cursor_pos
            print(f"Initializing Jedi Script with line={line}, column={column}")

            # Note: The Script interface has changed; adapt accordingly
            script = jedi.Script(code=self.code, environment=self.environment)
            try:
                completions = script.complete(line, column)
                print(f"Fetched {len(completions)} completions")
            except:
                return


            # completion_list = [completion.name for completion in completions]
            completion_list = []
            for completion in completions:
                completion_list.append(completion.name)
            print(f"Emitting completionsFetched signal with {len(completion_list)} items")
            self.signalEmitter.completionsFetched.emit(completion_list)

        except Exception as e:
            print(f"Exception occurred: {e}")
            print(f"Exception type: {type(e)}")
            traceback_str = ''.join(traceback.format_tb(e.__traceback__))
            print(f"Traceback: {traceback_str}")
            self.errorOccurred.emit(str(e))

def save_recent_files(file_list, max_files=5):
# Define the registry path
    registry_path = r"Software\PyDE\RecentFiles"
    try:
        # Open or create the key for writing
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, registry_path)

        # Clear existing values
        clear_recent_files(registry_path)

        # Save the most recent 'max_files' entries
        for i, file_path in enumerate(file_list[:max_files]):
            reg.SetValueEx(key, f"File{i}", 0, reg.REG_SZ, file_path)

        reg.CloseKey(key)
    except Exception as e:
        print(f"Error saving recent files: {e}")


def clear_recent_files(registry_path):
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, registry_path, 0, reg.KEY_ALL_ACCESS)
        i = 0
        while True:
            try:
                # Enumerate the next subkey
                name, value, type = reg.EnumValue(key, 0)
                reg.DeleteValue(key, name)
            except WindowsError:
                # A WindowsError exception means we've enumerated all values
                break  # Exit the loop
        reg.CloseKey(key)
    except Exception as e:
        print(f"Error clearing recent files: {e}")


def load_recent_files():
    # Define the registry path
    registry_path = r"Software\PyDE\RecentFiles"
    try:
        # Open the key for reading
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, registry_path, 0, reg.KEY_READ)
        file_list = []
        i = 0
        while True:
            try:
                # Read each value
                name, value, _ = reg.EnumValue(key, i)
                file_list.append(value)
                i += 1
            except WindowsError:  # End of values
                break
        reg.CloseKey(key)
        return file_list
    except Exception as e:
        print(f"Error loading recent files: {e}")
        return []


class ReplaceDialog(QDialog):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor  # Reference to the QsciScintilla editor
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Replace")
        layout = QVBoxLayout(self)

        # Find text label and field
        self.findLabel = QLabel("Find what:", self)
        layout.addWidget(self.findLabel)

        self.findField = QLineEdit(self)
        layout.addWidget(self.findField)

        # Replace text label and field
        self.replaceLabel = QLabel("Replace with:", self)
        layout.addWidget(self.replaceLabel)

        self.replaceField = QLineEdit(self)
        layout.addWidget(self.replaceField)

        # Find and Replace buttons
        self.findButton = QPushButton("Find Next", self)
        self.findButton.clicked.connect(self.findNext)
        layout.addWidget(self.findButton)

        self.replaceButton = QPushButton("Replace", self)
        self.replaceButton.clicked.connect(self.replace)
        layout.addWidget(self.replaceButton)

        self.replaceAllButton = QPushButton("Replace All", self)
        self.replaceAllButton.clicked.connect(self.replaceAll)
        layout.addWidget(self.replaceAllButton)

        self.findField.setFocus()


    def findNext(self):
        text = self.findField.text()
        if not self.editor.findFirst(text, False, True, False, True, True):
            QMessageBox.information(self, "Find", "The text was not found.")

    def replace(self):
        find_text = self.findField.text()
        if self.editor.findFirst(find_text, False, True, False, True, True):
            replace_text = self.replaceField.text()
            self.editor.replace(replace_text)

    def replaceAll(self):
        find_text = self.findField.text()
        replace_text = self.replaceField.text()
        self.editor.SendScintilla(self.editor.SCI_DOCUMENTSTART)
        found = self.editor.findFirst(find_text, False, True, False, True, True)
        while found:
            self.editor.replace(replace_text)
            found = self.editor.findNext()

class SearchDialog(QDialog):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor  # Reference to the QsciScintilla editor
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Search")
        layout = QVBoxLayout(self)

        self.label = QLabel("Enter the text to search:", self)
        layout.addWidget(self.label)

        self.searchField = QLineEdit(self)
        layout.addWidget(self.searchField)

        self.searchButton = QPushButton("Find Next", self)
        self.searchButton.clicked.connect(self.findNext)
        layout.addWidget(self.searchButton)

        self.searchField.setFocus()

    def findNext(self):
        text = self.searchField.text()
        if not self.editor.findFirst(text, False, True, False, True, True):
            # If nothing is found, wrap the search to the beginning
            self.editor.SendScintilla(self.editor.SCI_DOCUMENTSTART)
            if not self.editor.findFirst(text, False, True, False, True, True):
                self.label.setText("Text not found.")
class QScintillaEditorWidget(QWidget):
    fileSaved = pyqtSignal(str)

    def __init__(self, defaultFolderPath, parent=None):
        super().__init__(parent)
        self.defaultFolderPath = defaultFolderPath  # Store the path as an instance attribute
        self.current_file_path = None  # To keep track of the current file path
        self._themes = {
            "editor_theme": "#282a36",
            "margin_theme": "#333436",
            "lines_fg": "#FFFFFF",
            "paper": "#e7f20f",
            "caret_color": "#545c55",
            "font": "Consolas",
            "font_size": 10,
            "brace_match_bg": "#e7f20f",
            "brace_match_fg": "#545c55",
            "unmatched_brace_bg": "#e7f20f",
            "unmatched_brace_fg": "#e7f20f"
            # Add or adjust theme settings as necessary
        }
        self.setupUi()

    def setupUi(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Initialize the QScintilla editor
        self.editor = QsciScintilla()
        layout.addWidget(self.editor)

        # lexer = PythonLexer()
        # self.editor.setLexer(lexer)

        # Editor font
        font = QFont("Consolas", 10)
        self.editor.setFont(font)
        # lexer.setFont(font)

        # Enable line numbers in the left margin
        self.editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.editor.setMarginWidth(0, "0000")  # Adjust the number as needed
        self.applyTheme()
        self.saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self.editor)
        self.saveShortcut.activated.connect(self.saveFile)

    def applyTheme(self):
        self.editor.setEolVisibility(False)
        self.editor.setMarginWidth(1, "0000")
        self.editor.setMarginsBackgroundColor(QColor(self._themes["margin_theme"]))
        self.editor.setMarginsForegroundColor(QColor(self._themes["lines_fg"]))
        self.editor.setAutoIndent(True)
        self.editor.setBraceMatching(QsciScintilla.BraceMatch.SloppyBraceMatch)
        self.editor.setMatchedBraceBackgroundColor(QColor(self._themes["brace_match_bg"]))
        self.editor.setCaretForegroundColor(QColor(self._themes["caret_color"]))
        self.editor.setUnmatchedBraceBackgroundColor(QColor(self._themes["unmatched_brace_bg"]))
        self.editor.setUnmatchedBraceForegroundColor(QColor(self._themes["unmatched_brace_fg"]))

        font = QFont(self._themes["font"], self._themes["font_size"])
        self.editor.setFont(font)
        font = QFont(self._themes["font"], self._themes["font_size"])
        # Set the brace matching mode
        # self.editor.setBraceMatching(QsciScintilla.BraceMatch.Strict)

        # Set the colors for matching braces
        self.editor.setMatchedBraceBackgroundColor(QColor("#006600"))
        self.editor.setMatchedBraceForegroundColor(QColor("#FFFFFF"))

        # Optionally, set the colors for unmatched braces if you want
        self.editor.setUnmatchedBraceBackgroundColor(QColor("#660000"))
        self.editor.setUnmatchedBraceForegroundColor(QColor("#FFFFFF"))
    def setLexerForFile(self, filePath):
        # Instantiate ThemeManager to get themes
        themeManager = ThemeManager()
        themes = themeManager.getThemes()

        # Mapping of file extensions to custom lexer classes
        lexer_map = {
            '.py': CustomPythonLexer,
            '.json': CustomJSONLexer,
            '.js': CustomJavaScriptLexer,
            '.yaml': CustomYAMLLexer, '.yml': CustomYAMLLexer,
            '.html': CustomHTMLLexer, '.htm': CustomHTMLLexer,
            '.css': CustomCSSLexer,
            '.sql': CustomSQLLexer,
            '.xml': CustomXMLLexer,
            '.sh': CustomBashLexer,
            '.bat': CustomBatchLexer,
            # Add other file extensions and their corresponding custom lexers as needed
        }

        # Retrieve the file extension and select the appropriate custom lexer
        extension = os.path.splitext(filePath)[1].lower()
        lexer_class = lexer_map.get(extension)

        if lexer_class:
            # Initialize the selected lexer with the editor instance and themes
            lexer = lexer_class(self.editor)  # Assuming self.editor is your QScintilla editor instance
            lexer.setupLexer(themes, GLOBAL_COLOR_SCHEME)  # Setup lexer with themes and color scheme
            self.editor.setLexer(lexer)
        else:
            # If no custom lexer matches the file extension, set no lexer
            self.editor.setLexer(None)


    def maybeSave(self):
        if self.editor.isModified():
            response = QMessageBox.question(
                self, "Save Changes",
                "The document has been modified.\nDo you want to save your changes?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if response == QMessageBox.StandardButton.Save:
                return self.saveFile()
            elif response == QMessageBox.StandardButton.Cancel:
                return False  # User cancelled the operation
        return True  # No changes to save or user discarded changes

    def saveFile(self):
        if self.current_file_path:
            return self._saveToFile(self.current_file_path)
        else:
            return self.saveFileAs()

    def _saveToFile(self, filePath):
        try:
            with open(filePath, 'w') as file:
                text = self.editor.text()
                file.write(text)
                self.editor.setModified(False)
                self.fileSaved.emit(filePath)  # Emit the signal with the file path

            return True
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File", "An error occurred while saving the file:\n" + str(e))
            return False

    def saveFileAs(self, filePath=None):
        if not filePath:
            filePath, _ = QFileDialog.getSaveFileName(self, "Save File As", self.defaultFolderPath, "All Files (*)")
        if filePath:
            success = self._saveToFile(filePath)
            if success:
                self.current_file_path = filePath
                self.editor.setModified(False)
                return True, filePath  # Indicate success and provide the file path
        return False, None  # Indicate failure



class HotkeysDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hotkeys")
        self.setupUi()

    def setupUi(self):
        layout = QVBoxLayout(self)

        # Example hotkeys, replace with your application's hotkeys
        hotkeys = [
            ("Ctrl+N", "New Tab"),
            ("Ctrl+S", "Save File"),
            ("Ctrl+W", "Close Tab"),
            ("Ctrl+F", "Find"),
            ("Ctrl+R", "Replace"),
        ]

        for key, action in hotkeys:
            layout.addWidget(QLabel(f"{key}: {action}"))

        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.close)
        layout.addWidget(closeButton)

class EditorWidget(QWidget):

    def __init__(self, filePath=None, parent=None):
        super().__init__(parent)
        self.setupUi()
        self.active_workers = []
        self.debounceTimer = QTimer()
        self.debounceTimer.setSingleShot(True)  # Ensures the timer only fires once per start
        # self.debounceTimer.timeout.connect(self.debouncedHandleCompletionsFetched)
        self.pendingCompletionResult = None
        if filePath and os.path.isfile(filePath):
            self.newTab(filePath)

    def setupUi(self):
        self.layout = QVBoxLayout(self)
        self.menuBar = QMenuBar()
        self.layout.setMenuBar(self.menuBar)  # Add the menu bar to the layout

        # File menu
        fileMenu = self.menuBar.addMenu("&File")
        newAction = QAction("&New", self)
        newAction.setShortcut("Ctrl+N")


        newAction.triggered.connect(self.newTab)
        fileMenu.addAction(newAction)

        openAction = QAction("&Open", self)
        openAction.triggered.connect(self.openFile)
        fileMenu.addAction(openAction)

        self.recentFilesMenu = QMenu("&Recent Files", self)
        fileMenu.addMenu(self.recentFilesMenu)

        saveAction = QAction("&Save", self)
        saveAction.triggered.connect(self.saveFile)
        fileMenu.addAction(saveAction)

        saveAsAction = QAction("Save &As...", self)
        saveAsAction.triggered.connect(self.saveFileAs)
        fileMenu.addAction(saveAsAction)

        closeTabAction = QAction("&Close Tab", self)
        closeTabAction.setShortcut("Ctrl+W")


        closeTabAction.triggered.connect(lambda: self.closeTab(self.tabWidget.currentIndex()))
        fileMenu.addAction(closeTabAction)

        # Edit menu
        editMenu = self.menuBar.addMenu("&Edit")
        searchAction = QAction("&Find", self)
        searchAction.setShortcut("Ctrl+F")
        searchAction.triggered.connect(self.search)
        editMenu.addAction(searchAction)

        replaceAction = QAction("&Replace", self)
        replaceAction.setShortcut("Ctrl+R")
        replaceAction.triggered.connect(self.replace)
        editMenu.addAction(replaceAction)

        replaceAllAction = QAction("Replace &All", self)
        replaceAllAction.triggered.connect(self.replaceAll)
        editMenu.addAction(replaceAllAction)

        viewMenu = self.menuBar.addMenu("&View")

        zoomInAction = QAction("Zoom &In", self)
        zoomInAction.setShortcut("Ctrl++")
        zoomInAction.triggered.connect(self.zoomIn)
        viewMenu.addAction(zoomInAction)

        zoomOutAction = QAction("Zoom &Out", self)
        zoomOutAction.setShortcut("Ctrl+-")
        zoomOutAction.triggered.connect(self.zoomOut)
        viewMenu.addAction(zoomOutAction)

        helpMenu = self.menuBar.addMenu("&Help")
        aboutAction = QAction("&About", self)
        aboutAction.triggered.connect(self.showAboutDialog)
        helpMenu.addAction(aboutAction)
        hotkeysAction = QAction("&Hotkeys", self)
        hotkeysAction.triggered.connect(self.showHotkeysDialog)
        helpMenu.addAction(hotkeysAction)

        self.tabWidget = QTabWidget()
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.layout.addWidget(self.tabWidget)
        self.newTab()

        # Context menu actions
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        newAction = QAction("&New", self)
        newAction.triggered.connect(self.newTab)
        self.addAction(newAction)

        openAction = QAction("&Open", self)
        openAction.triggered.connect(self.openFile)
        self.addAction(openAction)

        saveAction = QAction("&Save", self)
        saveAction.triggered.connect(self.saveFile)
        self.addAction(saveAction)

        saveAsAction = QAction("Save &As...", self)
        saveAsAction.triggered.connect(self.saveFileAs)
        self.addAction(saveAsAction)

        closeTabAction = QAction("&Close Tab", self)
        closeTabAction.triggered.connect(lambda: self.closeTab(self.tabWidget.currentIndex()))
        self.addAction(closeTabAction)
        self.populateRecentFilesMenu()

    def showHotkeysDialog(self):
        dialog = HotkeysDialog(self)
        dialog.exec()

    def zoomIn(self):
        current_editor = self.getCurrentEditor()
        if current_editor:
            current_editor.zoomIn()

    def zoomOut(self):
        current_editor = self.getCurrentEditor()
        if current_editor:
            current_editor.zoomOut()

    def newTab(self, filePath=None):
        editorWidget = QScintillaEditorWidget(self.defaultFolderPath())
        editor = editorWidget.editor
        # Editor setup (auto-completion, auto-indent, etc.)
        editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
        editor.setAutoCompletionThreshold(1)  # Start autocompletion after 1 character
        editor.setAutoIndent(True)
        editor.setIndentationWidth(4)
        editor.setIndentationsUseTabs(False)
        if filePath and filePath.endswith(".py"):
            editor.jedi_environment = jedi.create_environment(sys.executable)
            editor.textChanged.connect(lambda: self.handle_text_changed(editor))


        tabIndex = self.tabWidget.addTab(editorWidget, "Untitled")
        self.tabWidget.setCurrentIndex(tabIndex)
        if filePath:
            self.loadFileIntoEditor(filePath, editorWidget)

    def onCompletionsFetched(self, completions, editor):
        # Convert completions to a list of strings
        completion_list = [c.text for c in completions]

        # Display the completions if there are any
        if completion_list:
            editor.showAutoCompletion(completion_list)

    def handle_text_changed(self, editor):
        if not hasattr(editor, 'jedi_environment') or editor.jedi_environment is None:
            print("Jedi environment is not configured.")
            return  # Jedi not configured

        code = editor.text()
        cursor_line, cursor_column = editor.getCursorPosition()
        cursor_line += 1  # Adjust for Jedi's 1-indexed lines

        signalEmitter = SignalEmitter()
        signalEmitter.completionsFetched.connect(self.handleCompletionsFetched, type=Qt.ConnectionType.QueuedConnection)  # Slot to handle completions
        signalEmitter.errorOccurred.connect(self.handleErrorOccurred)  # Slot to handle errors

        # Initialize the worker with necessary parameters
        worker = CompletionWorker(code=code, cursor_pos=(cursor_line, cursor_column),
                                  environment=editor.jedi_environment, signalEmitter=signalEmitter)

        self.active_editor = editor
        # Keep a reference to the worker to prevent premature destruction
        self.active_workers.append(worker)

        # Start the worker in a separate thread
        QThreadPool.globalInstance().start(worker)

    def handleCompletionsFetched(self, result):
        self.pendingCompletionResult = result  # Store the latest result
        # self.debounceTimer.start(500)

    def pendingCompletionResult(self, result):
        print("signal works: handleCompletionsFetched")
        # print(result)
        auto_complete_list = result
        editor = self.active_editor
        if result:
            editor.showUserList(1, auto_complete_list)
            editor.autoCompleteFromAll()
            editor.setAutoCompletionThreshold(10)

    # def debouncedHandleCompletionsFetched(self):
    #     print("Debounced: handleCompletionsFetched")
    #     if self.pendingCompletionResult:
    #         result = self.pendingCompletionResult
    #         auto_complete_list = result
    #         # editor = result[1]
    #         editor = self.active_editor
    #         if result:
    #             pass
    #             print(len(auto_complete_list))
    #             editor.showUserList(1, auto_complete_list)
    #             editor.autoCompleteFromAll()
    #             editor.setAutoCompletionThreshold(10)
    #         self.pendingCompletionResult = None  # Reset pending result

    def handleErrorOccurred(self, result):
        print("signal works: handleCompletionsFetched")
        print(result)


    def onWorkerFinished(self, worker):
        print(f"removing worker")
        # Remove the worker from active_workers
        if worker in self.active_workers:
            self.active_workers.remove(worker)


    def onErrorOccurred(self, error):
        print(f"Error fetching completions: {error}")

    def updateTabText(self, filePath):
        editorWidget = self.sender()
        if editorWidget:
            index = self.tabWidget.indexOf(editorWidget)
            if index != -1:
                self.tabWidget.setTabText(index, os.path.basename(filePath))

    def openFile(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Open File", self.defaultFolderPath(), "All Files (*)")
        if filePath:
            # Check if the file is already open
            for i in range(self.tabWidget.count()):
                editorWidget = self.tabWidget.widget(i)

                if editorWidget.current_file_path == filePath:
                    self.tabWidget.setCurrentIndex(i)
                    # editorWidget.fileSaved = True

                    return
            # Load the file into a new tab
            self.loadFileIntoEditor(filePath)
            self.updateRecentFiles(filePath)  # Update the list of recent files

    def defaultFolderPath(self):
        # Ensure the ./devops directory exists or create it
        basePath = os.getcwd()  # Get the current working directory
        devopsPath = os.path.join(basePath, "devops")
        if not os.path.exists(devopsPath):
            os.makedirs(devopsPath)
        return devopsPath
    def loadFileIntoEditor(self, filePath, editorWidget=None):
        if not editorWidget:
            editorWidget = QScintillaEditorWidget(self.defaultFolderPath())
            # Enable auto-completion
            editorWidget.editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
            editorWidget.editor.setAutoCompletionThreshold(1)  # Start autocompletion after 1 character

            # Enable auto-indent
            editorWidget.editor.setAutoIndent(True)

            # Set indentation width
            editorWidget.editor.setIndentationWidth(4)

            # Use spaces instead of tabs
            editorWidget.editor.setIndentationsUseTabs(False)
            editorWidget.editor.setModified(False)
            # Check if the file is a Python file and set up Jedi
            if filePath and filePath.endswith(".py"):
                editorWidget.editor.jedi_environment = jedi.create_environment(sys.executable)
                editorWidget.editor.textChanged.connect(lambda: self.handle_text_changed(editorWidget.editor))

            tabIndex = self.tabWidget.addTab(editorWidget, os.path.basename(filePath))
            self.tabWidget.setCurrentIndex(tabIndex)
        with open(filePath, 'r') as file:
            content = file.read()
        editorWidget.editor.setText(content)
        editorWidget.editor.setModified(False)

        editorWidget.current_file_path = filePath
        editorWidget.setLexerForFile(filePath)
        self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.basename(filePath))

    def saveFile(self):
        editor = self.tabWidget.currentWidget()
        if editor:
            editor.saveFile()

    def getCurrentEditorWidget(self):
        """
        Returns the QScintillaEditorWidget instance of the currently active tab.
        """
        # Access the currently active tab using the currentWidget method of QTabWidget
        currentEditor = self.tabWidget.currentWidget()
        return currentEditor

    def saveFileAs(self):
        editorWidget = self.getCurrentEditorWidget()
        if editorWidget:
            success, filePath = editorWidget.saveFileAs()  # Adjusted to capture return values
            if success and filePath:
                # Update the tab title
                filename = os.path.basename(filePath)
                tabIndex = self.tabWidget.currentIndex()
                self.tabWidget.setTabText(tabIndex, filename)
                self.updateRecentFiles(filePath)  # Update the list of recent files

                return True
        return False

    def populateRecentFilesMenu(self):
        self.recentFilesMenu.clear()
        recent_files = load_recent_files()  # Load recent files from registry
        for filePath in recent_files:
            action = self.recentFilesMenu.addAction(os.path.basename(filePath))
            action.triggered.connect(lambda checked, path=filePath: self.openFileAtPath(path))

    def openFileAtPath(self, filePath):
        self.loadFileIntoEditor(filePath)

    def updateRecentFiles(self, filePath):
        recent_files = load_recent_files()
        if filePath in recent_files:
            recent_files.remove(filePath)
        recent_files.insert(0, filePath)
        # Trim the list to the last N files, e.g., 5
        recent_files = recent_files[:5]
        save_recent_files(recent_files)
        self.populateRecentFilesMenu()

    def closeTab(self, index):
        editorWidget = self.tabWidget.widget(index)
        if editorWidget and editorWidget.maybeSave():
            self.tabWidget.removeTab(index)

    def maybeSave(self):
        for i in range(self.tabWidget.count()):
            editorWidget = self.tabWidget.widget(i)
            if editorWidget and not editorWidget.maybeSave():
                return False
        return True

    def closeEvent(self, event):
        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def search(self):
        current_editor = self.getCurrentEditor()
        if current_editor:
            self.searchDialog = SearchDialog(current_editor, self)
            self.searchDialog.show()

    def replace(self):
        current_editor = self.getCurrentEditor()
        if current_editor:
            self.replaceDialog = ReplaceDialog(current_editor, self)
            self.replaceDialog.show()

    def replaceAll(self):
        current_editor = self.getCurrentEditor()
        if current_editor:
            find_text, ok = QInputDialog.getText(self, "Find All Text",
                                                 "Enter the text to find and replace all occurrences:")
            if ok and find_text:
                replace_text, ok = QInputDialog.getText(self, "Replace With", "Enter the replacement text:")
                if ok:
                    # Ensure we search from the beginning
                    current_editor.SendScintilla(current_editor.SCI_DOCUMENTSTART)

                    # The first search to initiate
                    found = current_editor.findFirst(find_text, False, True, False, True)
                    while found:
                        # Replace the found text
                        current_editor.replace(replace_text)
                        # Continue searching from the last match
                        found = current_editor.findNext()
    def getCurrentEditor(self):
        return self.tabWidget.currentWidget().editor if self.tabWidget.currentWidget() else None

    def showAboutDialog(self):
        dialog = AboutDialog(self)
        dialog.show()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About PyEasyEdit")
        self.setFixedSize(400, 300)  # Adjust size as needed
        layout = QVBoxLayout()

        # Display the image
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"current dir: {base_dir}")
        image_path = os.path.join(base_dir, './images/easyedit.png')

        self.imageLabel = QLabel(self)
        pixmap = QPixmap(image_path)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.imageLabel)

        # TextBrowser for displaying link
        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setOpenExternalLinks(True)  # Allow opening links in external browser
        self.textBrowser.setText('''PyEasyEdit - <a href="https://github.com/scottpeterman/pyeasyedit">https://github.com/scottpeterman/pyeasyedit</a>''')
        self.textBrowser.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.textBrowser)

        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    app.setStyle("fusion")
    filePath = sys.argv[1] if len(sys.argv) > 1 else None
    editorWidget = EditorWidget(filePath=filePath)
    editorWidget.show()
    editorWidget.resize(900, 600)
    editorWidget.setWindowTitle("PyEasyEdit")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
