@echo off
chcp 65001 > nul

powershell -Command "git add ."
powershell -Command "git commit -m 'Séparation des JS'"
powershell -Command "git push"

echo commit mit à jour jusqu'a github !
pause