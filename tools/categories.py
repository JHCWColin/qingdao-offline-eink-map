# Shared OSM tag -> (render class, Chinese type label) classification.
# Render classes are the small fixed set the e-ink theme understands (tag "poi=<class>").

# (key, value) -> (class, label). value '*' matches any value of the key.
TABLE = {
    # food & drink
    ('amenity', 'restaurant'): ('food', '餐厅'), ('amenity', 'fast_food'): ('food', '快餐'),
    ('amenity', 'food_court'): ('food', '美食广场'), ('amenity', 'cafe'): ('cafe', '咖啡馆'),
    ('amenity', 'bar'): ('bar', '酒吧'), ('amenity', 'pub'): ('bar', '酒馆'),
    ('amenity', 'biergarten'): ('bar', '啤酒屋'), ('amenity', 'ice_cream'): ('cafe', '冷饮店'),
    ('shop', 'bakery'): ('cafe', '面包店'), ('shop', 'tea'): ('cafe', '茶叶店'),
    ('shop', 'beverages'): ('shop', '饮品店'), ('shop', 'pastry'): ('cafe', '糕点店'),
    # lodging
    ('tourism', 'hotel'): ('hotel', '酒店'), ('tourism', 'hostel'): ('hotel', '青年旅舍'),
    ('tourism', 'guest_house'): ('hotel', '宾馆'), ('tourism', 'motel'): ('hotel', '汽车旅馆'),
    ('tourism', 'apartment'): ('hotel', '公寓酒店'), ('tourism', 'camp_site'): ('hotel', '营地'),
    # money
    ('amenity', 'bank'): ('bank', '银行'), ('amenity', 'atm'): ('bank', 'ATM'),
    ('amenity', 'bureau_de_change'): ('bank', '外币兑换'),
    # health
    ('amenity', 'hospital'): ('hospital', '医院'), ('healthcare', 'hospital'): ('hospital', '医院'),
    ('amenity', 'clinic'): ('clinic', '诊所'), ('healthcare', 'clinic'): ('clinic', '诊所'),
    ('amenity', 'doctors'): ('clinic', '诊所'), ('amenity', 'dentist'): ('clinic', '牙科'),
    ('healthcare', 'dentist'): ('clinic', '牙科'), ('healthcare', 'centre'): ('clinic', '卫生服务中心'),
    ('amenity', 'pharmacy'): ('pharmacy', '药店'), ('healthcare', 'pharmacy'): ('pharmacy', '药店'),
    ('shop', 'chemist'): ('pharmacy', '药妆店'), ('amenity', 'veterinary'): ('clinic', '宠物医院'),
    # education
    ('amenity', 'school'): ('school', '学校'), ('amenity', 'kindergarten'): ('school', '幼儿园'),
    ('amenity', 'university'): ('university', '大学'), ('amenity', 'college'): ('university', '学院'),
    ('amenity', 'library'): ('culture', '图书馆'), ('amenity', 'language_school'): ('school', '语言学校'),
    ('amenity', 'driving_school'): ('school', '驾校'), ('amenity', 'training'): ('school', '培训机构'),
    ('amenity', 'research_institute'): ('office', '研究所'), ('office', 'research'): ('office', '研究机构'),
    # shopping
    ('shop', 'supermarket'): ('market', '超市'), ('shop', 'convenience'): ('shop', '便利店'),
    ('shop', 'mall'): ('mall', '购物中心'), ('shop', 'department_store'): ('mall', '百货商场'),
    ('amenity', 'marketplace'): ('market', '市场'), ('shop', 'wholesale'): ('market', '批发市场'),
    ('shop', 'greengrocer'): ('shop', '果蔬店'), ('shop', 'butcher'): ('shop', '肉店'),
    ('shop', 'seafood'): ('shop', '海鲜店'), ('shop', 'clothes'): ('shop', '服装店'),
    ('shop', 'shoes'): ('shop', '鞋店'), ('shop', 'books'): ('shop', '书店'),
    ('shop', 'mobile_phone'): ('shop', '手机店'), ('shop', 'electronics'): ('shop', '电器店'),
    ('shop', 'computer'): ('shop', '电脑店'), ('shop', 'furniture'): ('shop', '家具店'),
    ('shop', 'hardware'): ('shop', '五金店'), ('shop', 'doityourself'): ('shop', '建材店'),
    ('shop', 'car'): ('car', '汽车销售'), ('shop', 'car_repair'): ('car', '汽车维修'),
    ('shop', 'car_parts'): ('car', '汽车配件'), ('shop', 'tyres'): ('car', '轮胎店'),
    ('shop', 'motorcycle'): ('car', '摩托车店'), ('shop', 'bicycle'): ('shop', '自行车店'),
    ('shop', 'hairdresser'): ('shop', '美发店'), ('shop', 'beauty'): ('shop', '美容店'),
    ('shop', 'jewelry'): ('shop', '珠宝店'), ('shop', 'optician'): ('shop', '眼镜店'),
    ('shop', 'florist'): ('shop', '花店'), ('shop', 'gift'): ('shop', '礼品店'),
    ('shop', 'toys'): ('shop', '玩具店'), ('shop', 'sports'): ('shop', '体育用品店'),
    ('shop', 'alcohol'): ('shop', '烟酒店'), ('shop', 'tobacco'): ('shop', '烟草店'),
    ('shop', 'laundry'): ('shop', '洗衣店'), ('shop', 'dry_cleaning'): ('shop', '干洗店'),
    ('shop', 'stationery'): ('shop', '文具店'), ('shop', 'cosmetics'): ('shop', '化妆品店'),
    ('shop', 'pet'): ('shop', '宠物店'), ('shop', 'kiosk'): ('shop', '报亭'),
    ('shop', 'telecommunication'): ('shop', '通信营业厅'), ('shop', 'travel_agency'): ('shop', '旅行社'),
    ('shop', 'photo'): ('shop', '照相馆'), ('shop', 'copyshop'): ('shop', '图文打印'),
    ('shop', 'massage'): ('shop', '按摩'), ('shop', 'variety_store'): ('shop', '杂货店'),
    ('shop', 'general'): ('shop', '百货店'), ('shop', 'art'): ('shop', '艺术品店'),
    ('shop', 'music'): ('shop', '乐器店'), ('shop', 'bag'): ('shop', '箱包店'),
    ('shop', 'baby_goods'): ('shop', '母婴店'), ('shop', 'outdoor'): ('shop', '户外用品店'),
    ('shop', 'appliance'): ('shop', '家电店'), ('shop', 'houseware'): ('shop', '家居用品店'),
    ('shop', 'farm'): ('shop', '农产品店'), ('shop', 'confectionery'): ('shop', '糖果店'),
    ('shop', 'lottery'): ('shop', '彩票店'), ('shop', 'medical_supply'): ('shop', '医疗器械店'),
    ('shop', '*'): ('shop', '商店'),
    # car / transport facilities
    ('amenity', 'fuel'): ('fuel', '加油站'), ('amenity', 'charging_station'): ('fuel', '充电站'),
    ('amenity', 'parking'): ('parking', '停车场'), ('amenity', 'car_wash'): ('car', '洗车'),
    ('amenity', 'car_rental'): ('car', '租车'), ('amenity', 'bicycle_rental'): ('parking', '自行车租赁'),
    ('amenity', 'bus_station'): ('busstation', '汽车站'), ('amenity', 'ferry_terminal'): ('ferry', '轮渡码头'),
    ('amenity', 'taxi'): ('parking', '出租车站'),
    # public services
    ('amenity', 'police'): ('gov', '派出所/公安'), ('amenity', 'fire_station'): ('gov', '消防站'),
    ('amenity', 'post_office'): ('post', '邮局'), ('amenity', 'townhall'): ('gov', '政府机关'),
    ('office', 'government'): ('gov', '政府机构'), ('amenity', 'courthouse'): ('gov', '法院'),
    ('amenity', 'prison'): ('gov', '监狱'), ('amenity', 'embassy'): ('gov', '领事馆'),
    ('office', 'diplomatic'): ('gov', '领事馆'), ('amenity', 'community_centre'): ('gov', '社区中心'),
    ('amenity', 'social_facility'): ('gov', '社会福利机构'), ('amenity', 'toilets'): ('toilets', '公共厕所'),
    ('amenity', 'recycling'): ('misc', '回收站'), ('amenity', 'post_box'): ('misc', '邮筒'),
    ('amenity', 'grave_yard'): ('misc', '墓地'), ('landuse', 'cemetery'): ('misc', '公墓'),
    ('amenity', 'place_of_worship'): ('worship', '宗教场所'), ('amenity', 'monastery'): ('worship', '寺院'),
    ('amenity', 'shelter'): ('misc', '避难所'), ('emergency', 'assembly_point'): ('misc', '应急避难场所'),
    # culture & entertainment
    ('amenity', 'cinema'): ('culture', '电影院'), ('amenity', 'theatre'): ('culture', '剧院'),
    ('amenity', 'arts_centre'): ('culture', '艺术中心'), ('amenity', 'nightclub'): ('bar', '夜总会'),
    ('amenity', 'karaoke_box'): ('bar', 'KTV'), ('amenity', 'internet_cafe'): ('bar', '网吧'),
    ('amenity', 'events_venue'): ('culture', '活动场馆'), ('amenity', 'conference_centre'): ('culture', '会议中心'),
    ('amenity', 'exhibition_centre'): ('culture', '会展中心'), ('amenity', 'planetarium'): ('culture', '天文馆'),
    # tourism
    ('tourism', 'attraction'): ('sight', '景点'), ('tourism', 'museum'): ('museum', '博物馆'),
    ('tourism', 'gallery'): ('museum', '美术馆'), ('tourism', 'viewpoint'): ('sight', '观景点'),
    ('tourism', 'zoo'): ('sight', '动物园'), ('tourism', 'aquarium'): ('sight', '海洋馆'),
    ('tourism', 'theme_park'): ('sight', '主题公园'), ('tourism', 'artwork'): ('sight', '雕塑/艺术品'),
    ('tourism', 'information'): ('misc', '游客信息'), ('tourism', 'picnic_site'): ('sight', '野餐地'),
    ('historic', 'monument'): ('sight', '纪念碑'), ('historic', 'memorial'): ('sight', '纪念地'),
    ('historic', 'castle'): ('sight', '城堡'), ('historic', 'building'): ('sight', '历史建筑'),
    ('historic', 'archaeological_site'): ('sight', '考古遗址'), ('historic', 'ruins'): ('sight', '遗址'),
    ('historic', 'fort'): ('sight', '炮台/要塞'), ('historic', 'temple'): ('worship', '古寺庙'),
    ('historic', '*'): ('sight', '历史遗迹'),
    ('man_made', 'lighthouse'): ('sight', '灯塔'), ('man_made', 'tower'): ('sight', '塔'),
    ('man_made', 'pier'): ('sight', '栈桥/码头'),
    # leisure & sport
    ('leisure', 'park'): ('park', '公园'), ('leisure', 'garden'): ('park', '花园'),
    ('leisure', 'nature_reserve'): ('park', '自然保护区'), ('leisure', 'playground'): ('park', '游乐场'),
    ('leisure', 'stadium'): ('sport', '体育场'), ('leisure', 'sports_centre'): ('sport', '体育中心'),
    ('leisure', 'pitch'): ('sport', '运动场'), ('leisure', 'swimming_pool'): ('sport', '游泳池'),
    ('leisure', 'fitness_centre'): ('sport', '健身房'), ('leisure', 'golf_course'): ('sport', '高尔夫球场'),
    ('leisure', 'marina'): ('ferry', '游艇码头'), ('leisure', 'water_park'): ('sight', '水上乐园'),
    ('leisure', 'beach_resort'): ('sight', '海水浴场'), ('leisure', 'resort'): ('hotel', '度假村'),
    ('leisure', 'track'): ('sport', '跑道'), ('leisure', 'square'): ('park', '广场'),
    ('place', 'square'): ('park', '广场'), ('natural', 'beach'): ('sight', '海滩'),
    ('leisure', 'amusement_arcade'): ('bar', '游戏厅'), ('leisure', 'fishing'): ('sight', '垂钓'),
    # transport
    ('railway', 'station'): ('train', '火车站'), ('railway', 'halt'): ('train', '火车停靠站'),
    ('railway', 'stop'): ('train', '车站'), ('railway', 'subway_entrance'): ('subway_entrance', '地铁出入口'),
    ('railway', 'tram_stop'): ('busstop', '有轨电车站'), ('highway', 'bus_stop'): ('busstop', '公交站'),
    ('aeroway', 'aerodrome'): ('airport', '机场'), ('aeroway', 'terminal'): ('misc', '航站楼'),
    ('aeroway', 'helipad'): ('misc', '直升机坪'),
    ('highway', 'services'): ('fuel', '服务区'), ('highway', 'rest_area'): ('fuel', '停车区'),
    ('highway', 'toll_gantry'): ('misc', '收费站'), ('barrier', 'toll_booth'): ('misc', '收费站'),
    ('highway', 'motorway_junction'): ('junction', '高速出口'),
    # offices / industry
    ('office', 'company'): ('office', '公司'), ('office', '*'): ('office', '办公机构'),
    ('man_made', 'works'): ('office', '工厂'), ('landuse', 'industrial'): ('office', '工业区'),
    ('craft', '*'): ('office', '作坊'), ('amenity', 'studio'): ('office', '工作室'),
    # nature
    ('natural', 'peak'): ('peak', '山峰'), ('natural', 'volcano'): ('peak', '火山'),
    ('natural', 'cave_entrance'): ('sight', '洞穴'), ('natural', 'spring'): ('sight', '泉'),
    ('natural', 'cape'): ('sight', '岬角'), ('natural', 'saddle'): ('peak', '山口'),
    ('natural', 'ridge'): ('peak', '山脊'), ('natural', 'cliff'): ('sight', '悬崖'),
    ('natural', 'rock'): ('sight', '礁石'), ('natural', 'bay'): ('water', '海湾'),
    ('natural', 'strait'): ('water', '海峡'), ('natural', 'water'): ('water', '水域'),
    ('natural', 'wetland'): ('water', '湿地'), ('natural', 'wood'): ('park', '树林'),
    ('landuse', 'reservoir'): ('water', '水库'), ('water', 'reservoir'): ('water', '水库'),
    ('water', 'lake'): ('water', '湖泊'),
    # residential
    ('landuse', 'residential'): ('estate', '住宅区'), ('place', 'neighbourhood'): ('estate', '社区'),
    ('building', 'apartments'): ('estate', '住宅楼'), ('building', 'residential'): ('estate', '住宅楼'),
    ('landuse', 'commercial'): ('office', '商务区'), ('landuse', 'retail'): ('mall', '商业区'),
    ('landuse', 'military'): ('misc', '军事区'),
}

# Order in which keys are checked; the first hit wins.
KEY_ORDER = ('amenity', 'healthcare', 'railway', 'aeroway', 'tourism', 'historic', 'shop', 'leisure',
             'office', 'craft', 'emergency', 'barrier', 'highway', 'man_made', 'natural', 'water',
             'place', 'landuse', 'building')

PLACE = {'city': ('城市', 95), 'town': ('镇', 80), 'suburb': ('街道/片区', 75), 'village': ('村', 55),
         'quarter': ('片区', 60), 'neighbourhood': ('社区', 50), 'hamlet': ('自然村', 45),
         'locality': ('地名', 40), 'island': ('岛屿', 70), 'islet': ('小岛', 50), 'square': ('广场', 60)}

# Base importance per render class (0..100), used for search ranking and map label priority.
RANK = {'airport': 90, 'train': 85, 'university': 70, 'hospital': 72, 'sight': 68, 'museum': 68,
        'mall': 66, 'park': 62, 'busstation': 70, 'ferry': 65, 'sport': 55, 'gov': 55, 'hotel': 55,
        'market': 55, 'culture': 55, 'school': 50, 'estate': 52, 'peak': 50, 'water': 55, 'bank': 42,
        'food': 40, 'cafe': 38, 'bar': 35, 'shop': 35, 'pharmacy': 40, 'clinic': 42, 'fuel': 45,
        'parking': 30, 'post': 40, 'office': 38, 'car': 32, 'worship': 50, 'toilets': 25,
        'busstop': 45, 'subway_entrance': 40, 'subway': 86, 'building': 35, 'addr': 20, 'junction': 40, 'misc': 25}

HIGHWAY = {'motorway': ('高速公路', 90), 'trunk': ('快速路/国道', 85), 'primary': ('主干道', 80),
           'secondary': ('次干道', 72), 'tertiary': ('支路', 65), 'unclassified': ('乡村道路', 50),
           'residential': ('街巷', 55), 'living_street': ('生活街道', 50), 'pedestrian': ('步行街', 60),
           'service': ('辅路/内部道路', 30), 'track': ('机耕路', 25), 'footway': ('人行道', 25),
           'path': ('小径', 25), 'steps': ('台阶', 20), 'cycleway': ('自行车道', 30),
           'motorway_link': ('高速匝道', 40), 'trunk_link': ('快速路匝道', 40),
           'primary_link': ('连接线', 35), 'secondary_link': ('连接线', 35), 'tertiary_link': ('连接线', 30),
           'construction': ('在建道路', 30)}

RELIGION = {'buddhist': '佛教', 'christian': '基督教', 'muslim': '伊斯兰教', 'taoist': '道教',
            'confucian': '儒教', 'jewish': '犹太教'}


def classify(tags):
    """Return (render_class, label) for an OSM tag dict, or None."""
    for k in KEY_ORDER:
        v = tags.get(k)
        if not v or v == 'no':
            continue
        hit = TABLE.get((k, v)) or TABLE.get((k, '*'))
        if hit:
            cls, label = hit
            if k == 'amenity' and v == 'place_of_worship':
                rel = RELIGION.get(tags.get('religion', ''))
                if rel:
                    label = rel + '场所'
            cuisine = tags.get('cuisine')
            if cls == 'food' and cuisine:
                label = label + '·' + CUISINE.get(cuisine.split(';')[0], cuisine.split(';')[0])
            return cls, label
    return None


CUISINE = {'chinese': '中餐', 'seafood': '海鲜', 'regional': '地方菜', 'noodle': '面馆', 'burger': '汉堡',
           'chicken': '炸鸡', 'pizza': '披萨', 'japanese': '日料', 'korean': '韩餐', 'barbecue': '烧烤',
           'hot_pot': '火锅', 'coffee_shop': '咖啡', 'dumpling': '饺子', 'sandwich': '三明治',
           'western': '西餐', 'italian': '意餐', 'french': '法餐', 'thai': '泰餐', 'indian': '印度菜',
           'sichuan': '川菜', 'cantonese': '粤菜', 'shandong': '鲁菜', 'bubble_tea': '奶茶', 'tea': '茶饮',
           'vegetarian': '素食', 'buffet': '自助餐', 'kebab': '烤串', 'beef_bowl': '牛肉饭',
           'fried_chicken': '炸鸡', 'ice_cream': '冰淇淋', 'asian': '亚洲菜', 'american': '美式'}

# Overture basic_category -> render class/label (substring match, first hit wins)
OVERTURE = [
    ('airport', 'airport', '机场'), ('train_station', 'train', '火车站'), ('bus_station', 'busstation', '汽车站'),
    ('ferry', 'ferry', '码头'), ('hospital', 'hospital', '医院'), ('clinic', 'clinic', '诊所'),
    ('dentist', 'clinic', '牙科'), ('pharmacy', 'pharmacy', '药店'), ('college_university', 'university', '大学'),
    ('school', 'school', '学校'), ('place_of_learning', 'school', '教育机构'), ('kindergarten', 'school', '幼儿园'),
    ('museum', 'museum', '博物馆'), ('historic', 'sight', '历史遗迹'), ('landmark', 'sight', '地标'),
    ('beach', 'sight', '海滩'), ('mountain', 'peak', '山'), ('park', 'park', '公园'), ('zoo', 'sight', '动物园'),
    ('aquarium', 'sight', '海洋馆'), ('attraction', 'sight', '景点'), ('resort', 'hotel', '度假村'),
    ('hotel', 'hotel', '酒店'), ('lodging', 'hotel', '住宿'), ('hostel', 'hotel', '青年旅舍'),
    ('shopping_mall', 'mall', '购物中心'), ('department_store', 'mall', '百货商场'),
    ('supermarket', 'market', '超市'), ('grocery', 'market', '食品店'), ('convenience', 'shop', '便利店'),
    ('coffee', 'cafe', '咖啡馆'), ('tea', 'cafe', '茶馆'), ('bakery', 'cafe', '面包店'),
    ('dessert', 'cafe', '甜品店'), ('bar', 'bar', '酒吧'), ('pub', 'bar', '酒馆'), ('night', 'bar', '夜店'),
    ('fast_food', 'food', '快餐'), ('restaurant', 'food', '餐厅'), ('eatery', 'food', '餐馆'),
    ('food', 'food', '餐饮'), ('bank', 'bank', '银行'), ('atm', 'bank', 'ATM'),
    ('gas_station', 'fuel', '加油站'), ('charging', 'fuel', '充电站'), ('parking', 'parking', '停车场'),
    ('auto', 'car', '汽车服务'), ('car_', 'car', '汽车服务'), ('police', 'gov', '公安'),
    ('fire', 'gov', '消防'), ('post_office', 'post', '邮局'), ('government', 'gov', '政府机构'),
    ('embassy', 'gov', '领事馆'), ('church', 'worship', '教堂'), ('temple', 'worship', '寺庙'),
    ('religious', 'worship', '宗教场所'), ('cinema', 'culture', '电影院'), ('theater', 'culture', '剧院'),
    ('theatre', 'culture', '剧院'), ('library', 'culture', '图书馆'), ('art', 'culture', '艺术'),
    ('stadium', 'sport', '体育场'), ('gym', 'sport', '健身房'), ('fitness', 'sport', '健身'),
    ('sport', 'sport', '运动场所'), ('golf', 'sport', '高尔夫'), ('store', 'shop', '商店'),
    ('shop', 'shop', '商店'), ('beauty', 'shop', '美容美发'), ('salon', 'shop', '美容美发'),
    ('apartment', 'estate', '公寓'), ('residential', 'estate', '住宅区'), ('real_estate', 'office', '房产中介'),
    ('manufactur', 'office', '工厂'), ('industrial', 'office', '工业企业'), ('office', 'office', '公司'),
    ('service', 'office', '服务机构'), ('supplier', 'office', '供应商'), ('company', 'office', '公司'),
]


def classify_overture(basic, primary):
    s = (basic or '') + '|' + (primary or '')
    for key, cls, label in OVERTURE:
        if key in s:
            return cls, label
    return None
