import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 查找检波电路
cursor.execute("SELECT id, name, layer, weight FROM nodes WHERE name LIKE '%检波%'")
rows = cursor.fetchall()
print("=== 检波相关节点 ===")
for r in rows:
    print(f"  ID: {r[0]}, 名称: {r[1]}, 层级: {r[2]}, 权重: {r[3]}")

# 查找权重最大的节点
cursor.execute("SELECT id, name, layer, weight FROM nodes WHERE weight IS NOT NULL ORDER BY weight DESC LIMIT 10")
rows = cursor.fetchall()
print("\n=== 权重最大的10个节点 ===")
for r in rows:
    print(f"  ID: {r[0]}, 名称: {r[1]}, 层级: {r[2]}, 权重: {r[3]}")

# 统计有权重的节点
cursor.execute("SELECT COUNT(*) FROM nodes WHERE weight IS NOT NULL AND weight > 0")
count = cursor.fetchone()[0]
print(f"\n有权重的节点数: {count}")

conn.close()
