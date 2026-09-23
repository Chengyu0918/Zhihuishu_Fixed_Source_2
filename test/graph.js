// 多层知识图谱可视化
class KnowledgeGraph {
    constructor(containerId, data) {
        this.container = document.getElementById(containerId);
        this.svg = document.getElementById('graph-svg');
        this.data = data;
        this.nodeMap = new Map();
        this.selectedNode = null;
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        
        this.init();
    }

    init() {
        // 创建节点映射
        this.data.nodes.forEach(node => {
            this.nodeMap.set(node.id, node);
        });

        // 设置SVG尺寸
        this.svg.setAttribute('viewBox', `0 0 ${this.width} ${this.height}`);
        
        // 绘制图谱
        this.render();
        
        // 绑定事件
        this.bindEvents();
    }

    render() {
        // 清空SVG
        this.svg.innerHTML = '';

        // 创建defs用于渐变和滤镜
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        
        // 添加发光滤镜
        const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
        filter.setAttribute('id', 'glow');
        filter.innerHTML = `
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        `;
        defs.appendChild(filter);
        this.svg.appendChild(defs);

        // 绘制层级背景和标签
        this.drawLayers();

        // 创建连接线组（放在节点下面）
        this.linksGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.linksGroup.setAttribute('class', 'links-group');
        this.svg.appendChild(this.linksGroup);

        // 绘制连接线
        this.drawLinks();

        // 创建节点组
        this.nodesGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        this.nodesGroup.setAttribute('class', 'nodes-group');
        this.svg.appendChild(this.nodesGroup);

        // 绘制节点
        this.drawNodes();
    }

    drawLayers() {
        const layerGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        layerGroup.setAttribute('class', 'layers-group');

        this.data.layers.forEach((layer, index) => {
            // 层级标签
            const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            label.setAttribute('x', 20);
            label.setAttribute('y', layer.y);
            label.setAttribute('class', 'layer-label');
            label.setAttribute('fill', layer.color);
            label.textContent = layer.name;
            layerGroup.appendChild(label);

            // 层级分隔线（除了最后一层）
            if (index < this.data.layers.length - 1) {
                const nextLayer = this.data.layers[index + 1];
                const lineY = (layer.y + nextLayer.y) / 2 + 20;
                
                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line.setAttribute('x1', 0);
                line.setAttribute('y1', lineY);
                line.setAttribute('x2', this.width);
                line.setAttribute('y2', lineY);
                line.setAttribute('class', 'layer-separator');
                layerGroup.appendChild(line);
            }
        });

        this.svg.appendChild(layerGroup);
    }

    drawLinks() {
        this.data.links.forEach(link => {
            const sourceNode = this.nodeMap.get(link.source);
            const targetNode = this.nodeMap.get(link.target);
            
            if (!sourceNode || !targetNode) return;

            const sourceLayer = this.data.layers[sourceNode.layer];
            const targetLayer = this.data.layers[targetNode.layer];

            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            
            // 使用贝塞尔曲线创建平滑的连接
            const x1 = sourceNode.x;
            const y1 = sourceLayer.y;
            const x2 = targetNode.x;
            const y2 = targetLayer.y;
            
            const midY = (y1 + y2) / 2;
            const d = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
            
            path.setAttribute('d', d);
            path.setAttribute('class', 'link');
            path.setAttribute('data-source', link.source);
            path.setAttribute('data-target', link.target);
            
            this.linksGroup.appendChild(path);
        });
    }

    drawNodes() {
        this.data.nodes.forEach(node => {
            const layer = this.data.layers[node.layer];
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', 'node');
            group.setAttribute('data-id', node.id);
            group.setAttribute('data-layer', node.layer);
            group.setAttribute('transform', `translate(${node.x}, ${layer.y})`);

            // 节点圆形
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('r', this.getNodeRadius(node.layer));
            circle.setAttribute('fill', layer.color);
            circle.setAttribute('stroke', this.darkenColor(layer.color, 20));
            group.appendChild(circle);

            // 节点文字
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('y', this.getNodeRadius(node.layer) + 15);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('font-size', '11px');
            text.textContent = this.truncateText(node.name, 8);
            group.appendChild(text);

            // 添加title提示
            const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
            title.textContent = node.name;
            group.appendChild(title);

            this.nodesGroup.appendChild(group);
        });
    }

    getNodeRadius(layer) {
        // 根据层级返回不同大小的节点
        const sizes = [18, 15, 13, 12, 11];
        return sizes[layer] || 12;
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    darkenColor(color, percent) {
        const num = parseInt(color.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) - amt;
        const G = (num >> 8 & 0x00FF) - amt;
        const B = (num & 0x0000FF) - amt;
        return '#' + (0x1000000 + 
            (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + 
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + 
            (B < 255 ? B < 1 ? 0 : B : 255)
        ).toString(16).slice(1);
    }

    bindEvents() {
        // 节点点击事件
        this.nodesGroup.addEventListener('click', (e) => {
            const nodeGroup = e.target.closest('.node');
            if (nodeGroup) {
                const nodeId = nodeGroup.getAttribute('data-id');
                this.selectNode(nodeId);
            }
        });

        // 重置按钮
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetView();
        });

        // 窗口大小变化
        window.addEventListener('resize', () => {
            this.width = this.container.clientWidth;
            this.height = this.container.clientHeight;
            this.svg.setAttribute('viewBox', `0 0 ${this.width} ${this.height}`);
        });
    }

    selectNode(nodeId) {
        const node = this.nodeMap.get(nodeId);
        if (!node) return;

        this.selectedNode = node;

        // 找到所有连接到此节点的路径（向上追溯到顶层）
        const connectedNodes = this.findConnectedPath(nodeId);
        const connectedLinks = this.findConnectedLinks(connectedNodes);

        // 更新视觉效果
        this.updateVisuals(connectedNodes, connectedLinks);

        // 更新信息面板
        this.updateInfoPanel(node, connectedNodes);
    }

    findConnectedPath(nodeId) {
        const node = this.nodeMap.get(nodeId);
        if (!node) return new Set();

        const connected = new Set([nodeId]);
        
        // 向上追溯（找到所有target为当前节点或已连接节点的link）
        const findUpward = (currentIds) => {
            const newIds = new Set();
            this.data.links.forEach(link => {
                if (currentIds.has(link.source)) {
                    connected.add(link.target);
                    newIds.add(link.target);
                }
            });
            if (newIds.size > 0) {
                findUpward(newIds);
            }
        };

        // 向下追溯（找到所有source为当前节点或已连接节点的link）
        const findDownward = (currentIds) => {
            const newIds = new Set();
            this.data.links.forEach(link => {
                if (currentIds.has(link.target)) {
                    connected.add(link.source);
                    newIds.add(link.source);
                }
            });
            if (newIds.size > 0) {
                findDownward(newIds);
            }
        };

        findUpward(new Set([nodeId]));
        findDownward(new Set([nodeId]));

        return connected;
    }

    findConnectedLinks(connectedNodes) {
        const connectedLinks = new Set();
        this.data.links.forEach(link => {
            if (connectedNodes.has(link.source) && connectedNodes.has(link.target)) {
                connectedLinks.add(`${link.source}-${link.target}`);
            }
        });
        return connectedLinks;
    }

    updateVisuals(connectedNodes, connectedLinks) {
        // 更新节点样式
        this.nodesGroup.querySelectorAll('.node').forEach(nodeEl => {
            const nodeId = nodeEl.getAttribute('data-id');
            nodeEl.classList.remove('highlighted', 'dimmed', 'selected');
            
            if (nodeId === this.selectedNode.id) {
                nodeEl.classList.add('selected', 'highlighted');
            } else if (connectedNodes.has(nodeId)) {
                nodeEl.classList.add('highlighted');
            } else {
                nodeEl.classList.add('dimmed');
            }
        });

        // 更新连接线样式
        this.linksGroup.querySelectorAll('.link').forEach(linkEl => {
            const source = linkEl.getAttribute('data-source');
            const target = linkEl.getAttribute('data-target');
            const linkKey = `${source}-${target}`;
            
            linkEl.classList.remove('highlighted', 'dimmed');
            
            if (connectedLinks.has(linkKey)) {
                linkEl.classList.add('highlighted');
            } else {
                linkEl.classList.add('dimmed');
            }
        });
    }

    updateInfoPanel(node, connectedNodes) {
        const infoPanel = document.getElementById('node-info');
        const layer = this.data.layers[node.layer];

        // 按层级组织连接的节点
        const nodesByLayer = {};
        connectedNodes.forEach(nodeId => {
            const n = this.nodeMap.get(nodeId);
            if (n) {
                if (!nodesByLayer[n.layer]) {
                    nodesByLayer[n.layer] = [];
                }
                nodesByLayer[n.layer].push(n);
            }
        });

        let html = `
            <div style="margin-bottom: 15px;">
                <strong>选中节点：</strong>
                <span class="path-item" style="background: ${layer.color};">${node.name}</span>
                <br><br>
                <strong>所在层级：</strong> ${layer.name}（第${node.layer + 1}层）
            </div>
            <div>
                <strong>知识路径（从底层到顶层）：</strong>
                <div class="path-container">
        `;

        // 从底层到顶层显示路径
        for (let i = this.data.layers.length - 1; i >= 0; i--) {
            if (nodesByLayer[i] && nodesByLayer[i].length > 0) {
                const layerInfo = this.data.layers[i];
                html += `<div style="width: 100%; margin: 10px 0;">
                    <div style="color: ${layerInfo.color}; font-weight: bold; margin-bottom: 5px;">
                        ${layerInfo.name}：
                    </div>
                    <div>`;
                
                nodesByLayer[i].forEach(n => {
                    const isSelected = n.id === node.id;
                    html += `<span class="path-item" style="background: ${layerInfo.color}; ${isSelected ? 'border: 2px solid #333; font-weight: bold;' : ''}">${n.name}</span>`;
                });
                
                html += `</div></div>`;
                
                if (i > 0) {
                    html += `<div style="text-align: center; width: 100%; color: #999;">↑</div>`;
                }
            }
        }

        html += `</div></div>`;

        // 统计信息
        html += `
            <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #ddd;">
                <strong>连接统计：</strong>
                <ul style="margin-top: 10px; padding-left: 20px;">
                    <li>关联节点总数：${connectedNodes.size} 个</li>
                    <li>覆盖层级数：${Object.keys(nodesByLayer).length} 层</li>
                </ul>
            </div>
        `;

        infoPanel.innerHTML = html;
    }

    resetView() {
        this.selectedNode = null;

        // 移除所有高亮和暗淡效果
        this.nodesGroup.querySelectorAll('.node').forEach(nodeEl => {
            nodeEl.classList.remove('highlighted', 'dimmed', 'selected');
        });

        this.linksGroup.querySelectorAll('.link').forEach(linkEl => {
            linkEl.classList.remove('highlighted', 'dimmed');
        });

        // 重置信息面板
        document.getElementById('node-info').innerHTML = '点击节点查看详情';
    }
}

// 初始化图谱
document.addEventListener('DOMContentLoaded', () => {
    const graph = new KnowledgeGraph('graph-container', graphData);
});
