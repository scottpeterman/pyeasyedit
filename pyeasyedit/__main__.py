import sys
import jedi
from PyQt6.QtWidgets import QApplication, QTabWidget, QInputDialog, QMenuBar, QLabel, QLineEdit, QPushButton, QDialog, \
    QMenu, QTextBrowser
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QRunnable, QThreadPool, QObject, pyqtSlot, QTimer
from PyQt6.QtGui import QAction, QShortcut, QKeySequence, QPixmap, QKeyEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QFileDialog
from PyQt6.Qsci import QsciScintilla, QsciAPIs
from pyeasyedit.LexersCustom import *
from pyeasyedit.pyeasylib import AboutDialog, get_config_directory, get_imported_modules, LEXER_MAP_MENU, load_recent_files, \
    save_recent_files, HotkeysDialog, SearchDialog, ReplaceDialog


class CustomQsciScintilla(QsciScintilla):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentListItem = ""
        self.currentListIndex = -1  # Default to -1 indicating no selection
        self.userListActivated.connect(self.onUserListActivated)


    def onUserListActivated(self, index, text):
        self.currentListItem = text
        self.currentListIndex = index

        # Get the cursor position
        line, column = self.getCursorPosition()
        pos = self.positionFromLineIndex(line, column)

        # Find the position of the last period before the cursor
        last_period_pos = self.SendScintilla(self.SCI_POSITIONBEFORE, pos)
        while last_period_pos > 0 and chr(self.SendScintilla(self.SCI_GETCHARAT, last_period_pos)) != '.':
            last_period_pos = self.SendScintilla(self.SCI_POSITIONBEFORE, last_period_pos)

        # Check if the last character is a period and adjust the position
        if last_period_pos >= 0 and chr(self.SendScintilla(self.SCI_GETCHARAT, last_period_pos)) == '.':
            last_period_pos += 1

        # Set the selection and replace the text
        self.SendScintilla(self.SCI_SETSEL, last_period_pos, pos)
        self.SendScintilla(self.SCI_REPLACESEL, 0, text.encode())

        # Correctly position the cursor after insertion
        new_pos = last_period_pos + len(text)
        new_line, new_index = self.lineIndexFromPosition(new_pos)
        self.setCursorPosition(new_line, new_index)

        print(f"List Activated: {text} at index {index}, replaced from {last_period_pos} to {column}")

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if self.isListActive():
            if event.key() in [Qt.Key.Key_Tab, Qt.Key.Key_Return]:
                if self.currentListItem:
                    self.insert(self.currentListItem)
                    self.SendScintilla(self.SCI_CANCEL)
                    new_line, new_index = self.getCursorPosition()
                    self.setCursorPosition(new_line, new_index + len(self.currentListItem))
                    event.accept()
                    return

        if event.text() == '.':
            QTimer.singleShot(100, self.triggerJediCompletion)  # Delay fetching completions

    def triggerJediCompletion(self):
        code = self.text()
        cursor_line, cursor_column = self.getCursorPosition()
        cursor_line += 1  # Adjust for Jedi's 1-indexed lines
        try:
            script = jedi.Script(code=code, path=self.AContainer.filePath, environment=self.jedi_environment)
            completions = script.complete(line=cursor_line, column=cursor_column)
            if completions:
                self.AContainer.itemList = [comp.name for comp in completions]
                self.showUserList(1, self.AContainer.itemList)
        except Exception as e:
            print(f"Error fetching completions: {e}")


class QScintillaEditorWidget(QWidget):
    fileSaved = pyqtSignal(str)
    showUserListSignal = pyqtSignal(int, list)  # Define a signal


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
        self.itemList = []
        self.setupUi()
        self.showUserListSignal.connect(self.showUserList)  # Connect signal to slot

    def showUserList(self):
        print("Attempting to show user list...")
        itemList = self.itemList
        if self.editor:
            lexer = self.editor.lexer()
            if lexer:
                print(f"Using lexer: {str(lexer)}")
                api = QsciAPIs(lexer)
                api.clear()
                for word in itemList:
                    api.add(word)
                api.prepare()
                self.editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)

            # Set auto-completion settings to always show the list
            self.editor.setAutoCompletionUseSingle(
                QsciScintilla.AutoCompletionUseSingle.AcusNever)  # Important change here
            self.editor.setAutoCompletionCaseSensitivity(True)
            self.editor.setAutoCompletionReplaceWord(True)
            self.editor.setAutoCompletionThreshold(1)  # Adjust if needed
            self.editor.setAutoCompletionWordSeparators(['.'])  # Trigger on dot

            print("Auto-completion list prepared and should appear based on threshold settings.")


    def setupUi(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Initialize the QScintilla editor
        self.editor = CustomQsciScintilla()
        layout.addWidget(self.editor)

        # Editor font
        font = QFont("Consolas", 10)
        self.editor.setFont(font)

        # Enable line numbers in the left margin
        self.editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.editor.setMarginWidth(0, "0000")  # Adjust the number as needed
        self.applyTheme()
        self.saveShortcut = QShortcut(QKeySequence("Ctrl+S"), self.editor)
        self.saveShortcut.activated.connect(self.saveFile)
        self.configureFolding()  # Setup folding for the editor
        self.completionShortcut = QShortcut(QKeySequence('Ctrl+Space'), self.editor)
        self.completionShortcut.activated.connect(self.triggerCompletion)

    def triggerCompletion(self):
        # if not self.editor.isListActive():
        print("trigger here")
        for item in self.itemList:
            print(item)
        self.editor.showUserList(1, self.itemList)

    def configureFolding(self):
        # Assuming Python lexer, but you might want to set this dynamically
        lexer = QsciLexerPython(self.editor)
        self.editor.setLexer(lexer)

        # Enable folding
        self.editor.setFolding(QsciScintilla.FoldStyle.BoxedTreeFoldStyle)

        # Set the colors for the fold margin
        self.editor.setFoldMarginColors(QColor("#99CC66"), QColor("#CCFF99"))

        # Configure the margin for folding symbols
        self.editor.setMarginType(2, QsciScintilla.MarginType.SymbolMargin)
        self.editor.setMarginWidth(2, "12")
        self.editor.setMarginSensitivity(2, True)

        # Define markers using the correct constants from your list of available symbols
        self.editor.markerDefine(QsciScintilla.MarkerSymbol.BoxedMinus, QsciScintilla.SC_MARKNUM_FOLDEROPEN)
        self.editor.markerDefine(QsciScintilla.MarkerSymbol.BoxedPlus, QsciScintilla.SC_MARKNUM_FOLDER)
        self.editor.markerDefine(QsciScintilla.MarkerSymbol.BoxedMinusConnected, QsciScintilla.SC_MARKNUM_FOLDEROPENMID)
        self.editor.markerDefine(QsciScintilla.MarkerSymbol.BoxedPlusConnected, QsciScintilla.SC_MARKNUM_FOLDEREND)
        self.editor.markerDefine(QsciScintilla.MarkerSymbol.VerticalLine, QsciScintilla.SC_MARKNUM_FOLDERSUB)
        self.editor.markerDefine(QsciScintilla.MarkerSymbol.BoxedMinusConnected, QsciScintilla.SC_MARKNUM_FOLDERMIDTAIL)
        self.editor.markerDefine(QsciScintilla.MarkerSymbol.BoxedPlusConnected, QsciScintilla.SC_MARKNUM_FOLDERTAIL)

        # Connect the fold margin click event to the handler
        self.editor.marginClicked.connect(self.onMarginClicked)
        # Set the colors for the margin (where line numbers are displayed)
        self.editor.setMarginsForegroundColor(QColor("#CCCCCC"))  # Light grey color for text
        self.editor.setMarginsBackgroundColor(QColor("#333333"))  # Dark grey color for the background

        # Additional settings that you might want to configure for dark mode
        self.editor.setFoldMarginColors(QColor("#555555"), QColor("#333333"))  # Adjust fold margin colors
        self.editor.setCaretForegroundColor(QColor("#FFFFFF"))  # Color for the caret
        self.editor.setCaretLineBackgroundColor(QColor("#555555"))  # Color for the current line highlight

    def onMarginClicked(self, nmargin, nline, modifiers):
        # Check if the clicked margin is the fold margin (number 2 in this setup)
        if nmargin == 2:
            # Toggle the fold state if the clicked line is foldable (has a fold point)
            if self.editor.foldingAt(nline):
                self.editor.toggleFold(nline)

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

        # Connect the fold margin click event to the handler
        self.editor.marginClicked.connect(self.onMarginClicked)
        # Set the colors for the margin (where line numbers are displayed)
        self.editor.setMarginsForegroundColor(QColor("#CCCCCC"))  # Light grey color for text
        self.editor.setMarginsBackgroundColor(QColor("#333333"))  # Dark grey color for the background

        # Additional settings that you might want to configure for dark mode
        self.editor.setFoldMarginColors(QColor("#555555"), QColor("#333333"))  # Adjust fold margin colors
        self.editor.setCaretForegroundColor(QColor("#FFFFFF"))  # Color for the caret
        self.editor.setCaretLineBackgroundColor(QColor("#555555"))  # Color for the current line highlight

        lexer = self.editor.lexer()
        if lexer:  # Make sure there is a lexer set
            # Set default text color (foreground)
            lexer.setDefaultColor(QColor("#CCCCCC"))
            # Set default paper color (background)
            lexer.setDefaultPaper(QColor("#2b2b2b"))
            # Set default font
            lexer.setDefaultFont(QFont("Consolas", 10))


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
            success = self._saveToFile(self.current_file_path)
            if success:
                self.fileSaved.emit(self.current_file_path)  # Ensure this is emitted
            return success, self.current_file_path
        else:
            return self.saveFileAs()  # This should handle new files

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
            return False, filePath

    def saveFileAs(self, filePath=None):
        try:
            if not filePath:
                filePath, _ = QFileDialog.getSaveFileName(self, "Save File As", self.defaultFolderPath, "All Files (*)")
            if filePath:
                success = self._saveToFile(filePath)
                if success:
                    self.current_file_path = filePath
                    self.editor.setModified(False)
                    self.fileSaved.emit(filePath)  # Ensure this is emitted, it updates the tab title
                    return True, filePath
        except Exception as e:
            QMessageBox.critical(self, "Error Saving File", "An error occurred while saving the file:\n" + str(e))
            return False, filePath
        return False





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

        # Syntax highlighting submenu
        syntaxMenu = QMenu("Syntax", self)
        viewMenu.addMenu(syntaxMenu)

        # Populate the syntax menu with lexer options
        for name, lexer_class in LEXER_MAP_MENU.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, lx=lexer_class: self.changeLexer(lx))
            syntaxMenu.addAction(action)

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

    def populateRecentFilesMenu(self):
        self.recentFilesMenu.clear()
        recent_files = load_recent_files()
        for filePath in recent_files:
            action = QAction(os.path.basename(filePath), self)
            action.triggered.connect(lambda checked, path=filePath: self.openFileAtPath(path))
            self.recentFilesMenu.addAction(action)

    def changeLexer(self, lexer_class):
        current_editor_widget = self.getCurrentEditorWidget()
        if current_editor_widget:
            current_editor = current_editor_widget.editor
            # Set the new lexer
            lexer = lexer_class(parent=current_editor)
            current_editor.setLexer(lexer)

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
        editorWidget.fileSaved.connect(self.updateTabText)  # This connection should handle both Save and Save As

        editor = editorWidget.editor
        editor.AContainer = editorWidget
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
        # Check if the Jedi environment is configured
        if not hasattr(editor, 'jedi_environment') or editor.jedi_environment is None:
            print("Jedi environment is not configured.")
            return  # Early exit if Jedi not configured

        # Retrieve code and cursor position from the editor
        code = editor.text()
        cursor_line, cursor_column = editor.getCursorPosition()
        cursor_line += 1  # Adjust for Jedi's 1-indexed lines

        # Identify modules to preload based on current imports in the file
        preload_list = get_imported_modules(code)

        # Preloading modules using jedi.preload_module
        for module in preload_list:
            try:
                jedi.preload_module(module)
            except Exception as e:
                print(f"Error preloading module {module}: {e}")

        # Using Jedi to get completions directly
        try:
            script = jedi.Script(
                code=code, path=editor.AContainer.filePath,
                environment=editor.jedi_environment
            )
            completions = script.complete(line=cursor_line, column=cursor_column)
            completion_words = [comp.name for comp in completions]

            editor.AContainer.itemList = completion_words  # Update editor completion list

        except Exception as e:
            print(f"An error occurred while fetching completions: {e}")

    def handleCompletionsFetched(self, result):
        self.completionResult = result  # Corrected attribute name for storing the result
        print("handleCompletionsFetched")
        editor = self.active_editor
        if not editor:
            print("Editor is not initialized!")
            return
        editor.AContainer.showUserListSignal.emit(1, result)  # Use the correct userListId if needed


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
            #backlink
            editorWidget.editor.AContainer = editorWidget
            # Enable auto-completion
            editorWidget.editor.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAll)
            editorWidget.editor.setAutoCompletionThreshold(1)  # Start autocompletion after 1 character

            # Enable auto-indent
            editorWidget.editor.setAutoIndent(True)

            # Set indentation width
            editorWidget.editor.setIndentationWidth(4)
            editorWidget.filePath = filePath
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
        self.handle_text_changed(editorWidget.editor)
        self.tabWidget.setTabText(self.tabWidget.currentIndex(), os.path.basename(filePath))

    def saveFile(self):
        editorWidget = self.getCurrentEditorWidget()  # Ensure you are retrieving the editor widget
        if editorWidget:
            success, filePath = editorWidget.saveFile()  # Assuming saveFile returns a success flag and the file path
            if success:
                self.updateRecentFiles(filePath)  # Update the recent files list with the new path

    def getCurrentEditorWidget(self):
        """
        Returns the QScintillaEditorWidget instance of the currently active tab.
        """
        # Access the currently active tab using the currentWidget method of QTabWidget
        currentEditor = self.tabWidget.currentWidget()
        return currentEditor

    def saveFileAs(self):
        try:
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
        except Exception as e:
            print(e)
        return False


        # self.recentFilesMenu.clear()
        # recent_files = load_recent_files()  # Load recent files from registry
        # for filePath in recent_files:
        #     action = self.recentFilesMenu.addAction(os.path.basename(filePath))
        #     action.triggered.connect(lambda checked, path=filePath: self.openFileAtPath(path))

    def openFileAtPath(self, filePath):
        self.loadFileIntoEditor(filePath)

    def updateRecentFiles(self, filePath, remove=False):
        recent_files = load_recent_files()
        if remove and filePath in recent_files:
            recent_files.remove(filePath)
        elif filePath not in recent_files:
            recent_files.insert(0, filePath)
            recent_files = recent_files[:10]
        save_recent_files(recent_files)
        self.populateRecentFilesMenu()

    def closeTab(self, index):
        editorWidget = self.tabWidget.widget(index)
        if editorWidget and editorWidget.maybeSave():
            # Consider removing the file path from recent files if necessary
            recent_files = load_recent_files()
            if editorWidget.current_file_path in recent_files:
                # recent_files.remove(editorWidget.current_file_path)
                save_recent_files(recent_files)
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
