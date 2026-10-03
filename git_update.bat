@echo off
chcp 65001 > nul

powershell -Command "git add ."
echo git add. effectué !
pause

powershell -Command "git commit -m 'Enfin, Aënor v2 Whoooohohoo'"
echo git commit effectué !
pause

powershell -Command "git push"
echo git push effectué !

echo commit mit à jour jusqu'a github !
pause