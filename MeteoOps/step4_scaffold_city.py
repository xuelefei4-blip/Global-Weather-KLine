import os
import sys
import json
import random
import urllib.request
import urllib.parse
import subprocess

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

candidates = [
    os.path.join(CURRENT_DIR, 'static', 'data'),
    os.path.abspath(os.path.join(CURRENT_DIR, '..', 'MeteoSystem', 'static', 'data'))
]
DATA_ROOT = next((p for p in candidates if os.path.exists(p)), None)
if not DATA_ROOT:
    print("🚨 错误：找不到 static/data 文件夹！")
    sys.exit(1)

ROOT_INDEX = os.path.join(DATA_ROOT, 'index.json')
BASE_DIR = os.path.abspath(os.path.join(DATA_ROOT, '..', '..'))
SEED_DIR = os.path.join(CURRENT_DIR, "data_seed")

def get_city_geo(name, country):
    query = f"{name} {country}".strip()
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(query)}&count=1&language=en&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MeteoOps/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if "results" in data and data["results"]:
                item = data["results"][0]
                return round(item["latitude"], 2), round(item["longitude"], 2), item.get("timezone", "auto")
    except Exception as e:
        print(f"      ⚠️ 解析地理位置异常 ({name}): {e}")
    return 0.0, 0.0, "auto"

# 1. 扫描当前已有所有城市 ID
existing_cids = set()
if os.path.exists(ROOT_INDEX):
    try:
        with open(ROOT_INDEX, 'r', encoding='utf-8') as f:
            continents = json.load(f)
        for cont in continents:
            cont_path = os.path.join(BASE_DIR, cont.get('path', '').replace('\\', '/').strip('/'))
            if not os.path.exists(cont_path): continue
            with open(cont_path, 'r', encoding='utf-8') as f:
                cont_data = json.load(f)
                countries = cont_data.get('children', []) if isinstance(cont_data, dict) else cont_data
            for country in countries:
                country_path = os.path.join(BASE_DIR, country.get('path', '').replace('\\', '/').strip('/'))
                if not os.path.exists(country_path): continue
                with open(country_path, 'r', encoding='utf-8') as f:
                    cities = json.load(f)
                    for c in cities:
                        cid = str(c.get('id', '')).lower().strip()
                        if cid:
                            existing_cids.add(cid)
    except Exception as e:
        print(f"⚠️ 扫描已有城市时产生警告: {e}")

# 2. 载入全部 7 大洲候选池
SEED_FILES = {
    "Asia": "asia.json",
    "Europe": "europe.json",
    "North_America": "north_america.json",
    "South_America": "south_america.json",
    "Africa": "africa.json",
    "Oceania": "oceania.json",
    "Antarctica": "antarctica.json"
}

pending_candidates = []
for cont_folder, s_file in SEED_FILES.items():
    s_path = os.path.join(SEED_DIR, s_file)
    if not os.path.exists(s_path): continue
    with open(s_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for country_name, cities in data.items():
        for cname, cid in cities.items():
            cid_clean = str(cid).lower().strip()
            if cid_clean not in existing_cids:
                pending_candidates.append({
                    "continent": cont_folder,
                    "country": country_name,
                    "name": cname,
                    "id": cid_clean
                })

manual_args = [arg.lower().strip() for arg in sys.argv[1:] if arg.strip()]
selected_cities = []

if manual_args:
    print(f"🎯 手动指定建仓模式：锁定 {len(manual_args)} 个城市")
    for item in pending_candidates:
        if item['id'] in manual_args or item['name'].lower() in manual_args:
            selected_cities.append(item)
else:
    num = min(5, len(pending_candidates))
    print(f"🎲 自动随机建仓模式：从储备池抽取 {num} 个城市")
    selected_cities = random.sample(pending_candidates, num) if pending_candidates else []

if not selected_cities:
    print("☕ 没有找到待建仓的城市，或目标已全部存在。")
    sys.exit(0)

# 3. 闭环建仓
print("\n🚀 开始执行选城建仓：")
for idx, c in enumerate(selected_cities, 1):
    cont = c['continent']
    country = c['country'].replace(" ", "_")
    city_name = c['name'].replace(" ", "_")
    cid = c['id']

    print(f"   [{idx}/{len(selected_cities)}] 🌐 正在解析地理位置 ({c['name']} - {c['country']})...")
    lat, lon, tz = get_city_geo(c['name'], c['country'])

    # 统一路径格式
    rel_country_dir = f"static/data/{cont}/{country}"
    country_dir = os.path.join(BASE_DIR, rel_country_dir)
    os.makedirs(country_dir, exist_ok=True)

    cities_file = None
    for fname in os.listdir(country_dir):
        if fname.endswith("_cities.json") or fname == "cities.json":
            cities_file = os.path.join(country_dir, fname)
            break
    
    if not cities_file:
        prefix = country[:3].lower()
        cities_file = os.path.join(country_dir, f"{prefix}_cities.json")

    cities_data = []
    if os.path.exists(cities_file):
        try:
            with open(cities_file, 'r', encoding='utf-8') as f:
                cities_data = json.load(f)
        except Exception:
            cities_data = []

    rel_city_dir = f"static/data/{cont}/{country}/{city_name}/"
    new_node = {
        "id": cid,
        "name": c['name'],
        "path": rel_city_dir,
        "years": list(range(2015, 2027)),
        "lat": lat,
        "lon": lon,
        "tz": tz
    }

    if not any(str(item.get('id', '')).lower() == cid for item in cities_data):
        cities_data.append(new_node)
        with open(cities_file, 'w', encoding='utf-8') as f:
            json.dump(cities_data, f, indent=2, ensure_ascii=False)

    abs_city_dir = os.path.join(BASE_DIR, rel_city_dir.strip('/'))
    os.makedirs(abs_city_dir, exist_ok=True)

    print(f"      ✅ 已建仓: {c['name']} ({cid}) ➔ 经纬度: {lat}, {lon} | 时区: {tz}")

print(f"\n✨ 本次选城建仓完成！共新增建仓 {len(selected_cities)} 座城市。")

step1_path = os.path.join(CURRENT_DIR, "step1_detect_align.py")
if os.path.exists(step1_path):
    subprocess.run([sys.executable, step1_path], cwd=CURRENT_DIR)