from setuptools import setup, find_packages

setup(
    name="pyeasyedit",
    version="0.1.2",
    description="A PyQt6 multi-tabbed editor based on QScintilla",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    author="Scott Peterman",
    author_email="scottpeterman@gmail.com",
    url="https://github.com/scottpeterman/pyeasyedit",
    license="GPLv3",
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt6>=6.6.1",
        "PyQt6-Qt6>=6.6.2",
        "PyQt6-sip>=13.6.0",
        "PyQt6-QScintilla>=2.14.1",

    ],
    entry_points={
        "console_scripts": [
            "pyeasyedit = pyeasyedit.__main__:main"
        ],
    },
)
