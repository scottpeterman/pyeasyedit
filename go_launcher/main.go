package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: launcher <file_path>")
		os.Exit(1)
	}
	// Get the file path from command line arguments.
	filePath := os.Args[1]

	// Resolve the absolute path of the file.
	absPath, err := filepath.Abs(filePath)
	if err != nil {
		fmt.Printf("Error resolving file path: %s\n", err)
		os.Exit(1)
	}

	// Set the Python virtual environment path and the pyeasyedit home directory.
	homeDir := filepath.Join(os.Getenv("USERPROFILE"), "pyeasyedit")
	pythonwPath := filepath.Join(homeDir, "venv", "Scripts", "pythonw.exe")

	// Change the working directory to the pyeasyedit home directory.
	err = os.Chdir(homeDir)
	if err != nil {
		fmt.Printf("Error changing directory: %s\n", err)
		os.Exit(1)
	}

	// Start the pythonw command with the module and file path.
	cmd := exec.Command(pythonwPath, "-m", "pyeasyedit", absPath)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	// Start the command without waiting for it to finish.
	err = cmd.Start()
	if err != nil {
		fmt.Printf("Error starting pyeasyedit module: %s\n", err)
		os.Exit(1)
	}

	// At this point, the Go program can exit, and the pythonw process will continue.
	fmt.Println("pyeasyedit launched successfully.")
}
