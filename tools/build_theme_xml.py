# Render theme XML generator (imported by build_theme.py).
from build_theme import base, unscaled

X = []


def w(s):
    X.append(s)


HALO = 'stroke="#FFFFFF"'

# class, values, core px @z14, border px @z14, core colour, casing colour, first casing zoom, low-zoom {z: px}, low colour
ROADS = [
    ('service', 'service', 1.6, 0.6, '#FFFFFF', '#8C8C8C', 16, {15: 1.0}, '#999999'),
    ('pedestrian', 'pedestrian', 2.2, 0.7, '#E6E6E6', '#777777', 15, {14: 1.6}, '#999999'),
    ('minor', 'unclassified|residential|road|living_street', 2.4, 0.7, '#FFFFFF', '#777777', 14, {13: 1.2}, '#888888'),
    ('link', 'motorway_link|trunk_link|primary_link|secondary_link|tertiary_link', 2.4, 0.8, '#FFFFFF', '#333333', 14,
     {12: 1.0, 13: 1.4}, '#555555'),
    ('tertiary', 'tertiary', 3.0, 0.9, '#FFFFFF', '#555555', 14, {12: 1.3, 13: 1.8}, '#666666'),
    ('secondary', 'secondary', 3.6, 1.0, '#FFFFFF', '#333333', 13, {10: 1.0, 11: 1.4, 12: 2.0}, '#555555'),
    ('primary', 'primary', 4.2, 1.2, '#FFFFFF', '#000000', 13, {9: 1.0, 10: 1.4, 11: 1.8, 12: 2.4}, '#333333'),
    ('trunk', 'trunk', 4.6, 1.3, '#C8C8C8', '#000000', 13, {7: 1.2, 8: 1.4, 9: 1.8, 10: 2.2, 11: 2.6, 12: 3.0}, '#000000'),
    ('motorway', 'motorway', 5.0, 1.4, '#9A9A9A', '#000000', 13,
     {6: 1.4, 7: 1.6, 8: 1.8, 9: 2.2, 10: 2.4, 11: 2.8, 12: 3.2}, '#000000'),
]
ZMAX = 19


def core_px(c14, z):
    return c14 * 1.55 ** (z - 14)


def border_px(b14, z):
    return b14 * 1.2 ** (z - 14)


def zr(z):
    return 'zoom-min="%d" zoom-max="%d"' % (z, z) if z < ZMAX else 'zoom-min="%d"' % z


def line(stroke, px, z, extra='', cat='road'):
    c = ' cat="%s"' % cat if cat else ''
    return '<line stroke="%s" stroke-width="%s"%s %s/>' % (stroke, base(px, z), c, extra)


def roads():
    w('<rule e="way" k="area" v="~|no|false">')
    # tunnels: pale dashed
    w('<rule e="way" k="tunnel" v="yes">')
    for cls, vals, c14, b14, core, cas, zc, low, lowc in ROADS:
        w('<rule e="way" k="highway" v="%s">' % vals)
        for z in range(min(low or {zc: 0}), ZMAX + 1):
            if z < zc:
                if z in low:
                    w('<rule e="way" k="*" v="*" %s>%s</rule>' % (zr(z), line('#AAAAAA', low[z] * 0.8, z, 'stroke-dasharray="%s,%s"' % (unscaled(6), unscaled(3)))))
                continue
            c, b = core_px(c14, z), border_px(b14, z)
            w('<rule e="way" k="*" v="*" %s>%s%s</rule>' % (
                zr(z), line('#999999', c + 2 * b, z, 'stroke-dasharray="%s,%s" stroke-linecap="butt"' % (unscaled(8), unscaled(4))),
                line('#F2F2F2', c, z)))
        w('</rule>')
    w('</rule>')
    w('<rule e="way" k="tunnel" v="~|no|false">')
    # bridge outline
    w('<rule e="way" k="bridge" v="yes">')
    for cls, vals, c14, b14, core, cas, zc, low, lowc in ROADS:
        w('<rule e="way" k="highway" v="%s">' % vals)
        for z in range(max(zc, 14), ZMAX + 1):
            w('<rule e="way" k="*" v="*" %s>%s</rule>' % (
                zr(z), line('#000000', core_px(c14, z) + 2 * border_px(b14, z) + 3, z, 'stroke-linecap="butt"')))
        w('</rule>')
    w('</rule>')
    # low zoom single lines (minor first so majors draw on top)
    for cls, vals, c14, b14, core, cas, zc, low, lowc in ROADS:
        if not low:
            continue
        w('<rule e="way" k="highway" v="%s">' % vals)
        for z, px in sorted(low.items()):
            if z < zc:
                w('<rule e="way" k="*" v="*" %s>%s</rule>' % (zr(z), line(lowc, px, z)))
        w('</rule>')
    # casings
    for cls, vals, c14, b14, core, cas, zc, low, lowc in ROADS:
        w('<rule e="way" k="highway" v="%s">' % vals)
        for z in range(zc, ZMAX + 1):
            w('<rule e="way" k="*" v="*" %s>%s</rule>' % (zr(z), line(cas, core_px(c14, z) + 2 * border_px(b14, z), z)))
        w('</rule>')
    # cores
    for cls, vals, c14, b14, core, cas, zc, low, lowc in ROADS:
        w('<rule e="way" k="highway" v="%s">' % vals)
        for z in range(zc, ZMAX + 1):
            w('<rule e="way" k="*" v="*" %s>%s</rule>' % (zr(z), line(core, core_px(c14, z), z)))
        w('</rule>')
    w('</rule>')  # tunnel
    # paths: fixed pixel widths
    w('<rule e="way" k="highway" v="construction" zoom-min="14"><line stroke="#999999" stroke-width="%s" '
      'stroke-dasharray="%s,%s" stroke-linecap="butt" scale="none" cat="path"/></rule>' % (unscaled(2.4), unscaled(6), unscaled(4)))
    w('<rule e="way" k="highway" v="track" zoom-min="15"><line stroke="#777777" stroke-width="%s" '
      'stroke-dasharray="%s,%s" stroke-linecap="butt" scale="none" cat="path"/></rule>' % (unscaled(1.6), unscaled(8), unscaled(3)))
    w('<rule e="way" k="highway" v="footway|path|cycleway|bridleway" zoom-min="15"><line stroke="#555555" '
      'stroke-width="%s" stroke-dasharray="%s,%s" stroke-linecap="butt" scale="none" cat="path"/></rule>' % (unscaled(1.2), unscaled(4), unscaled(3)))
    w('<rule e="way" k="highway" v="steps" zoom-min="16"><line stroke="#333333" stroke-width="%s" '
      'stroke-dasharray="%s,%s" stroke-linecap="butt" scale="none" cat="path"/></rule>' % (unscaled(3.5), unscaled(1.5), unscaled(1.5)))
    w('</rule>')  # area


def rail():
    w('<rule e="way" k="railway" v="rail|narrow_gauge">')
    w('<rule e="way" k="tunnel" v="yes" zoom-min="12"><line stroke="#888888" stroke-width="%s" '
      'stroke-dasharray="%s,%s" stroke-linecap="butt" scale="none" cat="rail"/></rule>' % (unscaled(1.6), unscaled(6), unscaled(4)))
    w('<rule e="way" k="tunnel" v="~|no|false">')
    w('<rule e="way" k="*" v="*" zoom-max="12"><line stroke="#444444" stroke-width="%s" scale="none" cat="rail"/></rule>' % unscaled(1.4))
    w('<rule e="way" k="*" v="*" zoom-min="13"><line stroke="#000000" stroke-width="%s" stroke-linecap="butt" scale="none" cat="rail"/>'
      '<line stroke="#FFFFFF" stroke-width="%s" stroke-dasharray="%s,%s" stroke-linecap="butt" scale="none" cat="rail"/></rule>'
      % (unscaled(4), unscaled(2), unscaled(9), unscaled(9)))
    w('</rule></rule>')
    w('<rule e="way" k="railway" v="subway|light_rail">')
    w('<rule e="way" k="*" v="*" zoom-max="14"><line stroke="#333333" stroke-width="%s" stroke-dasharray="%s,%s" '
      'stroke-linecap="butt" scale="none" cat="rail"/></rule>' % (unscaled(2.6), unscaled(10), unscaled(3)))
    w('<rule e="way" k="*" v="*" zoom-min="15"><line stroke="#777777" stroke-width="%s" stroke-dasharray="%s,%s" '
      'stroke-linecap="butt" scale="none" cat="rail"/></rule>' % (unscaled(2.2), unscaled(10), unscaled(3)))
    w('</rule>')
    w('<rule e="way" k="railway" v="tram"><line stroke="#444444" stroke-width="%s" scale="none" cat="rail"/></rule>' % unscaled(1.4))
    w('<rule e="way" k="route" v="ferry"><line stroke="#8C8C8C" stroke-width="%s" stroke-dasharray="%s,%s" '
      'stroke-linecap="butt" scale="none" cat="transport"/></rule>' % (unscaled(1.2), unscaled(4), unscaled(8)))
    w('<rule e="way" k="aerialway" v="*"><line stroke="#000000" stroke-width="%s" stroke-dasharray="%s,%s" '
      'stroke-linecap="butt" scale="none" cat="transport"/></rule>' % (unscaled(1.4), unscaled(2), unscaled(5)))
    w('<rule e="way" k="aeroway" v="runway"><line stroke="#777777" stroke-width="%s" stroke-linecap="butt" cat="transport"/></rule>' % base(10, 14))
    w('<rule e="way" k="aeroway" v="taxiway"><line stroke="#999999" stroke-width="%s" cat="transport"/></rule>' % base(3, 14))
