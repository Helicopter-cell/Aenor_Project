@echo off
chcp 65001 > nul
powershell -Command "tree /F /A | Select-String -Pattern '__pycache__|\.git|\.vscode|\.pyc' -NotMatch | Out-File -Encoding utf8 arborescence.txt"
echo Arborescence générée dans arborescence.txt !
pause