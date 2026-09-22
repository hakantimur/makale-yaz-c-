@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam olusturuluyor...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if not exist ".env" (
    copy .env.example .env >nul
    echo .env dosyasi olusturuldu. OPENROUTER_API_KEY degerini girmeyi unutma ^(veya uygulama acildiktan sonra sidebar'dan gir^).
)

streamlit run app.py
pause
