' Launch SCB Statistics (Streamlit) with NO console window (used by the scheduled task "SCBStatistics").
' Waits for the server to exit so Task Scheduler shows the task as "running" while the app is alive
' (MultipleInstances=IgnoreNew then keeps the 5-minute self-heal trigger from starting a second copy).
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = root
rc = sh.Run("cmd.exe /c """ & root & "\run_service.bat""", 0, True)
WScript.Quit rc
