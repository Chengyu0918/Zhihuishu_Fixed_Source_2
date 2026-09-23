import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 检查涉及大类节点的关系数量
cursor.execute('''
    SELECT COUNT(*) FROM edges 
    WHERE source_id IN (SELECT id FROM nodes WHERE node_type = 'category') 
       OR target_id IN (SELECT id FROM nodes WHERE node_type = 'category')
''')
cat_count = cursor.fetchone()[0]

# 检查总关系数量
cursor.execute('SELECT COUNT(*) FROM edges')
total = cursor.fetchone()[0]

print(f'涉及大类节点的关系数量: {cat_count}')
print(f'总关系数量: {total}')

conn.close()
