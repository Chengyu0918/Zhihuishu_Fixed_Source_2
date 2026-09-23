#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查能力层节点"""

import sqlite3

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 查询各层节点数量
    print("各层节点数量:")
    cursor.execute("SELECT layer, COUNT(*) as cnt FROM nodes GROUP BY layer ORDER BY layer")
    for r in cursor.fetchall():
        print(f"  {r[0]}: {r[1]}")
    
    # 查询能力层节点
    print("\n能力层节点详情:")
    cursor.execute("SELECT id, name, node_type FROM nodes WHERE layer = 'LAYER_ABILITY' ORDER BY name")
    rows = cursor.fetchall()
    
    print(f"能力层节点数量: {len(rows)}")
    print("\n节点列表:")
    for r in rows:
        print(f"  {r[0]}: {r[1]} ({r[2]})")
    
    # 检查问题层节点
    print("\n问题层节点详情:")
    cursor.execute("SELECT id, name, node_type FROM nodes WHERE layer = 'LAYER_PROBLEM' ORDER BY name")
    rows = cursor.fetchall()
    print(f"问题层节点数量: {len(rows)}")
    print("\n前20个节点:")
    for r in rows[:20]:
        print(f"  {r[0]}: {r[1]} ({r[2]})")
    
    conn.close()

if __name__ == '__main__':
    main()
