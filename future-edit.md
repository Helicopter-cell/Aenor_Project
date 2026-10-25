## Graph obsidian (oui encore) : 
- rajouter un bouton  "ouvrir tout" et "fermer tout"

## Style page d'acceuil: 
J'adore les SVG dans les cartes, mais c'est dommage qu'il ne soit visible que au `:hover`. je propose donc de faire en sorte qu'ils soit visible tout le temps, mais que le :hover lance l'animation du SVG.

## `grammaire_3.html` :
Faire en sorte de "supprimer" de la template la "carte d'accordéon" qui contient toutes les autres : Il y a actuellement "Manuel de Référence & Grammaire Officielle de l'Aënor" qui est affiché au milieux, tout seule.

##  `obj_project` :
La page ne s'affiche tout simplement pas, liéé à un problème Flask.
Hypothèses de localisation du problème :

- Routes flask
- Test des modules et des routes
- Syntaxes du liens


## Modifier print global prompt :
Je veux que la fonction log le `nom` de tout les fichiers et leur destination, mais pas leur contenu.
Je veux aussi que print global prompt log le nom du model utilisé (gemini 3.5 pro, 3.6 flash ou jsp quoi)


# Logique de traduction des nombres et unités :
À ce stade, la traduction d'entrée en français : 30 km donne une ouput Aënor : 26 km.
Je veux donc franchir une étape supplémentaire, pour que cette traduction s'occupe également des unité. Génère moi un prompt complet à envoyer pour faire cette modification. Tu trouvera ci-dessou un descriptif du fonctionnement des nombres en aenor (extrait du manuel)
---
### 2.10 Le système numérique

#### 2.10.1 La base douze

L'Aënor compte en **base douze**. Ce choix repose sur la grande divisibilité de douze (par 2, 3, 4 et 6), qui facilite les calculs et les fractions. Chaque nombre a aussi une valeur symbolique : les nombres sont des concepts autant que des outils de calcul.

#### 2.10.2 Les chiffres

| Valeur | Chiffre | Nom | Valeur symbolique |
|---|---|---|---|
| 0 | `0` | `oro` | le Vide, l'absence, le néant |
| 1 | `1` | `val` | l'Origine, l'unité, le commencement |
| 2 | `2` | `der` | le Reflet, la dualité, l'équilibre |
| 3 | `3` | `vay` | le Chemin, la progression, le mouvement |
| 4 | `4` | `drèb` | les Racines, la stabilité, les fondations |
| 5 | `5` | `dar` | la Main, l'action, la création |
| 6 | `6` | `mel` | l'Équilibre, l'harmonie parfaite |
| 7 | `7` | `§yèl` | les Astres, le voyage, l'influence céleste |
| 8 | `8` | `cayr` | le Cycle, le retour, le renouvellement |
| 9 | `9` | `drav` | le Destin, les choix et leurs conséquences |
| dix | `°` | `µar` | la Transformation, le changement profond |
| onze | `¤` | `vèl` | l'Accomplissement, l'achèvement d'un cycle |

**Remarque.** Les noms de nombres sont des mots à part entière, parfois homophones de noms communs (`dar` cinq et `dar` bois, `mel` six). La position dans le GN, après le nom, suffit à lever toute ambiguïté.

#### 2.10.3 Les puissances

Au-delà de onze, on utilise la notation positionnelle. Deux mots nomment les premières puissances de douze :

| Valeur (base 10) | Écriture (base 12) | Nom | Valeur symbolique |
|---|---|---|---|
| 12 | `10` | `val²oro` | un cycle, le Premier Cycle complet |
| 144 | `100` | `gor²oro` | un grand cycle (12²) |

**Correspondances usuelles :**

| Base 10 | Base 12 | Lecture |
|---|---|---|
| 12 | `10` | `val²oro` |
| 13 | `11` | `val²oro val` |
| 24 | `20` | `der val²oro` |
| 36 | `30` | `vay val²oro` |
| 144 | `100` | `gor²oro` |
| 1728 | `1000` | `val²oro gor²oro` |

#### 2.10.4 Composition des nombres

Un nombre se lit en composant le **coefficient** et la **puissance** :

1. Le coefficient précède son mot de puissance : `der val²oro` = 2 × 12 = 24.
2. Le coefficient `1` devant un mot de puissance est omis : `gor²oro` = 144.
3. Une suite de composants **décroissants s'additionne** ; une suite **croissante se multiplie**.

```
27   (base 10)  =  23   (base 12)      der val²oro vay              (24 + 3)
171  (base 10)  =  123  (base 12)      gor²oro der val²oro vay      (144 + 24 + 3)
143  (base 10)  =  ¤¤   (base 12)      vèl val²oro vèl              (132 + 11)
288  (base 10)  =  200  (base 12)      der gor²oro                  (2 × 144)
1728 (base 10)  =  1000 (base 12)      val²oro gor²oro              (12 × 144)
```

Les grands nombres peuvent se lire chiffre à chiffre dans un contexte technique.

#### 2.10.5 Syntaxe des cardinaux

Les cardinaux suivent le nom, après les adjectifs, en position de numéral (§2.2.1) :

```
can         vay             « trois chiens »
can    gorè    vay          « trois grands chiens »
can    der val²oro vay      « vingt-sept chiens »     (base 10)
```

Un numéral ne se combine pas avec un quantificateur dans le même GN. Un cardinal peut former un GN à lui seul : `na vay` (trois, en patient).

#### 2.10.6 Les ordinaux

Les ordinaux se forment par le suffixe **`-ayn`** ajouté au nom du nombre. Ils occupent la position du numéral dans le GN :

| Cardinal | Ordinal |
|---|---|
| `val` | `valayn` : premier |
| `der` | `derayn` : deuxième |
| `vay` | `vayayn` : troisième |
| `val²oro` | `val²oroayn` : douzième |

```
var     valayn            « le premier homme »
can     vayayn            « le troisième chien »
```

Dans un nombre composé, `-ayn` s'ajoute au dernier composant : `der val²oro vayayn` (le vingt-septième, en base 10).

#### 2.10.7 Les fractions

Une fraction se dit par le numérateur suivi de l'ordinal du dénominateur : `val derayn` (une moitié), `val vayayn` (un tiers), `der vayayn` (deux tiers), `val drèbayn` (un quart).

---

### 2.11 La dérivation

#### 2.11.1 Les morphèmes productifs

| Morphème | Fonction | Exemple |
|---|---|---|
| `-è` | nom → adjectif | `dyad` (magie) → `dyadè` (magique) |
| `-o` (statif) | adjectif → verbe d'état | `gorè` → `goro` |
| `-ay` | adjectif → adverbe | `vèlnè` → `vèlnèay` |
| `-a` | verbe → interjection | cavexo → cavexa |
| `-èn` | racine → nom abstrait (état, qualité, résultat) | `silèn` (secret), `valèn` (vérité), `dravèn` (destin), `serèn` (promesse) |
| `-ar` | racine → nom d'agent ou de profession | `limar` (pêcheur) |
| `-ayn` | cardinal → ordinal | `valayn` |
| `-öj` | pronom → possessif | `röj` |
| `yu`, `sal`, `²oro` | radical interrogatif → indéfini | `µoyu` |

Quelques noms d'agent figés utilisent d'autres finales (`-ec`, `-an` : `modec` boulanger, `aorec` berger, `doran` fermier, `vosec` chef).
