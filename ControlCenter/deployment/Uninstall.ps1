[CmdletBinding()]
param([switch]$Execute, [string]$PanelSid)
. "$PSScriptRoot\Common.ps1"
if (-not $Execute) { Write-Output 'PREVIEW: remove matching manifest files and marked independent venv only; retain logs/export/private policy. Stop only the Control Center panel console manually first.'; return }
Assert-LayoutACL $PanelSid
$manifest = Get-Manifest $script:AppRoot -AllowMissing
Assert-PlainPath $script:VenvRoot
$marker = "$script:VenvRoot\CC03-owned.txt"
if (-not (Test-Path -LiteralPath $marker) -or (Get-Content -Raw -LiteralPath $marker).Trim() -ne 'CC03 independent venv only') { throw 'CC03_VENV_MARKER_REQUIRED' }
# Enumerate first; reject reparse links BEFORE any recursive removal.
$items = @(Get-ChildItem -Force -Recurse -LiteralPath $script:VenvRoot)
if (@($items | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count -ne 0) { throw 'VENV_REPARSE_FORBIDDEN' }
foreach ($entry in $manifest.files) {
    $file = Join-Path $script:AppRoot $entry.path
    if (Test-Path -LiteralPath $file) { Remove-Item -LiteralPath $file }
}
Remove-Item -LiteralPath "$script:AppRoot\deployment\manifest.json"
# All roots are fixed Control Center roots; no Task/process termination or H1 action.
foreach ($item in ($items | Where-Object { -not $_.PSIsContainer })) { Remove-Item -LiteralPath $item.FullName }
foreach ($item in ($items | Where-Object { $_.PSIsContainer } | Sort-Object { $_.FullName.Length } -Descending)) { Remove-Item -LiteralPath $item.FullName }
Write-Output 'CC03_REMOVED_OWN_FILES_DATA_RETAINED'
