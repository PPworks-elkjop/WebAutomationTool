@echo off
echo ================================================================================
echo Vusion Manager Pro API Setup and Test - Elkjop SE Lab
echo ================================================================================
echo.
echo This script will:
echo   1. Configure your Vusion Manager Pro API key
echo   2. Test the connection to elkjop_se_lab
echo   3. Display gateway/AP status information
echo.
echo ================================================================================
echo.
pause
echo.

echo Step 1: Configuring API key...
echo ================================================================================
python configure_vusion_se_lab.py
echo.

if %ERRORLEVEL% NEQ 0 (
    echo Error occurred during configuration.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo Step 2: Testing API connection...
echo ================================================================================
echo.
python test_elkjop_se_lab.py
echo.

echo ================================================================================
echo Setup and test complete!
echo ================================================================================
echo.
pause
