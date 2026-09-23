"""
知识图谱数据库模式定义
定义节点类型、关系类型和数据库表结构
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


class LayerType(Enum):
    """六层级枚举类型"""
    LAYER_ABILITY = 1        # 能力层 - 顶层标签
    LAYER_PROBLEM = 2        # 问题层 - 顶层标签
    LAYER_PROFESSIONAL = 3   # 专业课
    LAYER_DISCIPLINE_BASE = 4  # 学科基础
    LAYER_ADVANCED_BASE = 5  # 高阶基础
    LAYER_MATH_PHYSICS = 6   # 数理基础
    
    @classmethod
    def get_name(cls, value: int) -> str:
        """获取层级的中文名称"""
        names = {
            1: "能力层",
            2: "问题层", 
            3: "专业课",
            4: "学科基础",
            5: "高阶基础",
            6: "数理基础"
        }
        return names.get(value, "未知层级")
    
    @classmethod
    def is_top_level(cls, value: int) -> bool:
        """判断是否为顶层标签"""
        return value in [1, 2]


class NodeType(Enum):
    """节点类型枚举"""
    CATEGORY = "category"    # 大类节点 (Parent Nodes)
    LEAF = "leaf"           # 叶子节点 (知识点)
    TAG = "tag"             # 标签节点 (能力/问题层)


class RelationType(Enum):
    """关系类型枚举"""
    HIERARCHY = "hierarchy"      # 层级/归属关系 (Parent-Child)
    PEER = "peer"               # 同层关联 (Peer-to-Peer)
    CROSS_REFERENCE = "cross"   # 跨层关联 (Cross-layer)
    PREREQUISITE = "prereq"     # 前置依赖关系
    RELATED = "related"         # 相关关系


@dataclass
class Node:
    """节点数据类"""
    id: str
    name: str
    layer: LayerType
    node_type: NodeType
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "layer": self.layer.value,
            "layer_name": LayerType.get_name(self.layer.value),
            "node_type": self.node_type.value,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Edge:
    """边/关系数据类"""
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source_id,
            "target": self.target_id,
            "relation_type": self.relation_type.value,
            "weight": self.weight,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# SQL 建表语句
CREATE_TABLES_SQL = """
-- 节点表
CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    layer INTEGER NOT NULL CHECK (layer BETWEEN 1 AND 6),
    node_type TEXT NOT NULL CHECK (node_type IN ('category', 'leaf', 'tag')),
    description TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 关系表
CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL CHECK (relation_type IN ('hierarchy', 'peer', 'cross', 'prereq', 'related')),
    weight REAL DEFAULT 1.0,
    description TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE,
    UNIQUE(source_id, target_id, relation_type)
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_nodes_layer ON nodes(layer);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(relation_type);

-- 层级定义表 (用于存储层级元数据)
CREATE TABLE IF NOT EXISTS layer_definitions (
    layer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    is_top_level BOOLEAN DEFAULT FALSE,
    color TEXT DEFAULT '#666666',
    icon TEXT DEFAULT ''
);

-- 插入层级定义
INSERT OR IGNORE INTO layer_definitions (layer_id, name, description, is_top_level, color) VALUES
    (1, '能力层', '顶层能力标签，描述学习者应具备的核心能力', TRUE, '#e74c3c'),
    (2, '问题层', '顶层问题标签，描述可解决的问题类型', TRUE, '#9b59b6'),
    (3, '专业课', '专业领域的核心课程知识', FALSE, '#3498db'),
    (4, '学科基础', '学科的基础理论知识', FALSE, '#2ecc71'),
    (5, '高阶基础', '进阶的基础知识', FALSE, '#f39c12'),
    (6, '数理基础', '数学和物理的基础知识', FALSE, '#1abc9c');

-- 导入历史记录表
CREATE TABLE IF NOT EXISTS import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    import_type TEXT NOT NULL,
    nodes_added INTEGER DEFAULT 0,
    edges_added INTEGER DEFAULT 0,
    nodes_updated INTEGER DEFAULT 0,
    errors TEXT DEFAULT '[]',
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# 兼容旧表的迁移 SQL
MIGRATION_SQL = """
-- 如果存在旧的 links 表，迁移数据到新的 edges 表
INSERT OR IGNORE INTO edges (source_id, target_id, relation_type)
SELECT source, target, 'hierarchy' FROM links WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='links');

-- 如果存在旧的 nodes 表且缺少新字段，更新数据
-- 这里假设旧表的 group_level 对应新的 layer
"""
