# PyEasyEdit

PyEasyEdit is a lightweight, feature-rich text editor built with PyQt6 and QScintilla. Designed to offer a flexible and efficient editing environment, PyEasyEdit supports syntax highlighting for multiple programming languages, file management capabilities, and customizable themes, making it an ideal choice for developers and writers alike.

<div align="center">
  <img src="https://raw.githubusercontent.com/scottpeterman/pyeasyedit/main/screen-shots/main2.png" alt="PyEasyEdit" width="400px"> 
</div>

## Features

- **Syntax Highlighting**: Supports syntax coloring for Python, JavaScript, HTML, CSS, and more, making code easier to read and write.
- **Auto Completion**: Source code auto-completion
- **Code Folding**: Now you can collapse blocks of code
- **Jedi Support**: Auto-completion now includes improved jedi inspection (Python only)
- **Tab to space conversion**: Critical for python
- **File Management**: Open, edit, and save files with an intuitive interface. Recent files are tracked for quick access.
- **Search and Replace**: Powerful search and replace functionality to easily modify your documents.
- **Custom Dialogs**: Includes custom dialogs for searching, replacing, and more, enhancing the user experience.
- **Extensibility**: Designed with extensibility in mind, allowing for additional features and languages to be added.

## Getting Started via Pip

### Create a virtual env for Python:

```bash
md pyeasyedit
cd pyeasyedit
python -m venv venv
venv\Scripts\activate
pip install pyeasyedit
python -m pyeasyedit
```

## Getting Started From Source

### Prerequisites

Before you begin, ensure you have met the following requirements:
- Python 3.9 or later installed on your system.
- PyQt6 and QScintilla libraries installed. You can install these using pip:

  ```bash
  pip install PyQt6 QScintilla
  ```

### Installation

Clone the repository to your local machine:

```bash
git clone git@github.com:scottpeterman/pyeasyedit.git
cd pyeasyedit
pip install -r requirements.txt
```

### Running PyEasyEdit

To start the editor, run the following command from the terminal:

```bash
python -m pyeasyedit 
```

Optionally, you can specify a file to open directly:

```bash
python -m pyeasyedit /path/to/your/file.txt
```

## Usage

- **File Menu**: Use the File menu to open, save, or create new documents.
- **Edit Menu**: Access search and replace functions through the Edit menu.
- **Help Menu**: Contains the About dialog that provides information about the editor and a link to the project's GitHub page.


## License

PyEasyEdit is released under the GPLv3 License. See the LICENSE file for more information.

## Acknowledgments

- Special thanks to the PyQt and QScintilla teams for providing the powerful libraries that made this project possible.
- Learn more about PyQt and Qt at [Riverbank Computing](https://www.riverbankcomputing.com/) and [Qt Group](https://www.qt.io/), respectively.

```python
# Create a source distribution and a wheel, upload to pypi
python setup.py sdist bdist_wheel
twine upload dist/* 