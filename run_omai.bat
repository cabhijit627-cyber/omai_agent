@echo off

cd /d C:\Users\cabhi\omai_agent

start cmd /k "ollama serve"

timeout /t 5

call .venv\Scripts\activate

python -m streamlit run omai_agent.py

pause