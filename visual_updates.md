# Rapport de direction artistique — Aënor

## Diagnostic d’ensemble
L’identité actuelle évoque déjà un **atelier forestier nocturne** : fond minuit, verts profonds, accents cuivre, typographie Aënor réservée aux formes de la langue, et lueurs discrètes. Le socle est cohérent et distinctif. Mais l’expérience demeure surtout une collection d’outils sur une même palette : l’univers se ressent dans les composants, moins dans le récit, le rythme et la mise en scène des parcours.

## Points forts à préserver
- **Palette mémorable et structurée** : les tokens du `design system` distinguent bien nuit, forêt, terre et cuivre. Le contraste clair sur sombre soutient la lecture.
- **Signature linguistique authentique** : l’écriture Aënor dans le lexique, les exemples de grammaire et les exercices donne à la conlang une présence concrète.
- **Bonne matière interactive** : les cartes-portes SVG de l’`accueil`, les accordéons du `lexique` et de la `grammaire`, ainsi que la carte de notes `Scénario`, sont de bons supports d’immersion.
- **Premières finitions présentes** : la base `CSS` apporte une profondeur atmosphérique ; boutons et cartes ont des survols et lueurs ; la réduction des animations est prise en compte.

## Axes majeurs d’amélioration

### 1. Donner une narration au premier écran
L’`accueil` commence directement par « Où souhaitez-vous aller ? », puis propose six cartes de poids comparable. Il manque un seuil d’entrée dans l’univers : une courte accroche sur la langue, un motif ou sceau Aënor, et une mise en avant des deux parcours principaux. Je recommande une composition en **couverture de manuscrit** : titre éditorial, phrase d’ambiance, puis portes de navigation. Garder les SVG animés, mais faire de leur animation un rituel bref au survol/focus plutôt qu’un simple effet décoratif.

La navigation de `base.html` est fonctionnelle mais très utilitaire : un nom de marque ou symbole discret et un état visuel de page active renforceraient l’orientation et la continuité avec l’accueil.

### 2. Créer du rythme entre les pages-outils
Le même fond sombre et les mêmes surfaces arrondies risquent de rendre lexique, traducteur, exercice et historique trop interchangeables. Garder un langage commun, mais attribuer à chaque page un geste visuel :
- `Traducteur` : deux états clairement lisibles — texte source et réponse — comme deux colonnes d’un feuillet qui se répondent ; donner à la réponse une vraie qualité de destination.
- `Exercice` : traiter la consigne comme un défi bref, avec une hiérarchie nette consigne → saisie → validation, plutôt qu’un grand titre suivi d’un champ isolé.
- `Lexique` : accentuer la sensation de page de dictionnaire et la distinction visuelle entre graphie, translittération, prononciation et français.
- `Historique` : éviter les ruptures d’espacement faites par plusieurs `<br>` et en faire une archive organisée en sections, avec séparateurs et titres cohérents.

### 3. Réserver la lumière et la terre aux points d’accroche
Les lueurs cuivre sont pertinentes sur les CTA, cartes survolées, accordéons ouverts et focus. Leur multiplication uniforme les banaliserait. Je recommande une hiérarchie : **cuivre lumineux pour l’action**, cuivre doux pour les contours, terre brune pour les surfaces secondaires et séparateurs, blanc pour les contenus et l’état actif. Le marron `#4A3319` étant naturellement sombre, l’utiliser en mélange ou en filet plutôt qu’en grand aplat derrière du texte clair.

La matière peut venir de superpositions très fines — reflet en bord haut, halo radial éloigné, grain presque imperceptible — plutôt que de textures fortes. Les transitions doivent rester courtes et posées ; les ombres lumineuses se déclenchent sur les éléments interactifs, pas sur tous les blocs au repos. Les règles partagées des `cartes`, `boutons` et de la `navigation` sont les bons leviers.

## Direction créative proposée : « Le cabinet des voix »
Imaginer Aënor comme un **lieu de conservation et de découverte d’une langue vivante** : le vert évoque le refuge végétal, la terre la matière des tablettes, le cuivre les annotations et la lumière du savoir. Chaque page serait un espace de ce cabinet — portes, atelier de traduction, salle des exercices, pages du lexique, atlas des notes.

## Ordre de priorité recommandé
1. Recomposer l’accueil comme une véritable entrée, avec identité et priorités de navigation.
2. Donner des compositions spécifiques aux pages Traducteur et Exercice, tout en mutualisant leurs composants.
3. Appliquer la lumière cuivre de façon sélective et renforcer les séparateurs/surfaces terreuses secondaires.
4. Faire une passe responsive et accessibilité : focus, lisibilité des états, réduction du mouvement et maintien du contraste.