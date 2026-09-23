"""
综合导入脚本：
1. 将新增知识点添加到各层级并建立与课程的关系
2. 删除原有拓展路径，重新导入
3. 导入兴趣路径
"""

import sqlite3
import hashlib
import pandas as pd

DB_PATH = 'database.db'

# 层级映射：数字 -> LAYER_*格式
LAYER_MAPPING = {
    3: 'LAYER_PROFESSIONAL',      # 专业课
    4: 'LAYER_DISCIPLINE_BASE',   # 学科基础
    5: 'LAYER_ADVANCED_BASE',     # 高阶基础
    6: 'LAYER_MATH_BASE',         # 数理基础
}

# 路径类型配置
PATH_TYPES = {
    'main': {'id': 1, 'name': '主路径'},
    'extension': {'id_start': 2, 'name_prefix': '拓展路径'},
    'interest': {'id_start': 100, 'name_prefix': '兴趣路径'},
}

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_node_id(name, layer):
    """生成节点ID"""
    return hashlib.md5(f"{name}_{layer}".encode()).hexdigest()[:12]

def generate_edge_id(source_id, target_id, relation_type):
    """生成边ID"""
    return hashlib.md5(f"{source_id}_{target_id}_{relation_type}".encode()).hexdigest()[:12]

def step1_import_knowledge_with_relations():
    """步骤1：导入新增知识点并建立与课程的关系"""
    print("=" * 60)
    print("步骤1：导入新增知识点并建立与课程的关系")
    print("=" * 60)
    
    # 读取Excel文件
    df = pd.read_excel('data/2/新增知识点(1).xlsx')
    print(f"读取到 {len(df)} 条记录")
    
    conn = get_db()
    cursor = conn.cursor()
    
    added_nodes = 0
    added_edges = 0
    skipped_nodes = 0
    
    # 去重处理
    df_unique = df.drop_duplicates(subset=['知识点'])
    print(f"去重后 {len(df_unique)} 条唯一记录")
    
    for _, row in df_unique.iterrows():
        name = str(row['知识点']).strip()
        course = str(row['课程名']).strip()
        layer_num = int(row['层级'])
        
        # 转换层级
        layer = LAYER_MAPPING.get(layer_num)
        if not layer:
            print(f"⚠ 未知层级 {layer_num}: {name}")
            continue
        
        # 检查节点是否已存在
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (name,))
        existing = cursor.fetchone()
        
        if existing:
            node_id = existing['id']
            skipped_nodes += 1
        else:
            # 生成节点ID并插入
            node_id = generate_node_id(name, layer)
            try:
                cursor.execute('''
                    INSERT INTO nodes (id, name, layer, node_type, description, metadata)
                    VALUES (?, ?, ?, ?, ?, '{}')
                ''', (node_id, name, layer, 'leaf', f"课程: {course}"))
                added_nodes += 1
                print(f"✓ 添加节点: {name} (层级: {layer})")
            except sqlite3.IntegrityError as e:
                print(f"✗ 节点添加失败: {name} - {e}")
                continue
        
        # 查找课程节点
        cursor.execute('SELECT id, layer FROM nodes WHERE name = ?', (course,))
        course_node = cursor.fetchone()
        
        if course_node:
            # 建立知识点与课程的关系
            edge_id = generate_edge_id(course_node['id'], node_id, 'contains')
            cursor.execute('SELECT id FROM edges WHERE id = ?', (edge_id,))
            if not cursor.fetchone():
                try:
                    cursor.execute('''
                        INSERT INTO edges (id, source_id, target_id, relation_type, weight, metadata)
                        VALUES (?, ?, ?, ?, ?, '{}')
                    ''', (edge_id, course_node['id'], node_id, 'contains', 1.0))
                    added_edges += 1
                    print(f"  ✓ 建立关系: {course} -> {name}")
                except sqlite3.IntegrityError:
                    pass
        else:
            print(f"  ⚠ 未找到课程节点: {course}")
    
    conn.commit()
    conn.close()
    
    print(f"\n步骤1完成！新增 {added_nodes} 个节点，{added_edges} 条关系，跳过 {skipped_nodes} 个已存在节点")
    return added_nodes, added_edges

def step2_delete_extension_paths():
    """步骤2：删除原有拓展路径"""
    print("\n" + "=" * 60)
    print("步骤2：删除原有拓展路径")
    print("=" * 60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 删除path_id >= 2的所有路径（保留主路径）
    cursor.execute('SELECT path_id, path_name, COUNT(*) as count FROM main_path WHERE path_id >= 2 GROUP BY path_id, path_name')
    paths = cursor.fetchall()
    
    if paths:
        print("将删除以下路径:")
        for p in paths:
            print(f"  - 路径 {p['path_id']}: {p['path_name']} ({p['count']} 条记录)")
        
        cursor.execute('DELETE FROM main_path WHERE path_id >= 2')
        deleted = cursor.rowcount
        conn.commit()
        print(f"\n✓ 已删除 {deleted} 条路径记录")
    else:
        print("没有需要删除的拓展路径")
    
    conn.close()

def step3_import_extension_paths():
    """步骤3：重新导入拓展路径"""
    print("\n" + "=" * 60)
    print("步骤3：导入拓展路径")
    print("=" * 60)
    
    xl = pd.ExcelFile('data/2/电子信息工程拓展路径梳理（v1） (1).xlsx')
    print(f"Sheet列表: {xl.sheet_names}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 路径名称映射
    path_names = {
        'Sheet1': '拓展路径1-抗干扰协同感知',
        'Sheet2': '拓展路径2-分布式无源协同定位',
        'Sheet3': '拓展路径3-认知电子战闭环对抗',
        'Sheet5': '拓展路径4-多模态光电雷达识别',
        'Sheet6': '拓展路径5-资源受限轻量化感知',
    }
    
    path_id = 2  # 从2开始
    total_imported = 0
    
    for sheet_name in ['Sheet1', 'Sheet2', 'Sheet3', 'Sheet5', 'Sheet6']:
        if sheet_name not in xl.sheet_names:
            print(f"⚠ Sheet {sheet_name} 不存在，跳过")
            continue
        
        df = pd.read_excel(xl, sheet_name=sheet_name)
        
        # 识别列名
        source_col = None
        target_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if '出发' in col_lower or 'source' in col_lower:
                source_col = col
            elif '目的' in col_lower or '结束' in col_lower or 'target' in col_lower:
                target_col = col
        
        if not source_col or not target_col:
            # 使用前两列
            source_col = df.columns[0]
            target_col = df.columns[1]
        
        path_name = path_names.get(sheet_name, f'拓展路径{path_id-1}')
        print(f"\n导入 {sheet_name} -> {path_name}")
        
        imported = 0
        for _, row in df.iterrows():
            source_name = str(row[source_col]).strip() if pd.notna(row[source_col]) else None
            target_name = str(row[target_col]).strip() if pd.notna(row[target_col]) else None
            
            if not source_name or not target_name or source_name == 'nan' or target_name == 'nan':
                continue
            
            # 查找节点ID
            cursor.execute('SELECT id FROM nodes WHERE name = ?', (source_name,))
            source_row = cursor.fetchone()
            source_id = source_row['id'] if source_row else None
            
            cursor.execute('SELECT id FROM nodes WHERE name = ?', (target_name,))
            target_row = cursor.fetchone()
            target_id = target_row['id'] if target_row else None
            
            # 插入路径记录
            cursor.execute('''
                INSERT INTO main_path (path_id, path_name, source_id, target_id, source_name, target_name, path_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (path_id, path_name, source_id, target_id, source_name, target_name, imported))
            
            imported += 1
            
            if not source_id:
                print(f"  ⚠ 源节点不存在: {source_name}")
            if not target_id:
                print(f"  ⚠ 目标节点不存在: {target_name}")
        
        print(f"  ✓ 导入 {imported} 条记录")
        total_imported += imported
        path_id += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n拓展路径导入完成！共导入 {total_imported} 条记录")
    return total_imported

def step4_import_interest_paths():
    """步骤4：导入兴趣路径"""
    print("\n" + "=" * 60)
    print("步骤4：导入兴趣路径")
    print("=" * 60)
    
    xl = pd.ExcelFile('data/2/电子信息工程兴趣路径梳理（v1）.xlsx')
    print(f"Sheet列表: {xl.sheet_names}")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 兴趣路径从path_id=100开始
    path_id = 100
    total_imported = 0
    
    for i, sheet_name in enumerate(xl.sheet_names):
        df = pd.read_excel(xl, sheet_name=sheet_name)
        
        # 识别列名
        source_col = df.columns[0]  # 出发节点
        target_col = df.columns[1]  # 目的节点
        
        path_name = f'兴趣路径{i+1}'
        print(f"\n导入 {sheet_name} -> {path_name}")
        
        imported = 0
        for _, row in df.iterrows():
            source_name = str(row[source_col]).strip() if pd.notna(row[source_col]) else None
            target_name = str(row[target_col]).strip() if pd.notna(row[target_col]) else None
            
            if not source_name or not target_name or source_name == 'nan' or target_name == 'nan':
                continue
            
            # 查找节点ID
            cursor.execute('SELECT id FROM nodes WHERE name = ?', (source_name,))
            source_row = cursor.fetchone()
            source_id = source_row['id'] if source_row else None
            
            cursor.execute('SELECT id FROM nodes WHERE name = ?', (target_name,))
            target_row = cursor.fetchone()
            target_id = target_row['id'] if target_row else None
            
            # 插入路径记录
            cursor.execute('''
                INSERT INTO main_path (path_id, path_name, source_id, target_id, source_name, target_name, path_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (path_id, path_name, source_id, target_id, source_name, target_name, imported))
            
            imported += 1
            
            if not source_id:
                print(f"  ⚠ 源节点不存在: {source_name}")
            if not target_id:
                print(f"  ⚠ 目标节点不存在: {target_name}")
        
        print(f"  ✓ 导入 {imported} 条记录")
        total_imported += imported
        path_id += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n兴趣路径导入完成！共导入 {total_imported} 条记录")
    return total_imported

def show_summary():
    """显示汇总信息"""
    print("\n" + "=" * 60)
    print("导入汇总")
    print("=" * 60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT path_id, path_name, COUNT(*) as count,
               SUM(CASE WHEN source_id IS NOT NULL AND target_id IS NOT NULL THEN 1 ELSE 0 END) as valid_count
        FROM main_path
        GROUP BY path_id, path_name
        ORDER BY path_id
    ''')
    
    print("\n所有路径统计:")
    for row in cursor.fetchall():
        path_type = "主路径" if row['path_id'] == 1 else ("拓展路径" if row['path_id'] < 100 else "兴趣路径")
        print(f"  [{path_type}] 路径 {row['path_id']}: {row['path_name']}")
        print(f"    总记录数: {row['count']}, 有效记录数: {row['valid_count']}")
    
    conn.close()

def main():
    """主函数"""
    # 步骤1：导入新增知识点并建立关系
    step1_import_knowledge_with_relations()
    
    # 步骤2：删除原有拓展路径
    step2_delete_extension_paths()
    
    # 步骤3：重新导入拓展路径
    step3_import_extension_paths()
    
    # 步骤4：导入兴趣路径
    step4_import_interest_paths()
    
    # 显示汇总
    show_summary()

if __name__ == '__main__':
    main()
