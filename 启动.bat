@echo off
chcp 65001 >nul
title 文件翻译工具箱 v1.3.2
set PYTHONPATH=%CD%\src
"C:\Users\ASUS\AppData\Local\Python\pythoncore-3.14-64\python.exe" -c "from file_toolbox.main import main; main()"
