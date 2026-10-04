@echo off
chcp 65001 > nul

powershell -Command "git add ."
echo git add. effectué !
pause

powershell -Command "git commit -m 'ae_2.2 (c`est tjr la merde dans `path_index.json`)'"
echo git commit effectué !
pause

powershell -Command "git push"
echo git push effectué !

echo commit mit à jour jusqu'a github !
pause