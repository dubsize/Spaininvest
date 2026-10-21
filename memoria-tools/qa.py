#!/usr/bin/env python3
"""Contrôle qualité du dossier memoria/ avant glisser-déposer sur Netlify.

Usage : python3 memoria-tools/qa.py [--placeholders]
Vérifie : liens internes et ancres, métadonnées, hreflang réciproques,
formulaires Netlify, sitemap, poids des pages. Liste les [PLACEHOLDERS].
"""
import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'memoria')
BASE = 'https://memoriamadrid.com'


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.forms, self.h1 = [], set(), [], 0
        self.form = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
        if tag in ('link', 'script', 'img') and (a.get('href') or a.get('src')):
            if a.get('rel') not in ('canonical', 'alternate', 'preconnect'):
                self.links.append(a.get('href') or a.get('src'))
        if tag == 'h1':
            self.h1 += 1
        if tag == 'form':
            self.form = dict(attrs=a, fields=[])
            self.forms.append(self.form)
        if self.form is not None and tag in ('input', 'select', 'textarea') and a.get('name'):
            self.form['fields'].append((a.get('name'), a.get('type', tag), a.get('value'), 'required' in a))

    def handle_endtag(self, tag):
        if tag == 'form':
            self.form = None


def url_for(path):
    rel = '/' + os.path.relpath(path, ROOT).replace(os.sep, '/')
    return rel[:-len('index.html')] if rel.endswith('/index.html') else rel[:-5]


def resolve(path):
    """Fichier servi par Netlify pour un chemin d'URL (pretty URLs)."""
    p = path.split('#')[0].split('?')[0]
    cands = [p, p + '.html', p.rstrip('/') + '/index.html'] if not p.endswith('/') else [p + 'index.html']
    for c in cands:
        f = os.path.join(ROOT, c.lstrip('/'))
        if os.path.isfile(f):
            return f
    return None


def main():
    pages = {}
    for d, _, fs in os.walk(ROOT):
        for f in fs:
            if f.endswith('.html'):
                p = os.path.join(d, f)
                src = open(p, encoding='utf-8').read()
                parser = P()
                parser.feed(src)
                pages[p] = (src, parser)
    errors, warns = [], []
    for p, (src, ps) in sorted(pages.items()):
        u = url_for(p)
        rel = os.path.relpath(p, ROOT)
        lang = re.search(r'<html lang="(\w+)"', src)
        if not lang:
            errors.append(f'{rel}: <html lang> manquant')
        elif lang.group(1) == 'he' and 'dir="rtl"' not in src[:200]:
            errors.append(f'{rel}: page hébreu sans dir="rtl"')
        for tag in ('<title>', 'name="description"', 'rel="canonical"', 'name="viewport"'):
            if tag not in src:
                errors.append(f'{rel}: {tag} manquant')
        if ps.h1 != 1 and 'cap-body' not in src:
            warns.append(f'{rel}: {ps.h1} h1')
        if '/404' not in u and 'cookies.js' not in src and 'cap-body' not in src:
            errors.append(f'{rel}: cookies.js absent')
        if 'plausible.io' not in src:
            errors.append(f'{rel}: Plausible absent')
        if 'site-v2.js' not in src and 'cap-body' not in src:
            warns.append(f'{rel}: site-v2.js absent (pas de bouton WhatsApp)')
        # liens internes + ancres
        for href in ps.links:
            if href.startswith(('mailto:', 'tel:', 'javascript:')) or href.startswith('https://fonts') or 'plausible.io' in href:
                continue
            full = urljoin(BASE + u, href)
            pu = urlparse(full)
            if pu.netloc != 'memoriamadrid.com':
                continue
            target = resolve(pu.path or '/')
            if not target:
                errors.append(f'{rel}: lien cassé {href}')
                continue
            if pu.fragment and target in pages and pu.fragment not in pages[target][1].ids:
                errors.append(f'{rel}: ancre absente {href}')
        # hreflang réciproques
        for hl, href in re.findall(r'hreflang="([^"]+)" href="([^"]+)"', src):
            if hl == 'x-default':
                continue
            t = resolve(urlparse(href).path)
            if not t:
                errors.append(f'{rel}: hreflang {hl} vers une page inexistante {href}')
            elif BASE + u not in pages[t][0]:
                errors.append(f'{rel}: hreflang {hl} non réciproque ({href})')
        # formulaires
        for f in ps.forms:
            a, names = f['attrs'], [x[0] for x in f['fields']]
            name = a.get('name')
            if a.get('data-netlify') != 'true' or a.get('netlify-honeypot') != 'bot-field':
                errors.append(f'{rel}: formulaire {name} sans data-netlify/honeypot')
            if ('form-name', 'hidden', name, False) not in f['fields']:
                errors.append(f'{rel}: formulaire {name} sans champ caché form-name')
            if 'bot-field' not in names:
                errors.append(f'{rel}: formulaire {name} sans champ bot-field')
            if not any(n in ('consentement', 'consent') and r for n, _, _, r in f['fields']):
                errors.append(f'{rel}: formulaire {name} sans consentement obligatoire')
        size = os.path.getsize(p)
        if size > 120_000:
            warns.append(f'{rel}: {size // 1024} Ko de HTML')
    # mêmes champs pour un même formulaire dans les trois langues
    byname = {}
    for p, (_, ps) in pages.items():
        for f in ps.forms:
            byname.setdefault(f['attrs'].get('name'), []).append((os.path.relpath(p, ROOT), sorted({x[0] for x in f['fields']})))
    for name, lst in byname.items():
        if len({tuple(x[1]) for x in lst}) > 1:
            errors.append(f'formulaire {name} : champs différents selon les pages {lst}')
    # sitemap
    sm = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
    for loc in re.findall(r'<loc>([^<]+)</loc>', sm):
        t = resolve(urlparse(loc).path)
        if not t:
            errors.append(f'sitemap : {loc} introuvable')
        elif 'noindex' in pages[t][0]:
            errors.append(f'sitemap : {loc} est en noindex')
    for need in ('_redirects', 'netlify.toml', 'robots.txt', '404.html', 'site-v2.css', 'site-v2.js'):
        if not os.path.exists(os.path.join(ROOT, need)):
            errors.append(f'fichier manquant : {need}')

    print(f'{len(pages)} pages HTML, formulaires : ' + ', '.join(f'{k} ×{len(v)}' for k, v in sorted(byname.items())))
    print(f'{len(errors)} erreur(s)')
    for e in errors:
        print('  ERREUR', e)
    print(f'{len(warns)} avertissement(s)')
    for w in warns:
        print('  avert.', w)

    if '--placeholders' in sys.argv:
        pat = re.compile(r'\[(?:IMAGE :[^\]]*|[A-ZÉÈÀÂÎÔÛÇ_][A-ZÉÈÀÂÎÔÛÇ0-9 _\'’\-—]*(?: \d)?|X|[A-Z]+ \{n\}|LOGO CLIENT \d|CLIENT LOGO \d)\]'
                         r'|\[(?:לוגו לקוח \d|שם פרטי|אזרחות|תפקיד|תחום החברה|המלצה \d[^\]]*|ציטוט[^\]]*)\]'
                         r'|\[(?:TÉMOIGNAGE|TESTIMONIAL|CITATION|QUOTE)[^\]]*\]')
        print('\nPLACEHOLDERS')
        for d, _, fs in sorted(os.walk(ROOT)):
            for f in sorted(fs):
                if not f.endswith(('.html', '.js', '.css', '.toml', '.xml')):
                    continue
                p = os.path.join(d, f)
                for i, line in enumerate(open(p, encoding='utf-8'), 1):
                    found = sorted(set(m.group(0) for m in pat.finditer(line)))
                    if found:
                        print(f'{os.path.relpath(p, ROOT)}:{i}\t' + '  '.join(found))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
