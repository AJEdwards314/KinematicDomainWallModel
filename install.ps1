# Define the name of the directory to create and the target file
$ModulesDirName = "src"
$ScriptDirectory = $PSScriptRoot  # Use the directory where the script is saved
$ModulesPath = Resolve-Path -Path (Join-Path $ScriptDirectory $ModulesDirName)

# Step 3: Look for a '.venv' directory in the parent directory or its parents
$VenvDir = $null
$CurrentDir = Get-Location | Get-Item
Write-Host $CurrentDir
Write-Host "Outputted current dir"

while ($CurrentDir -ne $null -and -not (Test-Path -Path (Join-Path $CurrentDir.FullName ".venv"))) {
    Write-Host $CurrentDir
    $CurrentDir = $CurrentDir.Parent
    Write-Host $CurrentDir
}

if ($CurrentDir -ne $null) {
    $VenvDir = Join-Path $CurrentDir.FullName ".venv"
    Write-Host "Found '.venv' directory at: $VenvDir"
} else {
    Write-Host "'.venv' directory not found. Exiting." -ForegroundColor Red
    exit 1
}

# Step 4: Create or update the 'nmrc.pth' file in '.venv/Lib/site-packages'
$SitePackagesPath = Join-Path $VenvDir "Lib\site-packages"
if (-not (Test-Path -Path $SitePackagesPath)) {
    Write-Host "'Lib/site-packages' not found in '.venv'. Exiting." -ForegroundColor Red
    exit 1
}

$PthFilePath = Join-Path $SitePackagesPath "kdw.pth"
Set-Content -Path $PthFilePath -Value $ModulesPath
Write-Host "'kdw.pth' file created at: $PthFilePath with content pointing to: $ModulesPath"

