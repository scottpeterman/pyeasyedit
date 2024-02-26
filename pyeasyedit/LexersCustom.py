from PyQt6.Qsci import (
    QsciLexerBash, QsciLexerBatch, QsciLexerJavaScript, QsciLexerJSON,
    QsciLexerYAML, QsciLexerHTML, QsciLexerCSS, QsciLexerSQL,
    QsciLexerPython, QsciLexerXML
)
from PyQt6.QtGui import QColor, QFont

# Define the global color scheme
GLOBAL_COLOR_SCHEME = {
    "Keyword": "#FFC66D",
    "Comment": "#367d36",
    "Operator": "#16d930",
    "ClassName": "#FFEEAD",
    "FunctionMethodName": "#be6ff2",
    "TripleSingleQuotedString": "#479fbf",
    "TripleDoubleQuotedString": "#479fbf",
    "SingleQuotedString": "#479fbf",
    "DoubleQuotedString": "#479fbf",

}

# Base Lexer class for common functionality
class BaseLexerMixin:
    def setupLexer(self, editor, themes):
        self.setDefaultStyles(editor, themes)
        self.applyGlobalColorScheme(editor, GLOBAL_COLOR_SCHEME, themes)

    def setDefaultStyles(self, editor, themes):
        editor.setDefaultColor(QColor(themes["default_color"]))
        editor.setPaper(QColor(themes["paper"]))
        editor.setFont(QFont(themes["font"], themes["font_size"]))

    def applyGlobalColorScheme(self, editor, colorScheme, themes):
        for styleName, color in colorScheme.items():
            styleEnum = getattr(editor, styleName, None)
            if styleEnum is not None:
                editor.setColor(QColor(color), styleEnum)

# ThemeManager class for centralized theme management
class ThemeManager:
    def __init__(self):
        self.themes = {
            "default_color": "#D9D7CE",
            "paper": "#2b2b2b",
            "font": "Consolas",
            "font_size": 10,
        }

    # No longer needs to apply lexers directly, but provides themes
    def getThemes(self):
        return self.themes

class LexerSetupMixin:
    def setupLexer(self, themes, globalColorScheme):
        # Set common default styles
        self.setDefaultColor(QColor(themes["default_color"]))
        self.setPaper(QColor(themes["paper"]))
        self.setFont(QFont(themes["font"], themes["font_size"]))

        # Apply global color scheme
        for styleName, color in globalColorScheme.items():
            styleEnum = getattr(self, styleName, None)
            if styleEnum is not None:
                self.setColor(QColor(color), styleEnum)

class CustomPythonLexer(QsciLexerPython, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)

        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomJSONLexer(QsciLexerJSON, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomJavaScriptLexer(QsciLexerJavaScript,  LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomYAMLLexer(QsciLexerYAML, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomHTMLLexer(QsciLexerHTML, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomCSSLexer(QsciLexerCSS, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomSQLLexer(QsciLexerSQL, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomXMLLexer(QsciLexerXML, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomBashLexer(QsciLexerBash, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)

class CustomBatchLexer(QsciLexerBatch, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, GLOBAL_COLOR_SCHEME)


