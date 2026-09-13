import os
import sys
import json
import time
import urllib.request
import urllib.parse
from datetime import datetime

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
    print("❌ 错误：找不到 static/data 文件夹！")
    sys.exit(1)

ROOT_INDEX = os.path.join(DATA_ROOT, 'index.json')
BASE_DIR = os.path.abspath(os.path.join(DATA_ROOT, '..', '..'))
START_YEAR = 2015
END_YEAR = 2025

def get_weather_data(lat, lon, year, retries=3):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,relative_humidity_2m&timezone=auto"
    
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MeteoOps/1.0"})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            temps = hourly.get('temperature_2m', [])
            humids = hourly.get('relative_humidity_2m', [])
            
            if not times:
                return None

            values = []
            for i in range(len(times)):
                dt = datetime.fromisoformat(times[i])
                t = temps[i] if temps[i] is not None else 0
                values.append({
                    "time": int(dt.timestamp()),
                    "date": dt.strftime("%y/%m/%d/%H"),
                    "DATE": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": round(t, 1),
                    "high": round(t + 0.2, 1),
                    "low": round(t - 0.2, 1),
                    "close": round(t + 0.1, 1),
                    "vol": int(humids[i]) if humids[i] is not None else 0
                })
            return values
        except Exception as e:
            if attempt < retries:
                time.sleep(1.5)
            else:
                print(f"      ❌ 抓取失败 ({year}): {e}")
                return None

def run_task():
    print(">> [2/6] 补齐十年历史数据 (2015~2025) 启动...")
    if not os.path.exists(ROOT_INDEX):
        print(f"❌ 错误：找不到索引文件 {ROOT_INDEX}")
        return

    with open(ROOT_INDEX, 'r', encoding='utf-8') as f:
        continents = json.load(f)

    for cont in continents:
        cont_path = os.path.join(BASE_DIR, cont['path'].replace('\\', '/'))
        if not os.path.exists(cont_path): continue

        with open(cont_path, 'r', encoding='utf-8') as f:
            cont_data = json.load(f)
            countries = cont_data.get('children', []) if isinstance(cont_data, dict) else cont_data

        for country in countries:
            country_json_path = os.path.join(BASE_DIR, country['path'].replace('\\', '/'))
            if not os.path.exists(country_json_path): continue

            with open(country_json_path, 'r', encoding='utf-8') as f:
                cities = json.load(f)

            for city in cities:
                city_dir = os.path.join(BASE_DIR, city['path'].replace('\\', '/'))
                os.makedirs(city_dir, exist_ok=True)
                
                if city.get('lat', 0.0) == 0.0 and city.get('lon', 0.0) == 0.0:
                    print(f"☕ 跳过 {city.get('name', city['id'])} ({city['id']}): 经纬度未初始化")
                    continue

                for year in range(START_YEAR, END_YEAR + 1):
                    file_name = f"{city['id']}_{year}.json"
                    file_path = os.path.join(city_dir, file_name)

                    if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
                        continue

                    print(f"🚀 {city.get('name', city['id'])} ({city['id']}) ➔ 📅 抓取历史: {year}...")
                    weather_values = get_weather_data(city['lat'], city['lon'], year)

                    if weather_values:
                        output = {
                            "city": city['id'],
                            "year": str(year),
                            "values": weather_values
                        }
                        temp_p = f"{file_path}.tmp"
                        with open(temp_p, 'w', encoding='utf-8') as f:
                            json.dump(output, f, ensure_ascii=False)
                        os.replace(temp_p, file_path)
                        print(f"    ✅ 已保存: {file_name}")
                    
                    time.sleep(0.4)

    print("\n✨ Step 2 历史分片任务全部完成！")

    step1_script = os.path.join(CURRENT_DIR, "step1_detect_align.py")
    if os.path.exists(step1_script):
        import subprocess
        subprocess.run([sys.executable, step1_script], cwd=CURRENT_DIR)

if __name__ == "__main__":
    run_task()