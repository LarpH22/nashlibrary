Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Check if we need to elevate privileges
objShell.Run "net start MySQL80", 0, True
