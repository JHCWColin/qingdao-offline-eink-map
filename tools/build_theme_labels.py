# Areas, boundaries and labels for the render theme (imported by build_theme.py).
from build_theme import base, unscaled
from build_theme_xml import w, HALO

WATER = '#C4C4C4'


def areas():
    w('<rule e="way" k="natural" v="sea|issea" cat="water"><area fill="%s" cat="water"/></rule>' % WATER)
    w('<rule e="way" k="natural" v="nosea"><area fill="#FFFFFF" stroke="#FFFFFF" stroke-width="%s"/></rule>' % unscaled(1))
    w('<rule e="way" k="natural" v="coastline" zoom-min="10"><line stroke="#555555" stroke-width="%s" scale="none"/></rule>' % unscaled(1.2))
    a = [
        ('landuse', 'residential|commercial|retail', 11, '<area fill="#F2F2F2"/>'),
        ('landuse', 'industrial|port|railway', 12, '<area src="patterns/hatch.png"/>'),
        ('landuse', 'construction|quarry', 13, '<area src="patterns/construction.png"/>'),
        ('landuse', 'military', 12, '<area src="patterns/military.png" stroke="#777777" stroke-width="%s"/>' % unscaled(1)),
        ('landuse', 'cemetery', 13, '<area src="patterns/cemetery.png"/>'),
        ('amenity', 'grave_yard', 13, '<area src="patterns/cemetery.png"/>'),
        ('landuse', 'grass|meadow|recreation_ground|village_green|orchard', 13, '<area src="patterns/park.png"/>'),
        ('natural', 'grassland|heath|scrub', 12, '<area src="patterns/park.png"/>'),
        ('leisure', 'park|garden|nature_reserve|golf_course', 11, '<area src="patterns/park.png"/>'),
        ('natural', 'wood', 10, '<area src="patterns/wood.png"/>'),
        ('landuse', 'forest', 10, '<area src="patterns/wood.png"/>'),
        ('natural', 'beach|sand', 12, '<area src="patterns/sand.png"/>'),
        ('natural', 'bare_rock', 13, '<area fill="#E6E6E6"/>'),
        ('natural', 'wetland', 12, '<area src="patterns/marsh.png"/>'),
        ('amenity', 'school|university|college|kindergarten|hospital', 13,
         '<area fill="#FAFAFA" stroke="#999999" stroke-width="%s" scale="none"/>' % unscaled(1)),
        ('tourism', 'zoo|theme_park', 13, '<area stroke="#777777" stroke-width="%s" scale="none"/>' % unscaled(1.2)),
        ('leisure', 'stadium|sports_centre|pitch|track|playground|swimming_pool', 14,
         '<area fill="#E6E6E6" stroke="#888888" stroke-width="%s" scale="none"/>' % unscaled(1)),
        ('aeroway', 'aerodrome', 9, '<area fill="#EBEBEB" stroke="#888888" stroke-width="%s" scale="none"/>' % unscaled(1)),
        ('aeroway', 'apron', 13, '<area fill="#D6D6D6"/>'),
        ('amenity', 'parking', 15, '<area fill="#EBEBEB" stroke="#AAAAAA" stroke-width="%s" scale="none"/>' % unscaled(1)),
        ('railway', 'platform', 16, '<area fill="#D6D6D6" stroke="#777777" stroke-width="%s" scale="none"/>' % unscaled(1)),
        ('man_made', 'pier|breakwater|groyne', 13, '<area fill="#FFFFFF" stroke="#555555" stroke-width="%s" scale="none"/>' % unscaled(1)),
    ]
    for k, v, z, body in a:
        w('<rule e="way" k="%s" v="%s" zoom-min="%d" closed="yes">%s</rule>' % (k, v, z, body))
    w('<rule e="way" k="man_made" v="pier|breakwater|groyne" closed="no" zoom-min="13"><line stroke="#555555" '
      'stroke-width="%s"/></rule>' % base(4, 14))
    # water bodies (kept separate so they can be toggled)
    w('<rule e="way" k="natural" v="water" cat="water"><area fill="%s" cat="water"/></rule>' % WATER)
    w('<rule e="way" k="landuse" v="reservoir|basin|salt_pond|aquaculture" cat="water" zoom-min="10">'
      '<area fill="%s" cat="water"/></rule>' % WATER)
    w('<rule e="way" k="waterway" v="riverbank" cat="water" zoom-min="10"><area fill="%s" cat="water"/></rule>' % WATER)
    w('<rule e="way" k="waterway" v="riverbank" zoom-max="9" closed="yes"><area fill="%s"/></rule>' % WATER)
    for v, z, px, col in (('river', 10, 3.0, '#999999'), ('canal', 12, 2.2, '#999999'), ('stream', 14, 1.4, '#888888'),
                          ('drain|ditch', 15, 1.2, '#999999')):
        w('<rule e="way" k="waterway" v="%s" zoom-min="%d" closed="no"><line stroke="%s" stroke-width="%s" scale="none" cat="water"/></rule>'
          % (v, z, col, unscaled(px)))
    w('<rule e="way" k="building" v="*" zoom-min="15"><area fill="#DEDEDE" stroke="#8C8C8C" stroke-width="%s" scale="none" cat="building"/></rule>'
      % unscaled(1))


def boundaries():
    w('<rule e="way" k="qd_boundary" v="town" zoom-min="12"><line stroke="#999999" stroke-width="%s" '
      'stroke-dasharray="%s,%s,%s,%s" stroke-linecap="butt" scale="none" cat="boundary"/></rule>'
      % (unscaled(1.2), unscaled(6), unscaled(3), unscaled(2), unscaled(3)))
    w('<rule e="way" k="qd_boundary" v="district" zoom-min="8"><line stroke="#555555" stroke-width="%s" '
      'stroke-dasharray="%s,%s" stroke-linecap="butt" scale="none" cat="boundary"/></rule>'
      % (unscaled(2.2), unscaled(10), unscaled(5)))
    w('<rule e="way" k="qd_boundary" v="city"><line stroke="#000000" stroke-width="%s" '
      'stroke-dasharray="%s,%s,%s,%s" stroke-linecap="butt" scale="none" cat="boundary"/></rule>'
      % (unscaled(3.2), unscaled(14), unscaled(4), unscaled(3), unscaled(4)))


# poi class -> (zoom-min, font-size, bold, priority, symbol size, category)
POI = {
    'airport': (10, 14, 1, 95, 22, 'transport'), 'train': (11, 14, 1, 92, 22, 'transport'),
    'subway': (13, 13, 1, 88, 18, 'transport'), 'ferry': (13, 13, 1, 80, 18, 'transport'),
    'busstation': (14, 13, 1, 75, 18, 'transport'), 'university': (13, 13, 1, 74, 18, 'poi'),
    'hospital': (14, 13, 1, 76, 18, 'poi'), 'sight': (14, 13, 1, 72, 18, 'poi'),
    'museum': (14, 13, 1, 72, 18, 'poi'), 'park': (14, 13, 0, 66, 18, 'poi'), 'mall': (14, 13, 0, 66, 18, 'shop'),
    'peak': (12, 12, 0, 60, 14, 'poi'), 'school': (15, 12, 0, 56, 16, 'poi'), 'gov': (15, 12, 0, 55, 16, 'poi'),
    'hotel': (15, 12, 0, 54, 16, 'poi'), 'market': (15, 12, 0, 54, 16, 'shop'), 'culture': (15, 12, 0, 54, 16, 'poi'),
    'sport': (15, 12, 0, 50, 16, 'poi'), 'worship': (15, 12, 0, 50, 16, 'poi'), 'fuel': (15, 12, 0, 48, 16, 'transport'),
    'clinic': (16, 12, 0, 46, 16, 'poi'), 'pharmacy': (16, 12, 0, 44, 16, 'poi'),
    'bank': (16, 12, 0, 44, 16, 'poi'), 'post': (16, 12, 0, 44, 16, 'poi'), 'food': (16, 12, 0, 42, 16, 'food'),
    'cafe': (16, 12, 0, 40, 16, 'food'), 'bar': (16, 12, 0, 38, 16, 'food'), 'shop': (16, 12, 0, 36, 15, 'shop'),
    'car': (16, 12, 0, 34, 15, 'shop'), 'office': (16, 12, 0, 34, 15, 'poi'), 'building': (16, 12, 0, 33, 10, 'poi'),
    'parking': (16, 11, 0, 30, 15, 'transport'), 'toilets': (16, 11, 0, 30, 15, 'poi'), 'misc': (16, 11, 0, 28, 12, 'poi'),
}


def caption(k, size, prio, fill='#000000', bold=False, italic=False, halo=3.0, extra='', cat=None):
    style = 'bold_italic' if bold and italic else 'bold' if bold else 'italic' if italic else 'normal'
    return ('<caption k="%s" font-size="%s" font-style="%s" fill="%s" %s stroke-width="%s" priority="%d"%s %s/>'
            % (k, size, style, fill, HALO, halo, prio, ' cat="%s"' % cat if cat else '', extra))


def labels():
    # places / admin
    for k, v, z, zmax, size, bold, fill, prio, cat in (
            ('qd_admin', 'city', 6, 10, 22, 1, '#000000', 200, 'placename'),
            ('qd_admin', 'district', 8, 13, 19, 1, '#000000', 190, 'placename'),
            ('qd_admin', 'town', 11, 15, 15, 1, '#333333', 170, 'placename'),
            ('place', 'island', 11, 30, 13, 0, '#333333', 120, 'placename'),
            ('place', 'suburb|quarter', 13, 16, 13, 1, '#555555', 140, 'placename'),
            ('place', 'village', 13, 30, 13, 0, '#222222', 130, 'placename'),
            ('place', 'hamlet|islet', 14, 30, 12, 0, '#333333', 110, 'placename'),
            ('place', 'neighbourhood|locality|square', 15, 30, 12, 0, '#555555', 100, 'placename')):
        w('<rule e="node" k="%s" v="%s" zoom-min="%d" zoom-max="%d">%s</rule>'
          % (k, v, z, zmax, caption('name', size, prio, fill, bold=bool(bold), halo=3.5, cat=cat)))
    # POIs with icons
    for cls, (z, size, bold, prio, sym, cat) in POI.items():
        w('<rule e="node" k="poi" v="%s" zoom-min="%d">' % (cls, z))
        w('<symbol id="s_%s" src="symbols/%s.svg" symbol-width="%d" priority="%d" cat="%s"/>' % (cls, cls, sym, prio, cat))
        cz = z + 1 if cls in ('building', 'misc', 'parking', 'toilets') else z
        w('<rule e="node" k="name" v="*" zoom-min="%d">%s</rule>' % (
            cz, caption('name', size, prio, bold=bool(bold), cat=cat,
                        extra='symbol-id="s_%s" position="right"' % cls)))
        w('</rule>')
    w('<rule e="node" k="poi" v="estate" zoom-min="15">%s</rule>'
      % caption('name', 12, 52, '#444444', italic=True, cat='placename'))
    w('<rule e="node" k="poi" v="water" zoom-min="13">%s</rule>'
      % caption('name', 13, 58, '#333333', italic=True, cat='water'))
    w('<rule e="node" k="poi" v="junction" zoom-min="13">%s</rule>'
      % caption('name', 12, 60, '#000000', italic=True, cat='roadname'))
    w('<rule e="node" k="poi" v="subway_entrance" zoom-min="17"><symbol id="s_se" src="symbols/subway_entrance.svg" '
      'symbol-width="13" priority="35" cat="transport"/>%s</rule>'
      % caption('ref', 11, 35, extra='symbol-id="s_se" position="right"', cat='transport'))
    w('<rule e="node" k="poi" v="busstop">')
    w('<rule e="node" k="*" v="*" zoom-min="16" zoom-max="16"><symbol src="symbols/busstop.svg" symbol-width="12" priority="30" cat="transport"/></rule>')
    w('<rule e="node" k="*" v="*" zoom-min="17"><symbol id="s_bus" src="symbols/busstop.svg" symbol-width="14" priority="32" cat="transport"/>%s</rule>'
      % caption('name', 11, 32, '#222222', extra='symbol-id="s_bus" position="right"', cat='transport'))
    w('</rule>')
    w('<rule e="node" k="highway" v="traffic_signals" zoom-min="17"><symbol src="symbols/traffic_signals.svg" '
      'symbol-width="10" priority="5"/></rule>')
    w('<rule e="node" k="poi" v="addr" zoom-min="17">%s</rule>'
      % caption('addr:housenumber', 10, 5, '#555555', halo=2, cat='addr'))
    w('<rule e="way" k="building" v="*" zoom-min="17">%s</rule>'
      % caption('addr:housenumber', 10, 4, '#555555', halo=2, cat='addr'))
    # road / water / rail names
    for v, z, size, prio in (('motorway|trunk', 11, 13, 50), ('primary', 12, 13, 48), ('secondary', 13, 13, 46),
                             ('tertiary', 14, 12, 44), ('unclassified|residential|living_street|road|pedestrian', 15, 12, 40),
                             ('motorway_link|trunk_link|primary_link|secondary_link|tertiary_link', 16, 11, 34),
                             ('service|track', 16, 11, 30)):
        w('<rule e="way" k="highway" v="%s" zoom-min="%d"><pathText k="name" font-size="%d" font-style="bold" fill="#000000" '
          '%s stroke-width="3.5" priority="%d" repeat="true" repeat-gap="%d" cat="roadname"/></rule>' % (v, z, size, HALO, prio, 160))
    w('<rule e="way" k="highway" v="footway|path|steps|cycleway|bridleway" zoom-min="15"><pathText k="name" font-size="11" '
      'font-style="bold" fill="#444444" %s stroke-width="3.5" priority="28" repeat="true" repeat-gap="160" cat="pathname"/></rule>' % HALO)
    w('<rule e="way" k="highway" v="motorway|trunk" zoom-min="10"><rule e="way" k="ref" v="*">'
      '<pathText k="ref" font-size="12" font-style="bold" fill="#FFFFFF" stroke="#000000" stroke-width="4" priority="52" '
      'repeat="true" repeat-gap="220" cat="roadname"/></rule></rule>')
    w('<rule e="way" k="waterway" v="river|canal|stream" zoom-min="13"><pathText k="name" font-size="12" font-style="italic" '
      'fill="#333333" %s stroke-width="3" priority="20" cat="water"/></rule>' % HALO)
    w('<rule e="way" k="railway" v="rail|subway|light_rail" zoom-min="14"><pathText k="name" font-size="11" fill="#333333" '
      '%s stroke-width="3" priority="15" cat="rail"/></rule>' % HALO)
    w('<rule e="way" k="route" v="ferry" zoom-min="13"><pathText k="name" font-size="11" font-style="italic" fill="#333333" '
      '%s stroke-width="3" priority="15" cat="transport"/></rule>' % HALO)
    # one-way arrows
    w('<rule e="way" k="oneway" v="yes" zoom-min="16"><rule e="way" k="highway" v="*">'
      '<lineSymbol src="symbols/oneway.svg" symbol-width="10" repeat="true" repeat-gap="120" display="always" priority="-50" cat="road"/>'
      '</rule></rule>')


def stylemenu():
    """Layers exposed to the app; the app returns the enabled category ids."""
    w('<stylemenu id="eink" defaultvalue="default">')
    layers = [
        ('default', None, '标准', True),
        ('roads', 'road', '道路线条', True),
        ('path', 'path', '小径与步行道', True),
        ('roadname', 'roadname', '路名', True),
        ('pathname', 'pathname', '小径名称', False),
        ('rail', 'rail', '铁路', True),
        ('placename', 'placename', '地名与住宅区', True),
        ('poi', 'poi', '公共设施兴趣点', True),
        ('shop', 'shop', '商店与购物', True),
        ('food', 'food', '餐饮', True),
        ('transport', 'transport', '交通设施', True),
        ('building', 'building', '建筑轮廓', True),
        ('addr', 'addr', '门牌号', True),
        ('water', 'water', '水域', True),
        ('boundary', 'boundary', '行政边界', True),
    ]
    for lid, cat, title, enabled in layers:
        w('<layer id="%s" visible="true" enabled="%s"><name lang="zh" value="%s"/>%s</layer>'
          % (lid, 'true' if enabled else 'false', title, '<cat id="%s"/>' % cat if cat else ''))
    w('</stylemenu>')