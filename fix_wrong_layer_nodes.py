#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查和删除错误层级的节点"""

import sqlite3

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 查找错误层级的节点（layer 是数字而不是正确的层级名称）
    cursor.execute("SELECT id, name, layer FROM nodes WHERE layer NOT LIKE 'LAYER_%'")
    rows = cursor.fetchall()
    
    print(f"发现 {len(rows)} 个错误层级的节点:")
    for r in rows:
        print(f"  {r[0]}: {r[1]} (layer={r[2]})")
    
    if rows:
        print("\n正在删除这些错误节点...")
        cursor.execute("DELETE FROM nodes WHERE layer NOT LIKE 'LAYER_%'")
        deleted = cursor.rowcount
        conn.commit()
        print(f"已删除 {deleted} 个节点")
        
        # 同时删除相关的边
        cursor.execute("DELETE FROM edges WHERE source_id NOT IN (SELECT id FROM nodes) OR target_id NOT IN (SELECT id FROM nodes)")
        deleted_edges = cursor.rowcount
        conn.commit()
        print(f"已删除 {deleted_edges} 条孤立的边")
    
    # 显示当前各层节点数量
    print("\n当前各层节点数量:")
    cursor.execute("SELECT layer, COUNT(*) as cnt FROM nodes GROUP BY layer ORDER BY layer")
    for r in cursor.fetchall():
        print(f"  {r[0]}: {r[1]}")
    
    conn.close()

if __name__ == '__main__':
    main()
