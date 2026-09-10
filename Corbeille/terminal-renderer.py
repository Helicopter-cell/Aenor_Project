"""
Pyramide 3D rotative en ASCII, animée dans le terminal.

Améliorations par rapport à la version d'origine :
  1. Éclairage réaliste : chaque face de la pyramide est éclairée selon
     sa normale et une source de lumière fixe (comme un vrai rendu 3D),
     au lieu d'un pseudo-hasard basé sur les coordonnées. Résultat :
     on distingue clairement les faces de la pyramide.
  2. Zone d'affichage réduite (32x16) pour occuper moins de place.
  3. Rendu strictement identique quelle que soit la taille de la fenêtre
     du terminal : écran alterné (comme vim/less), curseur masqué, et
     effacement complet à l'initialisation.
"""

import math
import os
import shutil
import sys
import time

# Active le traitement des séquences ANSI sur les anciennes consoles Windows
# (astuce classique : un os.system("") suffit à activer le mode VT100)
if os.name == "nt":
    os.system("")

# --- Zone d'affichage : fixe et volontairement compacte ---
WIDTH, HEIGHT = 32, 16

# --- Angles de rotation ---
A, B, C = 0.0, 0.0, 0.0

# --- Rampe de caractères, du plus sombre au plus lumineux ---
CHARS = ".,-~:;=!*#$@"

# --- Paramètres de la pyramide et de la caméra ---
PYRAMID_HEIGHT = 12
DISTANCE = 60
K1 = 32  # constante de projection, mise à l'échelle avec WIDTH/HEIGHT

# --- Source de lumière fixe, exprimée dans l'espace de la caméra ---
_light = (0.0, 1.0, -1.0)
_norm = math.sqrt(sum(v * v for v in _light))
LIGHT = tuple(v / _norm for v in _light)


def rotate(i, j, k):
    """Applique la rotation courante (A, B, C) à un vecteur.

    Sert aussi bien pour les points (i, j, k) que pour les normales de
    face, car il s'agit d'une simple rotation (pas de translation ni
    de mise à l'échelle) : la formule est donc réutilisable telle quelle.
    """
    x = (
        j * math.sin(A) * math.sin(B) * math.cos(C)
        - k * math.cos(A) * math.sin(B) * math.cos(C)
        + j * math.cos(A) * math.sin(C)
        + k * math.sin(A) * math.sin(C)
        + i * math.cos(B) * math.cos(C)
    )
    y = (
        j * math.cos(A) * math.cos(C)
        + k * math.sin(A) * math.cos(C)
        - j * math.sin(A) * math.sin(B) * math.sin(C)
        + k * math.cos(A) * math.sin(B) * math.sin(C)
        - i * math.cos(B) * math.sin(C)
    )
    z = (
        k * math.cos(A) * math.cos(B)
        - j * math.sin(A) * math.cos(B)
        + i * math.sin(B)
    )
    return x, y, z


def face_normal(x_val, z_val, size, is_base):
    """Normale (non tournée) de la face à laquelle appartient le point.

    - la base est un plan horizontal : normale (0, 1, 0)
    - chaque paroi latérale est un plan incliné dont la pente vient du
      fait que `size` diminue linéairement vers le sommet
    - la pointe et les arêtes sont des cas limites gérés naturellement
    """
    if is_base:
        return (0.0, 1.0, 0.0)

    nx = 1.0 if x_val > 0 else (-1.0 if x_val < 0 else 0.0)
    nz = 1.0 if z_val > 0 else (-1.0 if z_val < 0 else 0.0)
    if abs(x_val) != size:
        nx = 0.0
    if abs(z_val) != size:
        nz = 0.0

    if nx == 0.0 and nz == 0.0:
        return (0.0, -1.0, 0.0)  # la pointe de la pyramide

    length = math.sqrt(nx * nx + 0.25 + nz * nz)
    return (nx / length, -0.5 / length, nz / length)


def render_frame():
    global A, B, C
    buffer = [" "] * (WIDTH * HEIGHT)
    z_buffer = [0.0] * (WIDTH * HEIGHT)

    for y_val in range(-PYRAMID_HEIGHT, PYRAMID_HEIGHT):
        size = (y_val + PYRAMID_HEIGHT) // 2
        is_base = y_val == PYRAMID_HEIGHT - 1

        for x_val in range(-size, size + 1):
            for z_val in range(-size, size + 1):
                # Seules les parois externes et la base sont calculées
                on_wall = abs(x_val) == size or abs(z_val) == size
                if not (on_wall or is_base):
                    continue

                x, y, z = rotate(x_val, y_val, z_val)
                z += DISTANCE
                if z <= 0:
                    continue
                ooz = 1 / z

                xp = int(WIDTH / 2 + K1 * ooz * x * 2)
                yp = int(HEIGHT / 2 + K1 * ooz * y)
                if not (0 <= xp < WIDTH and 0 <= yp < HEIGHT):
                    continue

                idx = xp + yp * WIDTH
                if ooz <= z_buffer[idx]:
                    continue  # un point plus proche est déjà dessiné ici

                # Éclairage réel : normale de la face tournée, produit
                # scalaire avec la lumière -> luminosité de la face
                nx, ny, nz = face_normal(x_val, z_val, size, is_base)
                rnx, rny, rnz = rotate(nx, ny, nz)
                luminance = rnx * LIGHT[0] + rny * LIGHT[1] + rnz * LIGHT[2]
                if luminance <= 0:
                    continue  # face à l'ombre ou cachée : on ne la dessine pas

                z_buffer[idx] = ooz
                char_idx = min(int(luminance * len(CHARS)), len(CHARS) - 1)
                buffer[idx] = CHARS[char_idx]

    # Rendu propre : on repositionne le curseur en haut à gauche et on
    # réécrit toute la zone (fixe), sans jamais dépendre de la taille
    # réelle du terminal.
    frame = "\n".join(
        "".join(buffer[row * WIDTH:(row + 1) * WIDTH]) for row in range(HEIGHT)
    )
    sys.stdout.write("\x1b[H" + frame)
    sys.stdout.flush()

    # Incrémentation de la rotation
    A += 0.03
    B += 0.02
    C += 0.015


def check_terminal_size():
    """Avertit si le terminal est plus petit que la zone d'affichage."""
    size = shutil.get_terminal_size(fallback=(80, 24))
    if size.columns < WIDTH or size.lines < HEIGHT + 1:
        print(
            f"Attention : ce terminal ({size.columns}x{size.lines}) est plus "
            f"petit que la zone d'affichage requise ({WIDTH}x{HEIGHT}). "
            "Agrandissez la fenêtre pour un rendu correct."
        )
        time.sleep(2)


def main():
    check_terminal_size()

    # Écran alterné : le rendu se fait sur une page dédiée, isolée de
    # l'historique/scrollback du terminal. C'est la même technique que
    # vim, less ou htop, et c'est ce qui garantit un résultat identique
    # à chaque lancement, peu importe ce qu'il y avait avant à l'écran.
    sys.stdout.write("\x1b[?1049h")
    sys.stdout.write("\x1b[?25l")  # masque le curseur (moins de scintillement)
    sys.stdout.write("\x1b[2J")    # efface tout, une bonne fois pour toutes

    try:
        while True:
            render_frame()
            time.sleep(0.03)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\x1b[?25h")    # réaffiche le curseur
        sys.stdout.write("\x1b[?1049l")  # quitte l'écran alterné, restaure le terminal
        sys.stdout.flush()
        print("Animation stoppée.")


if __name__ == "__main__":
    main()