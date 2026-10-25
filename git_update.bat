@echo off
chcp 65001 > nul

powershell -Command "git add ."
echo git add. effectué !
pause

powershell -Command "git commit -m 'ae_2.4 | amélioration du traitement/architecture de la traduction d`IA et passage au modèle par défaut gemini-3.1-pro-preview (lorsque que PAIEMENT_ACTIVEE == False)'"
echo git commit effectué !
pause

powershell -Command "git push"
echo git push effectué !

echo commit mit à jour jusqu'a github !
pause