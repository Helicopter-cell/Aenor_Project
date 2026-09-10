NEGATIONS = {
    "pas": "ten",
    "rien": "lutèn",
    "plus": "teni",
    "pas_encore": "tena",
    "pas_vraiment": "tenè",
    "que": "tenvar"
}

PRONOMS = {
    "sujet": {
        "je": "roy",
        "tu": "doy",
        "il": "loy",
        "elle": "loy",
        "nous": "µoy",
        "vous": "sinoy",
        "ils": "linoy",
        "elles": "linoy"
    },
    "objet": {
        "me": "ron",
        "te": "don",
        "se": "son",
        "nous": "µon",
        "vous": "sinon",
        "le": "lon",
        "la": "lon",
        "les": "linon"
    },
    "reflechi": {
        "me": "r*n",
        "te": "d*n",
        "se": "s*n",
        "nous": "µ*n",
        "vous": "sin*n"
    }
}

SUBORDONNANTS = {
    "si": "melpa",
    "quand": "vaypa",
    "lorsque": "derpa",
    "parce que": "bodpa",
    "puisque": "bècpa",
    "comme": "valpa",
    "bien que": "nèpa",
    "même si": "sbèpa",
    "afin que": "varpa",
    "avant que": "tirpa",
    "après que": "norpa",
    "jusqu'à ce que": "bèlypa",
    "tant que": "dèpa",
    "pendant que": "cayrpa",
    "que": "èpa",
}

ADVERBES = {

    "maintenant": "cayrè",
    "toujours": "cayr²gor",
    "souvent": "melcayr",
    "parfois": "nècayr",
    "rarement": "sèncayr",
    "jamais": "nor²cayr",
    "déjà": "val²cayr",
    "bientôt": "valir²cayr",
    "tard": "norir²cayr",
    "autrefois": "gunim²cayr",

    "ici": "derè",
    "là": "valè",
    "là-bas": "sènè",
    "partout": "tir²val",
    "nulle part": "nor²tir",
    "dedans": "nèè",
    "dehors": "val²nè",
    "autour": "tirval",
    "au loin": "sèn²vay",
    "près": "derè",

    "très": "bègor",
    "trop": "bègor²val",
    "peu": "nègor",
    "assez": "melgor",
    "beaucoup": "b§ébè",
    "complètement": "bèlyar",
    "presque": "nèlyar",
    "à peine": "nèly²gor",
    "entièrement": "valèn²gor",
    "fortement": "bègorè",

    "vite": "viro",
    "lentement": "noro",
    "doucement": "melè",
    "violemment": "zadrogè",
    "calmement": "velè",
    "facilement": "mélinè",
    "difficilement": "bècè",
    "précisément": "bèco",
    "silencieusement": "nor²sbè",
    "bruyamment": "sbègor",

    "oui": "val",
    "non": "cro",
    "peut-être": "melpa",
    "certainement": "valèn",
    "sûrement": "derèn",
    "probablement": "melèn",
    "impossible": "nègor",
    "évidemment": "valyè",
    "apparemment": "silè",
    "heureusement": "melgor",

}

VERBES_IMPERSONNELS = {
    "pleuvoir": "y²uao",
}

dico = {
    #-----------------------
    # Les determinants
    #-----------------------
    "mon": "na-ro",
    "ton": "na-do",
    "son": "na-loy",
    "notre": "na-µoy",
    "votre": "na-sin",
    "leur": "na-lin",

    #-----------------------
    # Les conjonction de coordination
    #-----------------------
    "et": "bèya",
    "mais": "borya",
    "ou": "bavya",
    "donc": "bensya",
    "car": "belya",
    "alors": "barya",
    "ainsi": "bèmelya",
    "cependant": "banya",
    "toutefois": "bèsya",
    "néanmoins": "bodza",
    "pourtant": "bènya",
    "c'est-à-dire": "balya",
    "ensuite": "bèrya",
    "au-contraire": "bèdya",
    "or": "bècya",




    #-----------------------
    # Les prépositions
    #-----------------------

    "dans": "nè",
    "sur": "val",
    "sous": "nor",
    "avec": "mel",
    "sans": "cro",
    "pour": "var",
    "contre": "zad",
    "entre": "der",
    "par": "tir",
    "vers": "vay",
    "depuis": "nor²tir",
    "avant": "val²tir",
    "après": "nor²der",
    "chez": "bèran",
    "autour": "tir²val",
    "à travers": "tir²nè",
    "loin de": "sèn",
    "près de": "derè",
    "grâce à": "mel²var",
    "à cause de": "cro²var",





    #-----------------------
    # Les verbes
    #-----------------------

    # Verbes de base
    "être": "to",
    "avoir": "jéno",
    "faire": "ato",
    "aller": "veyo",
    "venir": "nèxo",
    "voir": "bino",
    "dire": "sbéno",
    "prendre": "paco",
    "donner": "=afé",
    "trouver": "méxio",
    "sentir": "tado",

    "vouloir": "ja§o",
    "pouvoir": "bapo",
    "devoir":"doro",
    "souhaiter": "melo",
    "oser": "§aro",

    # Combat / action
    "attaquer": "zadco",
    "défendre": "=odzo",
    "combattre": "zadro",
    "tuer": "moro",
    "protéger": "bodzo",
    "garder": "vardo",
    "obéir": "dero",
    "trahir": "croxo",
    "fuir": "selo",
    "conquérir": "valzo",

    # Vie quotidienne
    "manger": "µaro",
    "préparer": "dilµo",
    "boire": "limo",
    "dormir": "noro",
    "travailler": "daro§o",
    "construire": "darè=o",
    "couper": "seco",
    "porter": "fèro",
    "ouvrir": "varo§o",
    "fermer": "nexco",
    "chercher": "silxo",
    "parler": "sbéna/o",

    # Esprit / pensée
    "penser": "méno",
    "croire": "lo²no",
    "savoir": "reno§o",
    "apprendre": "melco",
    "enseigner": "melzo",
    "comprendre": "cavexo",
    "oublier": "norxo",
    "souvenir": "gunixo",
    "mentir": "crovo",
    "promettre": "sereno",

    # Émotions
    "aimer": "mélino",
    "haïr": "croko",
    "craindre": "sipco",
    "espérer": "topo",
    "désespérer": "norco",
    "mettre-en-colère": "zadrod§o",
    "calmer": "velco",

    # Magie
    "lancer-un-sort": "vèlxo",
    "invoquer": "divo",
    "maudire": "croµo",
    "bénir": "izabo",
    "méditer": "lo²nexo",
    "prophétiser": "divexo",
    "sacrifier": "bogro",

    # Déplacement
    "courir": "viro",
    "marcher": "daro",
    "voler": "aèro",
    "nager": "limo§o",
    "tomber": "nexo§o",
    "monter": "valco",
    "descendre": "norco§o",
    "traverser": "tirxo",

    "écrire": "rèno§o",
    "lire": "bino§o",
    "compter": "cayro",
    "mesurer": "cayrèco",
    "peser": "bèco",
    "attendre": "noro§o",
    "rester": "varo",
    "suivre": "dero§o",
    "guider": "valeco",
    "perdre": "nèco",
    "gagner": "melco§o",
    "tomber (objet)": "nexo",
    "briser": "croco",
    "réparer": "bèdo",
    "allumer": "§yéro",
    "éteindre": "nor§o",
    "pousser": "pèco",
    "tirer": "tirco",
    "cacher": "silo§o",
    "montrer": "bino§o",
    #_-_-_-_-_-_-_-_-_#





    #-----------------------
    # Les noms communs
    #-----------------------

    "roi": "=ocval",
    "prince": "varèn",
    "seigneur": "talmor",
    "duc": "cared",
    "comte": "vajia",
    "baron": "sored",
    "noble": "ocvèn",
    "vassal": "deran",
    "suzerain": "ocvar",
    "régent": "melcar",
    "héritier": "varis",
    "usurpateur": "croval",

    "paysan": "terac",
    "serf": "neran",
    "fermier": "doran",
    "berger": "ovrec",
    "pêcheur": "limar",
    "boulanger": "mordec",
    "marchand": "dzuguo",

    "mage": "velcar",
    "sorcier": "velcro",
    "druide": "narvec",
    "dieu": "bogr&l",
    "déesse": "bogr&l",

    "dragon": "valcor",
    "loup": "varg",
    "chien": "can",
    "chat": "l*bin",

    "épée": "trèfèn",
    "arc": "cel",
    "flèche": "celis",

    "pierre": "car",
    "minéraux": "ir",
    "bois": "dar",
    "fer": "bof",

    "château": "*valcor",
    "village": "nerac",
    "royaume": "valen",

    "guerre": "zadca",
    "paix": "vélin",
    "amour": "melyèf",
    "haine": "xagyé",
    "magie": "dyad",
    "nuit": "nor",
    "jour": "val",

    "eau": "l*mé",
    "feu": "§yér",
    "vent": "vayr",
    "terre": "tèbar",
    "ciel": "alyér",
    "étoile": "§yèl",
    "lune": "norè",
    "soleil": "valè",
    "pluie": "l*var",
    "neige": "§yep",
    "orage": "vèd§ar",
    "brume": "l*néb",
    "ombre": "norya",
    "lumière": "valyé",
    "racine": "drèb",
    "feuille": "§yèl²dar",
    "fleur": "mel§a",
    "herbe": "tèlin",
    "forêt profonde": "dar²norya",
    "clairière": "val²dar",

    "maison": "bèran",
    "porte": "dèroc",
    "fenêtre": "val²bè",
    "table": "tèpal",
    "chaise": "sèvar",
    "lit": "noryel",
    "feu (foyer)": "§yéran",
    "pain": "mèp",
    "repas": "µarèl",
    "eau potable": "l*méval",
    "outil": "bècor",
    "corde": "tirè",
    "vêtement": "sèlyar",
    "chaussure": "cèbar",
    "sac": "vèrag",
    "bourse": "zèp",
    "clé": "rèn",
    "lampe": "val²§yér",
    "torche": "§yértir",
    "couteau": "trèc",

    "homme": "var",
    "femme": "vor",
    "enfant": "nèly",
    "ami": "melvar",
    "ennemi": "crovar",
    "famille": "vèlinar",
    "étranger": "sènor",
    "chef": "valec",
    "peuple": "nèran",
    "tribu": "vèragan",
    "nom": "rèno",
    "voix": "sbè",
    "parole": "sbènar",
    "secret": "silèn",
    "vérité": "valèn",
    "mensonge": "crovèn",
    "promesse": "serèn",
    "ordre": "valcor",
    "chaos": "cro§ar",
    "loi": "vèlcor",

    "temps": "cayr",
    "instant": "cayrè",
    "passé": "nor²cayr",
    "futur": "val²cayr",
    "destin": "dravèn",
    "chance": "melèn",
    "malchance": "cromel",
    "vie": "vèya",
    "mort": "morn",
    "âme": "alvè",
    "esprit (pensée)": "mèno",
    "volonté": "varèn",
    "doute": "silèc",
    "force": "bègor",
    "faiblesse": "nègor",
    "énergie": "vèlyar",
    "silence": "nor²sbè",
    "bruit": "sbègor",
    "vide": "nèlyar",
    "plein": "bèlyar",
    #_-_-_-_-_-_-_-_-_#
        

    
    #-----------------------
    # Les adjectif
    #-----------------------
    "gentil": "djyalè",
    "méchant": "*djolè",
    "meilleur": "=afè",
    "pire": "=a/ovè",
    "grand": "gorè",
    "petit": "nèlyè",
    "beaucoup": "b§ébè",
    "peu": "bapè", 
    "fort": "bègorè",
    "faible": "nègorè",
    "rapide": "viroè",
    "lent": "noroè",
    "beau": "melyè",
    "gros": "jip§è",
    "fin": "namorè",
    "laid": "croè",
    "joli": "maylè",
    "moche": "criaè",
    "clair": "valyè",
    "sombre": "noryè",
    "chaud": "§yérè",
    "froid": "l*méè",
    "doux": "melè",
    "dur": "bècè",
    "léger": "vayrè",
    "lourd": "bègorè",

    "vivant": "vèyaè",
    "mort": "mornè",
    "calme": "velè",
    "agité": "zadè",
    "heureux": "melènè",
    "triste": "norènè",
    "colérique": "zadrodè",
    "paisible": "vélinè",
    "fidèle": "derènè",
    "traître": "crovènè",
    "sage": "lo²nè",
    "fou": "cro§è",
    "lucide": "valènè",
    "perdu": "nècè",

    "ancien": "gunimè",
    "nouveau": "valirè",
    "jeune": "nèlyè",
    "vieux": "norè",
    "proche": "derè",
    "lointain": "sènorè",
    "plein": "bèlyè",
    "vide": "nèlyè",
    "sec": "secoè",
    "humide": "l*varè",
    "rugueux": "bècè",
    "lisse": "melè",
    "tranchant": "trèfè",
    "brisé": "crocoè",
    "entier": "valènè",

    "magique": "dyadè",
    "sacré": "bogrè",
    "maudit": "croµè",
    "béni": "izabè",
    "mystique": "divè",
    "spirituel": "alvairè",
    "invisible": "silè",
    "visible": "binoè",
    "ancien (sacré)": "lo²nè",
    "prophétique": "divènè",



    #-----------------------
    # Les couleurs
    #-----------------------
    "rouge": "zèvar",
    "bleu": "l*yon",
    "vert": "drasil",
    "jaune": "pèyra",
    "noir": "mornèc",
    "blanc": "alyon",
    "gris": "tèmor",
    "brun": "garun",
    "orange": "vèp§a",
    "violet": "syèlun",

    "rose": "melpè",
    "turquoise": "l*varin",
    "beige": "tèlan",
    "or": "valgor",
    "argent": "silvar",
    "cuivre": "bèrun",

    "sombre": "noryèc",
    "clair": "valyèc",
    "pâle": "nèlin",
    "vif": "vègor",
    "terne": "silgor"
    #_-_-_-_-_-_-_-_-_#
}


import spacy

# Charger le modèle français
nlp = spacy.load("fr_core_news_sm")

# ------------------------- #
#    OUTILS & PRÉPARATION   #
# ------------------------- #

def preparer_texte(texte):
    """
    Prépare le texte avant le passage dans SpaCy.
    On gère uniquement les locutions à plusieurs mots ici.
    """
    texte = texte.lower()
    
    # 1. Négations composées : on les fusionne SANS underscore pour ne pas piéger SpaCy
    texte = texte.replace("pas du tout", "rien")
    texte = texte.replace("pas encore", "pasencore")
    texte = texte.replace("pas vraiment", "pasvraiment")
    texte = texte.replace("plus jamais", "pasencore") 
    
    # 2. On remplace UNIQUEMENT les expressions de plusieurs mots
    # Les mots simples seront gérés pendant la traduction mot à mot
    toutes_locutions = {**SUBORDONNANTS, **ADVERBES}
    locutions_multi = {k: v for k, v in toutes_locutions.items() if " " in k or "'" in k}
    
    # On trie du plus long au plus court (pour ne pas casser "jusqu'à ce que" avec un "que")
    for expr in sorted(locutions_multi.keys(), key=len, reverse=True):
        texte = texte.replace(expr, locutions_multi[expr])
        
    return texte

def est_participe_passe(token):
    return "Part" in token.morph.get("VerbForm", [])

def est_auxiliaire(token):
    return token.pos_ == "AUX" and token.lemma_ in ["avoir", "être"]

def est_futur(token):
    return token.text.lower().endswith(("rai", "ras", "rons", "rez", "ront", "ra"))

def est_imparfait(token):
    return token.text.lower().endswith(("ais", "ait", "ions", "iez", "aient", "ais"))

def trouver_negation(doc, index_verbe):
    """Cherche une négation autour du verbe pour trouver le bon suffixe."""
    debut = max(0, index_verbe - 3)
    fin = min(len(doc), index_verbe + 4)

    # Dictionnaire de transition pour faire le lien avec ton dict NEGATIONS
    mapping_neg = {
        "pas": "pas", "rien": "rien", "plus": "plus",
        "pasencore": "pas_encore", "pasvraiment": "pas_vraiment"
    }

    # 1. Chercher d'abord les mots forts APRES ou AVANT le verbe
    for j in range(debut, fin):
        mot = doc[j].text.lower()
        lemme = doc[j].lemma_.lower()
        
        cle_trouvee = mapping_neg.get(mot) or mapping_neg.get(lemme)
        if cle_trouvee and cle_trouvee in NEGATIONS:
            return NEGATIONS[cle_trouvee]

    # 2. S'il n'y a que "ne", on vérifie si c'est un "ne... que"
    for j in range(debut, index_verbe):
        if doc[j].lemma_.lower() in ["ne", "n"]:
            for k in range(index_verbe + 1, fin):
                if doc[k].lemma_.lower() == "que":
                    return NEGATIONS.get("que", "tenvar")
            return NEGATIONS.get("pas", "ten") # Par défaut, "ne" agit comme "pas"

    return ""




# ------------------------- #
#       TRADUCTION          #
# ------------------------- #

def traduire(texte, dico_principal):
    texte_prepare = preparer_texte(texte)
    doc = nlp(texte_prepare)
    resultat = []
    
    # On isole les mots simples de tes dictionnaires
    mots_simples = {k: v for k, v in {**SUBORDONNANTS, **ADVERBES}.items() if " " not in k and "'" not in k}
    mots_a_ignorer = ["ne", "n", "pas", "rien", "plus", "pasencore", "pasvraiment"]

    for i, token in enumerate(doc):
        mot = token.text.lower()
        lemme = token.lemma_.lower()

        # 🔹 1. Propreté : Gestion directe de la ponctuation et des espaces
        if token.is_space:
            continue
        if token.is_punct:
            resultat.append(token.text)
            continue

        # 🔹 2. Ignorer les mots de négation (qui seront ajoutés en suffixes)
        if mot in mots_a_ignorer or lemme in mots_a_ignorer:
            continue
        # Exception pour ignorer "que" uniquement s'il fait partie de "ne... que"
        if lemme == "que" and token.head.pos_ in ["VERB", "AUX"]:
            if trouver_negation(doc, token.head.i) == NEGATIONS.get("que"):
                continue

        # 🔹 3. Ignorer les auxiliaires (si participe passé présent)
        if est_auxiliaire(token):
            skip = False
            for j in range(i + 1, len(doc)):
                if est_participe_passe(doc[j]):
                    skip = True
                    break
                if doc[j].pos_ not in ["ADV", "PRON", "PART"]:
                    break
            if skip:
                continue

        # 🔹 4. TRADUCTION DE BASE
        mot_traduit = mot 
        
        # On vérifie le mot brut (pour "ils") et le lemme (pour "j'")
        cle_sujet = mot if mot in PRONOMS["sujet"] else lemme
        cle_objet = mot if mot in PRONOMS["objet"] else lemme

        if token.pos_ == "DET":
            if mot in ["les", "des"]:
                mot_traduit = "s*né" if mot == "les" else "yuné"
            elif lemme in ["le", "la", "un", "une"]:
                mot_traduit = "s*" if lemme in ["le", "la"] else "yu"
        
        elif cle_sujet in PRONOMS["sujet"]:
            if cle_sujet == "il" and token.dep_ == "nsubj" and token.head.lemma_ in VERBES_IMPERSONNELS:
                mot_traduit = "oµo"
            else:
                mot_traduit = PRONOMS["sujet"][cle_sujet]
        
        elif cle_objet in PRONOMS["objet"]:
            if token.dep_ == "expl:pv":
                mot_traduit = PRONOMS["reflechi"].get(cle_objet, cle_objet)
            else:
                mot_traduit = PRONOMS["objet"][cle_objet]
        
        elif lemme in mots_simples:
            mot_traduit = mots_simples[lemme]
        elif mot in mots_simples:
            mot_traduit = mots_simples[mot]
        else:
            # Dictionnaire principal
            mot_traduit = dico_principal.get(lemme, dico_principal.get(mot, mot))

        # 🔹 5. TEMPS (Préfixes)
        prefixe = ""
        if est_futur(token):
            prefixe = "fon"
        elif est_imparfait(token):
            prefixe = "bal"
        elif est_participe_passe(token):
            for j in range(i - 1, -1, -1):
                if est_auxiliaire(doc[j]):
                    prefixe = "bal"
                    break
                if doc[j].pos_ not in ["ADV", "PRON", "PART"]:
                    break

        # 🔹 6. NÉGATION (Suffixes)
        suffixe = ""
        if token.pos_ in ["VERB", "AUX"]:
            suffixe = trouver_negation(doc, i)

        # 🔹 7. APPLICATION
        resultat.append(prefixe + mot_traduit + suffixe)

    # 🔹 8. ASSEMBLAGE SANS ARTEFACTS
    phrase_finale = ""
    for item in resultat:
        if item in [",", ".", "!", "?", ";", ":"] and phrase_finale:
            # Enlève l'espace avant la ponctuation
            phrase_finale = phrase_finale.rstrip() + item + " "
        else:
            phrase_finale += item + " "

    return phrase_finale.strip()