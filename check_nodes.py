"""查看现有节点的ID格式"""
from knowledge_graph.database import KnowledgeGraphDB

db = KnowledgeGraphDB()
nodes = db.get_all_nodes()[:30]

print("现有节点示例:")
for n in nodes:
    print(f"  ID: {n['id']}, Name: {n['name']}, Layer: {n['layer']}")

# 查看特定课程的节点
print("\n\n查找课程相关节点:")
courses = ["雷达原理与系统", "大数据导论", "人工智能引论", "电子战技术与应用"]
for course in courses:
    results = db.search_nodes(course)
    if results:
        for r in results[:3]:
            print(f"  ID: {r['id']}, Name: {r['name']}, Layer: {r['layer']}")
