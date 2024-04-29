import json
import os
import re

from PyQt6.QtCore import Qt, QObject, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextBrowser, QPushButton, QLineEdit, QMessageBox
from pyeasyedit.LexersCustom import *


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


def get_imported_modules(code):
    """
    Extracts all imported module names from the given code using regex.
    """
    module_names = set()
    # Regex to find simple imports and from-imports
    imports = re.findall(r'^\s*import\s+(\S+)|^\s*from\s+(\S+)\s+import', code, re.MULTILINE)
    for imp in imports:
        # Add both groups (import and from-import cases)
        module_names.update([i for i in imp if i])
    return list(module_names)


LEXER_MAP_MENU = {
    "Python": CustomPythonLexer,
    "JSON": CustomJSONLexer,
    "JavaScript": CustomJavaScriptLexer,
    "YAML": CustomYAMLLexer,
    "HTML": CustomHTMLLexer,
    "CSS": CustomCSSLexer,
    "SQL": CustomSQLLexer,
    "XML": CustomXMLLexer,
    "Bash": CustomBashLexer,
    "Batch": CustomBatchLexer
}

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

def save_recent_files(file_list, max_files=5):
    config_directory = get_config_directory()
    config_path = os.path.join(config_directory, "config.json")
    data = {"recent_files": file_list[:max_files]}  # Store only the most recent entries
    with open(config_path, "w") as config_file:
        json.dump(data, config_file)


def load_recent_files():
    config_directory = get_config_directory()
    config_path = os.path.join(config_directory, "config.json")
    try:
        with open(config_path, "r") as config_file:
            data = json.load(config_file)
        return data.get("recent_files", [])
    except FileNotFoundError:
        return []

def get_config_directory():
    home = os.path.expanduser("~")  # Gets the user's home directory universally
    config_directory = os.path.join(home, ".pyeasyedit")
    if not os.path.exists(config_directory):
        os.makedirs(config_directory)  # Create the directory if it doesn't exist
    return config_directory

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
