"""
清除数据库中的所有边（关联关系）数据
用于重新导入数据前清理旧的关联信息
"""

import sqlite3
import os

def clear_all_edges():
    """清除edges表中的所有数据"""
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 查看当前edges表中的数据量
        cursor.execute("SELECT COUNT(*) FROM edges")
        count_before = cursor.fetchone()[0]
        print(f"清除前edges表中有 {count_before} 条记录")
        
        # 清除所有edges数据
        cursor.execute("DELETE FROM edges")
        conn.commit()
        
        # 确认清除结果
        cursor.execute("SELECT COUNT(*) FROM edges")
        count_after = cursor.fetchone()[0]
        print(f"清除后edges表中有 {count_after} 条记录")
        
        print(f"\n成功删除 {count_before} 条关联记录！")
        print("现在可以重新导入数据了。")
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()
    finally:
        conn.close()

def show_edges_summary():
    """显示edges表的摘要信息"""
    db_path = 'database.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 按关系类型统计
        cursor.execute("""
            SELECT relation_type, COUNT(*) as count 
            FROM edges 
            GROUP BY relation_type
        """)
        results = cursor.fetchall()
        
        if results:
            print("\n当前edges表按关系类型统计:")
            print("-" * 40)
            for relation_type, count in results:
                print(f"  {relation_type}: {count} 条")
        else:
            print("\nedges表为空，没有关联数据")
            
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("清除数据库关联数据工具")
    print("=" * 50)
    
    # 先显示当前状态
    show_edges_summary()
    
    # 确认是否清除
    print("\n" + "=" * 50)
    response = input("确定要清除所有关联数据吗？(输入 'yes' 确认): ")
    
    if response.lower() == 'yes':
        clear_all_edges()
    else:
        print("操作已取消")
