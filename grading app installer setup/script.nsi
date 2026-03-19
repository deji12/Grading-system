!include "MUI.nsh"

Name "Grading App"
InstallDir "$DESKTOP\Grading App"
OutFile "GradingAppSetup.exe"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "" 
    SetOutPath $INSTDIR
    
    File "GradingApp.exe"
    File "config.json"
SectionEnd