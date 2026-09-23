#!/usr/bin/env python3
"""
列出每层的所有节点信息，方便配置自定义位置
输出格式：索引、节点ID、节点名称
"""

import sqlite3
import os

def list_nodes_by_layer():
    db_path = 'd:/project/1/database.db'
    if not os.path.exists(db_path):
        print(f"错误：数据库文件 {db_path} 不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取所有层级 - 从 layer 字段提取层级信息
    # layer 字段格式可能是 "1", "2" 等数字，或者是层级名称
    cursor.execute("""
        SELECT DISTINCT layer
        FROM nodes 
        ORDER BY layer
    """)
    layers_raw = cursor.fetchall()
    
    # 层级名称映射
    layer_names = {
        '1': '能力层',
        '2': '问题层', 
        '3': '专业课',
        '4': '学科基础',
        '5': '高阶基础',
        '6': '数理基础'
    }
    
    # 处理层级数据
    layers = []
    for (layer,) in layers_raw:
        try:
            layer_id = int(layer)
            layer_name = layer_names.get(str(layer_id), layer)
        except (ValueError, TypeError):
            # 如果 layer 不是数字，尝试从名称映射
            layer_id = None
            for lid, lname in layer_names.items():
                if lname == layer:
                    layer_id = int(lid)
                    break
            if layer_id is None:
                layer_id = 0
            layer_name = layer
        layers.append((layer_id, layer_name, layer))
    
    # 按层级ID排序
    layers.sort(key=lambda x: x[0])
    
    print("=" * 80)
    print("节点位置自定义配置参考")
    print("=" * 80)
    print()
    print("【使用方法】")
    print("在 static/js/graph.js 的 nodePositionConfig 中配置节点位置")
    print("可以使用索引、节点名称或节点ID来指定节点")
    print()
    print("【坐标系说明】")
    print("  x: 水平方向（左负右正）")
    print("  y: 垂直方向（下负上正）")
    print("  z: 深度方向（前负后正）")
    print()
    
    for layer_id, layer_name, layer_raw in layers:
        # 获取该层的所有节点
        cursor.execute("""
            SELECT id, name, color
            FROM nodes 
            WHERE layer = ?
            ORDER BY id
        """, (layer_raw,))
        nodes = cursor.fetchall()
        
        print("=" * 80)
        print(f"第 {layer_id} 层 - {layer_name} ({len(nodes)} 个节点)")
        print("=" * 80)
        
        # 默认 y 值
        y_values = {1: 300, 2: 180, 3: 60, 4: -60, 5: -180, 6: -300}
        default_y = y_values.get(layer_id, 0)
        print(f"默认 y 值: {default_y}")
        print()
        
        print("配置示例（复制到 nodePositionConfig[{0}] 中）:".format(layer_id))
        print("-" * 60)
        
        for idx, (node_id, name, color) in enumerate(nodes):
            # 显示节点信息
            print(f"// 索引 {idx}: {name}")
            print(f"// {idx}: {{ x: 0, z: 0 }},")
            print(f"// \"{name}\": {{ x: 0, z: 0 }},")
            print()
        
        print()
    
    # 生成完整的配置模板
    print("=" * 80)
    print("完整配置模板（可直接复制到 graph.js）")
    print("=" * 80)
    print()
    print("const nodePositionConfig = {")
    
    for layer_id, layer_name, layer_raw in layers:
        cursor.execute("""
            SELECT id, name
            FROM nodes 
            WHERE layer = ?
            ORDER BY id
        """, (layer_raw,))
        nodes = cursor.fetchall()
        
        print(f"    // 第 {layer_id} 层 - {layer_name}")
        print(f"    {layer_id}: {{")
        
        for idx, (node_id, name) in enumerate(nodes):
            # 生成默认圆形布局的坐标（仅供参考）
            import math
            if layer_id == 1:
                radius = 300
            else:
                radius = 100  # 其他层使用较小半径作为示例
            
            angle = (2 * math.pi * idx) / max(len(nodes), 1)
            x = int(radius * math.cos(angle))
            z = int(radius * math.sin(angle))
            
            # 转义名称中的特殊字符
            safe_name = name.replace('"', '\\"')
            print(f'        // {idx}: {{ x: {x}, z: {z} }},  // {safe_name}')
        
        print("    },")
        print()
    
    print("};")
    
    conn.close()

if __name__ == '__main__':
    list_nodes_by_layer()
