# Generate the e-ink render theme, symbols and fill patterns into app/src/main/assets/theme/.
# Widths are designed in device pixels for the 212 dpi target (mapsforge scale factor 212/160).
import os, re, shutil, sys
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'app', 'src', 'main', 'assets', 'theme')
MF = os.path.join(os.path.dirname(__file__), 'src', 'mapsforge-themes', 'assets')
DPI = 212 / 160.0


def base(px, z):
    """Theme width for `px` device pixels at zoom z (mapsforge scales by 1.5^(z-12) above z12)."""
    return round(px / (DPI * 1.5 ** max(z - 12, 0)), 4)


def unscaled(px):
    return round(px / DPI, 3)


# ------------------------------------------------------------------ symbols
ICONS = {  # class -> mapsforge symbol path or None for a custom one below
    'food': 'food/restaurant.svg', 'cafe': 'food/cafe.svg', 'bar': 'food/bar.svg', 'hotel': 'accommodation/hotel2.svg',
    'bank': 'money/bank2.svg', 'hospital': 'health/hospital.svg', 'clinic': 'health/doctors2.svg',
    'pharmacy': 'health/pharmacy.svg', 'school': 'education/school.svg', 'university': 'education/university.svg',
    'culture': 'tourist/theatre.svg', 'museum': 'tourist/museum.svg', 'sight': 'tourist/attraction.svg',
    'market': 'shopping/supermarket.svg', 'shop': 'shopping/convenience.svg', 'car': 'shopping/car_repair.svg',
    'fuel': 'transport/fuel.svg', 'parking': 'transport/parking.svg', 'post': 'amenity/post_office.svg',
    'toilets': 'amenity/toilets.svg', 'worship': 'place_of_worship/unknown.svg', 'sport': 'sport/stadium.svg',
    'train': 'transport/train_station2.svg', 'airport': 'transport/airport2.svg',
    'busstation': 'transport/bus_station.svg', 'oneway': 'oneway.svg', 'traffic_signals': 'traffic_signal.svg',
}
CUSTOM = {
    'subway': '<circle cx="50" cy="50" r="47" fill="#000"/><path d="M27 74V28l23 30 23-30v46" fill="none" stroke="#fff" stroke-width="11" stroke-linejoin="round"/>',
    'subway_entrance': '<rect x="6" y="6" width="88" height="88" rx="14" fill="#000"/><path d="M27 74V28l23 30 23-30v46" fill="none" stroke="#fff" stroke-width="11" stroke-linejoin="round"/>',
    'busstop': '<rect x="4" y="4" width="92" height="92" rx="18" fill="#000"/><rect x="22" y="18" width="56" height="58" rx="8" fill="#fff"/><rect x="29" y="26" width="42" height="22" fill="#000"/><circle cx="34" cy="64" r="5" fill="#000"/><circle cx="66" cy="64" r="5" fill="#000"/><rect x="26" y="76" width="10" height="10" fill="#fff"/><rect x="64" y="76" width="10" height="10" fill="#fff"/>',
    'park': '<circle cx="50" cy="50" r="47" fill="#000"/><path d="M50 14 74 58H26z" fill="#fff"/><path d="M50 32 78 74H22z" fill="#fff"/><rect x="45" y="72" width="10" height="16" fill="#fff"/>',
    'gov': '<circle cx="50" cy="50" r="47" fill="#000"/><path d="M50 16 82 36H18z" fill="#fff"/><rect x="24" y="40" width="9" height="30" fill="#fff"/><rect x="45.5" y="40" width="9" height="30" fill="#fff"/><rect x="67" y="40" width="9" height="30" fill="#fff"/><rect x="18" y="74" width="64" height="9" fill="#fff"/>',
    'mall': '<circle cx="50" cy="50" r="47" fill="#000"/><rect x="26" y="38" width="48" height="40" rx="4" fill="#fff"/><path d="M38 40V32a12 12 0 0 1 24 0v8" fill="none" stroke="#fff" stroke-width="7"/>',
    'peak': '<path d="M50 10 94 88H6z" fill="#000"/><path d="M50 30 66 58 58 54 50 62 42 54 34 58z" fill="#fff"/>',
    'ferry': '<circle cx="50" cy="50" r="47" fill="#000"/><path d="M20 56h60l-10 20H30z" fill="#fff"/><rect x="36" y="34" width="28" height="18" fill="#fff"/><rect x="47" y="20" width="6" height="14" fill="#fff"/>',
    'office': '<rect x="14" y="6" width="72" height="88" fill="#000"/><g fill="#fff"><rect x="26" y="18" width="14" height="12"/><rect x="60" y="18" width="14" height="12"/><rect x="26" y="40" width="14" height="12"/><rect x="60" y="40" width="14" height="12"/><rect x="42" y="68" width="16" height="26"/></g>',
    'estate': '<path d="M50 8 94 46H82V92H18V46H6z" fill="#000"/><rect x="40" y="60" width="20" height="32" fill="#fff"/>',
    'building': '<rect x="20" y="20" width="60" height="60" fill="#000"/>',
    'misc': '<circle cx="50" cy="50" r="40" fill="#000"/><circle cx="50" cy="50" r="16" fill="#fff"/>',
    'pin': '<path d="M50 96C50 96 14 58 14 36a36 36 0 0 1 72 0c0 22-36 60-36 60z" fill="#000" stroke="#fff" stroke-width="5"/><circle cx="50" cy="36" r="13" fill="#fff"/>',
}


def lum(hexcol):
    h = hexcol.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def bw(svg):
    def rep(m):
        return '#ffffff' if lum(m.group(0)) > 0.8 else '#000000'
    svg = re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', rep, svg)
    return svg


def write_symbols():
    d = os.path.join(OUT, 'symbols')
    os.makedirs(d, exist_ok=True)
    for cls, src in ICONS.items():
        svg = open(os.path.join(MF, 'symbols', src), encoding='utf-8').read()
        open(os.path.join(d, cls + '.svg'), 'w', encoding='utf-8').write(bw(svg))
    for cls, body in CUSTOM.items():
        open(os.path.join(d, cls + '.svg'), 'w', encoding='utf-8').write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">'
            + body + '</svg>')


# ------------------------------------------------------------------ patterns
def write_patterns():
    d = os.path.join(OUT, 'patterns')
    os.makedirs(d, exist_ok=True)

    def pat(name, size, draw_fn, bg=255):
        im = Image.new('L', (size, size), bg)
        draw_fn(ImageDraw.Draw(im), size)
        im.convert('RGB').save(os.path.join(d, name + '.png'))
    pat('park', 14, lambda dr, s: dr.rectangle([3, 3, 4, 4], fill=136) or dr.rectangle([10, 10, 11, 11], fill=136))
    pat('wood', 16, lambda dr, s: [dr.line([(x, y + 3), (x + 2, y), (x + 4, y + 3)], fill=102) for x, y in ((2, 3), (10, 11))])
    pat('sand', 12, lambda dr, s: dr.point([(2, 2), (8, 7)], fill=136))
    pat('marsh', 16, lambda dr, s: [dr.line([(x, y), (x + 6, y)], fill=119) for x, y in ((1, 4), (9, 12))])
    pat('hatch', 12, lambda dr, s: dr.line([(0, s - 1), (s - 1, 0)], fill=170), bg=246)
    pat('military', 10, lambda dr, s: dr.line([(0, s - 1), (s - 1, 0)], fill=119))
    pat('cemetery', 16, lambda dr, s: dr.line([(8, 3), (8, 12)], fill=102) or dr.line([(5, 6), (11, 6)], fill=102))
    pat('construction', 10, lambda dr, s: dr.point([(2, 2), (7, 7)], fill=119), bg=246)


def main():
    import build_theme_xml as tx
    import build_theme_labels as tl
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    write_symbols()
    write_patterns()
    tx.X.clear()
    tx.w('<?xml version="1.0" encoding="UTF-8"?>')
    tx.w('<rendertheme xmlns="http://mapsforge.org/renderTheme" version="5" map-background="#FFFFFF" '
         'map-background-outside="#E0E0E0" base-stroke-width="1" base-text-size="1">')
    tl.areas()
    tl.boundaries()
    tx.roads()
    tx.rail()
    tl.labels()
    tx.w('</rendertheme>')
    with open(os.path.join(OUT, 'qingdao_eink.xml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(tx.X) + '\n')
    # Keep category filtering available after regenerating the base theme.
    from annotate_theme import annotate
    annotate(os.path.join(OUT, 'qingdao_eink.xml'))
    print('theme rules:', sum(s.count('<rule') for s in tx.X), 'files:', len(os.listdir(os.path.join(OUT, 'symbols'))))


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(__file__))
    main()
