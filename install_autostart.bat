@echo off
echo Installing Vani to Windows Startup...
set "TARGET=%~dp0main.py"
:: Use a VBScript to create a silent shortcut in the Startup folder
set "VBS_SCRIPT=%TEMP%\create_vani_shortcut.vbs"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sLinkFile = "%STARTUP_DIR%\Vani Assistant.lnk" >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT%"
:: We want to run it via pythonw so no console pops up, but 'main.py' uses python.
:: We will just run standard python for now.
echo oLink.TargetPath = "pythonw.exe" >> "%VBS_SCRIPT%"
echo oLink.Arguments = """" ^& "%TARGET%" ^& """" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%~dp0" >> "%VBS_SCRIPT%"
echo oLink.Description = "Vani AI Assistant" >> "%VBS_SCRIPT%"
:: Run minimized (7 = Minimized, 1 = Normal)
echo oLink.WindowStyle = 7 >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

cscript /nologo "%VBS_SCRIPT%"
del "%VBS_SCRIPT%"

echo.
echo Success! Vani will now start automatically in the background whenever you boot your PC.
echo.
pause
