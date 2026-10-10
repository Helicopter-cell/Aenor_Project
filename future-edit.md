## Graph obsidian (oui encore) : 
- rajouter un bouton  "ouvrir tout" et "fermer tout"

## Style page d'acceuil: 
J'adore les SVG dans les cartes, mais c'est dommage qu'il ne soit visible que au :hover. je propose donc de faire en sorte qu'ils soit visible tout le temps, mais que le :hover lance l'animation du SVG.

## `grammaire_3.html` :
Faire en sorte de "supprimer" de la template la "carte d'accordéon" qui contient toutes les autres : Il y a actuellement "Manuel de Référence & Grammaire Officielle de l'Aënor" qui est affiché au milieux, tout seule.

##  `obj_project` :
La page ne s'affiche tout simplement pas, liéé à un problème Flask.
Hypothèses de localisation du problème :

- Routes flask
- Test des modules et des routes
- Syntaxes du liens

## Logique de traduction par IA :

### pt1 :
Actuellement, les prompts systèmes générer par `conlang-update.py` sont contradictoire vis-à-vis des indications liée à la gestion des nomnbres/bases ; 
- Le prompt ordonne à l'IA de conserver en décimale les nombres, et de les entourer de pourcentages pour les convertir en base 12. Le prompt évoque l'exemple %63%.
- Mais là vient la contradiction : le manuel garde la base 12, pouvant perturber l'IA, mais surtout présente de nouvelles uinités de mesure, dépendant donc de cette base.

Je suggère donc de modifier les prompt ainsi que les modules convertisseur pour respecter cette nouvelle logique : (on prendra ici le cas de fr2ae classique, mais la logique est renversable et repliquable.)
- L'IA conservera les nombres et leurs unités (diminué, du type kilomètre -> km, ou km -> km), mais toujours entre %. (Par exemple : %63 km%)
- Le module python fonctionnant sous regex (actuellement `base converter.py`) calculera et remplacera ces valeurs/unités par leurs équivalent Aënor.

Exemple étéape par étape :

1. L'utilisateur rentre : 63 kilomètre plus loins.
2. L'IA ressortira : %63 km% {traduction de plus loins}
3. Le module de conversion écrira si il existe en Aënor un unité équivalente à 1km : 53 {unité Aënor} {traduction de plus loins}
4. L'output  sera donc : 53 {unité Aënor} {traduction de plus loins}

### pt2 :
Actuellement, je crois que les prompt construit sont envoyé directe, mais il me semble qu'il y a un port spécifique à la gestion du contexte, qui serait bien plus adapté à notre énorme manuel.

Voilà comment je songerais répartire le tout :
- Contexte : Manuel
- Pièce jointe : Lexique
- Texte : Prompt système + phrase à traduire

Cella aiderais l'ia sur deux points principaux :
- Les ports seront plus adapté (en effet on utilise chaque ports pour sont utilité)
- Mais surtout ça sépare tout, en organisant les documents fournit à l'IA : Il n'y à plus de confusion, le prompt système n'est plus noyé au milieu du manuelle, le lexique est séparé du manuelle pour ne pas mélangers ces deux aspects etc...

Je pense que ça améliorerait considérablement les résultat et peut être même performance. Cette augmentation de performance sera doublé si on prend en compte le mode "traduction fiable".