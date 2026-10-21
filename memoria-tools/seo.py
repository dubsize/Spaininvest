#!/usr/bin/env python3
"""Outil de maintenance Mémoria (non déployé, aucune étape de build).

Réécrit dans chaque page HTML de memoria/ un bloc balisé
<!-- seo:start --> … <!-- seo:end --> contenant canonical, hreflang,
Open Graph et Twitter, à partir du registre PAGES ci-dessous.
Génère aussi memoria/sitemap.xml.

Usage : python3 memoria-tools/seo.py
Le titre et la meta description restent écrits à la main dans chaque page ;
le script les lit pour remplir og:title / og:description.
"""
import html
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memoria')
BASE = 'https://memoriamadrid.com'
LOCALES = {'fr': 'fr_FR', 'en': 'en_GB', 'he': 'he_IL'}

# Chaque entrée = une même page dans ses différentes langues (URL publiques, sans .html).
PAGES = [
    {'fr': '/', 'en': '/en/', 'he': '/he/'},
    {'fr': '/services/', 'en': '/en/services/', 'he': '/he/services/'},
    {'fr': '/entreprises/', 'en': '/en/corporate/', 'he': '/he/corporate/'},
    {'fr': '/proprietaires/', 'en': '/en/landlords/', 'he': '/he/landlords/'},
    {'fr': '/guides/', 'en': '/en/guides/', 'he': '/he/guides/'},
    {'fr': '/guides/nie-avant-le-depart', 'en': '/en/guides/nie-before-you-move', 'he': '/he/guides/nie-before-you-move'},
    {'fr': '/guides/empadronamiento-madrid', 'en': '/en/guides/empadronamiento-madrid', 'he': '/he/guides/empadronamiento-madrid'},
    {'fr': '/guides/certificat-numerique-clave', 'en': '/en/guides/digital-certificate-clave'},
    {'fr': '/guides/scolariser-madrid-hors-campagne', 'en': '/en/guides/school-enrolment-madrid-mid-year'},
    {'fr': '/guides/cita-previa-nie-certificat-ue-madrid', 'en': '/en/guides/cita-previa-nie-eu-certificate-madrid'},
    {'fr': '/guides/louer-madrid-expatrie', 'en': '/en/guides/renting-in-madrid-as-an-expat'},
    {'fr': '/guides/electricite-gaz-eau-madrid', 'en': '/en/guides/electricity-gas-water-madrid'},
    {'fr': '/legal/mentions-legales', 'en': '/en/legal/legal-notice', 'he': '/he/legal/legal-notice'},
    {'fr': '/legal/politique-confidentialite', 'en': '/en/legal/privacy-policy', 'he': '/he/legal/privacy-policy'},
    {'fr': '/legal/politique-cookies', 'en': '/en/legal/cookie-policy', 'he': '/he/legal/cookie-policy'},
    {'fr': '/legal/conditions-generales', 'en': '/en/legal/terms', 'he': '/he/legal/terms'},
    {'en': '/docs/memoria-capability-statement'},
]

# Pages exclues du sitemap (en plus de celles marquées noindex).
NO_SITEMAP = {'/404', '/en/404', '/he/404'}


def file_for(url):
    if url.endswith('/'):
        return os.path.join(ROOT, url.lstrip('/'), 'index.html')
    return os.path.join(ROOT, url.lstrip('/') + '.html')


def url_for(path):
    rel = '/' + os.path.relpath(path, ROOT).replace(os.sep, '/')
    if rel.endswith('/index.html'):
        return rel[:-len('index.html')]
    return rel[:-len('.html')]


def lang_of(url):
    seg = url.strip('/').split('/')[0]
    return seg if seg in ('en', 'he') else 'fr'


def group_of(url):
    for g in PAGES:
        if url in g.values():
            # On ne garde que les langues dont le fichier existe réellement.
            return {l: u for l, u in g.items() if os.path.exists(file_for(u))}
    return {lang_of(url): url}


def meta(src, pattern):
    m = re.search(pattern, src, re.S)
    return html.unescape(m.group(1).strip()) if m else ''


def esc(s):
    return html.escape(s, quote=True)


STRIP = [
    r'\s*<!-- seo:start -->.*?<!-- seo:end -->',
    r'\s*<link rel="canonical"[^>]*>',
    r'\s*<link rel="alternate" hreflang="[^"]*"[^>]*>',
    r'\s*<meta property="og:[^"]*"[^>]*>',
    r'\s*<meta name="twitter:[^"]*"[^>]*>',
]


def process(path):
    url = url_for(path)
    src = open(path, encoding='utf-8').read()
    for p in STRIP:
        src = re.sub(p, '', src, flags=re.S)
    lang = lang_of(url)
    group = group_of(url)
    title = meta(src, r'<title>(.*?)</title>')
    desc = meta(src, r'<meta name="description" content="([^"]*)"')
    is_article = '/guides/' in url and not url.endswith('/guides/')
    lines = ['<!-- seo:start -->', f'<link rel="canonical" href="{BASE}{url}">']
    if len(group) > 1:
        for l in ('fr', 'en', 'he'):
            if l in group:
                lines.append(f'<link rel="alternate" hreflang="{l}" href="{BASE}{group[l]}">')
        default = group.get('en') or group.get('fr')
        lines.append(f'<link rel="alternate" hreflang="x-default" href="{BASE}{default}">')
    lines += [
        '<meta property="og:site_name" content="Mémoria">',
        f'<meta property="og:type" content="{"article" if is_article else "website"}">',
        f'<meta property="og:url" content="{BASE}{url}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:locale" content="{LOCALES[lang]}">',
    ]
    for l, u in group.items():
        if l != lang:
            lines.append(f'<meta property="og:locale:alternate" content="{LOCALES[l]}">')
    lines += [
        '<!-- [IMAGE : visuel de partage 1200×630 (logo Mémoria sur fond vert), à déposer en /og-image.png puis décommenter les deux lignes suivantes] -->',
        f'<!-- <meta property="og:image" content="{BASE}/og-image.png"> -->',
        '<!-- <meta name="twitter:image" content="https://memoriamadrid.com/og-image.png"> -->',
        '<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:description" content="{esc(desc)}">',
        '<!-- seo:end -->',
    ]
    src = src.replace('</head>', '\n'.join(lines) + '\n</head>', 1)
    open(path, 'w', encoding='utf-8').write(src)
    noindex = 'name="robots" content="noindex' in src
    return url, noindex


def main():
    urls = []
    for d, _, files in os.walk(ROOT):
        for f in sorted(files):
            if f.endswith('.html'):
                urls.append(process(os.path.join(d, f)))
    entries = []
    for url, noindex in sorted(urls):
        if noindex or url in NO_SITEMAP:
            continue
        g = group_of(url)
        alts = ''
        if len(g) > 1:
            alts = ''.join(
                f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{BASE}{u}"/>'
                for l, u in g.items())
            alts += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{g.get("en") or g.get("fr")}"/>'
        entries.append(f'  <url>\n    <loc>{BASE}{url}</loc>{alts}\n  </url>')
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"'
               ' xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
               + '\n'.join(entries) + '\n</urlset>\n')
    open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8').write(sitemap)
    print(f'{len(urls)} pages traitées, {len(entries)} URL dans le sitemap', file=sys.stderr)


if __name__ == '__main__':
    main()
