import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

print('=== 高权重节点 (前15个) ===')
c.execute('SELECT name, weight, layer FROM nodes WHERE weight IS NOT NULL AND weight > 0 ORDER BY weight DESC LIMIT 15')
for row in c.fetchall():
    print(f'{row[0]}: weight={row[1]}, layer={row[2]}')

print('\n=== 检波相关节点 ===')
c.execute('SELECT name, weight, layer FROM nodes WHERE name LIKE "%检波%"')
for row in c.fetchall():
    print(f'{row[0]}: weight={row[1]}, layer={row[2]}')

print('\n=== 权重统计 ===')
c.execute('SELECT COUNT(*) FROM nodes WHERE weight IS NOT NULL AND weight > 0')
print(f'有权重的节点数: {c.fetchone()[0]}')

c.execute('SELECT COUNT(*) FROM nodes WHERE weight IS NULL OR weight = 0')
print(f'无权重的节点数: {c.fetchone()[0]}')

c.execute('SELECT MAX(weight), MIN(weight), AVG(weight) FROM nodes WHERE weight > 0')
row = c.fetchone()
print(f'最大权重: {row[0]}, 最小权重: {row[1]}, 平均权重: {row[2]:.2f}')

conn.close()
