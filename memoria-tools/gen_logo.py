#!/usr/bin/env python3
"""Logo Mémoria : un seuil en arche dont la serrure est le point rouge de la marque.

Génère dans memoria/ :
  favicon.svg, logo/memoria-mark.svg, logo/memoria-logo.svg (vert sur clair),
  logo/memoria-logo-white.svg (crème sur vert).
Le mot « Mémoria » est converti en tracés (Libre Caslon Display, licence SIL OFL,
fonts/LibreCaslonDisplay.ttf) : le logo s'affiche à l'identique sans police installée.
Usage : python3 memoria-tools/gen_logo.py   (requiert fonttools)
"""
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'memoria')
GREEN, GREEN_DEEP, PAPER, STAMP, BRASS = '#1E3D34', '#152B25', '#F6F4EE', '#B23A2E', '#A8843B'


def mark(bg=GREEN, fg=PAPER, accent=STAMP, line=BRASS, rx=14):
    """Pictogramme 64×64 : carré arrondi, arche de porte, seuil, serrure rouge."""
    return (f'<rect width="64" height="64" rx="{rx}" fill="{bg}"/>'
            f'<path d="M17.5 51V29a14.5 14.5 0 0 1 29 0v22" fill="none" stroke="{fg}" stroke-width="4"/>'
            f'<path d="M24.5 51V30.5a7.5 7.5 0 0 1 15 0V51" fill="none" stroke="{line}" stroke-width="1.6" opacity=".9"/>'
            f'<path d="M11 51.5h42" stroke="{fg}" stroke-width="3.4" stroke-linecap="round"/>'
            f'<circle cx="32" cy="36" r="3.9" fill="{accent}"/>'
            f'<path d="M30.1 38h3.8l1.3 7.8h-6.4z" fill="{accent}"/>')


def word_paths(text='Mémoria', size=40.0):
    """Tracés SVG du mot, ligne de base à y=0 ; renvoie (path_d, largeur)."""
    font = TTFont(os.path.join(HERE, 'fonts', 'LibreCaslonDisplay.ttf'))
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font['hmtx']
    scale = size / font['head'].unitsPerEm
    pen = SVGPathPen(gs)
    x = 0.0
    for ch in text:
        name = cmap[ord(ch)]
        gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, 0)))
        x += hmtx[name][0] * scale
    return pen.getCommands(), x


def write(path, svg):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w', encoding='utf-8').write(svg)


def main():
    d, w = word_paths()
    dot_r = 3.4
    # logo horizontal : pictogramme 64 + 16 d'espace + mot + point rouge
    width = round(64 + 16 + w + 4 + dot_r * 2 + 2)
    def logo(word_fill, mark_kwargs):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 64" role="img" aria-label="Mémoria">'
                f'{mark(**mark_kwargs)}'
                f'<g transform="translate(80 46)"><path d="{d}" fill="{word_fill}"/>'
                f'<circle cx="{w + 4 + dot_r:.1f}" cy="{-dot_r:.1f}" r="{dot_r}" fill="{STAMP}"/></g></svg>\n')
    write(os.path.join(OUT, 'logo', 'memoria-logo.svg'), logo(GREEN_DEEP, {}))
    write(os.path.join(OUT, 'logo', 'memoria-logo-white.svg'), logo(PAPER, dict(bg=PAPER, fg=GREEN, line=BRASS)))
    mk = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="Mémoria">{mark()}</svg>\n'
    write(os.path.join(OUT, 'logo', 'memoria-mark.svg'), mk)
    write(os.path.join(OUT, 'favicon.svg'), mk)
    print('logo généré, largeur', width)


if __name__ == '__main__':
    main()
