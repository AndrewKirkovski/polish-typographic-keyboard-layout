; Kirkouski Typographic Keyboard Layout — Inno Setup installer
; Handles KLID + Layout Id auto-allocation, locked-DLL replacement via
; MoveFileEx, and preload cleanup — all self-contained, no PowerShell.
;
; Based on installation logic from lelegard/winkbdlayouts (MIT).

#ifndef VERSION
  #define VERSION "0.10"
#endif

[Setup]
AppId={{B7E3F4A1-8C2D-4F5A-9E6B-1D2C3F4A5B6C}
AppName=Kirkouski Typographic Keyboard Layout
AppVersion={#VERSION}
AppPublisher=Andrew Kirkouski
AppPublisherURL=https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout
AppSupportURL=https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/issues
DefaultDirName={autopf}\KirkouskiTypographic
DisableDirPage=yes
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=kirkouski-typographic-v{#VERSION}-windows-setup
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
Compression=lzma2
SolidCompression=yes
AlwaysRestart=yes
SetupLogging=yes
VersionInfoVersion={#VERSION}.0.0
VersionInfoCompany=Andrew Kirkouski
VersionInfoCopyright=(c) 2026 Andrew Kirkouski. MIT License.
VersionInfoDescription=Keyboard layout installer
LicenseFile=LICENSE
InfoAfterFile=
SetupIconFile=web\public\favicon.ico
UninstallDisplayName=Kirkouski Typographic Keyboard Layout

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[CustomMessages]
english.TypeFull=All keyboard layouts
polish.TypeFull=Wszystkie układy klawiatury
russian.TypeFull=Все раскладки клавиатуры

english.TypeCustom=Choose layouts
polish.TypeCustom=Wybierz układy
russian.TypeCustom=Выбрать раскладки

english.CompPolish=Polish Typographic (AltGr diacritics on Polish Programmers QWERTY)
polish.CompPolish=Polski Typograficzny (diakrytyki AltGr na Polski Programisty QWERTY)
russian.CompPolish=Польская типографская (диакритика AltGr на Polish Programmers QWERTY)

english.CompRussian=Russian Typographic (Ukrainian/Belarusian letters + typography on ЙЦУКЕН)
polish.CompRussian=Rosyjski Typograficzny (litery ukraińskie/białoruskie + typografia na ЙЦУКЕН)
russian.CompRussian=Русская типографская (украинские/белорусские буквы + типографика на ЙЦУКЕН)

english.CompUs=US+POL Typographic (Polish characters under English US — no extra input language)
polish.CompUs=US+POL Typograficzny (polskie znaki pod angielskim US — bez dodatkowego języka wejściowego)
russian.CompUs=US+POL типографская (польские символы под английским US — без дополнительного языка ввода)

english.RebootWarningBody=DO NOT SWITCH to the Kirkouski Typographic layout before rebooting.%n%nWindows Explorer still holds the old keyboard state in memory. Switching now will crash Explorer. Your PC is otherwise safe to keep using until you reboot.
polish.RebootWarningBody=NIE PRZEŁĄCZAJ się na układ Kirkouski Typographic przed ponownym uruchomieniem.%n%nEksplorator Windows wciąż trzyma starą konfigurację klawiatury w pamięci. Przełączenie teraz spowoduje awarię Eksploratora. Komputer jest bezpieczny w użyciu do czasu restartu.
russian.RebootWarningBody=НЕ ПЕРЕКЛЮЧАЙТЕСЬ на раскладку Kirkouski Typographic до перезагрузки.%n%nПроводник Windows всё ещё хранит старое состояние клавиатуры в памяти. Переключение сейчас приведёт к сбою Проводника. В остальном компьютер безопасно использовать до перезагрузки.

english.FinishedRestartLabelCustom=Setup has finished installing Kirkouski Typographic.%n%n⚠ DO NOT SWITCH TO THE KIRKOUSKI LAYOUT BEFORE REBOOTING.%nWindows Explorer still holds the old keyboard state in memory — switching to the newly installed layout now will crash Explorer.%n%nReboot when convenient, then add the layout in Settings → Time & Language → Language & Region → Keyboard.
polish.FinishedRestartLabelCustom=Instalator zakończył instalację Kirkouski Typographic.%n%n⚠ NIE PRZEŁĄCZAJ SIĘ NA UKŁAD KIRKOUSKI PRZED PONOWNYM URUCHOMIENIEM.%nEksplorator Windows wciąż trzyma starą konfigurację klawiatury w pamięci — przełączenie się teraz spowoduje jego awarię.%n%nUruchom ponownie w dogodnym momencie, następnie dodaj układ w Ustawienia → Czas i język → Język i region → Klawiatura.
russian.FinishedRestartLabelCustom=Установщик завершил установку Kirkouski Typographic.%n%n⚠ НЕ ПЕРЕКЛЮЧАЙТЕСЬ НА РАСКЛАДКУ KIRKOUSKI ДО ПЕРЕЗАГРУЗКИ.%nПроводник Windows всё ещё хранит старое состояние клавиатуры в памяти — переключение на новую раскладку сейчас приведёт к сбою Проводника.%n%nПерезагрузите компьютер в удобное время, затем добавьте раскладку в Параметры → Время и язык → Язык и регион → Клавиатура.

[Messages]
english.FinishedRestartLabel={cm:FinishedRestartLabelCustom}
polish.FinishedRestartLabel={cm:FinishedRestartLabelCustom}
russian.FinishedRestartLabel={cm:FinishedRestartLabelCustom}

[Types]
Name: "full"; Description: "{cm:TypeFull}"
Name: "custom"; Description: "{cm:TypeCustom}"; Flags: iscustom

[Components]
Name: "polish"; Description: "{cm:CompPolish}"; Types: full
Name: "russian"; Description: "{cm:CompRussian}"; Types: full
Name: "us"; Description: "{cm:CompUs}"; Types: full

[Files]
Source: "dist\windows-v{#VERSION}\pltypo.dll"; DestDir: "{sys}"; Components: polish; \
  Flags: restartreplace uninsrestartdelete 64bit
Source: "dist\windows-v{#VERSION}\rutypo.dll"; DestDir: "{sys}"; Components: russian; \
  Flags: restartreplace uninsrestartdelete 64bit
Source: "dist\windows-v{#VERSION}\ustypo.dll"; DestDir: "{sys}"; Components: us; \
  Flags: restartreplace uninsrestartdelete 64bit

[Code]
const
  KB_REG_BASE = 'SYSTEM\CurrentControlSet\Control\Keyboard Layouts';
  LAYOUT_ID_MIN = $00C0;
  LAYOUT_ID_MAX = $0FFF;
  KLID_PREFIX_MIN = $A001;
  KLID_PREFIX_MAX = $A0FF;

type
  TLayoutDef = record
    DllName: String;
    LayoutText: String;
    LangId: String;
    ComponentName: String;
  end;

var
  Layouts: array[0..2] of TLayoutDef;
  InstalledKLIDs: array[0..2] of String;

procedure InitLayouts;
begin
  // These LayoutText strings are stored in HKLM registry — keep stable English across all installer languages.
  Layouts[0].DllName := 'pltypo.dll';
  Layouts[0].LayoutText := 'Polish Typographic by Kirkouski';
  Layouts[0].LangId := '0415';
  Layouts[0].ComponentName := 'polish';

  Layouts[1].DllName := 'rutypo.dll';
  Layouts[1].LayoutText := 'Russian Typographic by Kirkouski';
  Layouts[1].LangId := '0419';
  Layouts[1].ComponentName := 'russian';

  Layouts[2].DllName := 'ustypo.dll';
  Layouts[2].LayoutText := 'US+POL Typographic by Kirkouski';
  Layouts[2].LangId := '0409';
  Layouts[2].ComponentName := 'us';
end;

function FindInstalledKLID(DllName: String): String;
var
  Subkeys: TArrayOfString;
  I: Integer;
  LayoutFile: String;
begin
  Result := '';
  if RegGetSubkeyNames(HKEY_LOCAL_MACHINE, KB_REG_BASE, Subkeys) then
  begin
    for I := 0 to GetArrayLength(Subkeys) - 1 do
    begin
      if RegQueryStringValue(HKEY_LOCAL_MACHINE,
           KB_REG_BASE + '\' + Subkeys[I], 'Layout File', LayoutFile) then
      begin
        if CompareText(LayoutFile, DllName) = 0 then
        begin
          Result := Subkeys[I];
          Exit;
        end;
      end;
    end;
  end;
end;

function FindNextLayoutId: String;
var
  Subkeys: TArrayOfString;
  I, Id: Integer;
  IdStr: String;
  UsedIds: array[0..4095] of Boolean;
begin
  for I := 0 to 4095 do
    UsedIds[I] := False;

  if RegGetSubkeyNames(HKEY_LOCAL_MACHINE, KB_REG_BASE, Subkeys) then
  begin
    for I := 0 to GetArrayLength(Subkeys) - 1 do
    begin
      if RegQueryStringValue(HKEY_LOCAL_MACHINE,
           KB_REG_BASE + '\' + Subkeys[I], 'Layout Id', IdStr) then
      begin
        Id := StrToIntDef('$' + IdStr, -1);
        if (Id >= 0) and (Id <= 4095) then
          UsedIds[Id] := True;
      end;
    end;
  end;

  for I := LAYOUT_ID_MIN to LAYOUT_ID_MAX do
  begin
    if not UsedIds[I] then
    begin
      Result := Format('%.4x', [I]);
      Exit;
    end;
  end;

  RaiseException('No available Layout Id in range');
end;

function FindNextKLID(LangId: String): String;
var
  Prefix: Integer;
  Candidate, FullPath: String;
begin
  for Prefix := KLID_PREFIX_MIN to KLID_PREFIX_MAX do
  begin
    Candidate := Format('%.4x', [Prefix]) + LowerCase(LangId);
    FullPath := KB_REG_BASE + '\' + Candidate;
    if not RegKeyExists(HKEY_LOCAL_MACHINE, FullPath) then
    begin
      Result := Candidate;
      Exit;
    end;
  end;

  RaiseException('No available KLID for language ' + LangId);
end;

procedure RemovePreloadEntry(KLID: String);
var
  Hives: array[0..1] of Cardinal;
  HivePaths: array[0..1] of String;
  H, I, J: Integer;
  SubsPath, PreloadPath: String;
  ValueNames: TArrayOfString;
  ValueData: String;
  SubsToRemove: TArrayOfString;
  SubsCount: Integer;
  Remaining: TArrayOfString;
  RemCount: Integer;
begin
  Hives[0] := HKEY_CURRENT_USER;
  HivePaths[0] := 'Keyboard Layout';
  Hives[1] := HKEY_USERS;
  HivePaths[1] := '.DEFAULT\Keyboard Layout';

  for H := 0 to 1 do
  begin
    SubsPath := HivePaths[H] + '\Substitutes';
    PreloadPath := HivePaths[H] + '\Preload';
    SubsCount := 0;
    SetArrayLength(SubsToRemove, 16);

    if RegGetValueNames(Hives[H], SubsPath, ValueNames) then
    begin
      for I := 0 to GetArrayLength(ValueNames) - 1 do
      begin
        if RegQueryStringValue(Hives[H], SubsPath, ValueNames[I], ValueData) then
        begin
          if CompareText(ValueData, KLID) = 0 then
          begin
            if SubsCount < 16 then
            begin
              SubsToRemove[SubsCount] := ValueNames[I];
              Inc(SubsCount);
            end;
            RegDeleteValue(Hives[H], SubsPath, ValueNames[I]);
          end;
        end;
      end;
    end;

    if RegGetValueNames(Hives[H], PreloadPath, ValueNames) then
    begin
      RemCount := 0;
      SetArrayLength(Remaining, GetArrayLength(ValueNames));

      for I := 0 to GetArrayLength(ValueNames) - 1 do
      begin
        if RegQueryStringValue(Hives[H], PreloadPath, ValueNames[I], ValueData) then
        begin
          if CompareText(ValueData, KLID) = 0 then
          begin
            RegDeleteValue(Hives[H], PreloadPath, ValueNames[I]);
            Continue;
          end;

          for J := 0 to SubsCount - 1 do
          begin
            if CompareText(ValueData, SubsToRemove[J]) = 0 then
            begin
              RegDeleteValue(Hives[H], PreloadPath, ValueNames[I]);
              ValueData := '';
              Break;
            end;
          end;

          if ValueData <> '' then
          begin
            Remaining[RemCount] := ValueData;
            Inc(RemCount);
          end;
        end;
      end;

      if RemCount < GetArrayLength(ValueNames) then
      begin
        if RegGetValueNames(Hives[H], PreloadPath, ValueNames) then
          for I := 0 to GetArrayLength(ValueNames) - 1 do
            RegDeleteValue(Hives[H], PreloadPath, ValueNames[I]);

        for I := 0 to RemCount - 1 do
          RegWriteStringValue(Hives[H], PreloadPath,
            IntToStr(I + 1), Remaining[I]);
      end;
    end;
  end;
end;

procedure InstallLayout(Index: Integer);
var
  KLID, LayoutId, RegPath: String;
begin
  KLID := FindInstalledKLID(Layouts[Index].DllName);
  if KLID <> '' then
  begin
    RemovePreloadEntry(KLID);
    RegDeleteKeyIncludingSubkeys(HKEY_LOCAL_MACHINE, KB_REG_BASE + '\' + KLID);
    Log('Removed existing KLID: ' + KLID);
  end;

  LayoutId := FindNextLayoutId;
  KLID := FindNextKLID(Layouts[Index].LangId);
  RegPath := KB_REG_BASE + '\' + KLID;

  RegWriteStringValue(HKEY_LOCAL_MACHINE, RegPath,
    'Layout File', Layouts[Index].DllName);
  RegWriteStringValue(HKEY_LOCAL_MACHINE, RegPath,
    'Layout Text', Layouts[Index].LayoutText);
  RegWriteExpandStringValue(HKEY_LOCAL_MACHINE, RegPath,
    'Layout Display Name',
    '@%SystemRoot%\system32\' + Layouts[Index].DllName + ',-100');
  RegWriteStringValue(HKEY_LOCAL_MACHINE, RegPath,
    'Layout Id', LayoutId);

  InstalledKLIDs[Index] := KLID;
  Log('Installed ' + Layouts[Index].LayoutText + ': KLID=' + KLID + ', LayoutId=' + LayoutId);
end;

procedure UninstallLayout(Index: Integer);
var
  KLID: String;
begin
  KLID := FindInstalledKLID(Layouts[Index].DllName);
  if KLID = '' then
    Exit;

  RemovePreloadEntry(KLID);
  RegDeleteKeyIncludingSubkeys(HKEY_LOCAL_MACHINE, KB_REG_BASE + '\' + KLID);
  Log('Uninstalled ' + Layouts[Index].LayoutText + ': KLID=' + KLID);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  I: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    InitLayouts;
    for I := 0 to 2 do
    begin
      if WizardIsComponentSelected(Layouts[I].ComponentName) then
        InstallLayout(I);
    end;

    MsgBox(CustomMessage('RebootWarningBody'), mbCriticalError, MB_OK);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  I: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    InitLayouts;
    for I := 0 to 2 do
      UninstallLayout(I);
  end;
end;

function InitializeSetup: Boolean;
begin
  InitLayouts;
  Result := True;
end;
