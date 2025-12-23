@echo off
setlocal enabledelayedexpansion

cd /d E:\TLCN\BE_py\book-platform\recommendation-service

REM ==== Log file (overwrite mỗi lần chạy) ====
set LOG_DIR=E:\TLCN\BE_py\book-platform\recommendation-service\logs
set LOG=%LOG_DIR%\daily_recommend_jobs.log

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo ==== START %date% %time% ==== > "%LOG%"

REM ==== Python exe ====
set PY=E:\TLCN\BE_py\book-platform\.venv\Scripts\python.exe

REM ==== 1) Build CB TF-IDF ====
echo [1/4] Build TFIDF... >> "%LOG%"
%PY% E:\TLCN\BE_py\book-platform\recommendation-service\recommend_app\services\content_based\build_cb_tfidf.py >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] TFIDF failed. >> "%LOG%"
  goto :END
)

REM ==== 2) Build CF_IMPLICIT ====
echo [2/4] Build CF_IMPLICIT... >> "%LOG%"
%PY% E:\TLCN\BE_py\book-platform\recommendation-service\recommend_app\services\collab_filtering\build_cf_implicit.py >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] CF_IMPLICIT failed. >> "%LOG%"
  goto :END
)

REM ==== 3) Build CF_PURCHASE ====
echo [3/4] Build CF_PURCHASE... >> "%LOG%"
%PY% E:\TLCN\BE_py\book-platform\recommendation-service\recommend_app\services\collab_filtering\build_cf_purchase.py >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] CF_PURCHASE failed. >> "%LOG%"
  goto :END
)

REM ==== 4) Rebuild user CF cache (recommendations) ====
REM args: active_days history_days topn
echo [4/4] Rebuild CF recommendations for active users... >> "%LOG%"
%PY% E:\TLCN\BE_py\book-platform\recommendation-service\recommend_app\services\collab_filtering\rebuild_user_cf_batch.py 30 90 50 >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] rebuild_user_cf_batch failed. >> "%LOG%"
  goto :END
)

:END
echo ==== END %date% %time% ==== >> "%LOG%"
endlocal
