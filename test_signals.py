import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import QRunnable, QObject, pyqtSignal, QThreadPool, QTimer

# Signal Emitter Object
class SignalEmitter(QObject):
    completionsFetched = pyqtSignal(str)

# Worker Runnable
class CompletionWorker(QRunnable):
    def __init__(self, code, signalEmitter):
        super().__init__()
        self.code = code
        self.signalEmitter = signalEmitter

    def run(self):
        # Simulate some processing
        completion = f"Completions for: {self.code}"
        # Emit signal via the signalEmitter
        self.signalEmitter.completionsFetched.emit(completion)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Signal-Slot Example with Debounce")

        layout = QVBoxLayout()
        self.editor = QTextEdit()
        layout.addWidget(self.editor)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.threadPool = QThreadPool()
        self.debounceTimer = QTimer()
        self.debounceTimer.setSingleShot(True)
        self.debounceTimer.timeout.connect(self.processText)
        self.editor.textChanged.connect(self.debounceTextChanged)

        # Initialize the SignalEmitter
        self.signalEmitter = SignalEmitter()
        self.signalEmitter.completionsFetched.connect(self.onCompletionsFetched)

    def debounceTextChanged(self):
        self.debounceTimer.start(500)  # Adjust debounce time as needed

    def processText(self):
        code = self.editor.toPlainText()
        worker = CompletionWorker(code=code, signalEmitter=self.signalEmitter)
        self.threadPool.start(worker)

    def onCompletionsFetched(self, completions):
        print("Completions fetched:", completions)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
