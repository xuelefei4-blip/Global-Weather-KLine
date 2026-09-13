import os
import sys
import json
from datetime import datetime

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. 路径自适应检测
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
SEED_DIR = os.path.join(CURRENT_DIR, "data_seed")
EXPORT_LOG = os.path.join(CURRENT_DIR, "update_export_report.txt")

def run():
    print(">> [5/6] 导出本次更新与新增明细启动...")
    
    if not os.path.exists(ROOT_INDEX):
        print("❌ 错误：找不到根索引 index.json")
        return

    # 2. 扫出本地硬盘所有具体数据 JSON 文件及最后物理修改时间
    disk_files_info = {}
    for root, dirs, files in os.walk(DATA_ROOT):
        for f in files:
            # 过滤掉索引类辅助文件，精准定位年份分片
            if f.endswith(".json") and not f.endswith("_index.json") and not f.endswith("_cities.json") and f != "index.json":
                f_path = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(f_path)
                    disk_files_info[f.lower().strip()] = {
                        "path": f_path,
                        "mtime": mtime,
                        "time_str": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception:
                    pass

    # 3. 读取 161 城市全集种子进行映射比对
    continent_files = [
        "asia.json", "europe.json", "north_america.json",
        "south_america.json", "africa.json", "oceania.json", "antarctica.json"
    ]

    updated_records = []
    newly_added_records = []

    for c_file in continent_files:
        seed_path = os.path.join(SEED_DIR, c_file)
        if not os.path.exists(seed_path): 
            continue

        try:
            with open(seed_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            continue

        for country, cities in catalog.items():
            for name, cid in cities.items():
                cid_clean = str(cid).lower().strip()
                
                # 提取属于该城市的所有年份分片
                city_files = [f_name for f_name in disk_files_info.keys() if f_name.startswith(f"{cid_clean}_")]
                if not city_files:
                    continue

                # 判定该城市是否已具备 2026 实况切片
                has_2026 = f"{cid_clean}_2026.json" in disk_files_info
                
                for cf in city_files:
                    f_info = disk_files_info[cf]
                    # 提取具体年份标签
                    yr_part = cf.replace(f"{cid_clean}_", "").replace(".json", "")
                    
                    entry = {
                        "city_name": name,
                        "city_id": cid_clean.upper(),
                        "file": cf,
                        "year": yr_part,
                        "mtime": f_info["mtime"],
                        "time": f_info["time_str"]
                    }

                    # 分流：2026最新实况切片或有2026的归为更新流，纯历史切片归为底库流
                    if yr_part == "2026" or has_2026:
                        updated_records.append(entry)
                    else:
                        newly_added_records.append(entry)

    # 4. 严格按照物理文件修改时间倒序排列（最近更新的排最前）
    updated_records.sort(key=lambda x: x["mtime"], reverse=True)
    newly_added_records.sort(key=lambda x: x["mtime"], reverse=True)

    # 5. 组装完整报表内容
    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append(f" MeteoOps 数据更新与新增导出报告 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    report_lines.append("=" * 60 + "\n")

    # 打印第一区块：2026最新更新流
    updated_header = f"🔥 【更新记录 (包含2026最新实况)】 共计 {len(updated_records)} 项："
    print(updated_header)
    report_lines.append(updated_header)
    
    for item in updated_records[:20]:
        line = f"   - 更新: {item['city_name']} ({item['city_id']}) ➔ 切片: {item['file']} [时间: {item['time']}]"
        print(line)
        report_lines.append(line)
        
    if len(updated_records) > 20:
        omit_str = f"   ... (其余 {len(updated_records) - 20} 项已省略，详见文本报告)"
        print(omit_str)
        # 报告文件中写入全量，不省略
        for item in updated_records[20:]:
            report_lines.append(f"   - 更新: {item['city_name']} ({item['city_id']}) ➔ 切片: {item['file']} [时间: {item['time']}]")

    # 打印第二区块：2015~2025十年历史底库流
    added_header = f"\n📦 【新增历史底库记录 (2015~2025)】 共计 {len(newly_added_records)} 项："
    print(added_header)
    report_lines.append(added_header)
    
    for item in newly_added_records[:20]:
        line = f"   - 新增: {item['city_name']} ({item['city_id']}) ➔ 切片: {item['file']} [时间: {item['time']}]"
        print(line)
        report_lines.append(line)
        
    if len(newly_added_records) > 20:
        omit_str = f"   ... (其余 {len(newly_added_records) - 20} 项已省略，详见文本报告)"
        print(omit_str)
        # 报告文件中写入全量
        for item in newly_added_records[20:]:
            report_lines.append(f"   - 新增: {item['city_name']} ({item['city_id']}) ➔ 切片: {item['file']} [时间: {item['time']}]")

    # 6. 写入文本报告文件
    with open(EXPORT_LOG, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))

    print(f"\n✨ 导出完毕！详细变更清单已写入文件: {EXPORT_LOG}")

if __name__ == "__main__":
    run()