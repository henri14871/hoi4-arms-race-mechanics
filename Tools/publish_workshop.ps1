param(
    [Parameter(Mandatory = $true)]
    [string]$SteamUser,

    [Parameter(Mandatory = $false)]
    [string]$SteamCmdPath = "E:\SteamLibrary\steamapps\common\Arma 3 Tools\GameUpdater\steamcmd.exe",

    [Parameter(Mandatory = $false)]
    [string]$ChangeNote = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$vdfPath = Join-Path $scriptDir "workshop_item.vdf"
$previewPath = Join-Path $repoRoot "thumbnail.png"

if (-not (Test-Path -LiteralPath $SteamCmdPath)) {
    throw "steamcmd.exe not found at: $SteamCmdPath"
}

if (-not (Test-Path -LiteralPath $vdfPath)) {
    throw "Workshop VDF not found: $vdfPath"
}

if (-not (Test-Path -LiteralPath $previewPath)) {
    throw "Preview image not found: $previewPath"
}

$vdfContent = Get-Content -LiteralPath $vdfPath -Raw
$vdfContent = [regex]::Replace($vdfContent, '"changenote"\s*"[^"]*"', "`"changenote`" `"$ChangeNote`"")
Set-Content -LiteralPath $vdfPath -Value $vdfContent -Encoding ASCII

Write-Host "Publishing Workshop item 3683996696 with preview image:" $previewPath
Write-Host "steamcmd will prompt for password / Steam Guard if needed."

& $SteamCmdPath +login $SteamUser +workshop_build_item $vdfPath +quit
