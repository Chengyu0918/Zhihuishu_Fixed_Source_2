#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pandas as pd
from collections import Counter

# 读取Excel
df = pd.read_excel('data/2/新增知识点.xlsx')

col_name = df.columns[0]

# 获取所有非空知识点
names = [str(row).strip() for row in df[col_name] if pd.notna(row) and str(row).strip()]

output = []
output.append(f"Excel总行数: {len(df)}")
output.append(f"非空知识点数: {len(names)}")
output.append(f"唯一知识点数: {len(set(names))}")
output.append(f"重复数: {len(names) - len(set(names))}")

# 找出重复的知识点
counter = Counter(names)
duplicates = [(name, count) for name, count in counter.items() if count > 1]
output.append(f"\n重复的知识点 ({len(duplicates)} 个):")
for name, count in sorted(duplicates, key=lambda x: -x[1])[:20]:
    output.append(f"  {name}: {count}次")

# 保存到文件
with open('check_unique_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print("结果已保存到 check_unique_result.txt")
