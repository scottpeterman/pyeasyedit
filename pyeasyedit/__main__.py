import sys
import os
import winreg as reg

from PyQt6.QtWidgets import QApplication, QTabWidget, QInputDialog, QMenuBar, QLabel, QLineEdit, QPushButton, QDialog, \
    QMenu, QTextBrowser
from PyQt6.QtCore import Qt
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


class EditorWidget(QWidget):
    def __init__(self, filePath=None, parent=None):
        super().__init__(parent)
        self.setupUi()
        if filePath and os.path.isfile(filePath):
            self.newTab(filePath)

    def setupUi(self):
        self.layout = QVBoxLayout(self)
        self.menuBar = QMenuBar()
        self.layout.setMenuBar(self.menuBar)  # Add the menu bar to the layout

        # File menu
        fileMenu = self.menuBar.addMenu("&File")
        newAction = QAction("&New", self)
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
        closeTabAction.triggered.connect(lambda: self.closeTab(self.tabWidget.currentIndex()))
        fileMenu.addAction(closeTabAction)

        # Edit menu
        editMenu = self.menuBar.addMenu("&Edit")
        searchAction = QAction("&Search", self)
        searchAction.triggered.connect(self.search)
        editMenu.addAction(searchAction)

        replaceAction = QAction("&Replace", self)
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
        # file_list = load_recent_files()
        self.populateRecentFilesMenu()
        # self.setMinimumSize(QSize(800, 600))

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
        tabIndex = self.tabWidget.addTab(editorWidget, "Untitled")
        self.tabWidget.setCurrentIndex(tabIndex)
        if filePath:
            self.loadFileIntoEditor(filePath, editorWidget)

    def openFile(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Open File", self.defaultFolderPath(), "All Files (*)")
        if filePath:
            # Check if the file is already open
            for i in range(self.tabWidget.count()):
                editorWidget = self.tabWidget.widget(i)
                if editorWidget.current_file_path == filePath:
                    self.tabWidget.setCurrentIndex(i)
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
            tabIndex = self.tabWidget.addTab(editorWidget, os.path.basename(filePath))
            self.tabWidget.setCurrentIndex(tabIndex)
        with open(filePath, 'r') as file:
            content = file.read()
        editorWidget.editor.setText(content)
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
        # Your existing code to open a file, refactored if necessary...
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
        current_dir = os.path.dirname(__file__)
        print(f"current dir: {current_dir}")
        image_path = os.path.join(current_dir, 'images', 'easyedit.png')
        imagePath = os.path.join(os.path.dirname(__file__), image_path)  # Adjust path as needed
        self.imageLabel = QLabel(self)
        pixmap = QPixmap(imagePath)
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
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
