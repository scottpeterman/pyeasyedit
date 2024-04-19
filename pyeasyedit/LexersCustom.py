from PyQt6.Qsci import (
    QsciLexerBash, QsciLexerBatch, QsciLexerJavaScript, QsciLexerJSON,
    QsciLexerYAML, QsciLexerHTML, QsciLexerCSS, QsciLexerSQL,
    QsciLexerPython, QsciLexerXML
)
from PyQt6.QtGui import QColor, QFont
import os


# Define the global color scheme
GLOBAL_COLOR_SCHEME = {
    "Keyword": "#f5ec40",  # Brighter yellow
    "Comment": "#6C9E6E",  # Lighter green
    "Operator": "#55FF75",  # Brighter green
    "ClassName": "#FFF0AC",  # Brighter cream
    "FunctionMethodName": "#e1a1ff",  # Lighter purple
    "TripleSingleQuotedString": "#6AB0CF",  # Lighter blue-green
    "TripleDoubleQuotedString": "#6AB0CF",  # Lighter blue-green
    "SingleQuotedString": "#6AB0CF",  # Lighter blue-green
    "DoubleQuotedString": "#6AB0CF",  # Lighter blue-green
}
HTML_JS_DARK_COLOR_SCHEME = {
    # HTML styles
    "Default": "#c8c8c8",
    "Tag": "#f5ec40",
    "UnknownTag": "#ff6347",
    "Attribute": "#ffd700",
    "UnknownAttribute": "#ff6347",
    "HTMLNumber": "#dcdcaa",
    "HTMLDoubleQuotedString": "#ce9178",
    "HTMLSingleQuotedString": "#ce9178",
    "OtherInTag": "#d7ba7d",
    "HTMLComment": "#608b4e",
    "Entity": "#569cd6",
    # JavaScript styles
    "JavaScriptDefault": "#dcdcaa",
    "JavaScriptComment": "#608b4e",
    "JavaScriptCommentDoc": "#608b4e",
    "JavaScriptCommentLine": "#608b4e",
    "JavaScriptNumber": "#b5cea8",
    "JavaScriptWord": "#569cd6",
    "JavaScriptKeyword": "#c586c0",
    "JavaScriptDoubleQuotedString": "#ce9178",
    "JavaScriptSingleQuotedString": "#ce9178",
    "JavaScriptSymbol": "#dcdcaa",
    "JavaScriptUnclosedString": "#ce9178",
    "JavaScriptRegex": "#d16969",
    # ... other styles as needed
}

JAVASCRIPT_DARK_COLOR_SCHEME = {
    "Default": "#D4D4D4",  # Light grey for default text
    "Comment": "#57A64A",  # Green for comments
    "CommentDoc": "#57A64A",  # Green for documentation comments
    "CommentLine": "#57A64A",  # Green for line comments
    "CommentLineDoc": "#57A64A",  # Green for line doc comments
    "Keyword": "#f08e1f",  # orange for keywords
    "Number": "#B5CEA8",  # Light green for numbers
    "Operator": "#f5de0c",  # Grey for operators
    "Regex": "#D16969",  # Red for regular expressions
    "Identifier": "#ffffff",  # Light blue for identifiers
    "GlobalClass": "#4EC9B0",  # Turquoise for global classes
    # ... other styles as needed
    # Inactive styles are used when a part of the text is out of focus or inactive.
    # You can set them to a slightly dimmed color compared to the active ones.
    "InactiveDefault": "#808080",  # Dimmed grey
    "InactiveComment": "#408040",  # Dimmed green
    "InactiveKeyword": "#3A6DA2",  # Dimmed blue
    "DoubleQuotedString": "#f08e1f",  # Orange for double-quoted strings
    "SingleQuotedString": "#f08e1f",  # Orange for single-quoted strings

    # ... and so on for inactive styles
}


CUSTOM_JSON_COLOR_SCHEME = {
    "Default": "#ffffff",  # white
    "Number": "#ff4500",  # orange red
    "String": "#ffa500",  # orange
    "UnclosedString": "#ff6347",  # tomato
    "Property": "#1e90ff",  # dodger blue
    "EscapeSequence": "#20b2aa",  # light sea green
    "LineComment": "#008000",  # green
    "BlockComment": "#008000",  # green (same as line comment for consistency)
    "Operator": "#b22222",  # firebrick
    "IRI": "#4b0082",  # indigo
    "JSON-LDCompactIRI": "#da70d6",  # orchid
    "JSONKeyword": "#0000cd",  # medium blue
    "JSON-LDKeyword": "#b03060",  # maroon
    "ParsingError": "#ff0000"  # red
}


CUSTOM_YAML_COLOR_SCHEME = {
    "Default": "#dcdcdc",  # Light gray
    "Comment": "#00ff00",  # Bright green
    "Identifier": "#1e90ff",  # Dodger blue
    "Keyword": "#ff4500",  # Orange red
    "Number": "#ff6347",  # Tomato
    "Reference": "#4682b4",  # Steel blue
    "DocumentDelimiter": "#ffffff",  # White
    "TextBlockMarker": "#8a2be2",  # Blue violet
    "SyntaxErrorMarker": "#ff0000",  # Red
    "Operator": "#b22222"  # Firebrick
}


def print_lexer_styles(lexer):
    inst_lexer = lexer()
    print(dir(inst_lexer))

    for style_id in range(128):  # 128 is a safe upper limit for style IDs
        description = inst_lexer.description(style_id)

        lexer_style_color = inst_lexer.color(style_id)
        lexer_style_name = description.replace(" ","")
        if description:
            print(f"Style ID {style_id}: {lexer_style_name} : {lexer_style_color.name()}")


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
                # print(f"Applying color {color} to style {styleName}")
                self.setColor(QColor(color), styleEnum)
            else:
                print(f"Style {styleName} not found in lexer.")

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
        # print_lexer_styles(QsciLexerJSON)
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, CUSTOM_JSON_COLOR_SCHEME)


class CustomJavaScriptLexer(QsciLexerJavaScript,  LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        jsl = QsciLexerJavaScript()
        print(dir(jsl))
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, JAVASCRIPT_DARK_COLOR_SCHEME)

class CustomYAMLLexer(QsciLexerYAML, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        print_lexer_styles(QsciLexerYAML)
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, CUSTOM_YAML_COLOR_SCHEME)

class CustomHTMLLexer(QsciLexerHTML, LexerSetupMixin):
    def __init__(self, parent=None, themes=None):
        super().__init__(parent)
        # print_lexer_styles(QsciLexerHTML)
        # Assuming themes and GLOBAL_COLOR_SCHEME are available
        if themes is None:
            themes = ThemeManager().getThemes()
        # Use the mixin's method to setup the lexer
        self.setupLexer(themes, HTML_JS_DARK_COLOR_SCHEME)

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


