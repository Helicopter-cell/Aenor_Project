@echo off
chcp 65001 > nul

powershell -Command "git add ."
powershell -Command "git commit -m 'Mise à jour de la page d'accueil pour l'adapter aux nouvelles pages'"
powershell -Command "git push"

echo commit mit à jour jusqu'a github !
pause