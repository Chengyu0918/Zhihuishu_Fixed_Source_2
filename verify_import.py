"""验证新知识点导入结果"""
from knowledge_graph.database import KnowledgeGraphDB

db = KnowledgeGraphDB()

# 验证新增的知识点
print("=" * 60)
print("验证新增知识点")
print("=" * 60)

new_knowledge = [
    "MTI/MTD",
    "智能超表面辅助测向",
    "RGPO干扰建模",
    "张量分解多维特征",
    "TDOA定位"
]

for name in new_knowledge:
    nodes = db.search_nodes(name)
    if nodes:
        n = nodes[0]
        print(f"\n知识点: {n['name']}")
        print(f"  ID: {n['id']}")
        print(f"  层级: {n['layer']}")
        print(f"  描述: {n['description']}")
        
        # 查找父节点关系
        parents = db.get_parents(n['id'])
        if parents:
            print(f"  父节点: {[p['name'] for p in parents]}")
    else:
        print(f"\n未找到: {name}")

# 统计
print("\n" + "=" * 60)
print("数据库统计")
print("=" * 60)
stats = db.get_statistics()
print(f"节点总数: {stats['total_nodes']}")
print(f"关系总数: {stats['total_edges']}")
print(f"按层级分布: {stats['nodes_by_layer']}")
print(f"按关系类型分布: {stats['edges_by_relation']}")
