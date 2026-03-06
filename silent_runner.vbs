Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "d:\CIS\deal_flow_engine"
' The "0" means run completely invisibly in the background
WshShell.Run "cmd /c python run.py --schedule", 0, False
