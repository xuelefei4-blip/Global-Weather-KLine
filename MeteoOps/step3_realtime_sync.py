import os
import sys
import json
import time
import shutil
import urllib.request
import subprocess
from datetime import datetime, timedelta

# 锁死 UTF-8 编码，防止 Windows 终端崩溃
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ==================== 路径自适应区 ====================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

candidates = [
    os.path.join(CURRENT_DIR, 'static', 'data'),
    os.path.abspath(os.path.join(CURRENT_DIR, '..', 'MeteoSystem', 'static', 'data'))
]

DATA_ROOT = None
for p in candidates:
    if os.path.exists(os.path.join(p, 'index.json')):
        DATA_ROOT = p
        break

if not DATA_ROOT:
    print("🚨 错误：找不到 static/data/index.json 文件！")
    sys.exit(1)

ROOT_INDEX_PATH = os.path.join(DATA_ROOT, 'index.json')
BASE_DIR = os.path.abspath(os.path.join(DATA_ROOT, '..', '..'))
# ===================================================

def request_hourly(url):
    """请求 API 并提取 hourly 字典"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MeteoOps/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data.get('hourly', {})
    except Exception as e:
        print(f"      ⚠️ 网络请求异常: {e}")
        return {}

def append_records(existing_values, local_ts_set, hourly_data, current_hour_ts):
    """提取 hourly 并追加到 values 中"""
    times = hourly_data.get('time', [])
    temps = hourly_data.get('temperature_2m', [])
    humids = hourly_data.get('relative_humidity_2m', [])
    added = 0

    for i in range(len(times)):
        dt = datetime.fromisoformat(times[i])
        dt_ts = int(dt.timestamp())
        temp = temps[i]

        if dt_ts not in local_ts_set and dt_ts <= current_hour_ts and temp is not None:
            existing_values.append({
                "time": dt_ts,
                "date": dt.strftime("%y/%m/%d/%H"),
                "DATE": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "open": temp,
                "high": round(temp + 0.3, 1),
                "low": round(temp - 0.3, 1),
                "close": temp,
                "vol": int(humids[i]) if humids[i] is not None else 0
            })
            local_ts_set.add(dt_ts)
            added += 1
    return added

def sync_city_full(city, idx, total_count):
    city_id = city.get('id')
    city_name = city.get('name')
    lat, lon, tz = city.get('lat'), city.get('lon'), city.get('tz')

    rel_path = city.get('path', '').replace('\\', '/').strip('/')
    folder = os.path.join(BASE_DIR, rel_path)
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{city_id}_2026.json")

    # 1. 读出本地已有的数据
    existing_data = {"city": city_id, "year": "2026", "values": []}
    local_ts_set = set()
    last_dt = None

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                existing_data = content
                values = content.get('values', [])
                local_ts_set = {item['time'] for item in values if isinstance(item, dict) and 'time' in item}
                if values and 'time' in values[-1]:
                    last_dt = datetime.fromtimestamp(values[-1]['time'])
        except Exception:
            pass

    now = datetime.now()
    today = now.date()
    current_hour_ts = int(now.replace(minute=0, second=0, microsecond=0).timestamp())

    start_date = last_dt.date() if last_dt else datetime(2026, 1, 1).date()
    cutoff_14d = today - timedelta(days=14)

    # 若已到当前小时，跳过
    if start_date >= today and max(local_ts_set, default=0) >= current_hour_ts:
        latest_str = datetime.fromtimestamp(max(local_ts_set)).strftime('%Y-%m-%d %H:00')
        print(f"[{idx}/{total_count}] ☕ {city_name} ({city_id.upper()}): 已是最新 (截止至 {latest_str})")
        return

    print(f"[{idx}/{total_count}] 🚀 处理 {city_name} ({city_id.upper()}): 断点 {start_date} ➔ 接轨今天...")
    city_added = 0

    # 段 1：归档补齐（从断点至 14 天前）
    if start_date < cutoff_14d:
        s1 = start_date.strftime('%Y-%m-%d')
        e1 = cutoff_14d.strftime('%Y-%m-%d')
        url_arch = (f"https://archive-api.open-meteo.com/v1/archive?"
                    f"latitude={lat}&longitude={lon}&"
                    f"hourly=temperature_2m,relative_humidity_2m&"
                    f"start_date={s1}&end_date={e1}&timezone={tz}")
        
        h_arch = request_hourly(url_arch)
        add_arch = append_records(existing_data['values'], local_ts_set, h_arch, current_hour_ts)
        city_added += add_arch
        print(f"   ↳ [阶段1/历史归档] 补全 {s1} ~ {e1}: +{add_arch} 条")
        time.sleep(0.3)
        start_date = cutoff_14d

    # 段 2：实时补齐（14 天前至今）
    s2 = start_date.strftime('%Y-%m-%d')
    e2 = today.strftime('%Y-%m-%d')
    url_fore = (f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&"
                f"hourly=temperature_2m,relative_humidity_2m&"
                f"start_date={s2}&end_date={e2}&timezone={tz}")

    h_fore = request_hourly(url_fore)
    add_fore = append_records(existing_data['values'], local_ts_set, h_fore, current_hour_ts)
    city_added += add_fore
    print(f"   ↳ [阶段2/近期实况] 补全 {s2} ~ {e2}: +{add_fore} 条")

    # 3. 排序落盘，闭环当前城市
    if city_added > 0:
        existing_data['values'].sort(key=lambda x: x['time'])
        temp_file = f"{file_path}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        shutil.move(temp_file, file_path)

        final_str = datetime.fromtimestamp(existing_data['values'][-1]['time']).strftime('%Y-%m-%d %H:00')
        print(f"   ✅ {city_name} 闭环成功！共增补 {city_added} 条 ➔ 最新点: {final_str}\n")
    else:
        print(f"   ☕ {city_name} 核验完毕，无新增。\n")

def run():
    print(">> [3/6] 开始单站逐个闭环补全 2026 数据...")

    if not os.path.exists(ROOT_INDEX_PATH):
        print("❌ 未找到 index.json 索引文件！")
        return

    all_cities = []
    with open(ROOT_INDEX_PATH, 'r', encoding='utf-8') as f:
        continents = json.load(f)

    for cont in continents:
        cont_path = os.path.join(BASE_DIR, cont['path'].replace('\\', '/'))
        if not os.path.exists(cont_path): continue
        with open(cont_path, 'r', encoding='utf-8') as f:
            cont_data = json.load(f)
            countries = cont_data.get('children', []) if isinstance(cont_data, dict) else cont_data
        for country in countries:
            country_path = os.path.join(BASE_DIR, country['path'].replace('\\', '/'))
            if not os.path.exists(country_path): continue
            with open(country_path, 'r', encoding='utf-8') as f:
                cities = json.load(f)
                all_cities.extend(cities)

    total = len(all_cities)
    print(f"📋 检索到 {total} 个城市，严格按顺序逐一同步：\n")

    for i, city in enumerate(all_cities, 1):
        sync_city_full(city, i, total)
        time.sleep(0.3)

    print("✨ 所有城市 2026 数据全部无缝对齐至最新！")

if __name__ == "__main__":
    run()

    # 自动调用 step1 刷新状态给前端点亮绿灯
    step1_script = os.path.join(CURRENT_DIR, "step1_detect_align.py")
    if os.path.exists(step1_script):
        subprocess.run([sys.executable, step1_script], cwd=CURRENT_DIR)