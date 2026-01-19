@echo off
REM GeoDataHub QGIS Plugin Installation Script for Windows

echo ========================================
echo GeoDataHub QGIS Plugin Installer
echo ========================================
echo.

REM Find QGIS plugin directory
set "QGIS_PLUGINS=%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins"

echo QGIS plugins directory: %QGIS_PLUGINS%
echo.

REM Create plugins directory if it doesn't exist
if not exist "%QGIS_PLUGINS%" (
    echo Creating plugins directory...
    mkdir "%QGIS_PLUGINS%"
)

REM Create geodatahub plugin directory
set "PLUGIN_DIR=%QGIS_PLUGINS%\geodatahub"

if exist "%PLUGIN_DIR%" (
    echo Removing existing installation...
    rmdir /s /q "%PLUGIN_DIR%"
)

echo Creating plugin directory...
mkdir "%PLUGIN_DIR%"
mkdir "%PLUGIN_DIR%\icons"

REM Copy plugin files
echo Copying plugin files...
copy "%~dp0__init__.py" "%PLUGIN_DIR%\"
copy "%~dp0metadata.txt" "%PLUGIN_DIR%\"
copy "%~dp0geodatahub_plugin.py" "%PLUGIN_DIR%\"
copy "%~dp0geodatahub_dialog.py" "%PLUGIN_DIR%\"
copy "%~dp0recommendation_dialog.py" "%PLUGIN_DIR%\"
copy "%~dp0icons\icon.svg" "%PLUGIN_DIR%\icons\"

REM Copy core geodatahub package
echo Copying GeoDataHub core package...
xcopy "%~dp0..\geodatahub" "%PLUGIN_DIR%\geodatahub\" /E /I /Q

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Next steps:
echo 1. Open QGIS
echo 2. Go to Plugins ^> Manage and Install Plugins
echo 3. Find "GeoDataHub" in the Installed tab
echo 4. Enable the plugin
echo.
echo NOTE: Make sure required Python packages are installed in QGIS Python:
echo   - eodag
echo   - requests
echo.
pause
