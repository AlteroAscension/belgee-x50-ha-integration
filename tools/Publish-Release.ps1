[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^\d+\.\d+\.\d+$')]
    [string]$Version
)

$ErrorActionPreference = 'Stop'
$tag = "v$Version"
$ghInstallPath = Join-Path $env:ProgramFiles 'GitHub CLI'
if (Test-Path (Join-Path $ghInstallPath 'gh.exe')) {
    $env:Path = "$ghInstallPath;$env:Path"
}

function Require-Command([string]$Name) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required but was not found on PATH."
    }
}

Require-Command git
Require-Command gh
gh auth status | Out-Host

$manifest = Get-Content (Join-Path $PSScriptRoot '..\custom_components\belgee_x50\manifest.json') -Raw |
    ConvertFrom-Json
if ($manifest.version -ne $Version) {
    throw "manifest.json version is $($manifest.version), expected $Version."
}
if (git status --porcelain) {
    throw 'Worktree is not clean. Commit or stash changes before releasing.'
}
if (git tag --list $tag) {
    throw "Tag $tag already exists."
}

python -m unittest discover -s tests -v
python -m compileall -q custom_components tests

git push origin main
git tag -a $tag -m "Belgee X50 $Version"
git push origin $tag
gh release create $tag --title "Belgee X50 $Version" --generate-notes

Write-Host "Published $tag" -ForegroundColor Green
