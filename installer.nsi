; Kirkouski Typographic Keyboard Layout - NSIS Installer
; build.py passes /DVERSION and /DVERSION_TUPLE on the makensis command line.
; Direct invocations fall back to the values below; CI / build.py overrides.

!ifndef VERSION
    !define VERSION "0.3"
!endif
!ifndef VERSION_TUPLE
    !define VERSION_TUPLE "0.3.0.0"
!endif

!include "MUI2.nsh"

; ---- General ----
Name "Kirkouski Typographic Keyboard Layout"
OutFile "dist\kirkouski-typographic-v${VERSION}-windows-setup.exe"
InstallDir "$TEMP\kirkouski-typographic-install"
RequestExecutionLevel admin
Unicode true

; ---- Version Info ----
VIProductVersion "${VERSION_TUPLE}"
VIAddVersionKey "ProductName" "Kirkouski Typographic Keyboard Layout"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "CompanyName" "Andrew Kirkouski"
VIAddVersionKey "LegalCopyright" "(c) 2026 Andrew Kirkouski. MIT License."
VIAddVersionKey "FileDescription" "Keyboard layout installer"
VIAddVersionKey "FileVersion" "${VERSION}"

; ---- Interface Settings ----
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; ---- Pages ----
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES

; Custom finish page
!define MUI_FINISHPAGE_TITLE "Installation Complete — REBOOT REQUIRED"
!define MUI_FINISHPAGE_TEXT "Kirkouski Typographic keyboard layouts have been installed.$\r$\n$\r$\n*** REBOOT REQUIRED BEFORE USING THE NEW LAYOUT ***$\r$\n$\r$\nYour PC is fine to keep using right now — just don't switch to the Kirkouski Typographic layout until after a restart, or Windows Explorer will crash (it still holds the old keyboard state in memory until reboot). This is a Windows limitation, not a bug in the installer.$\r$\n$\r$\nAfter the reboot:$\r$\nSettings > Time & Language > Language & Region > Keyboard$\r$\nand add the new layout.$\r$\n$\r$\nTo apply to the login screen:$\r$\nWin+R > intl.cpl > Administrative > Copy settings"
!define MUI_FINISHPAGE_REBOOT
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ---- Language ----
!insertmacro MUI_LANGUAGE "English"

; ---- Installer Section ----
Section "Install Keyboard Layouts" SecInstall
    SetOutPath $INSTDIR

    ; Extract files to temp dir
    File "dist\windows-v${VERSION}\pltypo.dll"
    File "dist\windows-v${VERSION}\rutypo.dll"
    File "dist\windows-v${VERSION}\ustypo.dll"
    File "dist\windows-v${VERSION}\install.ps1"

    ; Run install.ps1 with -Force (non-interactive)
    DetailPrint "Installing keyboard layouts..."
    nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\install.ps1" -Force'
    Pop $0
    ${If} $0 != "0"
        DetailPrint "Warning: PowerShell installer returned code $0"
    ${EndIf}

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Add to Add/Remove Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "DisplayName" "Kirkouski Typographic Keyboard Layout"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "Publisher" "Andrew Kirkouski"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "URLInfoAbout" "https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic" \
        "EstimatedSize" 20  ; ~20 KB

SectionEnd

; ---- Uninstaller Section ----
Section "Uninstall"

    ; Run install.ps1 -Uninstall -Force
    DetailPrint "Uninstalling keyboard layouts..."
    nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\install.ps1" -Uninstall -Force'
    Pop $0

    ; Remove Add/Remove Programs entry
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\KirkouskiTypographic"

    ; Clean up installer files
    Delete "$INSTDIR\pltypo.dll"
    Delete "$INSTDIR\rutypo.dll"
    Delete "$INSTDIR\ustypo.dll"
    Delete "$INSTDIR\install.ps1"
    Delete "$INSTDIR\uninstall.exe"
    RMDir "$INSTDIR"

    ; Remind user to restart — same crash mechanic as install
    MessageBox MB_ICONEXCLAMATION|MB_OK "Kirkouski Typographic layouts have been removed.$\r$\n$\r$\n*** REBOOT REQUIRED ***$\r$\n$\r$\nYour PC is fine to keep using right now, but if you switch to the (now-deleted) Kirkouski Typographic layout before rebooting, Windows Explorer will crash. The keyboard state is unloaded only on next restart. This is a Windows limitation."

SectionEnd
