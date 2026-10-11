# Start Angel Attack: the local server in one window; the character bridge goes in another once it exists.
#   .\start.ps1             carry on in the existing world
#   .\start.ps1 -NewWorld   start again from the beginning (the old world is deleted)
param([switch]$NewWorld)

$root = $PSScriptRoot
$python = "D:\voice-assistant\.venv\Scripts\python.exe"

$serverArgs = @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$root\tools\server.ps1")
if ($NewWorld) { $serverArgs += "-NewWorld" }
Start-Process powershell -ArgumentList $serverArgs

Write-Host "Waiting for the server..."
$deadline = (Get-Date).AddMinutes(5)
do {
    Start-Sleep -Seconds 2
    & $python -I "$root\tools\rcon.py" "list" 2>$null | Out-Null
    if ((Get-Date) -gt $deadline) { throw "The server did not answer over RCON within 5 minutes. See its window." }
} until ($LASTEXITCODE -eq 0)

# TODO(characters_bridge): start the character bridge here once characters_bridge\bridge.py exists, e.g.
#   Start-Process powershell -ArgumentList @("-NoExit", "-Command", "& '$python' '$root\characters_bridge\bridge.py'")

Write-Host ""
Write-Host "Ready. In the Minecraft launcher choose the 'Angel Attack' profile and press Play,"
Write-Host "then Multiplayer -> Angel Attack."
