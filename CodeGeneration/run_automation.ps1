param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,

    [Parameter(Mandatory = $false)]
    [string]$Out = ""
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
$automationScript = Join-Path $scriptDir "automation_script.py"

if (-not (Test-Path $automationScript)) {
    Write-Error "automation_script.py not found at $automationScript"
    exit 1
}

if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = "python"
}

$args = @($automationScript, "--input", $InputFile)
if ($Out -ne "") {
    $args += @("--out", $Out)
}

& $pythonExe @args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
