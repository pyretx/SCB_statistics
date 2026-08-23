# Register SCB Statistics (Streamlit app.py on http://localhost:8501) as a per-user scheduled task:
# starts hidden at logon, restarts itself if it dies. No admin needed. Re-running replaces the task.
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -Uninstall
param([switch]$Uninstall)
$ErrorActionPreference = 'Stop'
$name = 'SCBStatistics'
$root = $PSScriptRoot
if ($Uninstall) {
  Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
  Write-Host "Removed scheduled task $name"
  exit 0
}
$vbs = Join-Path $root 'run_hidden.vbs'
if (-not (Test-Path $vbs)) { throw "Missing $vbs" }
if (-not (Test-Path (Join-Path $root '.venv\Scripts\python.exe'))) { throw "Missing .venv - create it first (uv venv / python -m venv .venv; pip install -r requirements.txt)" }
$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument "//B //Nologo `"$vbs`"" -WorkingDirectory $root
# at logon + every 5 minutes as self-heal (IgnoreNew: does nothing while the app is running)
$t1 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$t2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 3650)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
  -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -Hidden
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger @($t1, $t2) -Settings $settings -Principal $principal `
  -Description 'SCB Statistics / Salary Explorer - local Streamlit app (http://localhost:8501), hidden, autostart at logon' -Force | Out-Null
Write-Host "Registered scheduled task '$name' (at logon, user $env:USERNAME, hidden)."
Write-Host "Start now:   Start-ScheduledTask -TaskName $name"
Write-Host "Status:      Get-ScheduledTask -TaskName $name | Get-ScheduledTaskInfo"
Write-Host "Stop:        Disable-ScheduledTask -TaskName $name; Stop-ScheduledTask -TaskName $name   (plain Stop comes back within 5 min)"
Write-Host "Log:         $root\logs\svc_app.log"
Write-Host "App:         http://localhost:8501"
