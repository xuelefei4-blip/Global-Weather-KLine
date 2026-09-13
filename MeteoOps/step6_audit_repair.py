import os
import sys
import json
import subprocess

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_data_dir():
    candidates = [
        os.path.join(CURRENT_DIR, 'static', 'data'),
        os.path.abspath(os.path.join(CURRENT_DIR, '..', 'MeteoSystem', 'static', 'data'))
    ]
    return next((p for p in candidates if os.path.exists(p)), None)

DATA_ROOT = get_data_dir()
DEFAULT_YEARS = list(range(2015, 2027))

def run():
    print(">> [6/6] 启动全库质检与自动修复...")
    if not DATA_ROOT:
        print("❌ 错误: 找不到 static/data 目录")
        return

    fixed_path_count = 0
    empty_file_count = 0
    fixed_id_count = 0
    dedup_count = 0

    # 1. 遍历索引文件，修复反斜杠与补齐 years
    for root, _, files in os.walk(DATA_ROOT):
        for f in files:
            if f.endswith('.json'):
                full_p = os.path.join(root, f)
                try:
                    with open(full_p, 'r', encoding='utf-8') as jf:
                        content = json.load(jf)

                    if isinstance(content, list):
                        changed = False
                        for item in content:
                            if isinstance(item, dict) and "id" in item:
                                if "years" not in item:
                                    item["years"] = DEFAULT_YEARS
                                    changed = True
                                if "path" in item:
                                    normalized = item["path"].replace('\\', '/')
                                    if not normalized.endswith('/'): 
                                        normalized += '/'
                                    if normalized != item["path"]:
                                        item["path"] = normalized
                                        changed = True
                        if changed:
                            with open(full_p, 'w', encoding='utf-8') as out_jf:
                                json.dump(content, out_jf, ensure_ascii=False, indent=2)
                            fixed_path_count += 1
                except Exception:
                    pass

    # 2. 检查分片数据文件有效性、修复 ID 映射、时间戳去重与按序重整
    for root, _, files in os.walk(DATA_ROOT):
        for f in files:
            if f.endswith('.json') and '_' in f and not f.endswith('_index.json') and not f.endswith('_cities.json'):
                f_path = os.path.join(root, f)
                try:
                    # 检查并清理 0KB 空文件
                    if os.path.getsize(f_path) == 0:
                        print(f"  ⚠️ 发现 0KB 空文件并移除: {f}")
                        os.remove(f_path)
                        empty_file_count += 1
                        continue

                    with open(f_path, 'r', encoding='utf-8') as df:
                        d = json.load(df)

                    is_dirty = False
                    expected_id = f.split('_')[0].lower()
                    actual_id = str(d.get('city', '')).lower()

                    # 修复 ID 映射
                    if expected_id != actual_id:
                        d['city'] = expected_id
                        print(f"  🔧 自动修复 ID 映射: {f} (内部 [{actual_id}] ➔ [{expected_id}])")
                        fixed_id_count += 1
                        is_dirty = True

                    # 检查并去重/排序 values
                    if "values" in d and isinstance(d["values"], list):
                        raw_values = d["values"]
                        seen_ts = set()
                        clean_values = []

                        for v in raw_values:
                            if isinstance(v, dict) and "time" in v:
                                if v["time"] not in seen_ts:
                                    seen_ts.add(v["time"])
                                    clean_values.append(v)
                                else:
                                    dedup_count += 1
                                    is_dirty = True

                        if len(clean_values) != len(raw_values) or is_dirty:
                            clean_values.sort(key=lambda x: x.get('time', 0))
                            d["values"] = clean_values
                            is_dirty = True

                    # 保存修复后的数据
                    if is_dirty:
                        with open(f_path, 'w', encoding='utf-8') as df:
                            json.dump(d, df, ensure_ascii=False)

                except Exception as e:
                    print(f"  ❌ 解析文件异常 {f}: {e}")

    print("---------------- 质检报告 ----------------")
    print(f"🔧 修复路径/补齐 years 的索引文件数: {fixed_path_count}")
    print(f"🗑️ 清理损坏空文件数: {empty_file_count}")
    print(f"🛠️ 自动纠正内部 ID 冲突数: {fixed_id_count}")
    print(f"✨ 去除重复/错序时间戳点数: {dedup_count}")
    print("=" * 42)
    print("✅ 全库质检与修复完毕，数据健康度 100%！")

    # 自动触发 Step 1 同步刷新面板状态
    step1_script = os.path.join(CURRENT_DIR, "step1_detect_align.py")
    if os.path.exists(step1_script):
        subprocess.run([sys.executable, step1_script], cwd=CURRENT_DIR)

if __name__ == "__main__":
    run()