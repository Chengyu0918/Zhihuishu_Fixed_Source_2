"""
导入新知识点到数据库
从 data/2/新增知识点(1).xlsx 的Sheet1读取数据
第一列：知识点名称
第二列：所属课程名称
第三列：层级
"""

import pandas as pd
import hashlib
from knowledge_graph.database import KnowledgeGraphDB
from knowledge_graph.schema import Node, Edge, LayerType, NodeType, RelationType


def generate_node_id(name):
    """生成节点ID（使用名称的hash）"""
    return hashlib.md5(name.encode('utf-8')).hexdigest()[:12]


def get_layer_type(layer_value):
    """根据层级值获取LayerType枚举"""
    layer_map = {
        1: LayerType.LAYER_ABILITY,
        2: LayerType.LAYER_PROBLEM,
        3: LayerType.LAYER_PROFESSIONAL,
        4: LayerType.LAYER_DISCIPLINE_BASE,
        5: LayerType.LAYER_ADVANCED_BASE,
        6: LayerType.LAYER_MATH_PHYSICS
    }
    return layer_map.get(layer_value, LayerType.LAYER_PROFESSIONAL)


def find_course_node(db, course_name):
    """查找课程节点"""
    results = db.search_nodes(course_name)
    for r in results:
        if r['name'] == course_name:
            return r
    return None


def main():
    db = KnowledgeGraphDB()
    
    # 读取Excel文件
    excel_path = "data/2/新增知识点(1).xlsx"
    print(f"读取文件: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path, sheet_name="Sheet1")
    except Exception as e:
        print(f"读取Excel失败: {e}")
        return
    
    print(f"读取到 {len(df)} 行数据")
    print(f"列名: {df.columns.tolist()}")
    
    # 统计
    success_nodes = 0
    skip_nodes = 0
    success_edges = 0
    skip_edges = 0
    errors = []
    
    # 用于去重
    added_nodes = set()
    
    for idx, row in df.iterrows():
        try:
            # 获取数据
            knowledge_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            course_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            layer_value = int(row.iloc[2]) if pd.notna(row.iloc[2]) else 3
            
            # 跳过空行
            if not knowledge_name:
                continue
            
            # 跳过重复
            if knowledge_name in added_nodes:
                print(f"  跳过重复知识点: {knowledge_name}")
                continue
            added_nodes.add(knowledge_name)
            
            # 检查知识点是否已存在
            existing = db.search_nodes(knowledge_name)
            if any(n['name'] == knowledge_name for n in existing):
                print(f"  知识点已存在: {knowledge_name}")
                skip_nodes += 1
                continue
            
            # 生成节点ID
            node_id = generate_node_id(knowledge_name)
            
            # 检查ID是否已存在，如果存在则添加后缀
            if db.node_exists(node_id):
                node_id = generate_node_id(knowledge_name + str(idx))
            
            # 创建节点
            layer_type = get_layer_type(layer_value)
            node = Node(
                id=node_id,
                name=knowledge_name,
                layer=layer_type,
                node_type=NodeType.LEAF,
                description=f"知识点，属于{course_name}课程"
            )
            
            if db.add_node(node):
                success_nodes += 1
                print(f"  添加知识点: {knowledge_name} (ID: {node_id}, 层级: {layer_value})")
            else:
                skip_nodes += 1
                errors.append(f"行{idx+2}: 添加节点失败 '{knowledge_name}'")
                continue
            
            # 查找课程节点并建立关系
            if course_name:
                course_node = find_course_node(db, course_name)
                if course_node:
                    # 创建层级关系：课程 -> 知识点
                    edge = Edge(
                        source_id=course_node['id'],
                        target_id=node_id,
                        relation_type=RelationType.HIERARCHY,
                        weight=1.0,
                        description=f"{course_name} -> {knowledge_name}"
                    )
                    if db.add_edge(edge):
                        success_edges += 1
                        print(f"    建立关系: {course_name} -> {knowledge_name}")
                    else:
                        skip_edges += 1
                else:
                    errors.append(f"行{idx+2}: 找不到课程节点 '{course_name}'")
                    skip_edges += 1
                    
        except Exception as e:
            errors.append(f"行{idx+2}: 处理出错 - {str(e)}")
    
    # 输出统计
    print("\n" + "=" * 60)
    print("导入完成统计")
    print("=" * 60)
    print(f"成功添加节点: {success_nodes}")
    print(f"跳过节点: {skip_nodes}")
    print(f"成功添加关系: {success_edges}")
    print(f"跳过关系: {skip_edges}")
    
    if errors:
        print(f"\n错误信息 ({len(errors)} 条):")
        for err in errors[:20]:  # 只显示前20条错误
            print(f"  {err}")
    
    # 验证
    stats = db.get_statistics()
    print(f"\n数据库当前状态:")
    print(f"  节点总数: {stats['total_nodes']}")
    print(f"  关系总数: {stats['total_edges']}")
    print(f"  按层级分布: {stats['nodes_by_layer']}")


if __name__ == "__main__":
    main()
