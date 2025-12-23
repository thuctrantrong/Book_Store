@echo off
setlocal

REM ==== Config ====
set PROJECT_DIR=E:\TLCN\BE_py\book-platform\search-service
set VENV_PY=E:\TLCN\BE_py\book-platform\.venv\Scripts\python.exe
set LOG_DIR=%PROJECT_DIR%\logs
set LOG_FILE=%LOG_DIR%\sync_incremental.log

REM ==== Ensure logs folder exists ====
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM ==== START log ====
echo ================================================== > "%LOG_FILE%"
echo [START] %date% %time% >> "%LOG_FILE%"

REM ==== Go to project root ====
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo [ERROR] Cannot cd to %PROJECT_DIR% >> "%LOG_FILE%"
    echo [END] %date% %time% >> "%LOG_FILE%"
    exit /b 1
)

REM ==== Check python in venv ====
if not exist "%VENV_PY%" (
    echo [ERROR] venv python not found: %VENV_PY% >> "%LOG_FILE%"
    echo [END] %date% %time% >> "%LOG_FILE%"
    exit /b 1
)

REM ==== Check OpenSearch ====
"C:\Windows\System32\curl.exe" -k -s https://localhost:9200 >nul 2>&1
if errorlevel 1 (
    echo [ERROR] OpenSearch is DOWN >> "%LOG_FILE%"
    echo [END] %date% %time% >> "%LOG_FILE%"
    exit /b 1
)

REM ==== Run job ====
"%VENV_PY%" -m search_app.jobs.sync_incremental >> "%LOG_FILE%" 2>&1

REM ==== END ====
echo [END] %date% %time% >> "%LOG_FILE%"

endlocal
