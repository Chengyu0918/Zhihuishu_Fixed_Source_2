"""
知识图谱数据导入器
支持从 JSON、YAML、CSV 格式导入数据
"""

import json
import csv
import os
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from .schema import LayerType, NodeType, RelationType, Node, Edge
from .database import KnowledgeGraphDB


class DataImporter:
    """数据导入器类"""
    
    def __init__(self, db: KnowledgeGraphDB):
        """
        初始化导入器
        
        Args:
            db: KnowledgeGraphDB实例
        """
        self.db = db
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def import_from_json(self, filepath: str, clear_existing: bool = False) -> Dict[str, Any]:
        """
        从JSON文件导入数据
        
        Args:
            filepath: JSON文件路径
            clear_existing: 是否清空现有数据
            
        Returns:
            导入结果统计
        """
        self.errors = []
        self.warnings = []
        
        if not os.path.exists(filepath):
            return {"success": False, "error": f"文件不存在: {filepath}"}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"JSON解析错误: {str(e)}"}
        
        return self._import_data(data, filepath, clear_existing)
    
    def import_from_yaml(self, filepath: str, clear_existing: bool = False) -> Dict[str, Any]:
        """
        从YAML文件导入数据
        
        Args:
            filepath: YAML文件路径
            clear_existing: 是否清空现有数据
            
        Returns:
            导入结果统计
        """
        self.errors = []
        self.warnings = []
        
        try:
            import yaml
        except ImportError:
            return {"success": False, "error": "需要安装 PyYAML: pip install pyyaml"}
        
        if not os.path.exists(filepath):
            return {"success": False, "error": f"文件不存在: {filepath}"}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return {"success": False, "error": f"YAML解析错误: {str(e)}"}
        
        return self._import_data(data, filepath, clear_existing)
    
    def import_from_dict(self, data: Dict[str, Any], clear_existing: bool = False) -> Dict[str, Any]:
        """
        从字典导入数据
        
        Args:
            data: 数据字典
            clear_existing: 是否清空现有数据
            
        Returns:
            导入结果统计
        """
        self.errors = []
        self.warnings = []
        return self._import_data(data, "dict_import", clear_existing)
    
    def _import_data(self, data: Dict[str, Any], source: str, clear_existing: bool) -> Dict[str, Any]:
        """
        内部导入方法
        
        Args:
            data: 数据字典
            source: 数据来源标识
            clear_existing: 是否清空现有数据
            
        Returns:
            导入结果统计
        """
        if clear_existing:
            self.db.clear_all_data()
        
        nodes_added = 0
        nodes_updated = 0
        edges_added = 0
        
        # 导入节点
        if 'nodes' in data:
            for node_data in data['nodes']:
                result = self._import_node(node_data)
                if result == 'added':
                    nodes_added += 1
                elif result == 'updated':
                    nodes_updated += 1
        
        # 导入边/关系
        if 'edges' in data:
            for edge_data in data['edges']:
                if self._import_edge(edge_data):
                    edges_added += 1
        
        # 兼容旧格式的 links
        if 'links' in data:
            for link_data in data['links']:
                if self._import_edge(link_data):
                    edges_added += 1
        
        # 处理树状结构（如果存在）
        if 'tree' in data:
            tree_nodes, tree_edges = self._parse_tree_structure(data['tree'])
            for node_data in tree_nodes:
                result = self._import_node(node_data)
                if result == 'added':
                    nodes_added += 1
                elif result == 'updated':
                    nodes_updated += 1
            for edge_data in tree_edges:
                if self._import_edge(edge_data):
                    edges_added += 1
        
        # 记录导入历史
        self._record_import_history(source, nodes_added, edges_added, nodes_updated)
        
        return {
            "success": True,
            "nodes_added": nodes_added,
            "nodes_updated": nodes_updated,
            "edges_added": edges_added,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def _import_node(self, node_data: Dict[str, Any]) -> Optional[str]:
        """
        导入单个节点
        
        Args:
            node_data: 节点数据字典
            
        Returns:
            'added', 'updated', 或 None
        """
        try:
            # 必需字段
            node_id = node_data.get('id')
            name = node_data.get('name')
            
            if not node_id or not name:
                self.errors.append(f"节点缺少必需字段 id 或 name: {node_data}")
                return None
            
            # 解析层级
            layer_value = node_data.get('layer', node_data.get('group', node_data.get('group_level', 3)))
            if isinstance(layer_value, str):
                layer_value = self._parse_layer_string(layer_value)
            layer = LayerType(layer_value) if 1 <= layer_value <= 6 else LayerType.LAYER_PROFESSIONAL
            
            # 解析节点类型
            node_type_value = node_data.get('node_type', 'leaf')
            if layer.value in [1, 2]:
                node_type = NodeType.TAG
            elif node_data.get('children') or node_data.get('is_category'):
                node_type = NodeType.CATEGORY
            else:
                try:
                    node_type = NodeType(node_type_value)
                except ValueError:
                    node_type = NodeType.LEAF
            
            # 检查节点是否存在
            if self.db.node_exists(node_id):
                # 更新现有节点
                self.db.update_node(
                    node_id,
                    name=name,
                    layer=layer,
                    node_type=node_type,
                    description=node_data.get('description', ''),
                    metadata=node_data.get('metadata', {})
                )
                return 'updated'
            else:
                # 创建新节点
                node = Node(
                    id=node_id,
                    name=name,
                    layer=layer,
                    node_type=node_type,
                    description=node_data.get('description', ''),
                    metadata=node_data.get('metadata', {})
                )
                if self.db.add_node(node):
                    return 'added'
                else:
                    self.errors.append(f"添加节点失败: {node_id}")
                    return None
                    
        except Exception as e:
            self.errors.append(f"导入节点时出错: {str(e)}, 数据: {node_data}")
            return None
    
    def _import_edge(self, edge_data: Dict[str, Any]) -> bool:
        """
        导入单条边
        
        Args:
            edge_data: 边数据字典
            
        Returns:
            是否导入成功
        """
        try:
            # 支持多种字段名
            source_id = edge_data.get('source_id', edge_data.get('source', edge_data.get('from')))
            target_id = edge_data.get('target_id', edge_data.get('target', edge_data.get('to')))
            
            if not source_id or not target_id:
                self.errors.append(f"边缺少必需字段 source 或 target: {edge_data}")
                return False
            
            # 检查节点是否存在
            if not self.db.node_exists(source_id):
                self.warnings.append(f"源节点不存在: {source_id}")
                return False
            if not self.db.node_exists(target_id):
                self.warnings.append(f"目标节点不存在: {target_id}")
                return False
            
            # 解析关系类型
            relation_type_value = edge_data.get('relation_type', edge_data.get('type', 'hierarchy'))
            try:
                relation_type = RelationType(relation_type_value)
            except ValueError:
                relation_type = RelationType.HIERARCHY
            
            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=relation_type,
                weight=edge_data.get('weight', 1.0),
                description=edge_data.get('description', ''),
                metadata=edge_data.get('metadata', {})
            )
            
            return self.db.add_edge(edge)
            
        except Exception as e:
            self.errors.append(f"导入边时出错: {str(e)}, 数据: {edge_data}")
            return False
    
    def _parse_tree_structure(self, tree: Dict[str, Any], parent_id: str = None, layer: int = 1) -> Tuple[List[Dict], List[Dict]]:
        """
        解析树状结构数据
        
        Args:
            tree: 树状结构字典
            parent_id: 父节点ID
            layer: 当前层级
            
        Returns:
            (节点列表, 边列表)
        """
        nodes = []
        edges = []
        
        node_id = tree.get('id')
        if not node_id:
            return nodes, edges
        
        # 添加当前节点
        nodes.append({
            'id': node_id,
            'name': tree.get('name', node_id),
            'layer': tree.get('layer', layer),
            'node_type': 'category' if tree.get('children') else 'leaf',
            'description': tree.get('description', ''),
            'metadata': tree.get('metadata', {})
        })
        
        # 添加与父节点的边
        if parent_id:
            edges.append({
                'source_id': parent_id,
                'target_id': node_id,
                'relation_type': 'hierarchy'
            })
        
        # 递归处理子节点
        children = tree.get('children', [])
        for child in children:
            child_nodes, child_edges = self._parse_tree_structure(
                child, 
                node_id, 
                layer + 1 if layer < 6 else 6
            )
            nodes.extend(child_nodes)
            edges.extend(child_edges)
        
        return nodes, edges
    
    def _parse_layer_string(self, layer_str: str) -> int:
        """
        解析层级字符串
        
        Args:
            layer_str: 层级字符串
            
        Returns:
            层级数值
        """
        layer_map = {
            'ability': 1, '能力层': 1, 'LAYER_ABILITY': 1,
            'problem': 2, '问题层': 2, 'LAYER_PROBLEM': 2,
            'professional': 3, '专业课': 3, 'LAYER_PROFESSIONAL': 3,
            'discipline_base': 4, '学科基础': 4, 'LAYER_DISCIPLINE_BASE': 4,
            'advanced_base': 5, '高阶基础': 5, 'LAYER_ADVANCED_BASE': 5,
            'math_physics': 6, '数理基础': 6, 'LAYER_MATH_PHYSICS': 6
        }
        return layer_map.get(layer_str.lower(), 3)
    
    def _record_import_history(self, filename: str, nodes_added: int, edges_added: int, nodes_updated: int):
        """记录导入历史"""
        with self.db.get_connection() as conn:
            conn.execute('''
                INSERT INTO import_history (filename, import_type, nodes_added, edges_added, nodes_updated, errors)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                filename,
                'json' if filename.endswith('.json') else 'yaml' if filename.endswith(('.yaml', '.yml')) else 'other',
                nodes_added,
                edges_added,
                nodes_updated,
                json.dumps(self.errors, ensure_ascii=False)
            ))
    
    def get_import_history(self) -> List[Dict[str, Any]]:
        """获取导入历史记录"""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM import_history ORDER BY imported_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 便捷导入方法 ====================
    
    def import_simple_hierarchy(self, hierarchy_data: List[Dict[str, Any]], layer: int = 3) -> Dict[str, Any]:
        """
        导入简单的层级数据
        
        Args:
            hierarchy_data: 层级数据列表，每项包含 {id, name, children: [...]}
            layer: 起始层级
            
        Returns:
            导入结果
        """
        nodes = []
        edges = []
        
        def process_item(item: Dict, parent_id: str = None, current_layer: int = layer):
            node_id = item.get('id')
            if not node_id:
                return
            
            nodes.append({
                'id': node_id,
                'name': item.get('name', node_id),
                'layer': current_layer,
                'node_type': 'category' if item.get('children') else 'leaf',
                'description': item.get('description', '')
            })
            
            if parent_id:
                edges.append({
                    'source_id': parent_id,
                    'target_id': node_id,
                    'relation_type': 'hierarchy'
                })
            
            for child in item.get('children', []):
                process_item(child, node_id, min(current_layer + 1, 6))
        
        for item in hierarchy_data:
            process_item(item)
        
        return self.import_from_dict({'nodes': nodes, 'edges': edges})
    
    def import_knowledge_points(self, category_id: str, knowledge_points: List[Dict[str, Any]], layer: int = 4) -> Dict[str, Any]:
        """
        向指定大类导入知识点
        
        Args:
            category_id: 大类节点ID
            knowledge_points: 知识点列表
            layer: 知识点层级
            
        Returns:
            导入结果
        """
        if not self.db.node_exists(category_id):
            return {"success": False, "error": f"大类节点不存在: {category_id}"}
        
        nodes = []
        edges = []
        
        for kp in knowledge_points:
            kp_id = kp.get('id')
            if not kp_id:
                continue
            
            nodes.append({
                'id': kp_id,
                'name': kp.get('name', kp_id),
                'layer': layer,
                'node_type': 'leaf',
                'description': kp.get('description', ''),
                'metadata': kp.get('metadata', {})
            })
            
            edges.append({
                'source_id': category_id,
                'target_id': kp_id,
                'relation_type': 'hierarchy'
            })
            
            # 处理同层关联
            for peer_id in kp.get('peers', []):
                edges.append({
                    'source_id': kp_id,
                    'target_id': peer_id,
                    'relation_type': 'peer'
                })
            
            # 处理跨层关联
            for cross_id in kp.get('cross_refs', []):
                edges.append({
                    'source_id': kp_id,
                    'target_id': cross_id,
                    'relation_type': 'cross'
                })
        
        return self.import_from_dict({'nodes': nodes, 'edges': edges})
    
    def add_cross_layer_mapping(self, mappings: List[Tuple[str, str]]) -> int:
        """
        批量添加跨层映射关系
        
        Args:
            mappings: (源节点ID, 目标节点ID) 元组列表
            
        Returns:
            成功添加的数量
        """
        count = 0
        for source_id, target_id in mappings:
            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                relation_type=RelationType.CROSS_REFERENCE
            )
            if self.db.add_edge(edge):
                count += 1
        return count
    
    def add_peer_relations(self, relations: List[Tuple[str, str]]) -> int:
        """
        批量添加同层关联关系
        
        Args:
            relations: (节点1 ID, 节点2 ID) 元组列表
            
        Returns:
            成功添加的数量
        """
        count = 0
        for node1_id, node2_id in relations:
            edge = Edge(
                source_id=node1_id,
                target_id=node2_id,
                relation_type=RelationType.PEER
            )
            if self.db.add_edge(edge):
                count += 1
        return count


# ==================== 示例数据生成器 ====================

def generate_sample_data() -> Dict[str, Any]:
    """
    生成示例数据结构
    
    Returns:
        示例数据字典
    """
    return {
        "nodes": [
            # 能力层 (Layer 1)
            {"id": "ability_analysis", "name": "分析能力", "layer": 1, "node_type": "tag", "description": "分析和解决问题的能力"},
            {"id": "ability_design", "name": "设计能力", "layer": 1, "node_type": "tag", "description": "系统设计和架构能力"},
            {"id": "ability_implement", "name": "实现能力", "layer": 1, "node_type": "tag", "description": "编码和实现能力"},
            
            # 问题层 (Layer 2)
            {"id": "problem_signal", "name": "信号处理问题", "layer": 2, "node_type": "tag", "description": "信号分析与处理相关问题"},
            {"id": "problem_system", "name": "系统分析问题", "layer": 2, "node_type": "tag", "description": "系统建模与分析相关问题"},
            {"id": "problem_comm", "name": "通信系统问题", "layer": 2, "node_type": "tag", "description": "通信系统设计相关问题"},
            
            # 专业课 (Layer 3)
            {"id": "course_signals", "name": "信号与系统", "layer": 3, "node_type": "category", "description": "信号与系统课程"},
            {"id": "course_comm", "name": "通信原理", "layer": 3, "node_type": "category", "description": "通信原理课程"},
            {"id": "course_dsp", "name": "数字信号处理", "layer": 3, "node_type": "category", "description": "数字信号处理课程"},
            
            # 学科基础 (Layer 4) - 大类
            {"id": "cat_fourier", "name": "傅里叶分析", "layer": 4, "node_type": "category", "description": "傅里叶变换相关知识"},
            {"id": "cat_laplace", "name": "拉普拉斯变换", "layer": 4, "node_type": "category", "description": "拉普拉斯变换相关知识"},
            {"id": "cat_convolution", "name": "卷积理论", "layer": 4, "node_type": "category", "description": "卷积运算相关知识"},
            {"id": "cat_modulation", "name": "调制技术", "layer": 4, "node_type": "category", "description": "信号调制相关知识"},
            
            # 学科基础 (Layer 4) - 知识点
            {"id": "kp_ft_def", "name": "傅里叶变换定义", "layer": 4, "node_type": "leaf", "description": "连续时间傅里叶变换的定义"},
            {"id": "kp_ft_prop", "name": "傅里叶变换性质", "layer": 4, "node_type": "leaf", "description": "时移、频移、卷积等性质"},
            {"id": "kp_lt_def", "name": "拉普拉斯变换定义", "layer": 4, "node_type": "leaf", "description": "单边拉普拉斯变换定义"},
            {"id": "kp_lt_prop", "name": "拉普拉斯变换性质", "layer": 4, "node_type": "leaf", "description": "微分、积分、初值终值定理"},
            {"id": "kp_conv_def", "name": "卷积定义", "layer": 4, "node_type": "leaf", "description": "连续和离散卷积的定义"},
            {"id": "kp_conv_calc", "name": "卷积计算方法", "layer": 4, "node_type": "leaf", "description": "图解法、解析法"},
            
            # 高阶基础 (Layer 5)
            {"id": "adv_complex", "name": "复变函数", "layer": 5, "node_type": "category", "description": "复变函数基础"},
            {"id": "adv_integral", "name": "积分变换", "layer": 5, "node_type": "category", "description": "积分变换理论"},
            {"id": "kp_complex_int", "name": "复积分", "layer": 5, "node_type": "leaf", "description": "复变函数的积分"},
            {"id": "kp_residue", "name": "留数定理", "layer": 5, "node_type": "leaf", "description": "留数定理及应用"},
            
            # 数理基础 (Layer 6)
            {"id": "math_calculus", "name": "微积分", "layer": 6, "node_type": "category", "description": "微积分基础"},
            {"id": "math_linear", "name": "线性代数", "layer": 6, "node_type": "category", "description": "线性代数基础"},
            {"id": "kp_integral", "name": "定积分", "layer": 6, "node_type": "leaf", "description": "定积分的计算"},
            {"id": "kp_series", "name": "级数", "layer": 6, "node_type": "leaf", "description": "无穷级数"},
            {"id": "kp_matrix", "name": "矩阵运算", "layer": 6, "node_type": "leaf", "description": "矩阵的基本运算"}
        ],
        "edges": [
            # 层级关系 (hierarchy)
            {"source": "course_signals", "target": "cat_fourier", "relation_type": "hierarchy"},
            {"source": "course_signals", "target": "cat_laplace", "relation_type": "hierarchy"},
            {"source": "course_signals", "target": "cat_convolution", "relation_type": "hierarchy"},
            {"source": "course_comm", "target": "cat_modulation", "relation_type": "hierarchy"},
            
            {"source": "cat_fourier", "target": "kp_ft_def", "relation_type": "hierarchy"},
            {"source": "cat_fourier", "target": "kp_ft_prop", "relation_type": "hierarchy"},
            {"source": "cat_laplace", "target": "kp_lt_def", "relation_type": "hierarchy"},
            {"source": "cat_laplace", "target": "kp_lt_prop", "relation_type": "hierarchy"},
            {"source": "cat_convolution", "target": "kp_conv_def", "relation_type": "hierarchy"},
            {"source": "cat_convolution", "target": "kp_conv_calc", "relation_type": "hierarchy"},
            
            {"source": "adv_complex", "target": "kp_complex_int", "relation_type": "hierarchy"},
            {"source": "adv_complex", "target": "kp_residue", "relation_type": "hierarchy"},
            {"source": "math_calculus", "target": "kp_integral", "relation_type": "hierarchy"},
            {"source": "math_calculus", "target": "kp_series", "relation_type": "hierarchy"},
            {"source": "math_linear", "target": "kp_matrix", "relation_type": "hierarchy"},
            
            # 跨层关联 (cross) - 能力层映射
            {"source": "ability_analysis", "target": "kp_ft_prop", "relation_type": "cross"},
            {"source": "ability_analysis", "target": "kp_lt_prop", "relation_type": "cross"},
            {"source": "ability_design", "target": "cat_modulation", "relation_type": "cross"},
            {"source": "ability_implement", "target": "kp_conv_calc", "relation_type": "cross"},
            
            # 跨层关联 (cross) - 问题层映射
            {"source": "problem_signal", "target": "cat_fourier", "relation_type": "cross"},
            {"source": "problem_signal", "target": "cat_laplace", "relation_type": "cross"},
            {"source": "problem_system", "target": "cat_convolution", "relation_type": "cross"},
            {"source": "problem_comm", "target": "cat_modulation", "relation_type": "cross"},
            
            # 跨层关联 (cross) - 知识依赖
            {"source": "kp_ft_def", "target": "kp_integral", "relation_type": "cross"},
            {"source": "kp_lt_def", "target": "kp_complex_int", "relation_type": "cross"},
            {"source": "kp_residue", "target": "kp_lt_prop", "relation_type": "cross"},
            
            # 同层关联 (peer)
            {"source": "kp_ft_def", "target": "kp_lt_def", "relation_type": "peer"},
            {"source": "kp_ft_prop", "target": "kp_lt_prop", "relation_type": "peer"},
            {"source": "kp_conv_def", "target": "kp_ft_prop", "relation_type": "peer"},
            {"source": "course_signals", "target": "course_dsp", "relation_type": "peer"},
            
            # 前置依赖 (prereq)
            {"source": "kp_integral", "target": "kp_ft_def", "relation_type": "prereq"},
            {"source": "kp_complex_int", "target": "kp_lt_def", "relation_type": "prereq"},
            {"source": "kp_series", "target": "kp_ft_def", "relation_type": "prereq"}
        ]
    }


def create_sample_json_file(filepath: str = 'sample_knowledge_graph.json'):
    """创建示例JSON文件"""
    data = generate_sample_data()
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"示例数据已保存到: {filepath}")
    return filepath
