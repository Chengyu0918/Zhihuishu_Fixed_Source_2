# 知识图谱数据持久化工具

基于 SQLite 的多维知识图谱数据持久化系统，支持六层级结构和多种关系类型。

## 📋 功能特性

### 六层级结构
| 层级 | 名称 | 类型 | 说明 |
|------|------|------|------|
| 1 | 能力层 | 顶层标签 | 描述学习者应具备的核心能力 |
| 2 | 问题层 | 顶层标签 | 描述可解决的问题类型 |
| 3 | 专业课 | 大类 | 专业领域的核心课程知识 |
| 4 | 学科基础 | 大类/知识点 | 学科的基础理论知识 |
| 5 | 高阶基础 | 大类/知识点 | 进阶的基础知识 |
| 6 | 数理基础 | 大类/知识点 | 数学和物理的基础知识 |

### 节点类型
- **tag**: 标签节点（能力层、问题层）
- **category**: 大类节点（父节点）
- **leaf**: 叶子节点（具体知识点）

### 关系类型
- **hierarchy**: 层级/归属关系（Parent-Child）
- **peer**: 同层关联（Peer-to-Peer）
- **cross**: 跨层关联（Cross-layer）
- **prereq**: 前置依赖关系
- **related**: 相关关系

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask
# 可选：支持 YAML 格式
pip install pyyaml
```

### 2. 初始化数据库

```bash
# 初始化并导入示例数据
python init_knowledge_graph.py

# 仅初始化，不导入示例数据
python init_knowledge_graph.py --no-sample

# 创建示例 JSON 文件
python init_knowledge_graph.py --create-sample-file

# 从旧数据库迁移
python init_knowledge_graph.py --migrate --old-db old_database.db
```

### 3. 启动 Web 服务

```bash
python app.py
```

访问 http://localhost:5000 查看知识图谱可视化界面。

## 📁 项目结构

```
├── knowledge_graph/           # 核心模块
│   ├── __init__.py           # 模块入口
│   ├── schema.py             # 数据模式定义
│   ├── database.py           # 数据库操作
│   └── importer.py           # 数据导入器
├── app.py                    # Flask Web 应用
├── init_knowledge_graph.py   # 初始化脚本
├── sample_data.yaml          # 示例数据 (YAML)
├── database.db               # SQLite 数据库
├── templates/                # HTML 模板
└── static/                   # 静态资源
```

## 📊 数据格式

### JSON 格式

```json
{
  "nodes": [
    {
      "id": "node_id",
      "name": "节点名称",
      "layer": 3,
      "node_type": "category",
      "description": "节点描述",
      "metadata": {"key": "value"}
    }
  ],
  "edges": [
    {
      "source": "source_node_id",
      "target": "target_node_id",
      "relation_type": "hierarchy",
      "weight": 1.0,
      "description": "关系描述"
    }
  ]
}
```

### YAML 格式

```yaml
nodes:
  - id: node_id
    name: 节点名称
    layer: 3
    node_type: category
    description: 节点描述
    metadata:
      key: value

edges:
  - source: source_node_id
    target: target_node_id
    relation_type: hierarchy
```

## 🔌 API 接口

### 图谱数据

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/graph-data` | 获取完整图谱数据 |
| GET | `/api/statistics` | 获取统计信息 |
| GET | `/api/layers` | 获取层级定义 |

### 节点操作

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/nodes` | 获取所有节点 |
| GET | `/api/nodes?layer=3` | 按层级过滤 |
| GET | `/api/nodes?type=leaf` | 按类型过滤 |
| GET | `/api/nodes/<id>` | 获取单个节点 |
| POST | `/api/nodes` | 创建节点 |
| PUT | `/api/nodes/<id>` | 更新节点 |
| DELETE | `/api/nodes/<id>` | 删除节点 |

### 节点关系

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/node-path/<id>` | 获取节点路径 |
| GET | `/api/node/<id>/children` | 获取子节点 |
| GET | `/api/node/<id>/parents` | 获取父节点 |
| GET | `/api/node/<id>/peers` | 获取同层关联 |
| GET | `/api/node/<id>/cross-refs` | 获取跨层关联 |

### 边操作

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/edges` | 获取所有边 |
| POST | `/api/edges` | 创建边 |
| DELETE | `/api/edges?source=x&target=y` | 删除边 |

### 搜索

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/search?q=关键词` | 搜索节点 |
| GET | `/api/search?q=关键词&layer=3` | 按层级搜索 |

### 数据导入导出

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/import` | 导入 JSON 数据 |
| POST | `/api/import?clear=true` | 清空后导入 |
| POST | `/api/import/file` | 上传文件导入 |
| GET | `/api/import/history` | 导入历史 |
| GET | `/api/export` | 导出数据 |

## 💻 Python API 使用

### 基本操作

```python
from knowledge_graph import KnowledgeGraphDB, DataImporter
from knowledge_graph.schema import Node, Edge, LayerType, NodeType, RelationType

# 初始化数据库
db = KnowledgeGraphDB('database.db')

# 添加节点
node = Node(
    id='kp_example',
    name='示例知识点',
    layer=LayerType.LAYER_DISCIPLINE_BASE,
    node_type=NodeType.LEAF,
    description='这是一个示例知识点'
)
db.add_node(node)

# 添加边
edge = Edge(
    source_id='parent_node',
    target_id='kp_example',
    relation_type=RelationType.HIERARCHY
)
db.add_edge(edge)

# 查询节点
node = db.get_node('kp_example')
children = db.get_children('parent_node')
ancestors = db.get_ancestors('kp_example')

# 搜索
results = db.search_nodes('傅里叶')

# 统计
stats = db.get_statistics()
```

### 数据导入

```python
from knowledge_graph import KnowledgeGraphDB, DataImporter

db = KnowledgeGraphDB('database.db')
importer = DataImporter(db)

# 从 JSON 文件导入
result = importer.import_from_json('data.json', clear_existing=False)

# 从 YAML 文件导入
result = importer.import_from_yaml('data.yaml', clear_existing=True)

# 从字典导入
data = {
    'nodes': [...],
    'edges': [...]
}
result = importer.import_from_dict(data)

# 导入简单层级结构
hierarchy = [
    {
        'id': 'course1',
        'name': '课程1',
        'children': [
            {'id': 'ch1', 'name': '章节1'},
            {'id': 'ch2', 'name': '章节2'}
        ]
    }
]
result = importer.import_simple_hierarchy(hierarchy, layer=3)

# 向大类添加知识点
knowledge_points = [
    {'id': 'kp1', 'name': '知识点1', 'peers': ['kp2']},
    {'id': 'kp2', 'name': '知识点2', 'cross_refs': ['ability1']}
]
result = importer.import_knowledge_points('category_id', knowledge_points)

# 批量添加跨层映射
mappings = [
    ('ability1', 'kp1'),
    ('ability1', 'kp2'),
    ('problem1', 'category1')
]
count = importer.add_cross_layer_mapping(mappings)
```

### 数据导出

```python
# 导出为前端可视化格式
graph_data = db.export_graph_data()

# 导出到 JSON 文件
db.export_to_json('export.json')
```

## 📝 数据库表结构

### nodes 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT | 主键 |
| name | TEXT | 节点名称 |
| layer | INTEGER | 层级 (1-6) |
| node_type | TEXT | 节点类型 |
| description | TEXT | 描述 |
| metadata | TEXT | JSON 元数据 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### edges 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| source_id | TEXT | 源节点 ID |
| target_id | TEXT | 目标节点 ID |
| relation_type | TEXT | 关系类型 |
| weight | REAL | 权重 |
| description | TEXT | 描述 |
| metadata | TEXT | JSON 元数据 |
| created_at | TIMESTAMP | 创建时间 |

### layer_definitions 表
| 字段 | 类型 | 说明 |
|------|------|------|
| layer_id | INTEGER | 层级 ID |
| name | TEXT | 层级名称 |
| description | TEXT | 描述 |
| is_top_level | BOOLEAN | 是否顶层 |
| color | TEXT | 显示颜色 |

## 🔧 配置选项

### 数据库路径
```python
db = KnowledgeGraphDB('custom_path/database.db')
```

### 导入选项
```python
# 清空现有数据后导入
result = importer.import_from_json('data.json', clear_existing=True)
```

## 📄 许可证

MIT License
