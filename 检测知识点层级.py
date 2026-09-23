#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检测知识点层级程序
读取Excel文件（支持多个Sheet），检测第一列和第二列的知识点在数据库中的层级
- 第一列知识点的层级输出到第三列
- 第二列知识点的层级输出到第四列
"""

import sqlite3
import pandas as pd
import os

# 层级显示名称映射
LAYER_DISPLAY = {
    'LAYER_ABILITY': '1-能力层',
    'LAYER_PROBLEM': '2-问题层',
    'LAYER_PROFESSIONAL': '3-专业课',
    'LAYER_DISCIPLINE_BASE': '4-学科基础',
    'LAYER_ADVANCED_BASE': '5-高阶基础',
    'LAYER_MATH_PHYSICS': '6-数理基础',
}

def get_node_layer(cursor, name):
    """查询节点的层级"""
    if not name or pd.isna(name):
        return ''
    
    name = str(name).strip()
    if not name:
        return ''
    
    cursor.execute("SELECT layer FROM nodes WHERE name = ?", (name,))
    result = cursor.fetchone()
    
    if result:
        layer = result[0]
        return LAYER_DISPLAY.get(layer, layer)
    else:
        return '未找到'

def check_layers(input_file, output_file=None):
    """
    检测Excel中知识点的层级
    
    Args:
        input_file: 输入的Excel文件路径
        output_file: 输出的Excel文件路径（可选，默认在原文件名后加_层级）
    """
    if not os.path.exists(input_file):
        print(f"错误：文件不存在 - {input_file}")
        return
    
    # 生成输出文件名
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_层级{ext}"
    
    print(f"正在读取文件: {input_file}")
    
    # 连接数据库
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 读取所有Sheet
    try:
        excel_file = pd.ExcelFile(input_file)
        sheet_names = excel_file.sheet_names
        print(f"发现 {len(sheet_names)} 个Sheet: {sheet_names}")
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        conn.close()
        return
    
    # 处理每个Sheet
    result_sheets = {}
    
    for sheet_name in sheet_names:
        print(f"\n处理 Sheet: {sheet_name}")
        df = pd.read_excel(input_file, sheet_name=sheet_name)
        
        if len(df.columns) < 2:
            print(f"  警告：Sheet '{sheet_name}' 列数不足2列，跳过")
            result_sheets[sheet_name] = df
            continue
        
        # 获取原始列名
        col1 = df.columns[0]
        col2 = df.columns[1]
        
        # 创建新列名
        col3 = f"{col1}_层级"
        col4 = f"{col2}_层级"
        
        # 检测层级
        layers1 = []
        layers2 = []
        
        found_count = 0
        not_found_count = 0
        
        for index, row in df.iterrows():
            name1 = row[col1] if col1 in row else ''
            name2 = row[col2] if col2 in row else ''
            
            layer1 = get_node_layer(cursor, name1)
            layer2 = get_node_layer(cursor, name2)
            
            layers1.append(layer1)
            layers2.append(layer2)
            
            # 统计
            if layer1 and layer1 != '未找到':
                found_count += 1
            elif layer1 == '未找到':
                not_found_count += 1
                
            if layer2 and layer2 != '未找到':
                found_count += 1
            elif layer2 == '未找到':
                not_found_count += 1
        
        # 添加新列
        df[col3] = layers1
        df[col4] = layers2
        
        # 重新排列列顺序：第一列、第二列、第三列（第一列层级）、第四列（第二列层级）、其他列
        new_columns = [col1, col2, col3, col4] + [c for c in df.columns if c not in [col1, col2, col3, col4]]
        df = df[new_columns]
        
        result_sheets[sheet_name] = df
        print(f"  处理完成: {len(df)} 行, 找到 {found_count} 个, 未找到 {not_found_count} 个")
    
    conn.close()
    
    # 保存结果
    print(f"\n正在保存到: {output_file}")
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in result_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print("完成!")

def main():
    print("=" * 50)
    print("知识点层级检测程序")
    print("=" * 50)
    print("\n功能说明：")
    print("  读取Excel文件，检测第一列和第二列知识点的层级")
    print("  第一列知识点的层级 → 输出到第三列")
    print("  第二列知识点的层级 → 输出到第四列")
    print("  支持多个Sheet")
    print("-" * 50)
    
    # 列出 data/2 文件夹下的 Excel 文件
    data_dir = os.path.join('data', '2')
    if os.path.exists(data_dir):
        excel_files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.xls'))]
        if excel_files:
            print("\ndata/2 文件夹下的Excel文件：")
            for i, f in enumerate(excel_files, 1):
                print(f"  {i}. {f}")
    
    print()
    input_path = input("请输入Excel文件路径（如 data/2/test.xlsx）: ").strip()
    
    if input_path:
        # 如果只输入文件名，默认在 data/2 下
        if not os.path.dirname(input_path):
            input_path = os.path.join('data', '2', input_path)
        
        check_layers(input_path)
    else:
        print("未输入文件路径，退出程序")

if __name__ == '__main__':
    main()
