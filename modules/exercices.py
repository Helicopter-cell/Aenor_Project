# =============================
# exercices.py
# =============================

import random

PHRASES = [
    "je mange",
    "il pleut",
    "nous allons à la maison",
    "elle parle doucement",
    "il est très grand",
    "l'arbre est joli",
    "le ciel est bleu",
    "le roi parle de la guerre",

    "Le chat dort sous le grand arbre.",
    "Ma famille habite dans une petite maison.",
    "L'eau de la rivière est très froide.",
    "Le soleil brille fort aujourd'hui.",
    "Cet enfant marche doucement vers la forêt.",
    "Le vent souffle fort ce soir.",
    "Un petit oiseau chante sur la pierre.",
    "Nous mangeons du pain ensemble.",
    "La nuit tombe rapidement en hiver.",
    "Ton ami attend devant la porte.",

    "Pourquoi ne regardes-tu pas le ciel ?",
    "Il ne veut pas perdre son temps.",
    "As-tu vu mon livre sur la table ?",
    "Ne marche pas trop vite sur le chemin.",
    "Qui habite dans cette grande maison ?",
    "Je ne comprends pas cette nouvelle règle.",
    "N'oublie jamais d'où tu viens.",
    "Est-ce que tu entends ce bruit étrange ?",
    "Pourquoi le petit chien pleure-t-il ?",
    "Regarde la lumière qui passe à travers les arbres !",

    "Hier, nous avons marché pendant plusieurs heures.",
    "Quand j'étais jeune, je courais tous les matins.",
    "Demain, ma sœur viendra nous rendre visite.",
    "Le feu s'est éteint au milieu de la nuit.",
    "Nous construirons une nouvelle maison l'année prochaine.",
    "Elle a trouvé une belle pierre bleue sur la plage.",
    "Il pleuvait doucement quand le jour s'est levé.",
    "Tu comprendras la vérité quand tu seras plus grand.",
    "Ils ont parlé longuement de leur histoire.",
    "Le temps a changé très vite cette après-midi.",

    "L'homme que tu as vu ce matin est mon père.",
    "Si tu écoutes attentivement, tu entendras la mer.",
    "Elle sait que la route sera longue et difficile.",
    "Quand la pluie s'arrêtera, nous pourrons sortir.",
    "Le livre dont tu parles est très ancien.",
    "Bien qu'il soit fatigué, il continue de marcher.",
    "Je pense que cette idée est la meilleure pour nous.",
    "C'est l'arbre sous lequel nous avons joué hier.",
    "Si le vent se lève, le feu brûlera plus vite.",
    "Il cherche une pierre qui est plus lourde que les autres.",

    "La peur s'efface souvent devant le courage.",
    "Il y a beaucoup de choses à apprendre dans la vie.",
    "Personne ne peut arrêter le temps qui passe.",
    "Elle garde toujours un sourire sur son visage.",
    "Les souvenirs restent gravés dans la mémoire.",
    "Parfois, le silence dit plus que les mots.",
    "Il préfère marcher seul dans la montagne.",
    "Cette histoire montre la force de notre amitié.",
    "Chaque jour apporte une nouvelle chance d'apprendre.",
    "La terre donne la vie à toutes les plantes de la forêt."
    ]


def get_random_phrase():
    if not PHRASES:
        return None  # sécurité

    return random.choice(PHRASES)