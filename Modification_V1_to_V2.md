# Aënor V2.0 : reconstruction globale

**Conventions.** Les formes aënores sont en `code` et suivent l'orthographe V2 (§1). Un ✦ signale un mot ou un morphème créé ou modifié par la V2. Les codes (I5, E2, M4…) renvoient à ton audit.

---

## 0. Principes directeurs

La V1 empilait deux logiques. La V2 les sépare franchement, selon une règle unique :

> **Dans le groupe, la tête vient d'abord. Dans la proposition, le verbe vient en dernier.**

C'est le profil du persan ou du sumérien (verbe final, mais nom + adjectif + possesseur, prépositions). Il est attesté et stable. Il lève I19 en transformant la disharmonie en règle.

| Principe | Décision V2 | Audit |
|---|---|---|
| **P1. Thème libre, rôles explicites** | Le premier groupe est le thème. Chaque groupe dit son rôle par un *relateur*. Seul le thème-sujet peut rester nu. | I5, I6, I20, M4 |
| **P2. Pas de calque français** | Plus d'articles, de tu/vous, de conditionnel-temps, de passé composé, de « ne… que » négatif. | E1–E3 |
| **P3. Un gabarit verbal unique** | Onze positions ordonnées. L'ordre fixe la portée de la négation. | I11–I13, M8 |
| **P4. Un symbole, un son** | Valeur fixée pour chaque signe. `²` reçoit un rôle défini. | I1–I3, M1 |
| **P5. Catégories propres** | Clusivité, évidentialité à 3 termes, déixis à 3 termes, politesse par le thème. | E4 |
| **P6. ADN conservé** | Terminaisons `-oy / -o / -è / -ay / b…ya`, verbe en sandwich, point de vue sans passif, pas de sujet fantôme, racines motivées, base 12, négations graduées, `-ca` avec élision. | Phase 1 |

**Profil typologique V2**

| Trait | Valeur |
|---|---|
| Ordre de la proposition | Thème initial, verbe final |
| Alignement | Thème-pivot. Rôles marqués par relateurs prépositifs, thème-sujet nu. |
| Groupe nominal | Tête initiale : N Adj Num Dém Possesseur |
| Relatives et subordonnées | Préposées, closes par un marqueur final |
| Verbe | Préfixes (mode, temps, réfléchi), infixe (aspect), suffixes (négation, modalité, évidentialité) |
| Genre, article | Aucun |
| Nombre | Transnumérique (le nom ne varie jamais) |
| Personne | Clusivité (nous inclusif/exclusif), obviatif |
| Évidentialité | 3 termes + témoin direct |
| Phonologie | 24 consonnes, 8 voyelles |

---

## 1. Phonologie et orthographe V2

### 1.1 Les signes spéciaux

Presque tous les signes de la V1 sont des touches de clavier AZERTY (`§ µ = / ² ° ¤`). C'est une vraie signature, donc je la garde. Je ne remplace que les deux signes qui entrent en collision avec le Markdown et la ponctuation.

| V1 | V2 | Valeur | Décision |
|---|---|---|---|
| `§` | `§` | /ʃ/ (« ch ») | conservé |
| `µ` | `µ` | /ɲ/ (« gn ») | conservé. Valeur fixée. |
| `=` | `=` | /θ/ (« th » anglais) | conservé |
| `/` | `/` | /ʔ/ (coup de glotte) | conservé |
| `*` | **`ë`** | /ə/ (schwa) | remplacé. Définit aussi le `ë` du nom *Aënor*. |
| `;` | **`ö`** | /ø/ (« eu ») | remplacé |
| `²` | `²` | aucun son | rôle défini en §1.6 |
| `°` `¤` | `°` `¤` | chiffres dix et onze | conservés. Repli ASCII : `A` `B`. |

Pour le code, normalise en Unicode NFC. Fais attention à `µ` (U+00B5) et à la lettre grecque `μ` (U+03BC), qui sont deux caractères distincts.

### 1.2 Inventaire

**Consonnes (24)**

| Classe | Graphie → API |
|---|---|
| Occlusives | `p` /p/, `b` /b/, `t` /t/, `d` /d/, `c` /k/ (toujours dur), `g` /g/ (toujours dur), `/` /ʔ/ |
| Affriquées | `ts` /ts/, `dz` /dz/, `dj` /dʒ/ |
| Fricatives | `f` /f/, `v` /v/, `s` /s/, `z` /z/, `§` /ʃ/, `j` /ʒ/, `x` /x/, `=` /θ/ |
| Nasales | `m` /m/, `n` /n/, `µ` /ɲ/ |
| Liquides | `l` /l/, `r` /r/ (battu ou roulé, jamais /ʁ/) |
| Semi-voyelle | `y` /j/ |

Il n'y a ni `k`, `q`, `h`, `w`, ni `c` doux. Les trois digraphes `ts`, `dz`, `dj` sont les seuls de la langue : ils notent une consonne unique.

**Voyelles (8)**

| Graphie | `a` | `e` | `è` | `i` | `o` | `u` | `ë` | `ö` |
|---|---|---|---|---|---|---|---|---|
| API | /a/ | /e/ | /ɛ/ | /i/ | /o/ | /u/ | /ə/ | /ø/ |

- **Pas de voyelles nasales.** `ten`, `µon`, `en` se lisent toujours /ten/, /ɲon/, /en/. Cela règle I2.
- **Diphtongues :** uniquement `ay` /aj/ et `oy` /oj/. `y` est un attaque devant voyelle (`ve.yo` = [ve.jo]) et une coda devant consonne ou en fin de mot (`roy` = [roj]).
- **Hiatus :** les voyelles contiguës restent séparées. Il n'existe pas de /w/, donc `u` devant voyelle reste une voyelle (`y²uao` = [ju.a.o]).
- **`é` disparaît** et fusionne avec `e`. Le contraste é/è était fragile (I3). Le contraste `e` / `è` est conservé : `è` reste la voyelle-signature des adjectifs.

### 1.3 Structure syllabique et phonotactique

**Syllabe : (C)(C)V(C)**, où V est une voyelle ou une diphtongue.

- **Attaque simple :** n'importe quelle consonne, ou aucune.
- **Attaque complexe :** obstruante + `r`, `l` ou `y` (`dr-, cr-, tr-, br-, §y-, ly-…`). Aussi `s` + `b/d/g` (`sbè`).
- **Coda :** une consonne, n'importe laquelle sauf les affriquées.
- **Entre deux voyelles :** trois consonnes au maximum, et la dernière doit être `r`, `l` ou `y` (`za.dro`, `zad.co`).
- **Mots :** surtout bisyllabiques. Verbes en `-o`, adjectifs en `-è`, adverbes en `-ay`.

Cela décrit la sonorité de la V1 (CV(C)V, liquides et nasales abondantes) sans la changer.

### 1.4 Assimilations

| Règle | Énoncé | Exemple |
|---|---|---|
| **R1. Nasale** | `n` → [m] devant `p b m`, → [ŋ] devant `c g x`. L'écriture reste `n`. | `rin-bino` → [rimbino] ; `fon-paco` → [fompaco] |
| **R2. Voisement** | Dans un groupe coda + attaque d'obstruantes, la première prend le voisement de la seconde. | `zadco` → [zatko] |
| **R3. Géminées** | Deux consonnes identiques contiguës se prononcent longues. | `rinnèxo` → [rin:ɛxo] |

Ces règles sont automatiques et non écrites : l'orthographe reste morphologique (`rin-` s'écrit toujours `rin-`). Elles ne traversent ni une frontière de mot ni le signe `²`.

### 1.5 Accent

L'accent tombe sur l'avant-dernière syllabe du mot phonologique. Il ne se note pas. Les relateurs monosyllabiques (`ni na no ne nu`) et les enclitiques (`-ca`, `-vèt`) sont atones.

### 1.6 Rôle de `²`, trait d'union et espaces

`²` est une **soudure lexicale**. Il lie deux éléments en un seul mot figé, et aucune règle productive (préfixation, infixation, assimilation) ne le voit comme frontière. Il se place :
- dans les composés : `val²tir`, `dar²norya`, `falir²cayr` ;
- après un faux préfixe : `bal²bèdo` (« parler ») empêche la lecture *bal-bèdo*.

| Élément | Écriture |
|---|---|
| Mots autonomes (relateurs, subordonnants, conjonctions, degrés) | espace |
| Affixes verbaux (préfixes, infixes, suffixes) | soudés, sans trait d'union |
| Enclitiques (`-ca`, `-vèt`) | trait d'union |
| Composés lexicalisés | `²` |

Cela règle I10 : le trait d'union a désormais un seul sens.

### 1.7 Écriture

- **Ordre alphabétique :** a b c d dj dz e è ë f g i j l m n o ö p r s § t ts u v x y z µ = /
- **Majuscule :** noms propres seulement.
- **Ponctuation :** `.` fin de phrase. `,` facultative, après un thème-cadre ou une subordonnée. Pas de point d'interrogation (c'est le rôle de `-ca`). Exclamation par `=ö`.
- **Chiffres :** `0–9 ° ¤`.

### 1.8 Migration V1 → V2 (mécanique)

| V1 | V2 | Remarque |
|---|---|---|
| `*` | `ë` | `l*mé` → `lëme`, `b*go` → `bëgo` |
| `;` | `ö` | `r;j` → `röj` ; `=;` → `=ö` |
| `é` | `e` | `vélinè` → `velinè`. Vérifier les paires é/è, ex. `méno` / `mèno` restent distinctes. |
| `nè` (dans) | `ne` | cf. §2.3 |
| `nè-ca` (quoi) | `tè-ca` ✦ | évite l'homophonie avec le locatif |
| `der-ca` (où) | `jer-ca` ✦ | évite `der` = deux |
| `s*, s*né, yuné` | supprimés | plus d'articles |
| `-tenvar` | `-vèt` ✦ | restriction, pas négation (§2.9) |
| `-mel` (souhaiter) | `-mil` ✦ | évite `mel` = six. Motivé par `milanè`. |
| `gor` (plus) | `tos` ✦ | évite `gorè`, `bègor` |
| `axpa` / `-acpa` | `acpa` | |
| `l*µèo` (froid) | `lëmeo` | verbe statif de `lëmeè` |

---

## 2. Grammaire et syntaxe V2

### 2.1 Architecture de la phrase

```
[ subordonnées préposées ]  ·  THÈME  ·  (relateur + GN)*  ·  (adverbes)  ·  COMPLEXE VERBAL
```

1. Le **verbe** est le dernier mot de la proposition. Les enclitiques (`-ca`) en font partie.
2. Le **thème** est le premier groupe nominal : ce dont on parle.
3. Les groupes **relateur + GN** sont en ordre libre. Ordre conseillé : lieu/temps → sujet → destinataire → patient → instrument.
4. Les **adverbes** et mots de degré précèdent immédiatement ce qu'ils modifient.
5. Toute **proposition enchâssée** précède ce qu'elle complète et se ferme par un marqueur final. Son début est donc toujours lisible (I21).

*Thème-cadre* : un groupe suivi d'une virgule peut poser un cadre sans être argument du verbe (« quant au village, … »). C'est ce qui rend l'Aënor vraiment *topic-prominent* au sens de Li et Thompson (I20).

### 2.2 Le groupe nominal

```
[proposition relative + pa]  NOM  (Adj)*  (Num | Quant)  (Dém)  (Possesseur)
```

**Pas d'articles.** La définitude vient de la position (le thème est donné) ou d'un démonstratif.

**Nombre transnumérique.** `can` = chien(s). Pour préciser : numéral (`can vay`, trois chiens), quantificateur (`can b§ébè`, beaucoup de chiens, `can jab`, peu de chiens, `can sal`, tous les chiens ✦) ou `yu` (un) pour le singulier précis (`can yu`).

**Adjectifs.** Ils finissent en `-è` et suivent le nom : `var gorè`. Les mots de degré précèdent l'adjectif : `var mèl gorè` (très grand).

**Démonstratifs : 3 termes ancrés dans la conversation.** Ils suivent le nom.
- `derè` : proche de moi
- `falè` : proche de toi
- `sènè` : loin de nous deux

**Possession.** Le possédé précède le possesseur : `trèfèn =ocval` (l'épée du roi). Les possessifs pronominaux sont réguliers (§2.4). **Rattachement :** chaque modificateur se rattache au nom qui le précède immédiatement. `nèran nerac löj` = le peuple (de [son village]). Pour viser une tête plus éloignée, on ferme le groupe par une virgule. Le problème I8 disparaît parce que tout GN non-thème est ouvert par un relateur (§2.3).

**Noms relationnels.** Les anciennes prépositions spatiales sont des *noms* : `nor tèpal` (le dessous de la table), `paj`, `fela`, `sèn`, `=öʃ`, `naraj`, `tir²val`, `tir²nè`. Pour le temps : `val²tir` (avant), `oʃ²der` (après).

### 2.3 Pronoms

| Personne | Pronom | Possessif (régulier : `-oy` → `-öj`) |
|---|---|---|
| 1 sg | `roy` | `röj` |
| 1 pl exclusif (moi + eux, sans toi) | `µoy` | `µöj` |
| 1 pl inclusif (moi + toi) ✦ | `doµoy` | `doµöj` |
| 2 sg | `doy` | `döj` |
| 2 pl | `sinoy` | `sinöj` |
| 3 proximal (le thème en cours) | `loy` | `löj` |
| 3 pl | `linoy` | `linöj` |
| 3 obviatif (un autre tiers) ✦ | `lëy` | `lëj` |

- Plus de pronoms clitiques *me/te/le/la*. Un pronom objet est un pronom avec son relateur : `na doy` (toi, patient).
- **Réfléchi** : préfixe verbal invariable `lon-`. **Réciproque** : `linon-`. Il y a un seul proximal par proposition : « il se protège » = `loy lonbodzo`, « il le protège » = `loy na lëy bodzo`. Cela règle I14.
- **Pas de tu/vous de politesse** (§2.12).

### 2.4 Les relateurs : le cœur de l'alignement

Un relateur précède son GN et dit son rôle. La série centrale est un paradigme vocalique en `n-` :

| Relateur | Rôle |
|---|---|
| `ni` | sujet / agent |
| `na` | patient, complément direct, attribut |
| `no` | destinataire, but, direction (à, vers) |
| `ne` | lieu, moment (à, dans, en) |
| `nu` | instrument, moyen, cause (avec, par, grâce à, à cause de) |

Cinq relateurs lexicaux complètent la série :

| Relateur | Rôle |
|---|---|
| `=em` | compagnie (avec) |
| `=as` | bénéficiaire (pour) |
| `bro` | privation (sans) |
| `zad` | opposition (contre) |
| `tir` | origine, source, étalon de comparaison (de, depuis, que) |

**Réduction des 20 prépositions V1 :**
- 10 deviennent des relateurs (ci-dessus).
- 10 deviennent des noms relationnels (`paj, nor, fela, sèn, =öʃ, naraj, tir²val, tir²nè, val²tir, oʃ²der`).
- 3 sont retirées : `i=e`, `cro²var`, et *par*, absorbées par `nu` et `ni`.

La structure est : relateur + (nom relationnel) + possesseur, par exemple `ne nor tèpal` (sous la table).

### 2.5 La proposition : thème et rôles

**Règle d'or : tout GN dit son rôle, sauf le thème-sujet, qui peut rester nu.**

- Le thème est le premier GN. Il est **nu** s'il est sujet ou agent, et **marqué** dans tous les autres cas, y compris patient.
- Tout GN non-thème porte son relateur, y compris le sujet (`ni`).
- Le thème nu peut aussi prendre `ni` (forme pleine, emphatique). La forme pleine est toujours grammaticale : c'est le mode sûr pour apprendre.

| # | Configuration | Forme | Lecture |
|---|---|---|---|
| 1 | Thème = agent | `can na var µaro` | le chien mange l'homme |
| 2 | Thème = patient | `na var ni can µaro` | l'homme, le chien le mange |
| 3 | Thème = sujet, patient omis | `can µaro` | le chien mange |
| 4 | Thème = patient, agent omis | `na var µaro` | l'homme est mangé |
| 5 | Thème oblique | `ne nerac ni =abi pazo` | au village, le chat est |

Le **point de vue** est conservé : changer de thème change la perspective sans toucher au verbe. Il est maintenant adossé à des rôles lisibles. `can µaro` (3) et `na var µaro` (4) ne sont plus confondus (I6), et la formule « Thème + Agent + Verbe » est remplacée par la règle ci-dessus (I5).

**Sans thème :** une proposition qui n'a aucun GN est un état du monde : `y²uao` (il pleut), `lëmeo` (il fait froid). Il n'y a toujours pas de sujet fantôme.

### 2.6 Le verbe : gabarit complet

```
[MODE][TEMPS][SOI] RACINE [ASPECT] -o [NÉG₁] [MODAL] [NÉG₂] [ÉVID] (-ca)
  P1    P2     P3    P4      P5    P6   P7      P8     P9     P10   P11
```

- **P1 Mode :** `rin-` (irréel) ou `zo-` (directif), exclusifs ; ∅ = réel.
- **P2 Temps :** `bal-` (antérieur), `fon-` (postérieur), ∅ (contemporain de l'énonciation ou valeur générale). Il y a bien **trois repères**, et la grammaire le dit.
- **P3 Réfléchi / réciproque :** `lon-`, `linon-`.
- **P4 Racine.** Le *radical* est tout ce qui précède le `-o` final, dérivations comprises (`daro§-` dans `daro§o`). C'est là qu'on infixe (I13).
- **P5 Aspect (infixe, avant `-o`) :** `-iy-` imperfectif, `-en-` perfectif.
- **P6 `-o`** final (voyelle de citation).
- **P7, P9 Négation** (même série, deux positions).
- **P8 Modal.**
- **P10 Évidentiel.**
- **P11 `-ca`**, enclitique d'interrogation.

**Construction pas à pas :**
```
µaro                      manger / il mange
balµaro                   il mangea
balµariyo                 il mangeait
balµariyoten              il ne mangeait pas
balµariyojaʃ              il voulait manger (en continu)
balµariyojaʃten           il ne voulait pas manger
balµariyotenjaʃ           il voulait ne pas manger
```

**Aspect : perfectif / imperfectif** (au lieu du progressif et du parfait calqués) :

| Forme | Valeur |
|---|---|
| `µaro` | neutre : énoncé de fait |
| `µariyo` | imperfectif : en cours, habituel, répété |
| `µareno` | perfectif : événement vu comme borné et achevé |

Combiné au temps :
- `balµareno` = il mangea jusqu'au bout (aoriste)
- `fonµareno` = il aura fini de manger
- `µareno` (présent) = c'est fait (résultatif)

**Mode irréel.** `rin-` couvre l'hypothétique, le contrefactuel et le potentiel. Il se combine librement avec le temps : `rinµaro` (il mangerait), `rinbalµareno` (il aurait mangé), `rinfonµaro` (il mangerait plus tard). Cela règle I12.

**Directif.** `zo-` couvre l'impératif, l'hortatif et le jussif. Le pronom reste facultatif : `zoµaro` (mange !), `µoy zoµaro` (mangeons !), `loy zoveyo` (qu'il parte !). Négatif : `zoµaroten`. Il n'y a plus de « impératif inclusif » : c'est un hortatif.

**Négation : portée par adjacence.** La négation porte sur ce qui la précède.

| Suffixe | Sens |
|---|---|
| `-ten` | ne… pas |
| `-lutèn` | pas du tout |
| `-teni` | ne… plus |
| `-tenè` | pas vraiment |
| `-tena` | pas encore |
| `-tenor` | jamais |
| `-atenor` | plus jamais |

L'adverbe `nor²cayr` « jamais » est supprimé : la négation est codée une seule fois (I11). La restriction « ne… que » n'est plus une négation (`-vèt`, §2.9).

**Modaux :** `-jaʃ` (vouloir), `-bap` (pouvoir), `-dor` (devoir), `-mil` ✦ (souhaiter), `-§ar` (oser). Ils sont soudés comme tout suffixe verbal. Avec la négation :
- `µarotenjaʃ` : je veux ne pas manger
- `µarojaʃten` : je ne veux pas manger

**Évidentialité ✦** (dernier suffixe, racines motivées) :

| Suffixe | Valeur |
|---|---|
| ∅ | témoin direct, savoir propre |
| `-sbè` | rapporté (on dit) |
| `-sil` | inféré (d'après des indices) |
| `-div` | prophétique, destinal |

Exemple : `loy balveyosbè` (on dit qu'il est parti).

### 2.7 Verbes statiques, copule, existence, possession

- **Adjectif ↔ verbe statif :** tout adjectif en `-è` a un verbe statif en `-o`. `bègorè` (fort) → `bègoro` (être fort). On dit `loy bègoro` (il est fort), jamais `loy bègorè`. Cela règle I9 : `var gorè` est un GN, `var goro` une proposition.
- **Copule nominale :** `to` avec `na` : `loy na =ocval to` (il est roi).
- **Localisation et existence :** `pazo` avec `ne` : `roy ne bèran pazo` (je suis dans la maison) ; `ne bèran ni can pazo` (il y a un chien dans la maison).
- **Possession verbale :** `jeno` (ex-`jéno`) : `roy na can jeno` (j'ai un chien).
- **Adverbes :** adjectif + `-ay`, invariable, **avant le verbe** : `loy vèlnèay daro` (il court vite). Les adverbes de la V1 non conformes (`zadrogè`, `mélinè`, `bèco`, `sbègor`…) sont régularisés. « Vite » = `vèlnèay`, et non plus `rinèay` (I15).

### 2.8 Questions et exclamation

**`-ca` marque l'élément interrogé**, en place (*in situ*) : le verbe ne quitte jamais la fin (I7).

| Type | Exemple |
|---|---|
| Oui/non (sur le verbe) | `doy µaro-ca` : tu manges ? |
| Sujet | `µo-ca nèxo` : qui vient ? |
| Objet | `doy na tè-ca bino` : tu vois quoi ? |
| Adverbial | `doy jer-ca pazo` : tu es où ? |
| Quantité (dans le GN) | `doy na can gom-ca bino` : tu vois combien de chiens ? |

Mots interrogatifs : nominaux `µo` (qui), `tè` ✦ (quoi), qui prennent des relateurs. Adverbiaux `jer` ✦ (où), `=aj` (quand), `ëʃ` (pourquoi), `tef` (comment), `gom` (combien). Réponses : `ba` (oui), `no/` (non). `-ca` peut s'élider à l'oral quand le contexte est clair. À l'écrit, la forme complète reste la norme.

**Indéfinis :** radical interrogatif + `yu` (quelque), `sal` (tout), `²oro` (nul), par exemple `µoyu` (quelqu'un), `tèsal` (tout), `jer²oro` (nulle part). Un indéfini nul exclut la négation verbale : `µo²oro nèxo` (personne ne vient).

**Exclamation :** `=ö` à la fin (affect positif) ou au début (affect négatif). Exemple : `var melyè =ö`.

### 2.9 Pragmatique

- **Chaîne de thèmes.** Quand le thème est le même que celui de la proposition précédente, il s'omet.
- **Restriction :** `-vèt` ✦, enclitique de focus « seulement », sur n'importe quel GN : `roy na can-vèt bino` (je ne vois que le chien).
- **Politesse** par le point de vue : on honore quelqu'un en le plaçant en thème. `rin-` adoucit une demande (`doy rinveyo-ca` : tu partirais ?). Aucun honorifique structurel.

### 2.10 Subordination et coordination

**Subordonnants.** Mots autonomes qui ferment la subordonnée. L'adverbiale est préposée : elle ouvre la phrase.

| Subordonnant | Sens |
|---|---|
| `vaypa` | quand |
| `bodpa` | parce que |
| `nèpa` | bien que |
| `§a` | si (forme courte lexicalisée de *§apa*) |
| `nolpa` | afin que |
| `norvpa` | jusqu'à ce que |
| `decpa` | depuis que |
| `valpa` | comme |
| `acpa` | que (complétive) |
| `pa` | relatif, générique |

- **Condition :** `rin-` s'emploie dans la protase pour le contrefactuel, et seulement dans l'apodose pour l'éventuel. Cela remplace la concordance française.
- **Complétive :** le GN complétif porte son relateur : `roy na loy nèxo acpa reno` (je sais qu'il vient).
- **Même sujet :** le thème s'omet dans la subordonnée.
- **Relative.** Elle précède le nom et se ferme par `pa`. La lacune est le sujet par défaut. Pour un autre rôle, **un relateur orphelin marque la lacune** : `roy na bodzo pa var` (l'homme que je protège), `na roy bodzo pa var` (l'homme qui me protège).

**Coordination.**

| Coordonnant | Sens |
|---|---|
| `bèya` | et |
| `borya` | mais |
| `bavya` | ou |
| `bensya` | donc |

Les connecteurs de discours `bèrya` (ensuite), `banya` (pourtant, absorbe cependant/toutefois/néanmoins), `bèdya` (au contraire) et `bèmelya` (ainsi) restent des adverbes de la famille `b…ya`. Les autres sont retirés (E1). Un relateur devant des GN coordonnés vaut pour tous : `na can bèya var`.

### 2.11 Comparaison

| Degré | Particule |
|---|---|
| Comparatif de supériorité | `tos` ✦ |
| Comparatif d'infériorité | `ixi` |
| Comparatif d'égalité | `lem` |
| Superlatif | `bëgo` (le plus), `pix` (le moins) |

Elles précèdent l'adjectif ou le verbe statif. L'étalon est un GR en `tir`, placé avant le prédicat : `loy tir roy tos bègoro` (il est plus fort que moi). Le superlatif prend `ne` pour le groupe de référence : `var bëgo gorè ne talmor` (le plus grand homme parmi les seigneurs).

### 2.12 Nombres et dérivation

**Base 12** (inchangée), avec deux mots pour combler I18 :
- `val²oro` = 12, « un cycle »
- `gor²oro` ✦ = 144, « grand cycle »

Les cardinaux suivent le nom. Le coefficient précède le mot de puissance : `der val²oro` = 24. Les ordinaux en `-ayn` suivent le nom : `var valayn`.

**Dérivation (inventaire minimal) :**

| Morphème | Fonction | Exemple |
|---|---|---|
| `-è` | nom → adjectif | `dyad` → `dyadè` |
| `-o` (statif) | adjectif ↔ verbe | `gorè` → `goro` |
| `-ay` | adjectif → adverbe | `vélinè` → `velinèay` |
| `-èn` | nom abstrait | `silèn` (secret) |
| `-ar` | agent, profession | `limar` (pêcheur) |
| `lë-` | eau, liquide, froid | `lëme` |

Les familles de racines (`val-`, `nor-`, `sil-`, `cro-`, `sèn-`) restent de la morphologie lexicale. Les suffixes verbaux `-§o`, `-co`, `-xo` sont à documenter à l'étape lexique.

---

## 3. Corpus de validation

**Abréviations des gloses :** `1SG`/`2SG` personnes ; `3` troisième proximal ; `PASS` `FUT` `IRR` temps/mode ; `IPFV` imperfectif ; `FIN` voyelle finale `-o` ; `AGT` `PAT` `DIR` `LOC` relateurs ; `POSS` possessif ; `DÉM.1` démonstratif proximal ; `REFL` réfléchi ; `REL` clôture de relative ; `SI` subordonnant conditionnel.

### Phrase 1 : localisation (la plus simple)

**Aënor :** `=abi ne nor tèpal pazo`

**Français :** Le chat est sous la table.

**Analyse glosée :**
```
=abi   ne    nor       tèpal   pazo
chat   LOC   dessous   table   se-trouver
```
Traduction : « Le chat se trouve sous la table. » Le thème-sujet est nu. `ne nor tèpal` est un GR (relateur + nom relationnel + possesseur). Il n'y a ni copule ni article. Le verbe est final.

### Phrase 2 : transitive et point de vue

**Aënor :** `can gorè na var µaro`

**Français :** Le grand chien mange l'homme.

**Analyse glosée :**
```
can    gorè     na    var     µar-o
chien  grand    PAT   homme   manger-FIN
```
Traduction : « Le grand chien mange l'homme. » Le thème est le groupe `can gorè` (N + Adj), nu car sujet. `na` marque le patient.

**Même événement, autre point de vue :** `na var ni can gorè µaro` (« l'homme, le grand chien le mange »). Les deux sens ne sont plus confondus. Sans agent : `na var µaro` (l'homme est mangé).

### Phrase 3 : gabarit verbal complet

**Aënor :** `doy balveyojaʃtena bensya roy balµariyo`

**Français :** Tu ne voulais pas encore partir, donc je mangeais.

**Analyse glosée :**
```
doy   bal-vey-o-jaʃ-tena           bensya   roy   bal-µar-iy-o
2SG   PASS-aller-FIN-VOUL-NÉG.ENC  donc     1SG   PASS-manger-IPFV-FIN
```
Traduction : « Tu ne voulais pas encore partir, donc je mangeais. » Le verbe de la première proposition suit le gabarit : temps (P2), racine, `-o`, modal (P8), négation (P9, portée sur le vouloir). La seconde proposition ajoute l'infixe imperfectif. `bensya` coordonne deux propositions complètes.

### Phrase 4 : trois participants, groupe nominal complexe

**Aënor :** `talmor derè na velin no nèran nerac löj fonsereno`

**Français :** Ce seigneur promettra la paix au peuple de son village.

**Analyse glosée :**
```
talmor   derè      na    velin   no    nèran   nerac    l-öj    fon-seren-o
seigneur DÉM.1     PAT   paix    DIR   peuple  village  3-POSS  FUT-promettre-FIN
```
Traduction : « Ce seigneur-ci promettra la paix au peuple de son village. » Le thème porte un démonstratif de la série à 3 termes. Trois participants : agent (thème nu), patient `na`, destinataire `no`. `löj` (possessif régulier) se rattache à `nerac` par rattachement droit, et son référent est le thème proximal.

### Phrase 5 : subordination, relative et irréel (la plus complexe)

**Aënor :** `doy no nerac rinnèxo §a, roy na bodzo pa var rinlonsilo§o`

**Français :** Si tu venais au village, l'homme que je protège se cacherait.

**Analyse glosée :**
```
doy   no    nerac    rin-nèx-o    §a ,
2SG   DIR   village  IRR-venir-FIN SI

roy   na    bodz-o     pa     var     rin-lon-silo§-o
1SG   PAT   protéger-FIN REL   homme   IRR-REFL-cacher-FIN
```
Traduction : « Si tu venais au village, l'homme que je protège se cacherait. » La subordonnée conditionnelle est préposée et se clôt par `§a`. Elle porte `rin-` (hypothèse). La principale contient une relative préposée dont la lacune est marquée par le relateur orphelin `na` : on lit « l'homme que je protège ». La proposition se ferme par `pa`, puis la tête `var` est le thème-sujet de la principale. Le verbe principal cumule irréel et réfléchi (`rin-lon-`), dans l'ordre du gabarit.

---

## 4. Bilan

### Ce que la V2 règle

| Audit | Réponse V2 |
|---|---|
| I5, I6, I20 (rôles) | Relateurs `ni/na…`, règle du thème nu (§2.5) |
| I1–I3, M1, M10 (écriture) | Inventaire complet, `²` défini, symboles fixés (§1) |
| I4, I16, I17 (homophonies, conflits) | Renommages ✦ (§1.8) |
| I7, I21 (ordre) | Verbe final, subordonnées préposées closes |
| I8, I9 (possession, adjectif) | Relateurs ouvrant chaque GN, statif en `-o` |
| I10 (trait d'union) | Règle unique en §1.6 |
| I11–I13, M8 (verbe) | Gabarit en 11 positions |
| I14, M7 (pronoms) | Obviatif, réfléchi séparé, clusivité |
| I18 (nombres) | `val²oro`, `gor²oro` |
| E1–E3 (calques) | Articles, tu/vous, conditionnel-temps retirés |
| E4 (peu d'originalité) | Clusivité, évidentialité, déixis à 3 termes |
| M3, M4, M5, M6 | §2.7, §2.4, §2.10, §2.2 |

### Décisions à valider

1. `µ` = /ɲ/ (alternative : /ŋ/, plus exotique mais difficile pour un francophone).
2. Fusion `é` → `e`.
3. `*` → `ë` et `;` → `ö`.
4. Le système `ni/na` : c'est le changement le plus visible, et c'est lui qui fait fonctionner le point de vue.
5. Les ajouts de catégories : évidentialité, clusivité.
6. Les subordonnées préposées.

### Chantiers pour l'étape 3 (lexique)

- Migrer les ~600 entrées selon §1.8 et régulariser les adjectifs en `-è`.
- Résoudre les homophonies restantes de I4 (`daro`, `§yéro`, `bino§o`, `nor²cayr`, `bèco`, `nèxo`/`nexo`, `nègor`…).
- Combler les trous lexicaux (*donner, aider, encore, aussi, tout*, interjections).
- Documenter `-§o`, `-co`, `-xo`.
- Reformater le JSON : retirer les `:` des clés et le champ `$COMMENTAIRE$`.

Veux-tu que je mette tout ceci dans un fichier `.md` pour le projet ? 