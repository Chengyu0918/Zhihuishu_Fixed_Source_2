#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 读取Excel
df = pd.read_excel('data/2/新增知识点.xlsx')

# 获取所有知识点名称
col_name = df.columns[0]
col_category = df.columns[1]
col_layer = df.columns[2]

# 统计
existing_same_layer = 0
existing_diff_layer = 0
not_existing = 0

output = []
output.append("检查Excel中的知识点：")
output.append("-" * 80)

for index, row in df.iterrows():
    name = str(row[col_name]).strip() if pd.notna(row[col_name]) else ''
    if not name:
        continue
    
    cursor.execute("SELECT id, layer FROM nodes WHERE name = ?", (name,))
    result = cursor.fetchone()
    
    if result:
        layer_val = str(row[col_layer]).strip() if pd.notna(row[col_layer]) else ''
        # 简单映射
        layer_map = {'3': 'LAYER_PROFESSIONAL', '4': 'LAYER_DISCIPLINE_BASE', '5': 'LAYER_ADVANCED_BASE', '6': 'LAYER_MATH_PHYSICS'}
        expected_layer = layer_map.get(layer_val, layer_val)
        
        if result[1] == expected_layer:
            existing_same_layer += 1
        else:
            existing_diff_layer += 1
            output.append(f"层级不同: {name} - 数据库: {result[1]}, Excel: {expected_layer}")
    else:
        not_existing += 1
        category = str(row[col_category]).strip() if pd.notna(row[col_category]) else ''
        output.append(f"不存在: {name} (大类: {category})")

output.append("-" * 80)
output.append(f"\n统计：")
output.append(f"  已存在且层级相同: {existing_same_layer}")
output.append(f"  已存在但层级不同: {existing_diff_layer}")
output.append(f"  不存在: {not_existing}")

conn.close()

# 保存到文件
with open('check_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("结果已保存到 check_result.txt")
