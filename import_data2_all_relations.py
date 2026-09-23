"""
清空关系表并导入data/2文件夹下所有Excel文件的关系
关系格式：第一列大类+第二列小类 -> 第三列大类+第四列小类
"""

import os
import pandas as pd
from knowledge_graph.database import KnowledgeGraphDB
from knowledge_graph.schema import Edge, RelationType

def clear_all_edges(db):
    """清空所有关系"""
    with db.get_connection() as conn:
        cursor = conn.execute("DELETE FROM edges")
        deleted_count = cursor.rowcount
        print(f"已清空关系表，删除了 {deleted_count} 条关系")
    return deleted_count

def get_node_id_by_name(db, name):
    """根据名称查找节点ID"""
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM nodes WHERE name = ?",
            (name,)
        ).fetchone()
        if row:
            return row['id']
    return None

def import_excel_relations(db, excel_path):
    """导入单个Excel文件的关系"""
    print(f"\n处理文件: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"  读取Excel失败: {e}")
        return 0, 0, []
    
    # 检查列数
    if len(df.columns) < 4:
        print(f"  列数不足，需要至少4列，实际有 {len(df.columns)} 列")
        return 0, 0, []
    
    # 获取列名
    col_names = df.columns.tolist()
    print(f"  列名: {col_names[:6]}")  # 只显示前6列
    
    success_count = 0
    skip_count = 0
    errors = []
    
    # 用于去重
    added_relations = set()
    
    for idx, row in df.iterrows():
        try:
            # 获取四列数据
            source_category = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            source_item = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            target_category = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
            target_item = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            
            # 获取权重（第6列，相似度）
            weight = 1.0
            if len(df.columns) >= 6 and pd.notna(row.iloc[5]):
                try:
                    weight = float(row.iloc[5])
                except:
                    weight = 1.0
            
            # 跳过空行
            if not source_item or not target_item:
                continue
            
            # 查找源节点（小类/知识点）
            source_id = get_node_id_by_name(db, source_item)
            if not source_id:
                # 尝试查找大类
                source_id = get_node_id_by_name(db, source_category)
                if not source_id:
                    errors.append(f"行{idx+2}: 找不到源节点 '{source_item}' 或 '{source_category}'")
                    skip_count += 1
                    continue
            
            # 查找目标节点（小类/知识点）
            target_id = get_node_id_by_name(db, target_item)
            if not target_id:
                # 尝试查找大类
                target_id = get_node_id_by_name(db, target_category)
                if not target_id:
                    errors.append(f"行{idx+2}: 找不到目标节点 '{target_item}' 或 '{target_category}'")
                    skip_count += 1
                    continue
            
            # 避免自引用
            if source_id == target_id:
                continue
            
            # 去重检查
            relation_key = (source_id, target_id)
            if relation_key in added_relations:
                continue
            added_relations.add(relation_key)
            
            # 创建关系（使用peer类型表示同层关联，或cross表示跨层关联）
            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=RelationType.PEER,  # 默认使用peer类型
                weight=weight,
                description=f"从 {source_category}/{source_item} 到 {target_category}/{target_item}"
            )
            
            if db.add_edge(edge):
                success_count += 1
            else:
                skip_count += 1
                
        except Exception as e:
            errors.append(f"行{idx+2}: 处理出错 - {str(e)}")
            skip_count += 1
    
    print(f"  成功导入: {success_count} 条关系")
    print(f"  跳过: {skip_count} 条")
    if errors[:5]:  # 只显示前5个错误
        print(f"  部分错误: {errors[:5]}")
    
    return success_count, skip_count, errors

def main():
    db = KnowledgeGraphDB()
    
    # 1. 清空关系表
    print("=" * 60)
    print("步骤1: 清空关系表")
    print("=" * 60)
    clear_all_edges(db)
    
    # 2. 获取data/2文件夹下所有Excel文件
    data_dir = "data/2"
    excel_files = []
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            excel_files.append(os.path.join(data_dir, filename))
    
    print(f"\n找到 {len(excel_files)} 个Excel文件:")
    for f in excel_files:
        print(f"  - {f}")
    
    # 3. 导入所有Excel文件
    print("\n" + "=" * 60)
    print("步骤2: 导入关系")
    print("=" * 60)
    
    total_success = 0
    total_skip = 0
    all_errors = []
    
    for excel_path in excel_files:
        success, skip, errors = import_excel_relations(db, excel_path)
        total_success += success
        total_skip += skip
        all_errors.extend(errors)
    
    # 4. 输出统计
    print("\n" + "=" * 60)
    print("导入完成统计")
    print("=" * 60)
    print(f"总共成功导入: {total_success} 条关系")
    print(f"总共跳过: {total_skip} 条")
    print(f"总共错误: {len(all_errors)} 条")
    
    # 验证
    stats = db.get_statistics()
    print(f"\n数据库当前状态:")
    print(f"  节点总数: {stats['total_nodes']}")
    print(f"  关系总数: {stats['total_edges']}")
    print(f"  关系类型分布: {stats['edges_by_relation']}")

if __name__ == "__main__":
    main()
