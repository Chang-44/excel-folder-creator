@echo off
chcp 65001 >nul
echo === 安装依赖 ===
pip install -r requirements.txt

echo === 开始打包 ===
pyinstaller --noconfirm --clean ^
  --name "Excel文件夹创建工具" ^
  --windowed ^
  --onefile ^
  --collect-all ttkbootstrap ^
  --hidden-import openpyxl ^
  --hidden-import xlrd ^
  main.py

echo === 完成，exe 在 dist/ 目录 ===
pause