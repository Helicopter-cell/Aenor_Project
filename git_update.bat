@echo off
chcp 65001 > nul
powershell -Command "git add ."
powershell -Command "git commit -m 'Amélioration de `cours.html` pour la lecture phonétique et alphabet français.'"
powershell -Command "git push"

echo commit mit à jour dans github.com !
pause