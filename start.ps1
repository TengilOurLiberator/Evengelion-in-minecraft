# Start Angel Attack: the local server in one window, the world placed if it is new, the voice bridge in another.
#   .\start.ps1                       carry on in the existing world
#   .\start.ps1 -NewWorld             start again from the beginning (the old world and the characters' memory are deleted)
#   .\start.ps1 -Text                 type to the characters instead of talking (the bridge's text mode, against the live server)
#   .\start.ps1 -Output Oculus        the speakers, by name part or index (the bridge's --output); default: the Windows default
#   .\start.ps1 -AutoStart            once a player has joined, send `function angel:story/start`
#   .\start.ps1 -NoBridge             the server only
param([switch]$NewWorld, [switch]$Text, [string]$Output, [switch]$AutoStart, [switch]$NoBridge)

$root = $PSScriptRoot
$python = "D:\voice-assistant\.venv\Scripts\python.exe"
$rcon = Join-Path $root "tools\rcon.py"
$srv = Join-Path $root "server"
$latest = Join-Path $srv "logs\latest.log"

# the server's settings (read only: the port, the world's folder name)
$props = @{}
foreach ($line in [System.IO.File]::ReadAllLines((Join-Path $srv "server.properties"))) {
    if ($line -match '^([^#=]+)=(.*)$') { $props[$matches[1].Trim()] = $matches[2].Trim() }
}
$port = if ($props.ContainsKey("server-port")) { $props["server-port"] } else { "25565" }
$levelName = if ($props.ContainsKey("level-name")) { $props["level-name"] } else { "angel-world" }
$world = Join-Path $srv $levelName
# written once the world has been placed; it lives in the world's folder, so -NewWorld removes it with the world
$placedMarker = Join-Path $world "angel-placed.txt"

function Invoke-Rcon([string]$Command) {
    $out = & $python -I $rcon $Command 2>$null
    return [pscustomobject]@{ Code = $LASTEXITCODE; Text = (@($out) -join "`n") }
}

function Read-LogSince([string]$Path, [long]$Offset) {
    if (-not (Test-Path $Path)) { return "" }
    $share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
    $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share)
    try {
        if ($Offset -gt $fs.Length) { $Offset = 0 }
        $null = $fs.Seek($Offset, [System.IO.SeekOrigin]::Begin)
        $reader = New-Object System.IO.StreamReader($fs)
        return $reader.ReadToEnd()
    }
    finally { $fs.Dispose() }
}

if ($NewWorld) { Remove-Item (Join-Path $root "characters_bridge\state.json") -ErrorAction SilentlyContinue -Confirm:$false }

# the server, in its own window (the window stays open while it runs)
$serverArgs = @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$root\tools\server.ps1")
if ($NewWorld) { $serverArgs += "-NewWorld" }
Start-Process powershell -ArgumentList $serverArgs

Write-Host "Waiting for the server..."
$deadline = (Get-Date).AddMinutes(5)
do {
    Start-Sleep -Seconds 2
    $r = Invoke-Rcon "list"
    if ((Get-Date) -gt $deadline) { throw "The server did not answer over RCON within 5 minutes. See its window." }
} until ($r.Code -eq 0)

# the world: placed once (the blocks, the biomes, the sky's sets); a played world is never placed again
$datapackOn = Invoke-Rcon "datapack list enabled"
if ($datapackOn.Text -notmatch "file/angel") {
    Write-Warning "The angel datapack is not enabled; enabling it."
    $null = Invoke-Rcon 'datapack enable "file/angel"'
}

if (Test-Path $placedMarker) {
    Write-Host "The world is already placed."
}
else {
    Write-Host "Placing the world (about 25 s on a fresh world)..."
    $offset = if (Test-Path $latest) { (Get-Item $latest).Length } else { 0 }
    $r = Invoke-Rcon "function angel:world/place_all"
    if ($r.Code -ne 0 -or $r.Text -match 'Unknown|Incorrect|rror') { throw "place_all was not run: $($r.Text)" }
    # the last set's chain logs "[angel] every set is placed"; a failed chain logs "placement stopped" (world/abort)
    $deadline = (Get-Date).AddMinutes(10)
    do {
        Start-Sleep -Seconds 2
        $text = Read-LogSince $latest $offset
        if ($text -match "placement stopped") { throw "The world was not placed (placement stopped). See the server window." }
        if ((Get-Date) -gt $deadline) { throw "The world was not placed within 10 minutes. See the server window." }
    } until ($text -match "every set is placed")
    if ($text -match "BIOME CHECK FAILED") { Write-Warning "A biome check failed (see the server log). The world is placed; look at it before you trust it." }
    if (-not (Test-Path $world)) { New-Item -ItemType Directory -Force $world | Out-Null }
    Set-Content -Path $placedMarker -Value ("placed " + (Get-Date).ToString("s")) -Encoding ascii
    Write-Host "The world is placed."
}

# the voice bridge (its text mode talks to the live server with --live)
if (-not $NoBridge) {
    $bridgeCmd = "Set-Location -LiteralPath '$root\characters_bridge'; & '$python' bridge.py"
    if ($Text) { $bridgeCmd += " --text --live" }
    if ($Output) { $bridgeCmd += " --output '" + $Output.Replace("'", "''") + "'" }
    Start-Process powershell -ArgumentList ('-NoExit -Command "' + $bridgeCmd + '"')
}

Write-Host ""
Write-Host "Ready."
Write-Host "  Minecraft launcher: profile 'Angel Attack VR' (first time: run tools\setup_client.py, then add it with"
Write-Host "  --install-profile, or by hand as the script prints). Press Play."
Write-Host "  For the headset: start SteamVR first, then switch Vivecraft to VR."
Write-Host "  Multiplayer -> 'Angel Attack' (localhost:$port)."
Write-Host "  The story begins with   function angel:story/start   (in the server window, or with -AutoStart here)."

if ($AutoStart) {
    Write-Host ""
    Write-Host "Waiting for a player to join (Ctrl+C to stop)..."
    $deadline = (Get-Date).AddHours(1)
    $online = 0
    do {
        Start-Sleep -Seconds 3
        $l = Invoke-Rcon "list"
        if ($l.Text -match 'There (?:is|are) (\d+) of a max') { $online = [int]$matches[1] }
        if ((Get-Date) -gt $deadline) { throw "No player joined within an hour. Start the story by hand: tools\rcon.py `"function angel:story/start`"" }
    } until ($online -ge 1)
    Start-Sleep -Seconds 5
    $r = Invoke-Rcon "function angel:story/start"
    Write-Host "Player online; story started."
}
