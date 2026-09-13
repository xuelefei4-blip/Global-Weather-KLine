import os
import sys
import json

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. 查找数据落地根目录
candidates = [
    os.path.join(CURRENT_DIR, 'static', 'data'),
    os.path.abspath(os.path.join(CURRENT_DIR, '..', 'MeteoSystem', 'static', 'data'))
]

DATA_ROOT = next((p for p in candidates if os.path.exists(p)), None)
if not DATA_ROOT:
    print("❌ 未找到 static/data 文件夹！")
    sys.exit(1)

ROOT_INDEX = os.path.join(DATA_ROOT, 'index.json')
BASE_DIR = os.path.abspath(os.path.join(DATA_ROOT, '..', '..'))
SEED_DIR = os.path.join(CURRENT_DIR, "data_seed")

if not os.path.exists(SEED_DIR):
    print("❌ 未找到 data_seed 辅助 JSON 文件夹！")
    sys.exit(1)

# 2. 严密扫描实际索引树，提取真实已建仓的城市 ID 与文件夹
scaffolded_cids = set()
scaffolded_folders = set()

if os.path.exists(ROOT_INDEX):
    try:
        with open(ROOT_INDEX, 'r', encoding='utf-8') as f:
            continents = json.load(f)
        for cont in continents:
            cont_path = os.path.join(BASE_DIR, cont.get('path', '').replace('\\', '/'))
            if not os.path.exists(cont_path): 
                continue
            with open(cont_path, 'r', encoding='utf-8') as f:
                cont_data = json.load(f)
                countries = cont_data.get('children', []) if isinstance(cont_data, dict) else cont_data
            for country in countries:
                country_path = os.path.join(BASE_DIR, country.get('path', '').replace('\\', '/'))
                if not os.path.exists(country_path): 
                    continue
                with open(country_path, 'r', encoding='utf-8') as f:
                    cities = json.load(f)
                    for c in cities:
                        cid = str(c.get('id', '')).lower().strip()
                        if cid:
                            scaffolded_cids.add(cid)
                        folder_name = c.get('path', '').strip('/').split('/')[-1].lower()
                        if folder_name:
                            scaffolded_folders.add(folder_name)
    except Exception as e:
        print(f"⚠️ 扫描系统索引树发生警告: {e}")

# 3. 动态扫出硬盘上实际存在的 JSON 文件
disk_files = set()
for root, dirs, files in os.walk(DATA_ROOT):
    for f in files:
        if f.endswith(".json"):
            # 排除索引文件，仅统计数据分片切片
            if not f.endswith('_index.json') and not f.endswith('_cities.json') and f != 'index.json':
                disk_files.add(f.lower().strip())

result = {"updated": [], "current": [], "pending": []}

continent_files = [
    "asia.json", "europe.json", "north_america.json",
    "south_america.json", "africa.json", "oceania.json", "antarctica.json"
]

total_catalog_cities = 0

# 4. 遍历 161 种子全集，精准区分 绿(完备)、红(残缺/新建)、灰(未建/已删)
for c_file in continent_files:
    seed_path = os.path.join(SEED_DIR, c_file)
    if not os.path.exists(seed_path):
        continue

    with open(seed_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    for country, cities in catalog.items():
        for name, cid in cities.items():
            total_catalog_cities += 1
            cid_clean = str(cid).lower().strip()
            folder_clean = name.replace(" ", "_").lower().strip()

            # 判定当前城市在索引树中是否存在
            is_scaffolded = (cid_clean in scaffolded_cids) or (folder_clean in scaffolded_folders)

            # 检查硬盘上的物理文件分片
            has_2026 = f"{cid_clean}_2026.json" in disk_files
            has_2025 = f"{cid_clean}_2025.json" in disk_files
            
            # 统计 2015-2024 年历史数据分片
            history_years_present = [yr for yr in range(2015, 2025) if f"{cid_clean}_{yr}.json" in disk_files]
            has_full_history = (len(history_years_present) == 10)
            has_any_history = (len(history_years_present) > 0)

            # 是否在硬盘上有任何属于该城市的文件切片
            has_any_disk_file = has_2026 or has_2025 or has_any_history

            # ================= 状态判定逻辑 =================
            # 1. 绿标 (Updated)：数据全部完备闭环（必须建仓 且 有2026 且 有2025 且 历史齐全）
            if is_scaffolded and has_2026 and has_2025 and has_full_history:
                result["updated"].append({
                    "name": name, 
                    "id": cid_clean, 
                    "year": "2026"
                })

            # 2. 红标 (Current/新增/待补)：
            # 只要在索引树中存在建仓，或者硬盘残留了部分分片，但数据尚未达到绿标闭环
            elif is_scaffolded or has_any_disk_file:
                # 细分标注原因
                if has_2026 and not has_2025:
                    year_tag = "缺2025"
                elif has_2026 and not has_full_history:
                    year_tag = "缺历史"
                elif has_2025 and not has_2026:
                    year_tag = "缺2026"
                elif is_scaffolded and not has_any_disk_file:
                    year_tag = "新建仓"
                else:
                    year_tag = "待补全"

                result["current"].append({
                    "name": name, 
                    "id": cid_clean, 
                    "year": year_tag
                })

            # 3. 灰标 (Pending/未添/已删)：
            # 既没有索引建仓，也没有任何硬盘物理文件，完全视作待添加的储备状态
            else:
                result["pending"].append({
                    "name": name, 
                    "id": cid_clean, 
                    "year": ""
                })

# 5. 回写状态文件并输出控制台汇总
status_file = os.path.join(CURRENT_DIR, "cities_status.json")
with open(status_file, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"📊 辅助清单总名额: {total_catalog_cities} 城")
print(f"🟢 完备站点 (全套闭环): {len(result['updated'])} 城")
print(f"🔴 本次新增/待补数据 (标红): {len(result['current'])} 城")
print(f"⚪ 待建仓储备/已移除 (标灰): {len(result['pending'])} 城")