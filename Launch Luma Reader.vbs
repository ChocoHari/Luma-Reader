Option Explicit
Dim shell, files, root, python, script
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
root = files.GetParentFolderName(WScript.ScriptFullName)
python = files.BuildPath(root, ".venv313\Scripts\pythonw.exe")
If Not files.FileExists(python) Then python = files.BuildPath(root, ".venv\Scripts\pythonw.exe")
script = files.BuildPath(root, "app.py")
If Not files.FileExists(python) Then
    MsgBox "Run Setup.ps1 first to install the reader's local environment.", 48, "Luma Reader"
    WScript.Quit 1
End If
shell.CurrentDirectory = root
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & script & Chr(34), 0, False
