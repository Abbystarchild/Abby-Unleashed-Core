' Abby Unleashed - Silent Launcher
' Runs the server without showing a command window
' Double-click to start, use Task Manager to stop

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "cmd /c start_abby.bat", 0, False
