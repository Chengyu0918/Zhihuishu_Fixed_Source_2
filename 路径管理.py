#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
路径管理程序
支持导入和删除三种路径类型：
1 - 主路径
2 - 拓展路径
3 - 兴趣路径
"""

import pandas as pd
import sqlite3
import os

DB_PATH = 'database.db'

# 路径类型配置
PATH_TYPES = {
    1: '主路径',
    2: '拓展路径',
    3: '兴趣路径'
}


def get_node_id_by_name(cursor, name):
    """根据节点名称查找节点ID"""
    cursor.execute('SELECT id FROM nodes WHERE name = ?', (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def list_excel_files():
    """列出 data/2 文件夹下的 Excel 文件"""
    data_dir = os.path.join('data', '2')
    if os.path.exists(data_dir):
        excel_files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.xls'))]
        return excel_files
    return []


def list_sheets(excel_file):
    """列出 Excel 文件中的所有 Sheet"""
    try:
        excel = pd.ExcelFile(excel_file)
        return excel.sheet_names
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return []


def show_current_paths():
    """显示当前数据库中的所有路径"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT path_id, path_name, COUNT(*) as cnt 
        FROM main_path 
        GROUP BY path_id, path_name
        ORDER BY path_id
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    if results:
        print("\n当前数据库中的路径:")
        print("-" * 50)
        for row in results:
            path_type = PATH_TYPES.get(row[0], '未知')
            print(f"  路径ID: {row[0]} ({path_type})")
            print(f"  路径名称: {row[1]}")
            print(f"  记录数: {row[2]}")
            print("-" * 50)
    else:
        print("\n数据库中暂无路径数据")
    
    return results


def import_path_from_excel(path_id, excel_file, sheet_name=None, path_name=None):
    """
    从Excel导入路径
    
    Args:
        path_id: 路径类型 (1=主路径, 2=拓展路径, 3=兴趣路径)
        excel_file: Excel文件路径
        sheet_name: Sheet名称（可选，默认第一个Sheet）
        path_name: 路径名称（可选，默认使用路径类型名称）
    """
    if path_id not in PATH_TYPES:
        print(f"错误: 无效的路径类型 {path_id}")
        return False
    
    if not os.path.exists(excel_file):
        print(f"错误: 文件不存在 {excel_file}")
        return False
    
    # 读取Excel文件
    print(f"\n读取文件: {excel_file}")
    
    try:
        if sheet_name:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            print(f"读取 Sheet: {sheet_name}")
        else:
            df = pd.read_excel(excel_file)
            print("读取第一个 Sheet")
    except Exception as e:
        print(f"读取Excel失败: {e}")
        return False
    
    # 检查列
    if len(df.columns) < 2:
        print("错误: Excel至少需要2列（出发节点、目的节点）")
        return False
    
    # 获取列名（支持不同的列名格式）
    col1 = df.columns[0]  # 出发节点
    col2 = df.columns[1]  # 目的节点
    
    print(f"出发节点列: {col1}")
    print(f"目的节点列: {col2}")
    print(f"数据行数: {len(df)}")
    
    # 设置路径名称
    if path_name is None:
        path_name = PATH_TYPES[path_id]
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 确保main_path表有path_id和path_name列
    cursor.execute('PRAGMA table_info(main_path)')
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'path_id' not in columns:
        cursor.execute('ALTER TABLE main_path ADD COLUMN path_id INTEGER DEFAULT 1')
    if 'path_name' not in columns:
        cursor.execute('ALTER TABLE main_path ADD COLUMN path_name TEXT')
    
    # 获取当前最大的path_order
    cursor.execute('SELECT MAX(path_order) FROM main_path WHERE path_id = ?', (path_id,))
    max_order_result = cursor.fetchone()
    start_order = (max_order_result[0] or 0) + 1
    
    # 显示现有数据信息
    cursor.execute('SELECT COUNT(*) FROM main_path WHERE path_id = ?', (path_id,))
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print(f"\n当前 {PATH_TYPES[path_id]} (path_id={path_id}) 已有 {existing_count} 条记录")
        print("新数据将追加到现有数据后面（不会影响原有数据）")
    
    # 导入数据
    imported_count = 0
    missing_nodes = set()
    
    for idx, row in df.iterrows():
        source_name = str(row[col1]).strip() if pd.notna(row[col1]) else ''
        target_name = str(row[col2]).strip() if pd.notna(row[col2]) else ''
        
        if not source_name or not target_name:
            continue
        
        # 查找节点ID
        source_id = get_node_id_by_name(cursor, source_name)
        target_id = get_node_id_by_name(cursor, target_name)
        
        if not source_id:
            missing_nodes.add(source_name)
        if not target_id:
            missing_nodes.add(target_name)
        
        # 插入数据
        cursor.execute('''
            INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order, path_id, path_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (source_name, target_name, source_id, target_id, idx + 1, path_id, path_name))
        
        imported_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n导入完成!")
    print(f"  路径类型: {PATH_TYPES[path_id]} (path_id={path_id})")
    print(f"  路径名称: {path_name}")
    print(f"  导入记录数: {imported_count}")
    
    if missing_nodes:
        print(f"\n警告: 以下 {len(missing_nodes)} 个节点在数据库中不存在:")
        for node in sorted(missing_nodes)[:20]:
            print(f"  - {node}")
        if len(missing_nodes) > 20:
            print(f"  ... 还有 {len(missing_nodes) - 20} 个")
    
    return True


def delete_path(path_id):
    """
    删除指定类型的路径
    
    Args:
        path_id: 路径类型 (1=主路径, 2=拓展路径, 3=兴趣路径)
    """
    if path_id not in PATH_TYPES:
        print(f"错误: 无效的路径类型 {path_id}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查询现有数据
    cursor.execute('SELECT COUNT(*) FROM main_path WHERE path_id = ?', (path_id,))
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"\n{PATH_TYPES[path_id]} (path_id={path_id}) 没有数据")
        conn.close()
        return False
    
    print(f"\n{PATH_TYPES[path_id]} (path_id={path_id}) 共有 {count} 条记录")
    confirm = input("确认删除？(y/n): ").strip().lower()
    
    if confirm == 'y':
        cursor.execute('DELETE FROM main_path WHERE path_id = ?', (path_id,))
        conn.commit()
        print(f"已删除 {count} 条记录")
        conn.close()
        return True
    else:
        print("取消删除")
        conn.close()
        return False


def main():
    while True:
        print("\n" + "=" * 50)
        print("路径管理程序")
        print("=" * 50)
        print("\n操作选项:")
        print("  1. 导入路径")
        print("  2. 删除路径")
        print("  3. 查看当前路径")
        print("  0. 退出")
        print("-" * 50)
        
        action = input("请选择操作 (0-3): ").strip()
        
        if action == '0':
            print("退出程序")
            break
        
        elif action == '1':
            # 导入路径
            print("\n路径类型:")
            print("  1 - 主路径")
            print("  2 - 拓展路径")
            print("  3 - 兴趣路径")
            
            path_type = input("请选择路径类型 (1-3): ").strip()
            if path_type not in ['1', '2', '3']:
                print("无效的路径类型")
                continue
            
            path_id = int(path_type)
            
            # 列出Excel文件
            excel_files = list_excel_files()
            if excel_files:
                print("\ndata/2 文件夹下的Excel文件:")
                for i, f in enumerate(excel_files, 1):
                    print(f"  {i}. {f}")
            
            file_input = input("\n请输入Excel文件路径或编号: ").strip()
            
            # 处理输入
            if file_input.isdigit():
                idx = int(file_input) - 1
                if 0 <= idx < len(excel_files):
                    excel_file = os.path.join('data', '2', excel_files[idx])
                else:
                    print("无效的编号")
                    continue
            else:
                if not os.path.dirname(file_input):
                    excel_file = os.path.join('data', '2', file_input)
                else:
                    excel_file = file_input
            
            if not os.path.exists(excel_file):
                print(f"文件不存在: {excel_file}")
                continue
            
            # 列出Sheet
            sheets = list_sheets(excel_file)
            if sheets:
                print(f"\n文件中的Sheet:")
                for i, s in enumerate(sheets, 1):
                    print(f"  {i}. {s}")
                
                sheet_input = input("请选择Sheet编号（直接回车使用第一个）: ").strip()
                
                if sheet_input.isdigit():
                    idx = int(sheet_input) - 1
                    if 0 <= idx < len(sheets):
                        sheet_name = sheets[idx]
                    else:
                        print("无效的编号，使用第一个Sheet")
                        sheet_name = None
                else:
                    sheet_name = None
            else:
                sheet_name = None
            
            # 路径名称
            path_name = input(f"请输入路径名称（直接回车使用默认'{PATH_TYPES[path_id]}'）: ").strip()
            if not path_name:
                path_name = None
            
            # 执行导入
            import_path_from_excel(path_id, excel_file, sheet_name, path_name)
        
        elif action == '2':
            # 删除路径
            show_current_paths()
            
            print("\n路径类型:")
            print("  1 - 主路径")
            print("  2 - 拓展路径")
            print("  3 - 兴趣路径")
            
            path_type = input("请选择要删除的路径类型 (1-3): ").strip()
            if path_type not in ['1', '2', '3']:
                print("无效的路径类型")
                continue
            
            path_id = int(path_type)
            delete_path(path_id)
        
        elif action == '3':
            # 查看当前路径
            show_current_paths()
        
        else:
            print("无效的选项")


if __name__ == '__main__':
    main()
