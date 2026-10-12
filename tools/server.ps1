# Start the local Angel Attack server (this window stays open while it runs).
#   -NewWorld   throw the world away first, so the story starts again from the beginning
#   -Offline    accept clients without a Minecraft account (only for the automated visual test)
# The datapack (datapack\angel) is copied into the world's datapacks folder on every start, and file/angel is kept in
# initial-enabled-packs, so a new world starts with it enabled. server.properties is otherwise left as it is
# (generator-settings in particular, which give the void biome).
param([switch]$NewWorld, [switch]$Offline)

$root = Split-Path $PSScriptRoot -Parent
$srv = Join-Path $root "server"
$datapack = Join-Path $root "datapack\angel"
$java = Join-Path $env:LOCALAPPDATA "Packages\Microsoft.4297127D64EC6_8wekyb3d8bbwe\LocalCache\Local\runtime\java-runtime-epsilon\windows-x64\java-runtime-epsilon\bin\java.exe"

if (-not (Test-Path (Join-Path $datapack "pack.mcmeta"))) {
    throw "No datapack at $datapack. Build it first (tools\world\build.py, tools\story\build_story.py)."
}
if (-not (Test-Path $java)) { throw "Java not found: $java (Minecraft's own runtime is expected there)." }

$propsPath = Join-Path $srv "server.properties"
$lines = [System.IO.File]::ReadAllLines($propsPath, [System.Text.Encoding]::UTF8)
$levelName = "angel-world"
foreach ($l in $lines) { if ($l -match '^level-name=(.+)$') { $levelName = $matches[1].Trim() } }
$world = Join-Path $srv $levelName

if ($NewWorld -and (Test-Path $world)) { Remove-Item $world -Recurse -Force -Confirm:$false }

# the datapack, copied into the world (robocopy /MIR: exactly the repo's datapack, nothing stale)
New-Item -ItemType Directory -Force (Join-Path $world "datapacks") | Out-Null
robocopy $datapack (Join-Path $world "datapacks\angel") /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Copying the datapack into the world failed (robocopy exit code $LASTEXITCODE)." }

# server.properties: online-mode for this run; file/angel among the packs a new world starts with (the rest untouched)
$mode = if ($Offline) { "false" } else { "true" }
$out = foreach ($l in $lines) {
    if ($l -like "online-mode=*") { "online-mode=$mode" }
    elseif ($l -match '^initial-enabled-packs=(.*)$') {
        $v = $matches[1].Trim()
        if ($v -notmatch 'file/angel') {
            if ($v -eq "") { $v = "vanilla" }
            $v = "$v,file/angel"
        }
        "initial-enabled-packs=$v"
    }
    else { $l }
}
if (-not ($lines | Where-Object { $_ -like "initial-enabled-packs=*" })) { $out += "initial-enabled-packs=vanilla,file/angel" }
[System.IO.File]::WriteAllLines($propsPath, [string[]]@($out), (New-Object System.Text.UTF8Encoding($false)))

Set-Location $srv
& $java -Xms4G -Xmx10G -jar fabric-server-launch.jar nogui
