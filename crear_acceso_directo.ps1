$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\Users\Usuario\OneDrive\Desktop\Informes Instantaneos.lnk")
$Shortcut.TargetPath = "C:\Users\Usuario\OneDrive\Desktop\INFORMES\INICIAR_APP.bat"
$Shortcut.WorkingDirectory = "C:\Users\Usuario\OneDrive\Desktop\INFORMES"
$Shortcut.Description = "Iniciar Informes Instantaneos - Policia de Tucuman"
$Shortcut.WindowStyle = 1
$Shortcut.Save()
Write-Host "Acceso directo creado en el Escritorio"
