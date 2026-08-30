@echo off
chcp 65001 >nul
title Asansor Avan Hesaplama Programi
cd /d "%~dp0"

echo.
echo ==============================================================
echo    ASANSOR AVAN HESAPLAMA PROGRAMI
echo ==============================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo   Python bulunamadi.
  echo   https://www.python.org/downloads/ adresinden Python 3 kurun
  echo   ^(kurulumda "Add Python to PATH" secenegini isaretleyin^)
  echo   ve bu dosyayi yeniden cift tiklayin.
  echo.
  pause & exit /b 1
)

if not exist ".venv" (
  echo   Ilk kurulum yapiliyor ^(yalniz bir kez, ~1 dakika^)...
  python -m venv .venv || (echo   Sanal ortam olusturulamadi. & pause & exit /b 1)
  .venv\Scripts\python.exe -m pip install --upgrade pip -q
  .venv\Scripts\python.exe -m pip install -r requirements.txt -q || (
     echo   Kurulum basarisiz - internet baglantinizi kontrol edin. & pause & exit /b 1)
  echo   Kurulum tamamlandi.
  echo.
)

.venv\Scripts\python.exe main.py
echo.
pause
