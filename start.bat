@echo off
cd %~dp0
call .venv\Scripts\activate
.venv\Scripts\python.exe main.py
call deactivate