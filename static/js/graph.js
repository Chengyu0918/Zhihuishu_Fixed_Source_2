// 文件名: static/js/graph.js
// 六层知识图谱可视化 - 赛博朋克/学术美学风格

// ==========================================
// === 赛博朋克调色板 ===
// ==========================================
const CYBER_COLORS = {
    deepOrange: '#FF6B00',
    cyan: '#00F0FF',
    purple: '#9D00FF',
    neonGreen: '#00FF41',
    background: '#02020B',
    white: '#FFFFFF',
    gold: '#FFD700'
};

// 层级配置 - 使用赛博朋克配色
// 层级配置 (修改版：大幅缩小半径，使背景板更精致)
const layerConfig = {
    1: { name: '能力层', color: '#e74c3c', y: 300, radius: 250 },
    2: { name: '问题层', color: '#f39c12', y: 180, radius: 250 }, // 改小
    3: { name: '专业课', color: '#3498db', y: 60, radius: 280 },  // 改小
    4: { name: '学科基础', color: '#2ecc71', y: -60, radius: 300 }, // 改小
    5: { name: '高阶基础', color: '#9b59b6', y: -180, radius: 320 }, // 改小
    6: { name: '数理基础', color: '#1abc9c', y: -300, radius: 350 }  // 改小
};

// 集群颜色映射 - 为不同类别分配赛博朋克颜色
const clusterColorPalette = [
    CYBER_COLORS.deepOrange,
    CYBER_COLORS.cyan,
    CYBER_COLORS.purple,
    CYBER_COLORS.neonGreen,
    '#FF00FF', // 品红
    '#FFFF00', // 黄色
    '#00FFFF', // 青色
    '#FF4444'  // 红色
];

// ==========================================
// === 节点位置自定义配置 ===
// ==========================================
const nodePositionConfig = {
    1: {},
    2: {},
    3: {},
    4: {},
    5: {},
    6: {}
};

// 获取节点的自定义位置
function getCustomNodePosition(node, index, level) {
    const levelConfig = nodePositionConfig[level];
    if (!levelConfig) return null;
    
    if (node.name && levelConfig[node.name]) {
        return levelConfig[node.name];
    }
    if (node.id && levelConfig[node.id]) {
        return levelConfig[node.id];
    }
    if (levelConfig[index] !== undefined) {
        return levelConfig[index];
    }
    
    return null;
}

// 全局变量
let Graph;
let graphData = { nodes: [], links: [] };
let mainPathData = { nodes: [], links: [], path_order: [] }; // 主路径数据
let highlightNodes = new Set();
let highlightLinks = new Set();
let selectedNode = null;
let autoRotate = true;
let rotationAngle = 0;
let layerPlanes = [];
let layerLabels = [];
let categoryLabels = []; 
let animatingLinks = new Set();
let bloomComposer = null;
let mainPathTubes = []; // 存储主路径管道对象

// ==========================================
// === Phyllotaxis (叶序) 布局算法 ===
// ==========================================
// 黄金角度 ≈ 137.5°
const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));

function phyllotaxisLayout(index, spread = 8) {
    const angle = index * GOLDEN_ANGLE;
    const radius = spread * Math.sqrt(index);
    return {
        x: radius * Math.cos(angle),
        z: radius * Math.sin(angle)
    };
}

// ==========================================
// === 初始化图谱 ===
// ==========================================
function initGraph() {
    const container = document.getElementById('graph-container');
    
    Graph = ForceGraph3D()(container)
        .backgroundColor(CYBER_COLORS.background)
        .enableNodeDrag(false)
        .enableNavigationControls(true)
        .nodeLabel(node => {
            const group = parseInt(node.group);
            if (group === 1 || group === 2) return null;
            const layerName = layerConfig[group]?.name || node.layer_name || '未知';
            return `${node.name} (${layerName})`;
        })
        .nodeColor(node => {
            if (highlightNodes.size > 0) {
                return highlightNodes.has(node.id) ? (node.color || layerConfig[node.group]?.color || '#ffffff') : 'rgba(50,50,50,0.2)';
            }
            return node.color || layerConfig[node.group]?.color || '#ffffff';
        })
        .nodeRelSize(4)
        .nodeVal(node => {
            const group = parseInt(node.group);
            if (group >= 3) return 0.8;
            if (node.node_type === 'tag') return 20;
            if (node.node_type === 'category') return 15;
            return 8;
        })
        .nodeOpacity(1.0)
        // === 连线样式 - 聚焦光束效果 ===
        .linkWidth(link => {
            if (animatingLinks.has(link)) return 2;
            if (highlightLinks.has(link)) return 1.5;
            return 0.7;
        })
        .linkColor(link => {
            if (animatingLinks.has(link)) return CYBER_COLORS.cyan;
            if (highlightLinks.size > 0) {
                return highlightLinks.has(link) ? CYBER_COLORS.cyan : 'rgba(0,240,255,0.03)';
            }
            return 'rgba(0,240,255,0.15)';
        })
        .linkOpacity(0.35) // 降低普通连线透明度，突出学习路径
        .linkDirectionalParticles(link => {
            if (animatingLinks.has(link)) return 4;
            if (highlightLinks.has(link)) return 2;
            return 0;
        })
        .linkDirectionalParticleWidth(2)
        .linkDirectionalParticleSpeed(0.006)
        .linkDirectionalParticleColor(() => CYBER_COLORS.cyan)
        
        // === 自定义节点渲染 ===
        .nodeThreeObject(node => {
            const group = parseInt(node.group);
            const THREE = window.THREE;
            if (!THREE) return null;

            if (group === 1) {
                return createCyberPentagonNode(node);
            }
            
            if (group === 2) {
                return createCyberTriangleNode(node);
            }

            // 第3-6层：发光圆盘节点
            return createGlowingDiscNode(node);
        })
        .nodeThreeObjectExtend(node => {
            const group = parseInt(node.group);
            return false; // 完全替换所有层的默认节点
        })
        
        .onNodeClick(handleNodeClick)
        .onBackgroundClick(() => {
            clearHighlight();
            hideInfoPanel();
        });

    // 设置后处理效果
    setupPostProcessing();
    
    // 加载数据
    loadGraphData();
    
    // 启动自动旋转
    startAutoRotate();
}

// ==========================================
// === 后处理效果 (Bloom) ===
// ==========================================
function setupPostProcessing() {
    const THREE = window.THREE;
    if (!THREE) return;
    
    // 添加环境光和点光源
    const scene = Graph.scene();
    
    // 环境光 - 柔和的整体照明
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);
    
    // 主点光源 - 从上方照射
    const pointLight1 = new THREE.PointLight(CYBER_COLORS.cyan, 1, 2000);
    pointLight1.position.set(0, 500, 0);
    scene.add(pointLight1);
    
    // 辅助点光源 - 侧面照射
    const pointLight2 = new THREE.PointLight(CYBER_COLORS.purple, 0.5, 1500);
    pointLight2.position.set(500, 200, 500);
    scene.add(pointLight2);
    
    const pointLight3 = new THREE.PointLight(CYBER_COLORS.deepOrange, 0.5, 1500);
    pointLight3.position.set(-500, 200, -500);
    scene.add(pointLight3);
}

// ==========================================
// === 发光球体节点 (第3-6层) ===
// ==========================================
function createGlowingDiscNode(node) {
    const THREE = window.THREE;
    if (!THREE) return null;
    
    const color = node.color || layerConfig[node.group]?.color || CYBER_COLORS.cyan;
    const group = new THREE.Group();
    
    // 根据weight计算半径 - 版本 v20251209_4
    // 使用统一的 getNodeRadius 函数确保一致性
    const weight = node.weight || 0;
    const baseRadius = getNodeRadius(weight);
    
    // 调试日志 - 每个节点都输出（前100个）
    if (window._nodeLogCount === undefined) window._nodeLogCount = 0;
    if (window._nodeLogCount < 100) {
        console.log(`[节点v4] ${node.name}: weight=${weight}, radius=${baseRadius.toFixed(2)}`);
        window._nodeLogCount++;
    }
    
    // 高权重节点特别标记
    if (weight > 50) {
        console.log(`%c[高权重节点v4] ${node.name}: weight=${weight}, radius=${baseRadius.toFixed(2)}`, 'color: red; font-weight: bold;');
    }
    
    // 主球体 - 使用 SphereGeometry 创建立体球（增加分段数使球更圆滑）
    const sphereGeometry = new THREE.SphereGeometry(baseRadius, 32, 32);
    const sphereMaterial = new THREE.MeshPhongMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.6,
        shininess: 120,
        transparent: true,
        opacity: 0.9
    });
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    group.add(sphere);
    
    // 外层发光球壳 - 半透明光晕效果（只对大球添加）
    if (baseRadius > 5) {
        const glowRadius = baseRadius * 1.2;
        const glowGeometry = new THREE.SphereGeometry(glowRadius, 24, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: color,
            transparent: true,
            opacity: 0.2,
            side: THREE.BackSide
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        group.add(glow);
    }
    
    // 最外层光晕 - 只对非常大的球添加
    if (baseRadius > 15) {
        const outerGlowRadius = baseRadius * 1.4;
        const outerGlowGeometry = new THREE.SphereGeometry(outerGlowRadius, 16, 12);
        const outerGlowMaterial = new THREE.MeshBasicMaterial({
            color: '#ffffff',
            transparent: true,
            opacity: 0.15,
            side: THREE.BackSide
        });
        const outerGlow = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
        group.add(outerGlow);
    }
    
    return group;
}

// ==========================================
// === 赛博朋克五边形节点 (第1层) ===
// ==========================================
function createCyberPentagonNode(node) {
    const THREE = window.THREE;
    if (!THREE) return null;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 600;
    canvas.height = 180;
    
    const shapeColor = node.color || CYBER_COLORS.deepOrange;
    const pentagonRadius = 60;
    const pentagonCenterX = 80;
    const centerY = canvas.height / 2;
    
    // 绘制外发光效果
    ctx.shadowColor = shapeColor;
    ctx.shadowBlur = 25;
    
    // 绘制五边形
    ctx.beginPath();
    ctx.fillStyle = shapeColor;
    for (let i = 0; i < 5; i++) {
        const angle = (i * 2 * Math.PI / 5) - Math.PI / 2;
        const x = pentagonCenterX + pentagonRadius * Math.cos(angle);
        const y = centerY + pentagonRadius * Math.sin(angle);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fill();
    
    // 内部发光边框
    ctx.strokeStyle = 'rgba(255,255,255,0.5)';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // 重置阴影
    ctx.shadowBlur = 0;
    
    // 绘制连接线 - 发光效果
    const lineStartX = pentagonCenterX + pentagonRadius + 10;
    const lineEndX = lineStartX + 50;
    
    ctx.beginPath();
    ctx.strokeStyle = shapeColor;
    ctx.lineWidth = 3;
    ctx.shadowColor = shapeColor;
    ctx.shadowBlur = 10;
    ctx.moveTo(lineStartX, centerY);
    ctx.lineTo(lineEndX, centerY);
    ctx.stroke();
    
    // 绘制文字 - 发光效果
    ctx.shadowBlur = 15;
    ctx.shadowColor = shapeColor;
    ctx.font = 'bold 34px "Microsoft YaHei", Arial, sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText(node.name, lineEndX + 15, centerY);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    const material = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true,
        depthTest: false
    });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(150, 45, 1);
    
    const anchorX = pentagonCenterX / canvas.width;
    sprite.center.set(anchorX, 0.5);

    return sprite;
}

// ==========================================
// === 赛博朋克三角形节点 (第2层) ===
// ==========================================
function createCyberTriangleNode(node) {
    const THREE = window.THREE;
    if (!THREE) return null;

    const color = node.color || CYBER_COLORS.cyan;
    const group = new THREE.Group();
    
    // 三棱锥主体 - 使用 MeshPhongMaterial
    const geometry = new THREE.ConeGeometry(5, 12, 3);
    const material = new THREE.MeshPhongMaterial({ 
        color: color,
        emissive: color,
        emissiveIntensity: 0.4,
        shininess: 80,
        transparent: true,
        opacity: 0.95
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = Math.PI / 2;
    group.add(mesh);
    
    // 底部发光环
    const ringGeometry = new THREE.RingGeometry(5, 7, 3);
    const ringMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.25,
        side: THREE.DoubleSide
    });
    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = Math.PI / 2;
    ring.rotation.z = Math.PI / 6;
    ring.position.z = -6;
    group.add(ring);
    
    return group;
}

// ==========================================
// === 加载图谱数据 ===
// ==========================================
// 辅助函数：根据weight计算节点半径（与createGlowingDiscNode保持一致）
// v20251209_5: 减小大球半径，小球保持不变
function getNodeRadius(weight) {
    if (weight === 0 || weight === undefined) {
        return 1;
    } else if (weight < 10) {
        // 小球保持不变
        return 1 + weight * 0.2;
    } else if (weight < 50) {
        // 中小球保持不变
        return 3 + (weight - 10) * 0.15;
    } else if (weight < 100) {
        // 中大球：减小增长系数 0.2 -> 0.1
        return 9 + (weight - 50) * 0.1;
    } else {
        // 大球：减小增长系数 0.1 -> 0.04，并降低基数
        return 14 + (weight - 100) * 0.04;
    }
}

// 加载图谱数据
// 加载图谱数据
function loadGraphData() {
    fetch('/api/graph-data')
        .then(response => response.json())
        .then(data => {
            
            // 0. 数据预处理 & 大类索引
            const categoryNodeMap = new Map();
            data.nodes.forEach(node => {
                if (node.node_type === 'category') {
                    categoryNodeMap.set(node.id, node);
                }
            });

            // 过滤节点 (保留1-2层，过滤3-6层的大类)
            const visibleNodes = data.nodes.filter(node => {
                const group = parseInt(node.group || 1);
                if (group >= 3 && node.node_type === 'category') {
                    return false; 
                }
                return true;
            });

            // 过滤连线
            const visibleNodeIds = new Set(visibleNodes.map(n => n.id));
            const visibleLinks = data.links.filter(link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return visibleNodeIds.has(sourceId) && visibleNodeIds.has(targetId);
            });

            graphData = { nodes: visibleNodes, links: visibleLinks };

            // 1. 清理旧场景
            const scene = Graph.scene();
            if (window.categoryLabels) {
                window.categoryLabels.forEach(label => scene.remove(label));
            }
            window.categoryLabels = [];

            // 2. 按层级分组
            const nodesByLevel = {};
            graphData.nodes.forEach(node => {
                const group = node.group || 1;
                if (!nodesByLevel[group]) nodesByLevel[group] = [];
                nodesByLevel[group].push(node);
            });
            
            // 3. 计算位置
            Object.keys(nodesByLevel).forEach(level => {
                const nodes = nodesByLevel[level];
                const levelConfig = layerConfig[level] || { y: 0, radius: 150 };
                const levelInt = parseInt(level);

                if (levelInt >= 2) {
                    // A. 分簇
                    const clusters = {};
                    nodes.forEach(node => {
                        const key = node.color || 'default';
                        if (!clusters[key]) clusters[key] = [];
                        clusters[key].push(node);
                    });
                    const clusterKeys = Object.keys(clusters).sort();
                    const totalClusters = clusterKeys.length;

                    // B. 网格布局计算
                    let gridCols;
                    if (totalClusters <= 3) {
                        gridCols = totalClusters;
                    } else {
                        gridCols = Math.ceil(Math.sqrt(totalClusters));
                    }
                    const clusterSpacing = 200; // 调整大类间距
                    
                    clusterKeys.forEach((key, clusterIndex) => {
                        const clusterNodes = clusters[key];
                        
                        const col = clusterIndex % gridCols;
                        const row = Math.floor(clusterIndex / gridCols);
                        const totalRows = Math.ceil(totalClusters / gridCols);

                        const centerX = (col - (gridCols - 1) / 2) * clusterSpacing;
                        const centerZ = (row - (totalRows - 1) / 2) * clusterSpacing;

                        // === 修改点1：排序 ===
                        // 按照权重从大到小排序，让大的球在中心，小的在外面包围
                        clusterNodes.sort((a, b) => (b.weight || 0) - (a.weight || 0));

                        // === 修改点2：圆环分层布局算法 v20251209_7 ===
                        // 大球在中心，小球按圆环围绕，类似向日葵效果
                        
                        // 计算所有节点的半径
                        const nodeRadii = clusterNodes.map(n => getNodeRadius(n.weight || 0));
                        
                        // 找出最大的球（放在中心）
                        const centerNodeRadius = nodeRadii[0] || 5;
                        
                        // 分层放置：第一个大球在中心，其余按圆环分布
                        let currentRingRadius = centerNodeRadius + 5; // 第一圈的起始半径
                        let ringIndex = 0; // 当前圈数
                        let nodesInCurrentRing = 0; // 当前圈已放置的节点数
                        let currentRingCapacity = 0; // 当前圈的容量
                        let currentAngle = 0; // 当前角度
                        
                        clusterNodes.forEach((node, i) => {
                            const nodeRadius = nodeRadii[i];
                            
                            if (i === 0) {
                                // 第一个（最大的）球放在中心
                                node.fx = centerX;
                                node.fy = levelConfig.y;
                                node.fz = centerZ;
                                
                                // 计算第一圈的参数
                                currentRingRadius = centerNodeRadius + nodeRadii[1] * 2 + 8;
                                // 第一圈能放多少个球：周长 / (球直径 + 间隙)
                                const avgSmallRadius = nodeRadii.slice(1, 10).reduce((a, b) => a + b, 0) / Math.min(9, nodeRadii.length - 1) || 3;
                                currentRingCapacity = Math.floor(2 * Math.PI * currentRingRadius / (avgSmallRadius * 2 + 4));
                                currentRingCapacity = Math.max(currentRingCapacity, 6); // 至少6个
                            } else {
                                // 检查是否需要开始新的一圈
                                if (nodesInCurrentRing >= currentRingCapacity) {
                                    ringIndex++;
                                    nodesInCurrentRing = 0;
                                    currentAngle = ringIndex * 0.5; // 每圈错开一点角度
                                    
                                    // 计算新圈的半径：上一圈半径 + 当前节点半径 * 2 + 间隙
                                    const prevRingMaxRadius = nodeRadii.slice(
                                        1 + (ringIndex - 1) * currentRingCapacity,
                                        1 + ringIndex * currentRingCapacity
                                    ).reduce((max, r) => Math.max(max, r), 3);
                                    
                                    currentRingRadius += prevRingMaxRadius * 2 + nodeRadius * 2 + 6;
                                    
                                    // 重新计算新圈的容量
                                    const remainingNodes = clusterNodes.length - i;
                                    const avgRemainingRadius = nodeRadii.slice(i, i + 10).reduce((a, b) => a + b, 0) / Math.min(10, remainingNodes) || 2;
                                    currentRingCapacity = Math.floor(2 * Math.PI * currentRingRadius / (avgRemainingRadius * 2 + 3));
                                    currentRingCapacity = Math.max(currentRingCapacity, 8);
                                }
                                
                                // 计算当前节点在圈上的角度
                                const angleStep = (2 * Math.PI) / currentRingCapacity;
                                const angle = currentAngle + nodesInCurrentRing * angleStep;
                                
                                // 计算位置
                                const offsetX = currentRingRadius * Math.cos(angle);
                                const offsetZ = currentRingRadius * Math.sin(angle);
                                
                                node.fx = centerX + offsetX;
                                node.fy = levelConfig.y;
                                node.fz = centerZ + offsetZ;
                                
                                nodesInCurrentRing++;
                            }
                        });

                        // D. 显示标签
                        let specificCategoryName = "";
                        if (clusterNodes.length > 0) {
                            const firstNode = clusterNodes[0];
                            if (firstNode.parent_id && categoryNodeMap.has(firstNode.parent_id)) {
                                specificCategoryName = categoryNodeMap.get(firstNode.parent_id).name;
                            } else if (firstNode.category_name) {
                                specificCategoryName = firstNode.category_name;
                            }
                        }

                        if (specificCategoryName && typeof addCategoryLabel === 'function') {
                            // 因为中间可能有很大的球，把标签稍微再抬高一点 (y + 60)
                            addCategoryLabel(specificCategoryName, centerX, levelConfig.y + 60, centerZ, key);
                        }
                    });

                } else {
                    // 第1层 - 阵列布局（网格形式）
                    const totalNodes = nodes.length;
                    // 计算网格的列数和行数
                    const cols = Math.ceil(Math.sqrt(totalNodes));
                    const rows = Math.ceil(totalNodes / cols);
                    const spacing = 120; // 节点间距
                    
                    nodes.forEach((node, index) => {
                        const col = index % cols;
                        const row = Math.floor(index / cols);
                        
                        // 居中对齐
                        const offsetX = (cols - 1) * spacing / 2;
                        const offsetZ = (rows - 1) * spacing / 2;
                        
                        node.fx = col * spacing - offsetX;
                        node.fy = levelConfig.y;
                        node.fz = row * spacing - offsetZ;
                    });
                }
            });
            
            Graph.graphData(graphData);

            setTimeout(() => {
                if (typeof addLayerPlanes === 'function') addLayerPlanes();
                // 加载并绘制主路径
                loadAndDrawMainPath();
                Graph.cameraPosition({ x: 400, y: 400, z: 400 });
            }, 500);
            
            if (typeof updateLayerLabels === 'function') updateLayerLabels();
        })
        .catch(error => {
            console.error('加载数据失败:', error);
        });
}

// ==========================================
// === 加载并绘制主路径 ===
// ==========================================
function loadAndDrawMainPath() {
    fetch('/api/main-path')
        .then(response => response.json())
        .then(data => {
            mainPathData = data;
            console.log('主路径数据:', mainPathData);
            console.log(`主路径数量: ${mainPathData.paths ? mainPathData.paths.length : 1}`);
            console.log(`主路径节点总数: ${mainPathData.nodes ? mainPathData.nodes.length : 0}`);
            
            // 绘制所有主路径
            drawAllMainPaths();
        })
        .catch(error => {
            console.error('加载主路径数据失败:', error);
        });
}

// ==========================================
// === 绘制所有主路径（支持多条路径不同颜色）===
// ==========================================
function drawAllMainPaths() {
    const THREE = window.THREE;
    if (!THREE) return;
    const scene = Graph.scene();
    
    // 清除旧的路径管道
    mainPathTubes.forEach(obj => scene.remove(obj));
    mainPathTubes = [];
    
    // 检查是否有路径数据
    if (!mainPathData.paths || mainPathData.paths.length === 0) {
        console.warn('没有主路径数据');
        return;
    }
    
    // 创建节点ID到图谱节点的映射
    const graphNodeMap = new Map();
    graphData.nodes.forEach(node => graphNodeMap.set(node.id, node));
    
    // 为每条路径绘制管道
    mainPathData.paths.forEach((pathInfo, pathIndex) => {
        const pathId = pathInfo.path_id;
        const pathName = pathInfo.path_name;
        const colorConfig = pathInfo.color;
        const links = pathInfo.links;
        
        if (!links || links.length === 0) {
            console.warn(`路径 ${pathId} 没有连线数据`);
            return;
        }
        
        console.log(`绘制路径 ${pathId}: ${pathName}, 颜色: ${colorConfig.primary}`);
        
        // 构建有序的节点ID列表
        const sortedLinks = [...links].sort((a, b) => a.order - b.order);
        const orderedNodeIds = [];
        sortedLinks.forEach((link, index) => {
            if (index === 0) {
                orderedNodeIds.push(link.source);
            }
            orderedNodeIds.push(link.target);
        });
        
        // 收集路径点（使用图谱中节点的实际位置）
        const points = [];
        orderedNodeIds.forEach(nodeId => {
            const node = graphNodeMap.get(nodeId);
            if (node && node.fx !== undefined) {
                points.push(new THREE.Vector3(node.fx, node.fy, node.fz));
            }
        });
        
        if (points.length < 2) {
            console.warn(`路径 ${pathId} 点不足，无法绘制管道`);
            return;
        }
        
        console.log(`路径 ${pathId} 共 ${points.length} 个点`);
        
        // 创建平滑曲线
        const curve = new THREE.CatmullRomCurve3(points);
        curve.closed = false;
        curve.tension = 0.3;
        
        // 绘制单条路径的管道
        drawSinglePathTube(scene, curve, points.length, colorConfig, pathId, pathIndex);
        
        // 添加流动粒子效果
        addFlowingParticlesForPath(curve, scene, colorConfig, pathId);
    });
    
    // 添加路径信息标签（显示所有路径）
    addMultiPathInfoLabel(scene);
}

// ==========================================
// === 绘制单条路径的管道 ===
// ==========================================
function drawSinglePathTube(scene, curve, pointCount, colorConfig, pathId, pathIndex) {
    const THREE = window.THREE;
    if (!THREE) return;
    
    const primaryColor = colorConfig.primary;
    const secondaryColor = colorConfig.secondary;
    
    // 获取路径粗细系数（默认1.0为主路径粗细）
    const widthFactor = colorConfig.width || 1.0;
    
    // 基础管道半径（主路径为3）
    const baseRadius = 3 * widthFactor;
    const glowRadius = 5 * widthFactor;
    const outerGlowRadius = 8 * widthFactor;
    
    // 根据路径索引稍微偏移位置，避免重叠
    const offsetY = pathIndex * 2;
    
    // === 主管道 ===
    const tubeGeometry = new THREE.TubeGeometry(
        curve, 
        pointCount * 30,
        baseRadius,
        16,
        false
    );
    
    const tubeMaterial = new THREE.MeshPhongMaterial({
        color: primaryColor,
        emissive: secondaryColor,
        emissiveIntensity: 0.9,
        transparent: true,
        opacity: 0.95,
        shininess: 150,
        side: THREE.DoubleSide
    });
    
    const tubeMesh = new THREE.Mesh(tubeGeometry, tubeMaterial);
    tubeMesh.position.y += offsetY;
    tubeMesh.name = `mainPathTube_${pathId}`;
    scene.add(tubeMesh);
    mainPathTubes.push(tubeMesh);
    
    // === 外层发光管道 ===
    const glowGeometry = new THREE.TubeGeometry(
        curve, 
        pointCount * 30,
        glowRadius,
        16,
        false
    );
    
    const glowMaterial = new THREE.MeshBasicMaterial({
        color: primaryColor,
        transparent: true,
        opacity: 0.35,
        side: THREE.DoubleSide
    });
    
    const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
    glowMesh.position.y += offsetY;
    glowMesh.name = `mainPathGlow_${pathId}`;
    scene.add(glowMesh);
    mainPathTubes.push(glowMesh);
    
    // === 最外层光晕 ===
    const outerGlowGeometry = new THREE.TubeGeometry(
        curve, 
        pointCount * 20,
        outerGlowRadius,
        12,
        false
    );
    
    const outerGlowMaterial = new THREE.MeshBasicMaterial({
        color: '#ffffff',
        transparent: true,
        opacity: 0.15,
        side: THREE.DoubleSide
    });
    
    const outerGlowMesh = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
    outerGlowMesh.position.y += offsetY;
    outerGlowMesh.name = `mainPathOuterGlow_${pathId}`;
    scene.add(outerGlowMesh);
    mainPathTubes.push(outerGlowMesh);
}

// ==========================================
// === 为单条路径添加流动粒子效果 ===
// ==========================================
function addFlowingParticlesForPath(curve, scene, colorConfig, pathId) {
    const THREE = window.THREE;
    if (!THREE) return;
    
    const primaryColor = new THREE.Color(colorConfig.primary);
    const particleCount = 80;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    
    // 初始化粒子位置和颜色
    for (let i = 0; i < particleCount; i++) {
        const t = i / particleCount;
        const point = curve.getPoint(t);
        positions[i * 3] = point.x;
        positions[i * 3 + 1] = point.y;
        positions[i * 3 + 2] = point.z;
        
        // 使用路径颜色渐变到白色
        colors[i * 3] = primaryColor.r + (1 - primaryColor.r) * t * 0.3;
        colors[i * 3 + 1] = primaryColor.g + (1 - primaryColor.g) * t * 0.3;
        colors[i * 3 + 2] = primaryColor.b + (1 - primaryColor.b) * t * 0.3;
    }
    
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    const particleMaterial = new THREE.PointsMaterial({
        size: 6,
        vertexColors: true,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending
    });
    
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    particles.name = `flowingParticles_${pathId}`;
    scene.add(particles);
    mainPathTubes.push(particles);
    
    // 动画更新粒子位置
    let offset = 0;
    function animateParticles() {
        offset += 0.003;
        if (offset > 1) offset = 0;
        
        const positions = particles.geometry.attributes.position.array;
        for (let i = 0; i < particleCount; i++) {
            const t = ((i / particleCount) + offset) % 1;
            const point = curve.getPoint(t);
            positions[i * 3] = point.x;
            positions[i * 3 + 1] = point.y;
            positions[i * 3 + 2] = point.z;
        }
        particles.geometry.attributes.position.needsUpdate = true;
        
        requestAnimationFrame(animateParticles);
    }
    animateParticles();
}

// ==========================================
// === 添加多路径信息标签 ===
// ==========================================
function addMultiPathInfoLabel(scene) {
    const THREE = window.THREE;
    if (!THREE) return;
    
    const paths = mainPathData.paths || [];
    const totalNodes = mainPathData.nodes ? mainPathData.nodes.length : 0;
    
    // 计算画布高度（根据路径数量）
    const lineHeight = 35;
    const headerHeight = 50;
    const canvasHeight = headerHeight + paths.length * lineHeight + 20;
    
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 550;
    canvas.height = Math.max(120, canvasHeight);
    
    // 背景
    context.fillStyle = 'rgba(2, 2, 11, 0.9)';
    context.beginPath();
    context.roundRect(0, 0, canvas.width, canvas.height, 10);
    context.fill();
    
    // 边框 - 使用第一条路径的颜色
    const borderColor = paths.length > 0 ? paths[0].color.primary : CYBER_COLORS.gold;
    context.strokeStyle = borderColor;
    context.lineWidth = 3;
    context.stroke();
    
    // 标题
    context.shadowColor = borderColor;
    context.shadowBlur = 15;
    context.fillStyle = '#ffffff';
    context.font = 'bold 24px "Microsoft YaHei", Arial';
    context.fillText(`◈ 主路径 (共 ${totalNodes} 个知识点)`, 20, 35);
    
    // 每条路径的信息
    context.shadowBlur = 0;
    context.font = '18px "Microsoft YaHei", Arial';
    
    paths.forEach((path, index) => {
        const y = headerHeight + index * lineHeight + 20;
        const color = path.color.primary;
        
        // 颜色指示器
        context.fillStyle = color;
        context.beginPath();
        context.arc(30, y, 8, 0, Math.PI * 2);
        context.fill();
        
        // 路径名称
        context.fillStyle = color;
        context.fillText(path.path_name, 50, y + 5);
        
        // 节点数量
        context.fillStyle = 'rgba(255,255,255,0.7)';
        const nodeCount = path.node_ids ? path.node_ids.length : 0;
        context.fillText(`(${nodeCount} 个节点)`, 250, y + 5);
    });
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true,
        depthTest: false
    });
    
    const sprite = new THREE.Sprite(material);
    const scale = canvas.height / 100;
    sprite.scale.set(200, 40 * scale, 1);
    sprite.position.set(350, 380, 0);
    sprite.name = "pathInfoLabel";
    scene.add(sprite);
    mainPathTubes.push(sprite);
}

// ==========================================
// === 绘制主路径发光管道（旧版兼容）===
// ==========================================
function drawMainPathTube() {
    // 兼容旧版API格式，转换为新格式后调用新函数
    if (mainPathData.paths) {
        drawAllMainPaths();
        return;
    }
    
    // 旧版格式处理
    const THREE = window.THREE;
    if (!THREE) return;
    const scene = Graph.scene();
    
    // 清除旧的路径管道
    mainPathTubes.forEach(obj => scene.remove(obj));
    mainPathTubes = [];
    
    if (!mainPathData.links || mainPathData.links.length === 0) {
        console.warn('没有主路径数据');
        return;
    }
    
    // 构建有序的节点ID列表
    const sortedLinks = [...mainPathData.links].sort((a, b) => a.order - b.order);
    const orderedNodeIds = [];
    sortedLinks.forEach((link, index) => {
        if (index === 0) {
            orderedNodeIds.push(link.source);
        }
        orderedNodeIds.push(link.target);
    });
    
    // 创建节点ID到图谱节点的映射
    const graphNodeMap = new Map();
    graphData.nodes.forEach(node => graphNodeMap.set(node.id, node));
    
    // 收集路径点（使用图谱中节点的实际位置）
    const points = [];
    orderedNodeIds.forEach(nodeId => {
        const node = graphNodeMap.get(nodeId);
        if (node && node.fx !== undefined) {
            points.push(new THREE.Vector3(node.fx, node.fy, node.fz));
        }
    });
    
    if (points.length < 2) {
        console.warn('路径点不足，无法绘制管道');
        return;
    }
    
    console.log(`绘制主路径管道，共 ${points.length} 个点`);
    
    // 创建平滑曲线
    const curve = new THREE.CatmullRomCurve3(points);
    curve.closed = false;
    curve.tension = 0.3; // 曲线张力，越小越平滑
    
    // === 主管道 - 金色发光 ===
    const tubeGeometry = new THREE.TubeGeometry(
        curve, 
        points.length * 30, // 分段数
        3,                  // 半径
        16,                 // 横截面分段
        false               // 不闭合
    );
    
    const tubeMaterial = new THREE.MeshPhongMaterial({
        color: CYBER_COLORS.gold,
        emissive: CYBER_COLORS.deepOrange,
        emissiveIntensity: 0.9,
        transparent: true,
        opacity: 0.95,
        shininess: 150,
        side: THREE.DoubleSide
    });
    
    const tubeMesh = new THREE.Mesh(tubeGeometry, tubeMaterial);
    tubeMesh.name = "mainPathTube";
    scene.add(tubeMesh);
    mainPathTubes.push(tubeMesh);
    
    // === 外层发光管道 ===
    const glowGeometry = new THREE.TubeGeometry(
        curve, 
        points.length * 30,
        5,  // 稍大的半径
        16,
        false
    );
    
    const glowMaterial = new THREE.MeshBasicMaterial({
        color: CYBER_COLORS.gold,
        transparent: true,
        opacity: 0.35,
        side: THREE.DoubleSide
    });
    
    const glowMesh = new THREE.Mesh(glowGeometry, glowMaterial);
    glowMesh.name = "mainPathGlow";
    scene.add(glowMesh);
    mainPathTubes.push(glowMesh);
    
    // === 最外层光晕 ===
    const outerGlowGeometry = new THREE.TubeGeometry(
        curve, 
        points.length * 20,
        8, // 更大的半径
        12,
        false
    );
    
    const outerGlowMaterial = new THREE.MeshBasicMaterial({
        color: '#ffffff',
        transparent: true,
        opacity: 0.15,
        side: THREE.DoubleSide
    });
    
    const outerGlowMesh = new THREE.Mesh(outerGlowGeometry, outerGlowMaterial);
    outerGlowMesh.name = "mainPathOuterGlow";
    scene.add(outerGlowMesh);
    mainPathTubes.push(outerGlowMesh);
    
    // === 添加流动粒子效果 ===
    addFlowingParticles(curve, scene);
    
    // 添加路径信息标签
    addPathInfoLabel(scene);
}

// ==========================================
// === 添加流动粒子效果 ===
// ==========================================
function addFlowingParticles(curve, scene) {
    const THREE = window.THREE;
    if (!THREE) return;
    
    const particleCount = 80;
    const particleGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    
    // 初始化粒子位置
    for (let i = 0; i < particleCount; i++) {
        const t = i / particleCount;
        const point = curve.getPoint(t);
        positions[i * 3] = point.x;
        positions[i * 3 + 1] = point.y;
        positions[i * 3 + 2] = point.z;
        
        // 金色到白色渐变
        colors[i * 3] = 1.0;     // R
        colors[i * 3 + 1] = 0.8 + t * 0.2; // G
        colors[i * 3 + 2] = t * 0.5;   // B
    }
    
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    
    const particleMaterial = new THREE.PointsMaterial({
        size: 6,
        vertexColors: true,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending
    });
    
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    particles.name = "flowingParticles";
    scene.add(particles);
    mainPathTubes.push(particles);
    
    // 动画更新粒子位置
    let offset = 0;
    function animateParticles() {
        offset += 0.003;
        if (offset > 1) offset = 0;
        
        const positions = particles.geometry.attributes.position.array;
        for (let i = 0; i < particleCount; i++) {
            const t = ((i / particleCount) + offset) % 1;
            const point = curve.getPoint(t);
            positions[i * 3] = point.x;
            positions[i * 3 + 1] = point.y;
            positions[i * 3 + 2] = point.z;
        }
        particles.geometry.attributes.position.needsUpdate = true;
        
        requestAnimationFrame(animateParticles);
    }
    animateParticles();
}

// ==========================================
// === 添加路径信息标签 ===
// ==========================================
function addPathInfoLabel(scene) {
    const THREE = window.THREE;
    if (!THREE) return;
    
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 500;
    canvas.height = 100;
    
    // 背景
    context.fillStyle = 'rgba(2, 2, 11, 0.9)';
    context.beginPath();
    context.roundRect(0, 0, canvas.width, canvas.height, 10);
    context.fill();
    
    // 边框
    context.strokeStyle = CYBER_COLORS.gold;
    context.lineWidth = 3;
    context.stroke();
    
    // 标题
    context.shadowColor = CYBER_COLORS.gold;
    context.shadowBlur = 15;
    context.fillStyle = CYBER_COLORS.gold;
    context.font = 'bold 28px "Microsoft YaHei", Arial';
    context.fillText('◈ 电子信息工程主路径', 20, 40);
    
    // 信息
    context.shadowBlur = 0;
    context.fillStyle = '#ffffff';
    context.font = '20px "Microsoft YaHei", Arial';
    context.fillText(`共 ${mainPathData.nodes.length} 个知识点`, 20, 75);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true,
        depthTest: false
    });
    
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(180, 36, 1);
    sprite.position.set(350, 380, 0);
    sprite.name = "pathInfoLabel";
    scene.add(sprite);
    mainPathTubes.push(sprite);
}

// 更新层级标签中的节点数量
function updateLayerLabels() {
    // 此函数可用于动态更新UI中的层级信息
    console.log('图谱数据已加载，节点数:', graphData.nodes.length, '连线数:', graphData.links.length);
}

// ==========================================
// === 赛博朋克大类标签 ===
// ==========================================
// 别名函数，保持兼容性
function addCategoryLabel(text, x, y, z, color) {
    addCyberCategoryLabel(text, x, y, z, color);
}

function addCyberCategoryLabel(text, x, y, z, color) {
    const THREE = window.THREE;
    if (!THREE) return;
    const scene = Graph.scene();

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 1024;
    canvas.height = 128;

    // 发光效果
    context.shadowColor = color || CYBER_COLORS.cyan;
    context.shadowBlur = 20;
    
    context.fillStyle = color || CYBER_COLORS.cyan;
    context.font = 'bold 38px "Microsoft YaHei", Arial';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    
    // 处理长文本
    let displayText = text;
    const maxWidth = canvas.width - 60;
    let textWidth = context.measureText(displayText).width;
    
    if (textWidth > maxWidth) {
        const quoteMatch = text.match(/[""]([^""]+)[""]/);
        const aroundMatch = text.match(/围绕(.+?)的/);
        
        if (quoteMatch) {
            const numMatch = text.match(/^[一二三四五六七八九十]+、/);
            const prefix = numMatch ? numMatch[0] : '';
            displayText = prefix + quoteMatch[1];
        } else if (aroundMatch) {
            const numMatch = text.match(/^[一二三四五六七八九十]+、/);
            const prefix = numMatch ? numMatch[0] : '';
            displayText = prefix + aroundMatch[1];
        }
        
        textWidth = context.measureText(displayText).width;
        if (textWidth > maxWidth - 30) {
            while (textWidth > maxWidth - 30 && displayText.length > 10) {
                displayText = displayText.slice(0, -1);
                textWidth = context.measureText(displayText + '...').width;
            }
            displayText += '...';
        }
    }
    
    // 绘制发光文本
    context.fillText(displayText, canvas.width / 2, canvas.height / 2);
    
    // 再绘制一层白色文本增强可读性
    context.shadowBlur = 0;
    context.fillStyle = '#ffffff';
    context.globalAlpha = 0.9;
    context.fillText(displayText, canvas.width / 2, canvas.height / 2);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true,
        depthTest: false 
    });
    
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(200, 25, 1);
    sprite.position.set(x, y + 40, z); // 浮在集群上方
    
    scene.add(sprite);
    categoryLabels.push(sprite);
    window.categoryLabels = categoryLabels;
}

// ==========================================
// === 赛博朋克层级平面 ===
// ==========================================
// 别名函数，保持兼容性
function addLayerPlanes() {
    addCyberLayerPlanes();
}

function addCyberLayerPlanes() {
    const scene = Graph.scene();
    const THREE = window.THREE;
    if (!THREE) return;
    
    // 清除旧的平面和标签
    layerPlanes.forEach(plane => scene.remove(plane));
    layerLabels.forEach(label => scene.remove(label));
    layerPlanes = [];
    layerLabels = [];
    
    Object.keys(layerConfig).forEach(level => {
        const config = layerConfig[level];
        const squareSize = (config.radius + 80) * 2;
        
        // === 毛玻璃效果背景平面 ===
        const glassSize = squareSize * 1.1; // 稍微大一点
        const glassGeometry = new THREE.PlaneGeometry(glassSize, glassSize);
        
        // 创建毛玻璃材质 - 更白更清晰
        const glassMaterial = new THREE.MeshPhysicalMaterial({
            color: '#ffffff',     // 改为白色
            transparent: true,
            opacity: 0.15,        // 增加不透明度
            roughness: 0.7,       // 降低粗糙度使其更清晰
            metalness: 0.0,
            transmission: 0.1,    // 降低透光性
            thickness: 0.5,       // 玻璃厚度
            side: THREE.DoubleSide,
            depthWrite: false,
            blending: THREE.NormalBlending
        });
        
        const glassPlane = new THREE.Mesh(glassGeometry, glassMaterial);
        glassPlane.rotation.x = -Math.PI / 2; // 水平放置
        glassPlane.position.y = config.y - 0.5; // 略低于网格
        scene.add(glassPlane);
        layerPlanes.push(glassPlane);
        
        // === 毛玻璃边缘发光效果 ===
        const edgeGeometry = new THREE.PlaneGeometry(glassSize + 10, glassSize + 10);
        const edgeMaterial = new THREE.MeshBasicMaterial({
            color: config.color,
            transparent: true,
            opacity: 0.05,
            side: THREE.DoubleSide,
            depthWrite: false
        });
        const edgePlane = new THREE.Mesh(edgeGeometry, edgeMaterial);
        edgePlane.rotation.x = -Math.PI / 2;
        edgePlane.position.y = config.y - 1;
        scene.add(edgePlane);
        layerPlanes.push(edgePlane);
        
        // 网格线效果 - 赛博朋克风格
        const gridHelper = new THREE.GridHelper(squareSize, 20, config.color, config.color);
        gridHelper.position.y = config.y;
        gridHelper.material.opacity = 0.12; // 稍微增加网格可见度
        gridHelper.material.transparent = true;
        scene.add(gridHelper);
        layerPlanes.push(gridHelper);
        
        // 发光边框
        const scale = Math.sqrt(2);
        const borderRadius = (config.radius + 80) * scale;
        
        const points = [];
        for (let i = 0; i < 4; i++) {
            const angle = (i * Math.PI / 2) + Math.PI / 4;
            points.push(new THREE.Vector3(
                borderRadius * Math.cos(angle),
                0,
                borderRadius * Math.sin(angle)
            ));
        }
        points.push(points[0].clone());
        
        const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
        const lineMaterial = new THREE.LineBasicMaterial({
            color: config.color,
            transparent: true,
            opacity: 0.5, // 增加边框可见度
            depthWrite: false
        });
        const borderLine = new THREE.Line(lineGeometry, lineMaterial);
        borderLine.position.y = config.y;
        scene.add(borderLine);
        layerPlanes.push(borderLine);
        
        // === 内发光边框 ===
        const innerBorderRadius = borderRadius - 15;
        const innerPoints = [];
        for (let i = 0; i < 4; i++) {
            const angle = (i * Math.PI / 2) + Math.PI / 4;
            innerPoints.push(new THREE.Vector3(
                innerBorderRadius * Math.cos(angle),
                0,
                innerBorderRadius * Math.sin(angle)
            ));
        }
        innerPoints.push(innerPoints[0].clone());
        
        const innerLineGeometry = new THREE.BufferGeometry().setFromPoints(innerPoints);
        const innerLineMaterial = new THREE.LineBasicMaterial({
            color: '#ffffff',
            transparent: true,
            opacity: 0.15,
            depthWrite: false
        });
        const innerBorderLine = new THREE.Line(innerLineGeometry, innerLineMaterial);
        innerBorderLine.position.y = config.y;
        scene.add(innerBorderLine);
        layerPlanes.push(innerBorderLine);

        // 创建层级标签
        createCyberTextLabel(scene, config, level, THREE);
    });
}

// ==========================================
// === 赛博朋克层级标签 ===
// ==========================================
function createCyberTextLabel(scene, config, level, THREE) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 512;
    canvas.height = 128;
    
    // 背景 - 半透明黑色
    context.fillStyle = 'rgba(2, 2, 11, 0.85)';
    context.beginPath();
    context.roundRect(0, 0, canvas.width, canvas.height, 15);
    context.fill();
    
    // 发光边框
    context.shadowColor = config.color;
    context.shadowBlur = 15;
    context.strokeStyle = config.color;
    context.lineWidth = 3;
    context.stroke();
    
    // 左侧色块
    context.shadowBlur = 0;
    context.fillStyle = config.color;
    context.fillRect(0, 0, 15, canvas.height);
    
    // 文字
    context.fillStyle = '#ffffff';
    context.font = 'bold 40px "Microsoft YaHei", Arial';
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    
    const nodeCount = graphData.nodes.filter(n => n.group == level).length;
    context.fillText(`${config.name} (${nodeCount})`, canvas.width / 2 + 10, canvas.height / 2);
    
    const texture = new THREE.CanvasTexture(canvas);
    const spriteMaterial = new THREE.SpriteMaterial({ 
        map: texture, 
        transparent: true 
    });
    const sprite = new THREE.Sprite(spriteMaterial);
    
    sprite.scale.set(160, 42, 1);
    sprite.position.set(-config.radius - 150, config.y, 0);
    scene.add(sprite);
    layerLabels.push(sprite);
}

// ==========================================
// === 节点点击处理 ===
// ==========================================
function handleNodeClick(node) {
    if (!node) return;
    
    selectedNode = node;
    
    highlightNodes.clear();
    highlightLinks.clear();
    animatingLinks.clear();
    
    highlightNodes.add(node.id);
    graphData.links.forEach(link => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        if (sourceId === node.id || targetId === node.id) {
            highlightLinks.add(link);
            highlightNodes.add(sourceId);
            highlightNodes.add(targetId);
        }
    });
    
    if (node.node_type === 'category') {
        graphData.nodes.forEach(n => {
            if (n.parent_id === node.id) highlightNodes.add(n.id);
        });
    }
    if (node.parent_id) highlightNodes.add(node.parent_id);
    
    // 更新节点高亮状态 - 修改自定义节点的透明度
    updateNodeHighlight();
    
    // 强制刷新图谱渲染
    Graph.nodeColor(Graph.nodeColor());
    Graph.linkWidth(Graph.linkWidth());
    Graph.linkColor(Graph.linkColor());
    Graph.linkDirectionalParticles(Graph.linkDirectionalParticles());

    showNodeInfo(node);
    
    const distance = 250;
    const distRatio = 1 + distance / Math.hypot(node.x || 0, node.y || 0, node.z || 0);
    Graph.cameraPosition(
        { x: (node.x || 0) * distRatio, y: (node.y || 0) + 100, z: (node.z || 0) * distRatio },
        node,
        1500
    );
}

// ==========================================
// === 更新节点高亮状态 ===
// ==========================================
function updateNodeHighlight() {
    const THREE = window.THREE;
    if (!THREE) return;
    
    let updatedCount = 0;
    let visibleCount = 0;
    let hiddenCount = 0;
    
    // 遍历所有节点，更新其视觉状态
    graphData.nodes.forEach(node => {
        const threeObj = node.__threeObj;
        if (!threeObj) return;
        
        updatedCount++;
        const isHighlighted = highlightNodes.size === 0 || highlightNodes.has(node.id);
        
        if (isHighlighted) {
            visibleCount++;
        } else {
            hiddenCount++;
        }
        
        // 方案1：直接使用 visible 属性控制可见性（最可靠）
        threeObj.visible = isHighlighted;
        
        // 方案2：同时调整透明度和缩放（增强效果）
        const targetOpacity = isHighlighted ? 1.0 : 0.02;
        const targetScale = isHighlighted ? 1.0 : 0.2;
        const targetEmissive = isHighlighted ? 0.6 : 0.01;
        
        if (threeObj.isSprite) {
            // Sprite 类型 (第1层五边形)
            if (threeObj.material) {
                threeObj.material.opacity = targetOpacity;
                threeObj.material.needsUpdate = true;
            }
            // 缩放 Sprite
            if (!threeObj.userData) threeObj.userData = {};
            if (!threeObj.userData.baseScale) {
                threeObj.userData.baseScale = { 
                    x: threeObj.scale.x, 
                    y: threeObj.scale.y, 
                    z: threeObj.scale.z 
                };
            }
            const baseScale = threeObj.userData.baseScale;
            const scaleFactor = isHighlighted ? 1.0 : 0.3;
            threeObj.scale.set(
                baseScale.x * scaleFactor,
                baseScale.y * scaleFactor,
                baseScale.z
            );
        } else if (threeObj.isGroup) {
            // Group 类型 (第2-6层)
            threeObj.children.forEach(child => {
                if (child.material) {
                    // 保存原始透明度
                    if (!child.material.userData) {
                        child.material.userData = { originalOpacity: child.material.opacity };
                    }
                    
                    const origOpacity = child.material.userData.originalOpacity || 0.9;
                    child.material.opacity = isHighlighted ? origOpacity : targetOpacity;
                    
                    // 如果是 MeshPhongMaterial，调整发光强度
                    if (child.material.emissiveIntensity !== undefined) {
                        child.material.emissiveIntensity = targetEmissive;
                    }
                    
                    child.material.needsUpdate = true;
                }
                // 子对象也设置可见性
                child.visible = isHighlighted;
            });
            threeObj.scale.setScalar(targetScale);
        } else if (threeObj.material) {
            // 单个 Mesh
            threeObj.material.opacity = targetOpacity;
            if (threeObj.material.emissiveIntensity !== undefined) {
                threeObj.material.emissiveIntensity = targetEmissive;
            }
            threeObj.material.needsUpdate = true;
        }
    });
    
    console.log(`[高亮更新] 更新了 ${updatedCount} 个节点, 可见: ${visibleCount}, 隐藏: ${hiddenCount}, 高亮集合大小: ${highlightNodes.size}`);
}

// ==========================================
// === 信息面板 ===
// ==========================================
function showNodeInfo(node) {
    const infoPanel = document.getElementById('infoPanel');
    const nodeInfo = document.getElementById('nodeInfo');
    const pathContainer = document.getElementById('pathContainer');
    const levelConfig = layerConfig[node.group] || { name: '未知', color: '#ffffff' };
    
    // 检查节点是否在主路径上
    const isOnMainPath = mainPathData.nodes.some(n => n.id === node.id);
    
    nodeInfo.innerHTML = `
        <div class="label">节点名称</div>
        <div style="font-size: 16px; margin-bottom: 10px; color: ${node.color || levelConfig.color};">${node.name}</div>
        <div class="label">所属层级</div>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <span style="width: 12px; height: 12px; border-radius: 50%; background: ${node.color || levelConfig.color}; margin-right: 8px; box-shadow: 0 0 10px ${node.color || levelConfig.color};"></span>
            第${node.group}层 - ${node.layer_name || levelConfig.name}
        </div>
        <div class="label">节点类型</div>
        <div style="margin-bottom: 10px;">${node.node_type === 'category' ? '大类' : node.node_type === 'tag' ? '标签' : '知识点'}</div>
        ${isOnMainPath ? `<div style="margin-bottom: 10px; padding: 5px 10px; background: rgba(255,215,0,0.2); border-left: 3px solid ${CYBER_COLORS.gold}; color: ${CYBER_COLORS.gold};">✨ 主路径节点</div>` : ''}
    `;

    let pathHTML = '';
    if (node.node_type === 'category') {
        const children = graphData.nodes.filter(n => n.parent_id === node.id);
        if (children.length > 0) {
            pathHTML += `
                <div class="path-section">
                    <h5>📚 包含知识点 (${children.length}个)</h5>
                    ${children.slice(0, 20).map(child => `
                        <div class="path-item" onclick="focusNode('${child.id}')">
                            <div class="dot" style="background: ${child.color || levelConfig.color}; box-shadow: 0 0 8px ${child.color || levelConfig.color};"></div>
                            <span class="name">${child.name}</span>
                        </div>
                    `).join('')}
                    ${children.length > 20 ? `<div style="color: rgba(255,255,255,0.5); font-size: 12px; padding: 5px;">... 还有 ${children.length - 20} 个</div>` : ''}
                </div>
            `;
        }
    }
    if (node.parent_id) {
        const parent = graphData.nodes.find(n => n.id === node.parent_id);
        if (parent) {
            pathHTML += `
                <div class="path-section">
                    <h5>📁 所属大类</h5>
                    <div class="path-item" onclick="focusNode('${parent.id}')">
                        <div class="dot" style="background: ${parent.color || levelConfig.color}; box-shadow: 0 0 8px ${parent.color || levelConfig.color};"></div>
                        <span class="name">${parent.name}</span>
                    </div>
                </div>
            `;
        }
    }
    
    pathContainer.innerHTML = pathHTML;
    infoPanel.classList.add('show');
}

function hideInfoPanel() {
    document.getElementById('infoPanel').classList.remove('show');
}

function clearHighlight() {
    highlightNodes.clear();
    highlightLinks.clear();
    animatingLinks.clear();
    selectedNode = null;
    
    // 恢复所有节点的透明度
    updateNodeHighlight();
    
    // 强制刷新图谱渲染
    Graph.nodeColor(Graph.nodeColor());
    Graph.linkWidth(Graph.linkWidth());
    Graph.linkColor(Graph.linkColor());
    Graph.linkDirectionalParticles(Graph.linkDirectionalParticles());
}

function focusNode(nodeId) {
    const node = graphData.nodes.find(n => n.id === nodeId);
    if (node) handleNodeClick(node);
}

// ==========================================
// === 搜索功能 ===
// ==========================================
function searchNodes(query) {
    if (!query.trim()) {
        document.getElementById('searchResults').innerHTML = '';
        return;
    }
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(results => {
            const resultsContainer = document.getElementById('searchResults');
            if (results.length === 0) {
                resultsContainer.innerHTML = '<div style="color: rgba(255,255,255,0.5); font-size: 12px; padding: 5px;">未找到结果</div>';
                return;
            }
            resultsContainer.innerHTML = results.slice(0, 10).map(node => `
                <div class="search-result-item" style="border-left: 3px solid ${node.color || layerConfig[node.group]?.color || '#ffffff'}; box-shadow: inset 0 0 10px rgba(0,240,255,0.1);" onclick="focusNode('${node.id}')">
                    ${node.name}
                    <span style="font-size: 10px; color: ${CYBER_COLORS.cyan}; margin-left: 5px;">${node.layer_name}</span>
                </div>
            `).join('');
        })
        .catch(error => console.error('搜索失败:', error));
}

function showAllNodes() {
    clearHighlight();
    hideInfoPanel();
    Graph.cameraPosition({ x: 600, y: 400, z: 600 }, { x: 0, y: 0, z: 0 }, 1000);
}

function resetView() {
    Graph.cameraPosition({ x: 600, y: 400, z: 600 }, { x: 0, y: 0, z: 0 }, 1000);
}

// ==========================================
// === 自动旋转 ===
// ==========================================
function startAutoRotate() {
    function rotate() {
        if (autoRotate && Graph) {
            rotationAngle += 0.0008;
            const currentPos = Graph.cameraPosition();
            const dist = Math.sqrt(currentPos.x * currentPos.x + currentPos.z * currentPos.z);
            Graph.cameraPosition({
                x: dist * Math.sin(rotationAngle),
                y: currentPos.y,
                z: dist * Math.cos(rotationAngle)
            });
        }
        requestAnimationFrame(rotate);
    }
    rotate();
}

function toggleAutoRotate() {
    autoRotate = !autoRotate;
    document.getElementById('toggleRotateBtn').textContent = `自动旋转: ${autoRotate ? '开' : '关'}`;
}

function filterByLevel(level) {
    highlightNodes.clear();
    highlightLinks.clear();
    animatingLinks.clear();
    
    graphData.nodes.forEach(node => {
        if (node.group === parseInt(level)) highlightNodes.add(node.id);
    });
    
    graphData.links.forEach(link => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        const sourceNode = graphData.nodes.find(n => n.id === sourceId);
        const targetNode = graphData.nodes.find(n => n.id === targetId);
        if (sourceNode && targetNode && 
            (sourceNode.group === parseInt(level) || targetNode.group === parseInt(level))) {
            highlightLinks.add(link);
        }
    });
    
    Graph.nodeColor(Graph.nodeColor());
    Graph.linkWidth(Graph.linkWidth());
    Graph.linkColor(Graph.linkColor());
    
    const levelY = layerConfig[level]?.y || 0;
    Graph.cameraPosition({ x: 500, y: levelY + 200, z: 500 }, { x: 0, y: levelY, z: 0 }, 1000);
}

// ==========================================
// === 事件绑定 ===
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    initGraph();
    
    document.getElementById('searchInput').addEventListener('input', function(e) {
        searchNodes(e.target.value);
    });
    document.getElementById('showAllBtn').addEventListener('click', showAllNodes);
    document.getElementById('resetViewBtn').addEventListener('click', resetView);
    document.getElementById('toggleRotateBtn').addEventListener('click', toggleAutoRotate);
    document.getElementById('closeInfoBtn').addEventListener('click', function() {
        hideInfoPanel();
        clearHighlight();
    });
    document.querySelectorAll('.layer-label').forEach(label => {
        label.addEventListener('click', function() {
            const level = this.getAttribute('data-level');
            filterByLevel(level);
        });
    });
});
