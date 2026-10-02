"""Multilingual dictionaries (ES / FR / DE / IT / EN / PT).

All patterns operate on *folded* text (lower-case, no accents; see ``text.fold``).
Order matters where noted: more specific phrases must be checked first.
"""

from __future__ import annotations

import re

from arbscan.db.enums import Condition

# --------------------------------------------------------------------------- materials
# (canonical value, patterns). Specific (white/rose gold) before generic gold.
MATERIALS: list[tuple[str, list[str]]] = [
    ("white_gold", [r"white gold", r"or blanc", r"oro blanco", r"weissgold", r"weiss ?gold", r"oro bianco", r"ouro branco", r"\bwg\b"]),
    ("rose_gold", [r"rose gold", r"pink gold", r"or rose", r"oro rosa", r"rosegold", r"rose ?gold", r"rotgold", r"ouro rosa", r"\brg\b", r"sedna"]),
    ("two_tone", [r"two[- ]tone", r"bicolor", r"bicolore", r"acier ?/ ?or", r"acero ?(y|/) ?oro", r"stahl ?/ ?gold", r"rolesor", r"acciaio ?(e|/) ?oro"]),
    ("yellow_gold", [r"yellow gold", r"or jaune", r"oro amarillo", r"gelbgold", r"gelb ?gold", r"oro giallo", r"ouro amarelo", r"\byg\b", r"\b18k gold\b"]),
    ("platinum", [r"platinum", r"platine", r"platino", r"platin\b", r"\bpt950\b"]),
    ("titanium", [r"titanium", r"titane", r"titanio", r"titan\b"]),
    ("steel", [r"stainless steel", r"\bsteel\b", r"\bacier\b", r"\bacero\b", r"edelstahl", r"\bstahl\b", r"acciaio", r"\baco\b", r"\binox\b"]),
    ("monogram_canvas", [r"monogram", r"monogramme", r"monograma"]),
    ("damier_ebene", [r"damier eb[e]?ne", r"damier ebene"]),
    ("damier_azur", [r"damier azur"]),
    ("leather", [r"\bleather\b", r"\bcuir\b", r"\bpiel\b", r"\bleder\b", r"\bpelle\b", r"\bcouro\b", r"lambskin", r"caviar", r"agneau", r"cordero"]),
    ("onyx", [r"\bonyx\b", r"\bonix\b", r"\bonice\b"]),
    ("mother_of_pearl", [r"mother of pearl", r"nacre", r"\bnacar\b", r"perlmutt", r"madreperla"]),
    ("malachite", [r"malachite", r"malaquita", r"malachit"]),
    ("carnelian", [r"carnelian", r"cornaline", r"cornalina", r"karneol"]),
]

# --------------------------------------------------------------------------- colours (generic)
COLORS: list[tuple[str, list[str]]] = [
    ("black", [r"\bblack\b", r"\bnoir[e]?\b", r"\bnegr[oa]\b", r"\bschwarz\b", r"\bner[oa]\b", r"\bpret[oa]\b"]),
    ("white", [r"\bwhite\b", r"\bblanc(he)?\b", r"\bblanc[oa]\b", r"\bweiss\b", r"\bbianc[oa]\b", r"\bbranc[oa]\b"]),
    ("beige", [r"\bbeige\b", r"\bnude\b", r"\btan\b"]),
    ("blue", [r"\bblue\b", r"\bbleu[e]?\b", r"\bazul\b", r"\bblau\b", r"\bblu\b"]),
    ("green", [r"\bgreen\b", r"\bvert[e]?\b", r"\bverde\b", r"\bgrun\b"]),
    ("red", [r"\bred\b", r"\brouge\b", r"\brojo\b", r"\brot\b", r"\brosso\b"]),
    ("silver", [r"\bsilver\b", r"\bargent\b", r"\bplata\b", r"\bsilber\b", r"\bargento\b"]),
    ("grey", [r"\bgr[ae]y\b", r"\bgris\b", r"\bgrau\b", r"\bgrigio\b", r"space gr[ae]y"]),
]

# --------------------------------------------------------------------------- generic size
SIZE_PATTERNS: list[str] = [
    r"(?:taille|talla|size|grosse|groesse|misura|tamano|tamanho|taglia)\s*:?\s*(\d{2})\b",
    r"\bt\.?\s?(\d{2})\b",
    r"\bsz\.?\s?(\d{2})\b",
]

CASE_SIZE_PATTERN = r"\b(\d{2})\s?mm\b"

# --------------------------------------------------------------------------- condition
# Ordered: most specific first. Returned value is the first match.
CONDITIONS: list[tuple[Condition, list[str]]] = [
    (Condition.FOR_PARTS, [
        r"for parts", r"para piezas", r"pour pieces", r"\bdefekt\b", r"no funciona", r"ne fonctionne pas",
        r"\bhs\b", r"averiad[oa]", r"\bbroken\b", r"non funzionante", r"per ricambi", r"para pecas", r"\brotto\b",
        r"not working", r"ersatzteil",
    ]),
    (Condition.LIKE_NEW, [
        r"como nuevo", r"comme neuf", r"wie neu", r"come nuovo", r"como novo", r"like new", r"\bmint\b",
        r"a estrenar", r"sin estrenar", r"jamais porte", r"nunca usad[oa]", r"never used", r"neuwertig",
        r"etat neuf", r"perfecto estado", r"estado impecable", r"impecable", r"pari al nuovo",
        r"used - like new", r"open box",
    ]),
    (Condition.NEW, [
        r"\bnuevo\b", r"\bneuf\b", r"\bneu\b", r"\bnuovo\b", r"\bnovo\b", r"\bbrand new\b", r"^new\b", r"\bnew\b",
        r"precintad[oa]", r"\bsealed\b", r"scelle", r"\bovp\b", r"sous blister", r"con etiqueta", r"avec etiquette",
        r"new with tags", r"\bnwt\b", r"sigillat[oa]",
    ]),
    (Condition.VERY_GOOD, [
        r"muy buen estado", r"tres bon etat", r"sehr gut", r"sehr guter zustand", r"ottime condizioni",
        r"ottimo stato", r"muito bom estado", r"very good", r"excellent", r"excelente", r"excellente",
        r"pre-owned - excellent",
    ]),
    (Condition.GOOD, [
        r"buen estado", r"bon etat", r"guter zustand", r"\bgut\b", r"buone condizioni", r"buono stato",
        r"bom estado", r"\bgood\b", r"pre-owned", r"pre owned", r"gebraucht", r"\bused\b", r"usad[oa]", r"usat[oa]",
        r"occasion", r"seminuevo",
    ]),
    (Condition.FAIR, [
        r"estado aceptable", r"etat correct", r"\baceptable\b", r"akzeptabel", r"condizioni accettabili",
        r"\bfair\b", r"signs of wear", r"signes d'usure", r"marcas de uso", r"gebrauchsspuren", r"segni di usura",
        r"rayures", r"aranazos", r"kratzer", r"graffi",
    ]),
]

# Value multipliers relative to "good" condition, used by valuation to make comparables comparable.
CONDITION_FACTORS: dict[str, float] = {
    Condition.NEW: 1.12,
    Condition.LIKE_NEW: 1.06,
    Condition.VERY_GOOD: 1.03,
    Condition.GOOD: 1.0,
    Condition.FAIR: 0.88,
    Condition.FOR_PARTS: 0.45,
    Condition.UNKNOWN: 0.98,
}

# --------------------------------------------------------------------------- accessories
# Negative forms are checked first: "sin caja" must not count as box present.
ACCESSORY_NEGATIVE: dict[str, list[str]] = {
    "box": [r"sin caja", r"sans (la )?bo[iî]te", r"ohne (box|ovp|karton)", r"no box", r"without box", r"senza scatola", r"sem caixa", r"sans boite"],
    "papers": [r"sin papeles", r"sans papiers", r"ohne papiere", r"no papers", r"without papers", r"senza (documenti|garanzia)", r"sem papeis", r"sin certificado", r"sans certificat"],
    "receipt": [r"sin factura", r"sans facture", r"ohne rechnung", r"no receipt", r"no invoice", r"senza scontrino", r"sem fatura", r"sin ticket"],
}
ACCESSORY_POSITIVE: dict[str, list[str]] = {
    "box": [r"\bcaja\b", r"\bbo[iî]te\b", r"\bbox\b", r"\bovp\b", r"\bscatola\b", r"\bcaixa\b", r"\bestuche\b", r"\bcoffret\b", r"\bfull set\b", r"juego completo"],
    "papers": [r"\bpapeles\b", r"\bpapiers\b", r"\bpapers\b", r"\bpapiere\b", r"garantia", r"garantie", r"warranty", r"certificat", r"certificado", r"certificate", r"garanzia", r"\bfull set\b", r"tarjeta de garantia", r"carte de garantie"],
    "receipt": [r"\bfactura\b", r"\bticket\b", r"\bfacture\b", r"\brechnung\b", r"\binvoice\b", r"\breceipt\b", r"\bscontrino\b", r"\bfattura\b", r"\bfatura\b", r"justificatif", r"preuve d'achat", r"kaufbeleg"],
    "dust_bag": [r"dust ?bag", r"\bhousse\b", r"\bpochon\b", r"staubbeutel", r"\bfunda\b", r"\bdustbag\b"],
    "screwdriver": [r"destornillador", r"tournevis", r"schraubendreher", r"screwdriver", r"cacciavite"],
    "charger": [r"cargador", r"chargeur", r"ladegerat", r"\bcharger\b", r"caricabatterie"],
}

# --------------------------------------------------------------------------- accessory-only listings
# A listing that sells only the box / a case / a manual must not be valued as the product.
ACCESSORY_ONLY_PATTERNS: list[str] = [
    r"solo (la )?caja", r"caja vacia", r"bo[iî]te vide", r"seulement (la )?bo[iî]te", r"leere (box|schachtel|verpackung)",
    r"nur (die )?(box|ovp|verpackung)", r"empty box", r"box only", r"only (the )?box", r"scatola vuota", r"solo scatola",
    r"\bdust ?bag only\b", r"\bmanual only\b", r"\bsolo (el )?manual\b", r"\bnotice seule\b",
    r"\b(funda|housse|hulle|cover|carcasa|custodia|skin|protector) (para|pour|fur|for|per)\b",
    r"\b(compatible|compatibles|kompatibel|compatibile) (con|avec|mit|with)\b",
    r"\b(replacement|recambio|piece detachee|ersatz) ",
    r"\b(strap|bracelet en cuir|correa|bracelet de montre|armband) (para|pour|fur|for)\b",
    r"\bsticker\b", r"\bpegatina\b", r"\bposter\b", r"\bcatalog(ue|o)?\b",
]

# --------------------------------------------------------------------------- authenticity statements
AUTHENTICITY_PATTERNS: list[str] = [
    r"authenti[cq]", r"autentic", r"autentic[oa]", r"\bechtheit", r"\becht\b", r"\boriginal\b", r"\boriginale\b",
    r"certificat d'authenticite", r"certificado de autenticidad", r"entrupy", r"\bserial\b", r"numero de serie",
    r"seriennummer", r"date code", r"\bcodigo\b", r"\bfactura\b", r"\bfacture\b", r"\brechnung\b",
    r"\binvoice\b", r"\breceipt\b", r"comprado en", r"achete (en|chez|a)", r"gekauft (bei|in)", r"acquistato",
]

# --------------------------------------------------------------------------- counterfeit indicators
COUNTERFEIT_PATTERNS: list[str] = [
    r"\breplica\b", r"\breplique\b", r"\brepliki?\b", r"\bfake\b", r"\bimitacion\b", r"\bimitation\b", r"\bcopia\b",
    r"\bcopie\b", r"\bnachbildung\b", r"\binspired\b", r"\binspire\b", r"\bestilo\b", r"\bstyle\b", r"\btipo\b",
    r"\baaa\b", r"\b1:1\b", r"\bmirror quality\b", r"\bsuperclone\b", r"\bclone\b", r"\bdupe\b", r"\bsimilar a\b",
    r"\bfacon\b",
]

# --------------------------------------------------------------------------- off-platform / payment language
# Strong signals: classic scam payment methods / moving the conversation off-platform.
OFF_PLATFORM_PATTERNS: list[str] = [
    r"whats ?app", r"\btelegram\b", r"\bwechat\b",
    r"western union", r"moneygram",
    r"paypal (amigos|friends|famille|amici|freunde)", r"amigos y familiares", r"friends (and|&) family",
    r"entre (amis|proches)", r"\bcrypto\b", r"\bbitcoin\b", r"\busdt\b", r"\bgift ?card", r"tarjeta regalo",
    r"carte cadeau", r"\bmandat cash\b", r"\bpcs\b", r"\bneosurf\b",
    r"escribe(me)? (al|a mi) (correo|email|mail)", r"contacte?z?[- ]moi (par|sur) (mail|email|sms|whatsapp)",
    r"schreib(en sie)? mir (per|eine) (mail|e-mail)", r"contattami (su|via|per)",
    r"pago por adelantado", r"paiement d'avance", r"vorkasse", r"pagamento anticipato",
    r"fuera de (la app|wallapop)", r"hors (de )?(leboncoin|la plateforme)", r"ausserhalb von (ebay|kleinanzeigen)",
]
# Weaker signals: payment methods without buyer protection (common, but worth noting).
UNPROTECTED_PAYMENT_PATTERNS: list[str] = [
    r"\bbizum\b", r"transferencia", r"\bvirement\b", r"uberweisung", r"bonifico", r"solo (envio|pago) (por|con)",
    r"envoi uniquement", r"nur versand", r"\blydia\b", r"\bpaylib\b",
]
EMAIL_PATTERN = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)
PHONE_PATTERN = re.compile(
    r"(?<![\d.])(?:(?:\+|00)(?:34|33|49|39|351)[\s.-]?)?(?:[67]\d{2}[\s-]?\d{3}[\s-]?\d{3}|0[67](?:[\s.-]?\d{2}){4})(?![\d.])"
)

# --------------------------------------------------------------------------- stock photo hints
STOCK_PHOTO_PATTERNS: list[str] = [
    r"foto(s)? de internet", r"imagen(es)? de internet", r"photo(s)? non contractuelle", r"photo(s)? internet",
    r"symbolbild", r"beispielbild", r"foto(s)? (di|da) internet", r"stock photo", r"imagen ilustrativa",
    r"foto ilustrativa", r"photo d'illustration", r"image d'illustration",
]
STOCK_IMAGE_HOSTS: list[str] = [
    "cartier.com", "louisvuitton.com", "chanel.com", "vancleefarpels.com", "rolex.com", "omegawatches.com",
    "tudorwatch.com", "apple.com", "sonos.com", "dyson", "thermomix", "vorwerk", "loewe.com", "bugaboo.com",
    "cybex-online.com", "shutterstock", "istockphoto", "gettyimages", "amazon.com/images", "m.media-amazon.com",
]


def compile_all(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p) for p in patterns]
