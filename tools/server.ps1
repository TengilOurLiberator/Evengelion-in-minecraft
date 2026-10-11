# Start the local Angel Attack server (this window stays open while it runs).
#   -NewWorld   throw the world away first, so the story starts again from the beginning
#   -Offline    accept clients without a Minecraft account (only for the automated visual test)
param([switch]$NewWorld, [switch]$Offline)

$root = Split-Path $PSScriptRoot -Parent
$srv = Join-Path $root "server"
$world = Join-Path $srv "angel-world"
$java = Join-Path $env:LOCALAPPDATA "Packages\Microsoft.4297127D64EC6_8wekyb3d8bbwe\LocalCache\Local\runtime\java-runtime-epsilon\windows-x64\java-runtime-epsilon\bin\java.exe"

if ($NewWorld -and (Test-Path $world)) { Remove-Item $world -Recurse -Force -Confirm:$false }
New-Item -ItemType Directory -Force "$world\datapacks" | Out-Null
robocopy (Join-Path $root "datapack\angel") "$world\datapacks\angel" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null

$props = Get-Content "$srv\server.properties"
$mode = if ($Offline) { "false" } else { "true" }
$props = $props | ForEach-Object { if ($_ -like "online-mode=*") { "online-mode=$mode" } else { $_ } }
$props | Out-File -Encoding ascii "$srv\server.properties"

Set-Location $srv
& $java -Xms4G -Xmx10G -jar fabric-server-launch.jar nogui
