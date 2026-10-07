@echo off
chcp 65001 > nul

powershell -Command "git add ."
echo git add. effectué !
pause

powershell -Command "git commit -m 'ae_2.3 (c`est tjr la merde dans `path_index.json`) et amélioration des graphes de `scenario.html` ENCORE. (moins de latence, amélioration de la physique des cartes)'"
echo git commit effectué !
pause

powershell -Command "git push"
echo git push effectué !

echo commit mit à jour jusqu'a github !
pause