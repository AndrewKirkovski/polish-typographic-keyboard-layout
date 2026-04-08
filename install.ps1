<#
.SYNOPSIS
    Install or uninstall Kirkouski Typographic keyboard layouts on Windows.

.DESCRIPTION
    Interactive installer that detects existing installations and offers
    appropriate actions. Auto-elevates to Administrator if needed.

.PARAMETER Uninstall
    Remove previously installed layouts.

.PARAMETER HardCleanup
    Remove ALL traces of Kirkouski layouts (for broken installs / Explorer crashes).

.PARAMETER Layout
    Which layout: "polish", "russian", or "all" (default: "all").

.PARAMETER Force
    Skip confirmation prompts (for scripted/CI use).

.EXAMPLE
    .\install.ps1                        # Interactive mode
    .\install.ps1 -Uninstall             # Uninstall all
    .\install.ps1 -HardCleanup           # Nuclear cleanup
    .\install.ps1 -Force                 # Install without prompts
#>

param(
    [switch]$Uninstall,
    [switch]$HardCleanup,
    [switch]$Force,
    [ValidateSet("all", "polish", "russian", "us")]
    [string]$Layout = "all"
)

# Wrap everything so errors don't silently close the window
trap {
    Write-Host ""
    Write-Host "UNEXPECTED ERROR: $_" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$ErrorActionPreference = "Stop"

# -- Layout definitions -------------------------------------------------
$Layouts = @{
    "polish" = @{
        DllName    = "pltypo.dll"
        LayoutText = "Polish Typographic by Kirkouski"
        LangId     = "0415"
    }
    "russian" = @{
        DllName    = "rutypo.dll"
        LayoutText = "Russian Typographic by Kirkouski"
        LangId     = "0419"
    }
    "us" = @{
        DllName    = "ustypo.dll"
        LayoutText = "US+POL Typographic by Kirkouski"
        LangId     = "0409"
    }
}

$RegBase = "HKLM:\SYSTEM\CurrentControlSet\Control\Keyboard Layouts"

# -- Self-elevation -----------------------------------------------------
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    # Build the command to re-run this script elevated
    $scriptPath = if ($MyInvocation.MyCommand.Path) {
        $MyInvocation.MyCommand.Path
    } else {
        # Fallback: resolve from current location
        Join-Path $PWD.Path "install.ps1"
    }

    $params = ""
    if ($Uninstall) { $params += " -Uninstall" }
    if ($HardCleanup) { $params += " -HardCleanup" }
    if ($Force) { $params += " -Force" }
    if ($Layout -ne "all") { $params += " -Layout $Layout" }

    $elevatedCmd = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"$params"

    Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow
    try {
        Start-Process powershell.exe -ArgumentList $elevatedCmd -Verb RunAs -Wait
    } catch {
        Write-Host ""
        Write-Host "ERROR: Administrator privileges required. Elevation was cancelled." -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to close"
    }
    exit
}

# -- Targets ------------------------------------------------------------
if ($Layout -eq "all") {
    $targets = @($Layouts.Keys)
} else {
    $targets = @($Layout)
}

# =======================================================================
#  HELPER FUNCTIONS
# =======================================================================

function Find-InstalledLayout {
    param([string]$DllName)
    return Get-ChildItem $RegBase -ErrorAction SilentlyContinue | Where-Object {
        (Get-ItemProperty $_.PSPath -Name "Layout File" -ErrorAction SilentlyContinue)."Layout File" -eq $DllName
    }
}

function Find-NextLayoutId {
    $usedIds = @()
    Get-ChildItem $RegBase | ForEach-Object {
        $id = (Get-ItemProperty $_.PSPath -Name "Layout Id" -ErrorAction SilentlyContinue)."Layout Id"
        if ($id) { $usedIds += [Convert]::ToInt32($id, 16) }
    }
    for ($i = 0x00C0; $i -le 0x0FFF; $i++) {
        if ($i -notin $usedIds) {
            return "{0:x4}" -f $i
        }
    }
    throw "No available Layout Id in range 0x00C0-0x0FFF"
}

function Find-NextRegKey {
    param([string]$LangId)
    for ($prefix = 0xa001; $prefix -le 0xa0FF; $prefix++) {
        $key = ("{0:x4}{1}" -f $prefix, $LangId).ToLower()
        $fullPath = Join-Path $RegBase $key
        if (-not (Test-Path $fullPath)) {
            return $key
        }
    }
    throw "No available registry key for language $LangId"
}

function Remove-LayoutFromPreload {
    param([string]$Klid)
    foreach ($hive in @("HKCU:\Keyboard Layout", "Registry::HKU\.DEFAULT\Keyboard Layout")) {
        $subsPath = "$hive\Substitutes"
        $preloadPath = "$hive\Preload"
        $subsToRemove = @()

        if (Test-Path $subsPath) {
            $subs = Get-ItemProperty $subsPath -ErrorAction SilentlyContinue
            if ($subs) {
                foreach ($prop in $subs.PSObject.Properties) {
                    if ($prop.Name -match '^\w{8}$' -and $prop.Value -eq $Klid) {
                        $subsToRemove += $prop.Name
                        Remove-ItemProperty -Path $subsPath -Name $prop.Name -Force -ErrorAction SilentlyContinue
                        Write-Host "    Removed substitute: $($prop.Name) -> $($prop.Value)"
                    }
                }
            }
        }

        if (Test-Path $preloadPath) {
            $preload = Get-ItemProperty $preloadPath -ErrorAction SilentlyContinue
            if ($preload) {
                $entriesToRemove = @()
                foreach ($prop in $preload.PSObject.Properties) {
                    if ($prop.Name -match '^\d+$') {
                        if ($prop.Value -eq $Klid -or $prop.Value -in $subsToRemove) {
                            $entriesToRemove += $prop.Name
                        }
                    }
                }
                foreach ($name in $entriesToRemove) {
                    Remove-ItemProperty -Path $preloadPath -Name $name -Force -ErrorAction SilentlyContinue
                    Write-Host "    Removed preload entry: $name"
                }
                if ($entriesToRemove.Count -gt 0) {
                    $remaining = @()
                    $preload = Get-ItemProperty $preloadPath -ErrorAction SilentlyContinue
                    if ($preload) {
                        foreach ($prop in $preload.PSObject.Properties) {
                            if ($prop.Name -match '^\d+$') {
                                $remaining += $prop.Value
                                Remove-ItemProperty -Path $preloadPath -Name $prop.Name -Force -ErrorAction SilentlyContinue
                            }
                        }
                        for ($i = 0; $i -lt $remaining.Count; $i++) {
                            Set-ItemProperty -Path $preloadPath -Name ($i + 1).ToString() -Value $remaining[$i]
                        }
                    }
                }
            }
        }
    }
}

function Invoke-Uninstall {
    param([string]$Target)
    $cfg = $Layouts[$Target]
    $dllName = $cfg.DllName
    $dllPath = Join-Path $env:SystemRoot "System32\$dllName"

    $entries = Find-InstalledLayout -DllName $dllName
    if (-not $entries) {
        Write-Host "  $($cfg.LayoutText) -not installed." -ForegroundColor DarkGray
        return
    }

    Write-Host "  Uninstalling $($cfg.LayoutText)..." -ForegroundColor Cyan
    foreach ($entry in $entries) {
        $klid = $entry.PSChildName
        Remove-LayoutFromPreload -Klid $klid
        try {
            Remove-Item $entry.PSPath -Force
            Write-Host "    Removed registry key: $klid"
        } catch {
            Write-Host "    WARNING: Could not remove $klid : $_" -ForegroundColor Yellow
        }
    }
    if (Test-Path $dllPath) {
        try {
            Remove-Item $dllPath -Force
            Write-Host "    Deleted $dllPath"
        } catch {
            Write-Host "    WARNING: Could not delete $dllPath (may be in use)." -ForegroundColor Yellow
            Write-Host "    Switch to a different keyboard layout, then try again."
        }
    }
}

function Invoke-Install {
    param([string]$Target, [string]$DistDir)
    $cfg = $Layouts[$Target]
    $dllName = $cfg.DllName
    $dllSource = Join-Path $DistDir $dllName
    $dllDest = Join-Path $env:SystemRoot "System32\$dllName"

    if (-not (Test-Path $dllSource)) {
        Write-Host "  SKIP: $dllSource not found." -ForegroundColor Yellow
        Write-Host "  Build first: python build_kbd_c.py $Target; python compile_kbd.py $Target"
        return $false
    }

    Write-Host "  Installing $($cfg.LayoutText)..." -ForegroundColor Cyan
    try {
        Copy-Item $dllSource $dllDest -Force
        Write-Host "    Copied $dllName -> $dllDest"
    } catch {
        Write-Host "    ERROR: Could not copy DLL." -ForegroundColor Red
        Write-Host "    If the layout is active, switch to another keyboard first."
        Write-Host "    $_" -ForegroundColor DarkRed
        return $false
    }

    $layoutId = Find-NextLayoutId
    $regKey = Find-NextRegKey -LangId $cfg.LangId
    $regPath = Join-Path $RegBase $regKey

    New-Item -Path $regPath -Force | Out-Null
    Set-ItemProperty -Path $regPath -Name "Layout File" -Value $dllName
    Set-ItemProperty -Path $regPath -Name "Layout Text" -Value $cfg.LayoutText
    New-ItemProperty -Path $regPath -Name "Layout Display Name" -PropertyType ExpandString -Value "@%SystemRoot%\system32\$dllName,-100" -Force | Out-Null
    Set-ItemProperty -Path $regPath -Name "Layout Id" -Value $layoutId

    Write-Host "    Registry key: $regKey" -ForegroundColor Green
    Write-Host "    Layout Id:    $layoutId" -ForegroundColor Green
    return $true
}

function Invoke-HardCleanup {
    Write-Host ""
    Write-Host "  Removing ALL traces of Kirkouski layouts..." -ForegroundColor Red
    $dllNames = @("pltypo.dll", "rutypo.dll", "ustypo.dll")

    $allEntries = Get-ChildItem $RegBase -ErrorAction SilentlyContinue | Where-Object {
        $lf = (Get-ItemProperty $_.PSPath -Name "Layout File" -ErrorAction SilentlyContinue)."Layout File"
        $lt = (Get-ItemProperty $_.PSPath -Name "Layout Text" -ErrorAction SilentlyContinue)."Layout Text"
        ($lf -in $dllNames) -or ($lt -like "*Kirkouski*")
    }

    if ($allEntries) {
        foreach ($entry in $allEntries) {
            $klid = $entry.PSChildName
            Remove-LayoutFromPreload -Klid $klid
            try {
                Remove-Item $entry.PSPath -Force
                Write-Host "    Removed registry key: $klid" -ForegroundColor Green
            } catch {
                Write-Host "    WARNING: Could not remove $klid : $_" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "    No registry entries found." -ForegroundColor DarkGray
    }

    foreach ($dll in $dllNames) {
        foreach ($dir in @("System32", "SysWOW64")) {
            $path = Join-Path $env:SystemRoot "$dir\$dll"
            if (Test-Path $path) {
                try {
                    Remove-Item $path -Force
                    Write-Host "    Deleted $path" -ForegroundColor Green
                } catch {
                    Write-Host "    WARNING: Could not delete $path : $_" -ForegroundColor Yellow
                }
            }
        }
    }
}

# =======================================================================
#  NON-INTERACTIVE MODES (when called with explicit flags)
# =======================================================================

if ($HardCleanup) {
    Write-Host ""
    Write-Host "=== HARD CLEANUP ===" -ForegroundColor Red
    if (-not $Force) {
        Write-Host "This will remove ALL traces of Kirkouski layouts."
        $confirm = Read-Host "Type YES to proceed"
        if ($confirm -ne "YES") {
            Write-Host "Cancelled."
            Write-Host ""
            Read-Host "Press Enter to close"
            exit
        }
    }
    Invoke-HardCleanup
    Write-Host ""
    Write-Host "Done. Restart your computer." -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to close"
    exit
}

if ($Uninstall) {
    Write-Host ""
    Write-Host "=== UNINSTALL ===" -ForegroundColor Cyan
    Write-Host ""
    foreach ($target in $targets) {
        Invoke-Uninstall -Target $target
        Write-Host ""
    }
    Write-Host "Done. Restart your computer." -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to close"
    exit
}

# =======================================================================
#  INTERACTIVE MODE (default -no flags)
# =======================================================================

Write-Host ""
Write-Host "  Kirkouski Typographic Keyboard Layout" -ForegroundColor White
Write-Host "  ======================================" -ForegroundColor DarkGray
Write-Host ""

# -- Detect what's installed --------------------------------------------
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = $scriptDir
if (-not (Test-Path (Join-Path $distDir "pltypo.dll")) -and (Test-Path (Join-Path $distDir "dist"))) {
    $distDir = Join-Path $scriptDir "dist"
}

$installedLayouts = @()
$availableLayouts = @()

foreach ($target in $targets) {
    $cfg = $Layouts[$target]
    $existing = Find-InstalledLayout -DllName $cfg.DllName
    $dllAvailable = Test-Path (Join-Path $distDir $cfg.DllName)

    if ($existing) {
        $regKey = ($existing | Select-Object -First 1).PSChildName
        $installedLayouts += @{ Target = $target; Config = $cfg; RegKey = $regKey }
    } elseif ($dllAvailable) {
        $availableLayouts += @{ Target = $target; Config = $cfg }
    }
}

# -- Show status --------------------------------------------------------
if ($installedLayouts.Count -gt 0) {
    Write-Host "  Installed:" -ForegroundColor Green
    foreach ($l in $installedLayouts) {
        Write-Host "    - $($l.Config.LayoutText)  [$($l.RegKey)]" -ForegroundColor Green
    }
    Write-Host ""
}

if ($availableLayouts.Count -gt 0) {
    Write-Host "  Available to install:" -ForegroundColor Cyan
    foreach ($l in $availableLayouts) {
        Write-Host "    - $($l.Config.LayoutText)" -ForegroundColor Cyan
    }
    Write-Host ""
}

if ($installedLayouts.Count -eq 0 -and $availableLayouts.Count -eq 0) {
    Write-Host "  No layouts installed, no DLL files found in this directory." -ForegroundColor Yellow
    Write-Host "  Build first: python build.py windows"
    Write-Host ""
    Read-Host "Press Enter to close"
    exit
}

# -- Build menu based on state ------------------------------------------
$options = @()

if ($availableLayouts.Count -gt 0) {
    $names = ($availableLayouts | ForEach-Object { $_.Config.LayoutText }) -join ", "
    $options += @{ Key = "I"; Label = "Install ($names)"; Action = "install" }
}

if ($installedLayouts.Count -gt 0 -and $availableLayouts.Count -gt 0) {
    $options += @{ Key = "A"; Label = "Install all (reinstall existing + install new)"; Action = "install_all" }
}

if ($installedLayouts.Count -gt 0 -and $availableLayouts.Count -eq 0) {
    # Everything is installed -offer reinstall
    $options += @{ Key = "R"; Label = "Reinstall (uninstall + install fresh)"; Action = "reinstall" }
}

if ($installedLayouts.Count -gt 0) {
    $options += @{ Key = "U"; Label = "Uninstall"; Action = "uninstall" }
    $options += @{ Key = "H"; Label = "Hard cleanup (remove all traces)"; Action = "hard_cleanup" }
}

$options += @{ Key = "Q"; Label = "Quit"; Action = "quit" }

Write-Host "  What would you like to do?" -ForegroundColor White
Write-Host ""
foreach ($opt in $options) {
    Write-Host "    [$($opt.Key)] $($opt.Label)"
}
Write-Host ""
$choice = (Read-Host "  Choice").Trim().ToUpper()

$selectedAction = ($options | Where-Object { $_.Key -eq $choice }).Action
if (-not $selectedAction) { $selectedAction = "quit" }

Write-Host ""

switch ($selectedAction) {
    "install" {
        foreach ($l in $availableLayouts) {
            $result = Invoke-Install -Target $l.Target -DistDir $distDir
        }
    }
    "install_all" {
        foreach ($l in $installedLayouts) {
            Invoke-Uninstall -Target $l.Target
            Write-Host ""
        }
        foreach ($target in $targets) {
            $cfg = $Layouts[$target]
            if (Test-Path (Join-Path $distDir $cfg.DllName)) {
                $result = Invoke-Install -Target $target -DistDir $distDir
                Write-Host ""
            }
        }
    }
    "reinstall" {
        foreach ($l in $installedLayouts) {
            Invoke-Uninstall -Target $l.Target
            Write-Host ""
            $result = Invoke-Install -Target $l.Target -DistDir $distDir
            Write-Host ""
        }
    }
    "uninstall" {
        foreach ($l in $installedLayouts) {
            Invoke-Uninstall -Target $l.Target
            Write-Host ""
        }
    }
    "hard_cleanup" {
        Write-Host "  This will remove ALL traces of Kirkouski layouts." -ForegroundColor Red
        $confirm = Read-Host "  Type YES to proceed"
        if ($confirm -eq "YES") {
            Invoke-HardCleanup
        } else {
            Write-Host "  Cancelled."
        }
    }
    default {
        Write-Host "  Bye!"
    }
}

# -- Final message ------------------------------------------------------
if ($selectedAction -in @("install", "install_all", "reinstall", "uninstall", "hard_cleanup")) {
    Write-Host ""
    Write-Host "  Restart your computer for changes to take effect." -ForegroundColor Yellow

    if ($selectedAction -in @("install", "install_all", "reinstall")) {
        Write-Host ""
        Write-Host "  After restart:" -ForegroundColor DarkGray
        Write-Host "    Settings > Time & Language > Language & Region > Keyboard" -ForegroundColor DarkGray
        Write-Host "    Add the new Kirkouski Typographic layout" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "  To apply to login screen & new users:" -ForegroundColor DarkGray
        Write-Host "    Win+R > intl.cpl > Administrative > Copy settings" -ForegroundColor DarkGray
    }
}

Write-Host ""
Read-Host "Press Enter to close"
