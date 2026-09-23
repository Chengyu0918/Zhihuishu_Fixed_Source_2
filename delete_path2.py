#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""删除 path_id=2 的主路径数据"""

import sqlite3

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 删除 path_id=2 的数据
    cursor.execute('DELETE FROM main_path WHERE path_id = 2')
    deleted_count = cursor.rowcount
    conn.commit()
    
    print(f'已删除 {deleted_count} 条记录')
    
    # 查看当前主路径
    cursor.execute('SELECT DISTINCT path_id, path_name FROM main_path')
    print('当前主路径:', cursor.fetchall())
    
    conn.close()

if __name__ == '__main__':
    main()
