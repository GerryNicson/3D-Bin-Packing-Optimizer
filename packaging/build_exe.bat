@echo off
cd /d "%~dp0.."
pyinstaller --onefile --windowed --name BinPacker --paths src packaging/run_gui.py
