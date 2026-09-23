"""
知识图谱数据库管理器
提供数据库连接、CRUD操作和查询功能
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

from .schema import (
    LayerType, NodeType, RelationType, 
    Node, Edge, CREATE_TABLES_SQL
)


class KnowledgeGraphDB:
    """知识图谱数据库管理类"""
    
    def __init__(self, db_path: str = 'database.db'):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
    
    # ==================== 节点操作 ====================
    
    def add_node(self, node: Node) -> bool:
        """
        添加节点
        
        Args:
            node: Node对象
            
        Returns:
            是否添加成功
        """
        with self.get_connection() as conn:
            try:
                conn.execute('''
                    INSERT INTO nodes (id, name, layer, node_type, description, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    node.id,
                    node.name,
                    node.layer.value,
                    node.node_type.value,
                    node.description,
                    json.dumps(node.metadata, ensure_ascii=False)
                ))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def add_nodes_batch(self, nodes: List[Node]) -> Tuple[int, int]:
        """
        批量添加节点
        
        Args:
            nodes: Node对象列表
            
        Returns:
            (成功数量, 失败数量)
        """
        success_count = 0
        fail_count = 0
        
        with self.get_connection() as conn:
            for node in nodes:
                try:
                    conn.execute('''
                        INSERT INTO nodes (id, name, layer, node_type, description, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        node.id,
                        node.name,
                        node.layer.value,
                        node.node_type.value,
                        node.description,
                        json.dumps(node.metadata, ensure_ascii=False)
                    ))
                    success_count += 1
                except sqlite3.IntegrityError:
                    fail_count += 1
        
        return success_count, fail_count
    
    def update_node(self, node_id: str, **kwargs) -> bool:
        """
        更新节点属性
        
        Args:
            node_id: 节点ID
            **kwargs: 要更新的字段
            
        Returns:
            是否更新成功
        """
        allowed_fields = {'name', 'layer', 'node_type', 'description', 'metadata'}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_fields:
            return False
        
        # 处理特殊字段
        if 'layer' in update_fields and isinstance(update_fields['layer'], LayerType):
            update_fields['layer'] = update_fields['layer'].value
        if 'node_type' in update_fields and isinstance(update_fields['node_type'], NodeType):
            update_fields['node_type'] = update_fields['node_type'].value
        if 'metadata' in update_fields and isinstance(update_fields['metadata'], dict):
            update_fields['metadata'] = json.dumps(update_fields['metadata'], ensure_ascii=False)
        
        update_fields['updated_at'] = datetime.now().isoformat()
        
        set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
        values = list(update_fields.values()) + [node_id]
        
        with self.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE nodes SET {set_clause} WHERE id = ?",
                values
            )
            return cursor.rowcount > 0
    
    def delete_node(self, node_id: str) -> bool:
        """
        删除节点（同时删除相关的边）
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否删除成功
        """
        with self.get_connection() as conn:
            cursor = conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            return cursor.rowcount > 0
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点字典或None
        """
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM nodes WHERE id = ?", 
                (node_id,)
            ).fetchone()
            
            if row:
                return self._row_to_node_dict(row)
            return None
    
    def get_nodes_by_layer(self, layer: int) -> List[Dict[str, Any]]:
        """
        按层级获取节点
        
        Args:
            layer: 层级值 (1-6)
            
        Returns:
            节点列表
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM nodes WHERE layer = ? ORDER BY name",
                (layer,)
            ).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def get_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """
        按节点类型获取节点
        
        Args:
            node_type: 节点类型 ('category', 'leaf', 'tag')
            
        Returns:
            节点列表
        """
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM nodes WHERE node_type = ? ORDER BY layer, name",
                (node_type,)
            ).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """获取所有节点"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM nodes ORDER BY layer, name"
            ).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def search_nodes(self, query: str, layer: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        搜索节点
        
        Args:
            query: 搜索关键词
            layer: 可选的层级过滤
            
        Returns:
            匹配的节点列表
        """
        with self.get_connection() as conn:
            if layer:
                rows = conn.execute(
                    "SELECT * FROM nodes WHERE name LIKE ? AND layer = ? ORDER BY name",
                    (f'%{query}%', layer)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM nodes WHERE name LIKE ? ORDER BY layer, name",
                    (f'%{query}%',)
                ).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def node_exists(self, node_id: str) -> bool:
        """检查节点是否存在"""
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM nodes WHERE id = ?",
                (node_id,)
            ).fetchone()
            return row is not None
    
    # ==================== 边/关系操作 ====================
    
    def add_edge(self, edge: Edge) -> bool:
        """
        添加边/关系
        
        Args:
            edge: Edge对象
            
        Returns:
            是否添加成功
        """
        with self.get_connection() as conn:
            try:
                conn.execute('''
                    INSERT INTO edges (source_id, target_id, relation_type, weight, description, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    edge.source_id,
                    edge.target_id,
                    edge.relation_type.value,
                    edge.weight,
                    edge.description,
                    json.dumps(edge.metadata, ensure_ascii=False)
                ))
                return True
            except sqlite3.IntegrityError:
                return False
    
    def add_edges_batch(self, edges: List[Edge]) -> Tuple[int, int]:
        """
        批量添加边
        
        Args:
            edges: Edge对象列表
            
        Returns:
            (成功数量, 失败数量)
        """
        success_count = 0
        fail_count = 0
        
        with self.get_connection() as conn:
            for edge in edges:
                try:
                    conn.execute('''
                        INSERT INTO edges (source_id, target_id, relation_type, weight, description, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        edge.source_id,
                        edge.target_id,
                        edge.relation_type.value,
                        edge.weight,
                        edge.description,
                        json.dumps(edge.metadata, ensure_ascii=False)
                    ))
                    success_count += 1
                except sqlite3.IntegrityError:
                    fail_count += 1
        
        return success_count, fail_count
    
    def delete_edge(self, source_id: str, target_id: str, relation_type: Optional[str] = None) -> bool:
        """
        删除边
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relation_type: 可选的关系类型
            
        Returns:
            是否删除成功
        """
        with self.get_connection() as conn:
            if relation_type:
                cursor = conn.execute(
                    "DELETE FROM edges WHERE source_id = ? AND target_id = ? AND relation_type = ?",
                    (source_id, target_id, relation_type)
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM edges WHERE source_id = ? AND target_id = ?",
                    (source_id, target_id)
                )
            return cursor.rowcount > 0
    
    def get_edges_from_node(self, node_id: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取从指定节点出发的所有边
        
        Args:
            node_id: 节点ID
            relation_type: 可选的关系类型过滤
            
        Returns:
            边列表
        """
        with self.get_connection() as conn:
            if relation_type:
                rows = conn.execute(
                    "SELECT * FROM edges WHERE source_id = ? AND relation_type = ?",
                    (node_id, relation_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM edges WHERE source_id = ?",
                    (node_id,)
                ).fetchall()
            return [self._row_to_edge_dict(row) for row in rows]
    
    def get_edges_to_node(self, node_id: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取指向指定节点的所有边
        
        Args:
            node_id: 节点ID
            relation_type: 可选的关系类型过滤
            
        Returns:
            边列表
        """
        with self.get_connection() as conn:
            if relation_type:
                rows = conn.execute(
                    "SELECT * FROM edges WHERE target_id = ? AND relation_type = ?",
                    (node_id, relation_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM edges WHERE target_id = ?",
                    (node_id,)
                ).fetchall()
            return [self._row_to_edge_dict(row) for row in rows]
    
    def get_all_edges(self) -> List[Dict[str, Any]]:
        """获取所有边"""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM edges").fetchall()
            return [self._row_to_edge_dict(row) for row in rows]
    
    # ==================== 图谱查询操作 ====================
    
    def get_children(self, node_id: str) -> List[Dict[str, Any]]:
        """获取子节点（层级关系）"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT n.* FROM nodes n
                JOIN edges e ON n.id = e.target_id
                WHERE e.source_id = ? AND e.relation_type = 'hierarchy'
                ORDER BY n.name
            ''', (node_id,)).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def get_parents(self, node_id: str) -> List[Dict[str, Any]]:
        """获取父节点（层级关系）"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT n.* FROM nodes n
                JOIN edges e ON n.id = e.source_id
                WHERE e.target_id = ? AND e.relation_type = 'hierarchy'
                ORDER BY n.layer, n.name
            ''', (node_id,)).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def get_peers(self, node_id: str) -> List[Dict[str, Any]]:
        """获取同层关联节点"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT DISTINCT n.* FROM nodes n
                JOIN edges e ON (n.id = e.target_id OR n.id = e.source_id)
                WHERE (e.source_id = ? OR e.target_id = ?) 
                AND e.relation_type = 'peer'
                AND n.id != ?
                ORDER BY n.name
            ''', (node_id, node_id, node_id)).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def get_cross_references(self, node_id: str) -> List[Dict[str, Any]]:
        """获取跨层关联节点"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT DISTINCT n.* FROM nodes n
                JOIN edges e ON (n.id = e.target_id OR n.id = e.source_id)
                WHERE (e.source_id = ? OR e.target_id = ?) 
                AND e.relation_type = 'cross'
                AND n.id != ?
                ORDER BY n.layer, n.name
            ''', (node_id, node_id, node_id)).fetchall()
            return [self._row_to_node_dict(row) for row in rows]
    
    def get_ancestors(self, node_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        递归获取所有祖先节点
        
        Args:
            node_id: 节点ID
            max_depth: 最大递归深度
            
        Returns:
            祖先节点列表
        """
        ancestors = []
        visited = set()
        
        def _get_ancestors_recursive(nid: str, depth: int):
            if depth > max_depth or nid in visited:
                return
            visited.add(nid)
            
            parents = self.get_parents(nid)
            for parent in parents:
                if parent['id'] not in visited:
                    ancestors.append(parent)
                    _get_ancestors_recursive(parent['id'], depth + 1)
        
        _get_ancestors_recursive(node_id, 0)
        return ancestors
    
    def get_descendants(self, node_id: str, max_depth: int = 10) -> List[Dict[str, Any]]:
        """
        递归获取所有后代节点
        
        Args:
            node_id: 节点ID
            max_depth: 最大递归深度
            
        Returns:
            后代节点列表
        """
        descendants = []
        visited = set()
        
        def _get_descendants_recursive(nid: str, depth: int):
            if depth > max_depth or nid in visited:
                return
            visited.add(nid)
            
            children = self.get_children(nid)
            for child in children:
                if child['id'] not in visited:
                    descendants.append(child)
                    _get_descendants_recursive(child['id'], depth + 1)
        
        _get_descendants_recursive(node_id, 0)
        return descendants
    
    def get_node_path(self, node_id: str) -> Dict[str, Any]:
        """
        获取节点的完整路径信息（上下游）
        
        Args:
            node_id: 节点ID
            
        Returns:
            包含当前节点、祖先、后代和相关边的字典
        """
        current = self.get_node(node_id)
        if not current:
            return {"error": "节点不存在"}
        
        ancestors = self.get_ancestors(node_id)
        descendants = self.get_descendants(node_id)
        peers = self.get_peers(node_id)
        cross_refs = self.get_cross_references(node_id)
        
        # 获取相关的边
        all_node_ids = {node_id}
        all_node_ids.update(n['id'] for n in ancestors)
        all_node_ids.update(n['id'] for n in descendants)
        
        related_edges = []
        with self.get_connection() as conn:
            for edge in conn.execute("SELECT * FROM edges").fetchall():
                if edge['source_id'] in all_node_ids and edge['target_id'] in all_node_ids:
                    related_edges.append(self._row_to_edge_dict(edge))
        
        return {
            "current": current,
            "ancestors": ancestors,
            "descendants": descendants,
            "peers": peers,
            "cross_references": cross_refs,
            "related_edges": related_edges
        }
    
    # ==================== 节点权重计算 ====================
    
    def get_node_weight(self, node_id: str) -> int:
        """
        获取单个节点的权重（被引用次数）
        权重 = 指向该节点的边数量 + 从该节点出发的边数量
        
        Args:
            node_id: 节点ID
            
        Returns:
            节点权重值
        """
        with self.get_connection() as conn:
            # 统计指向该节点的边（入度）
            in_degree = conn.execute(
                "SELECT COUNT(*) FROM edges WHERE target_id = ?",
                (node_id,)
            ).fetchone()[0]
            
            # 统计从该节点出发的边（出度）
            out_degree = conn.execute(
                "SELECT COUNT(*) FROM edges WHERE source_id = ?",
                (node_id,)
            ).fetchone()[0]
            
            return in_degree + out_degree
    
    def get_node_in_degree(self, node_id: str) -> int:
        """获取节点入度（被多少节点引用）"""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM edges WHERE target_id = ?",
                (node_id,)
            ).fetchone()[0]
    
    def get_node_out_degree(self, node_id: str) -> int:
        """获取节点出度（引用了多少节点）"""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM edges WHERE source_id = ?",
                (node_id,)
            ).fetchone()[0]
    
    def get_all_node_weights(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有节点的权重信息
        
        Returns:
            {node_id: {"in_degree": x, "out_degree": y, "total": z}}
        """
        with self.get_connection() as conn:
            # 统计入度
            in_degrees = {}
            for row in conn.execute(
                "SELECT target_id, COUNT(*) as cnt FROM edges GROUP BY target_id"
            ).fetchall():
                in_degrees[row['target_id']] = row['cnt']
            
            # 统计出度
            out_degrees = {}
            for row in conn.execute(
                "SELECT source_id, COUNT(*) as cnt FROM edges GROUP BY source_id"
            ).fetchall():
                out_degrees[row['source_id']] = row['cnt']
            
            # 获取所有节点ID
            all_nodes = conn.execute("SELECT id FROM nodes").fetchall()
            
            result = {}
            for row in all_nodes:
                node_id = row['id']
                in_deg = in_degrees.get(node_id, 0)
                out_deg = out_degrees.get(node_id, 0)
                result[node_id] = {
                    "in_degree": in_deg,
                    "out_degree": out_deg,
                    "total": in_deg + out_deg
                }
            
            return result
    
    def get_layer_node_weights(self, layer: int) -> List[Dict[str, Any]]:
        """
        获取指定层级所有节点的权重信息
        
        Args:
            layer: 层级 (1-6)
            
        Returns:
            节点列表，每个节点包含权重信息
        """
        nodes = self.get_nodes_by_layer(layer)
        weights = self.get_all_node_weights()
        
        for node in nodes:
            weight_info = weights.get(node['id'], {"in_degree": 0, "out_degree": 0, "total": 0})
            node['in_degree'] = weight_info['in_degree']
            node['out_degree'] = weight_info['out_degree']
            node['weight'] = weight_info['total']
        
        # 按权重降序排序
        nodes.sort(key=lambda x: x['weight'], reverse=True)
        return nodes
    
    def get_top_weighted_nodes(self, limit: int = 20, layer: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取权重最高的节点
        
        Args:
            limit: 返回数量限制
            layer: 可选的层级过滤
            
        Returns:
            按权重降序排列的节点列表
        """
        if layer:
            nodes = self.get_nodes_by_layer(layer)
        else:
            nodes = self.get_all_nodes()
        
        weights = self.get_all_node_weights()
        
        for node in nodes:
            weight_info = weights.get(node['id'], {"in_degree": 0, "out_degree": 0, "total": 0})
            node['in_degree'] = weight_info['in_degree']
            node['out_degree'] = weight_info['out_degree']
            node['weight'] = weight_info['total']
        
        # 按权重降序排序
        nodes.sort(key=lambda x: x['weight'], reverse=True)
        return nodes[:limit]
    
    def calculate_node_size(self, node_id: str, min_size: float = 5.0, max_size: float = 50.0) -> float:
        """
        计算节点的可视化大小（基于权重）
        
        Args:
            node_id: 节点ID
            min_size: 最小尺寸
            max_size: 最大尺寸
            
        Returns:
            节点大小值
        """
        weight = self.get_node_weight(node_id)
        
        # 获取所有节点的最大权重用于归一化
        all_weights = self.get_all_node_weights()
        max_weight = max((w['total'] for w in all_weights.values()), default=1)
        
        if max_weight == 0:
            return min_size
        
        # 线性映射到 [min_size, max_size]
        normalized = weight / max_weight
        return min_size + normalized * (max_size - min_size)
    
    def get_all_node_sizes(self, min_size: float = 5.0, max_size: float = 50.0) -> Dict[str, float]:
        """
        计算所有节点的可视化大小
        
        Args:
            min_size: 最小尺寸
            max_size: 最大尺寸
            
        Returns:
            {node_id: size}
        """
        all_weights = self.get_all_node_weights()
        max_weight = max((w['total'] for w in all_weights.values()), default=1)
        
        if max_weight == 0:
            return {node_id: min_size for node_id in all_weights.keys()}
        
        result = {}
        for node_id, weight_info in all_weights.items():
            normalized = weight_info['total'] / max_weight
            result[node_id] = min_size + normalized * (max_size - min_size)
        
        return result
    
    # ==================== 统计和元数据 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图谱统计信息"""
        with self.get_connection() as conn:
            total_nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            total_edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            
            # 按层级统计节点
            layer_stats = {}
            for row in conn.execute(
                "SELECT layer, COUNT(*) as count FROM nodes GROUP BY layer ORDER BY layer"
            ).fetchall():
                layer_stats[LayerType.get_name(row['layer'])] = row['count']
            
            # 按类型统计节点
            type_stats = {}
            for row in conn.execute(
                "SELECT node_type, COUNT(*) as count FROM nodes GROUP BY node_type"
            ).fetchall():
                type_stats[row['node_type']] = row['count']
            
            # 按关系类型统计边
            relation_stats = {}
            for row in conn.execute(
                "SELECT relation_type, COUNT(*) as count FROM edges GROUP BY relation_type"
            ).fetchall():
                relation_stats[row['relation_type']] = row['count']
            
            return {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "nodes_by_layer": layer_stats,
                "nodes_by_type": type_stats,
                "edges_by_relation": relation_stats
            }
    
    def get_layer_definitions(self) -> List[Dict[str, Any]]:
        """获取层级定义"""
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM layer_definitions ORDER BY layer_id"
            ).fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 导出功能 ====================
    
    def export_graph_data(self, min_size: float = 5.0, max_size: float = 50.0) -> Dict[str, Any]:
        """
        导出完整的图谱数据（用于前端可视化）
        包含节点大小（基于边的引用次数计算）
        
        Args:
            min_size: 节点最小尺寸
            max_size: 节点最大尺寸
            
        Returns:
            包含nodes和links的字典
        """
        nodes = self.get_all_nodes()
        edges = self.get_all_edges()
        
        # 获取所有节点的权重和大小
        all_weights = self.get_all_node_weights()
        node_sizes = self.get_all_node_sizes(min_size, max_size)
        
        return {
            "nodes": [{
                "id": n['id'],
                "name": n['name'],
                "group": n['layer'],
                "layer_name": n['layer_name'],
                "node_type": n['node_type'],
                "description": n['description'],
                "in_degree": all_weights.get(n['id'], {}).get('in_degree', 0),
                "out_degree": all_weights.get(n['id'], {}).get('out_degree', 0),
                "weight": all_weights.get(n['id'], {}).get('total', 0),
                "size": node_sizes.get(n['id'], min_size)
            } for n in nodes],
            "links": [{
                "source": e['source'],
                "target": e['target'],
                "relation_type": e['relation_type'],
                "weight": e['weight']
            } for e in edges]
        }
    
    def export_to_json(self, filepath: str):
        """导出图谱数据到JSON文件"""
        import json
        data = {
            "nodes": self.get_all_nodes(),
            "edges": self.get_all_edges(),
            "layer_definitions": self.get_layer_definitions(),
            "statistics": self.get_statistics(),
            "exported_at": datetime.now().isoformat()
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ==================== 辅助方法 ====================
    
    def _row_to_node_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为节点字典"""
        return {
            "id": row['id'],
            "name": row['name'],
            "layer": row['layer'],
            "layer_name": LayerType.get_name(row['layer']),
            "node_type": row['node_type'],
            "description": row['description'],
            "metadata": json.loads(row['metadata']) if row['metadata'] else {},
            "created_at": row['created_at'],
            "updated_at": row['updated_at']
        }
    
    def _row_to_edge_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """将数据库行转换为边字典"""
        return {
            "id": row['id'],
            "source": row['source_id'],
            "target": row['target_id'],
            "relation_type": row['relation_type'],
            "weight": row['weight'],
            "description": row['description'],
            "metadata": json.loads(row['metadata']) if row['metadata'] else {},
            "created_at": row['created_at']
        }
    
    def clear_all_data(self):
        """清空所有数据（谨慎使用）"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM edges")
            conn.execute("DELETE FROM nodes")
