import sqlite3
import pandas as pd
import os

def export_db_to_excel(db_path='database.db', output_file='knowledge_graph_data.xlsx'):
    """
    将 SQLite 数据库中的 nodes 和 edges 表导出到 Excel
    """
    # 1. 检查数据库是否存在
    if not os.path.exists(db_path):
        print(f"错误: 找不到数据库文件 {db_path}")
        return

    print(f"正在读取数据库: {db_path} ...")
    
    # 2. 连接数据库
    conn = sqlite3.connect(db_path)
    
    try:
        # 3. 读取 nodes 表
        # 使用 pandas 的 read_sql_query 直接读取为 DataFrame
        df_nodes = pd.read_sql_query("SELECT * FROM nodes", conn)
        print(f"读取到 {len(df_nodes)} 个节点")

        # 4. 读取 edges 表
        df_edges = pd.read_sql_query("SELECT * FROM edges", conn)
        print(f"读取到 {len(df_edges)} 条关系")

        # 5. 写入 Excel
        print(f"正在写入 Excel 文件: {output_file} ...")
        
        # 使用 ExcelWriter 创建多 Sheet 的 Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Sheet1: 节点信息
            df_nodes.to_excel(writer, sheet_name='Nodes (节点)', index=False)
            
            # Sheet2: 关系信息
            df_edges.to_excel(writer, sheet_name='Edges (关系)', index=False)
            
        print("导出成功！")
        
    except Exception as e:
        print(f"导出失败: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    export_db_to_excel()