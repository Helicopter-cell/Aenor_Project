## Idée 1 :
Créer un booléenne 'autoriser l'apprentissage' controlable par l'utilisateur :

    True : L'IA rédigera 3 petits paragraphes :

        - Une explication des difficultés rencontrée dans la traducion(si c'est le cas) vis à vis de la grammaire, du lexique, ou de quelconque explication manquante.

        - Une critique du l'inspiration trop "facilement oriental" de la langue (uniquement par rapport à la phrase traduite : si un élément est critiquable, mais non-présent dans al phrase, ça n'est pas un sujet.);
    
    False : Traduction classique, comme actuellement.

La traductions restera au même format qu'avant (La phrase seule), mais pour le commentaire concerné, ils seront encadré par la séquence de symboles : |@|
Par exemple :
|@|Il m'a manqué des informations vis à vis des expressions idiomatiques.
Mais il est pourtant trop "facilement orientale" d'écrire "il pleut des cordes".|@|

Il faut donc prévoir :
- Un .json qui contiendra la traductions ET leurs commentaires cncerné. 
- Un script python qui enlèvera les commentaires de l'output de traductions, dans les deux sens, ae2fr et fr2ae. (en utilisant le fait que ces commmentaires soit entre |@|)
- Deux autres versions de prompt : ae2fr_comment et fr2ae_comment, où uniquement leur prompt système sera modifié, en passant toujours 'par conlang-update.py'

---

## Idée 2 : 
Rajouter une booléenne 'traductions fiable' controlable par les utilisateur dans 'IA-trad.html'.
    True :
        -> Enverra la traduction classique, (en prenant en compte la valeurs booléenne de 'autoriser l'apprentissage')

        -> Enverra la réponse à l'aide du prompt d'exercice, pour vérifier la véracité de la traduction :

            -> Si la note est supperieur ou égale à **9/10** : la réponse de la traductions classique est donc affiché normalement

            -> Si la note est **inferieur à 9/10** : la traduction sera renvoyée avec un autre prompt :
                - Une explication de la situation
                - l'input ET l'output de la première étape
                - la *"réponse du professeur"*
                - fin du prompt systeme demandant de corriger selon les critiques précédentes. 

    False : Comme avant, traduction normale, et prends en compte la valeur de 'autoriser l'apprentissage'.

---

## Idée 3 :
Créer un compte 'loginless' basée sur l'IP à chaque nouvelle utilisateur qui arrive sur le site.

Il pourra ainsi voir les précédentes traductions que l'utilisateur, et uniquement lui-même (et l'admin) pourra voir ses anciennes traductions, et/ou ces anciens exercices corrigée.

Il faut donc prévoir :
    - Un moyen de mémiriser les exercices ET leur correction
    - Une nouvelle page pour cette fonction, comme 'historique.html' qui affichera : un tableau avec toutes les traductions déjà fait, et tout les exetcices ET leur correction.
    - Un moyen de mémoriser toutes ces information **en fonction de l'IP concerné**
