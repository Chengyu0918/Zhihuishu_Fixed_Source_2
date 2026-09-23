// 多层知识图谱数据
// 5层结构：能力图谱 -> 问题图谱 -> 专业课程知识 -> 高阶基础知识 -> 数理基础知识

const graphData = {
    // 层级配置
    layers: [
        { id: 0, name: "能力图谱", color: "#FFD700", y: 60 },
        { id: 1, name: "问题图谱", color: "#FF6B6B", y: 180 },
        { id: 2, name: "专业课程知识", color: "#4ECDC4", y: 320 },
        { id: 3, name: "高阶基础知识", color: "#45B7D1", y: 480 },
        { id: 4, name: "数理基础知识", color: "#96CEB4", y: 620 }
    ],

    // 节点数据
    nodes: [
        // 第1层：能力图谱（能力目标）
        { id: "ability_1", name: "系统设计能力", layer: 0, x: 300 },
        { id: "ability_2", name: "问题分析能力", layer: 0, x: 500 },
        { id: "ability_3", name: "工程实践能力", layer: 0, x: 700 },
        { id: "ability_4", name: "创新研究能力", layer: 0, x: 900 },
        { id: "ability_5", name: "综合应用能力", layer: 0, x: 1100 },

        // 第2层：问题图谱（综合问题/应用问题/基础问题）
        { id: "problem_1", name: "电子战技术与应用", layer: 1, x: 200 },
        { id: "problem_2", name: "雷达数据处理", layer: 1, x: 350 },
        { id: "problem_3", name: "信号检测与估计", layer: 1, x: 500 },
        { id: "problem_4", name: "无源测向与定位技术", layer: 1, x: 680 },
        { id: "problem_5", name: "通信系统设计", layer: 1, x: 860 },
        { id: "problem_6", name: "图像处理应用", layer: 1, x: 1020 },
        { id: "problem_7", name: "机器学习应用", layer: 1, x: 1180 },

        // 第3层：专业课程知识
        { id: "course_1", name: "光电探测原理", layer: 2, x: 150 },
        { id: "course_2", name: "雷达原理与系统", layer: 2, x: 300 },
        { id: "course_3", name: "雷达信号处理", layer: 2, x: 450 },
        { id: "course_4", name: "阵列信号处理", layer: 2, x: 600 },
        { id: "course_5", name: "数字信号处理", layer: 2, x: 750 },
        { id: "course_6", name: "通信原理", layer: 2, x: 900 },
        { id: "course_7", name: "数字图像处理", layer: 2, x: 1050 },
        { id: "course_8", name: "模式识别", layer: 2, x: 1200 },

        // 第4层：高阶基础知识
        { id: "advanced_1", name: "程序设计(C)", layer: 3, x: 200 },
        { id: "advanced_2", name: "数据结构", layer: 3, x: 350 },
        { id: "advanced_3", name: "大数据导论", layer: 3, x: 500 },
        { id: "advanced_4", name: "人工智能导论", layer: 3, x: 680 },
        { id: "advanced_5", name: "电路分析", layer: 3, x: 860 },
        { id: "advanced_6", name: "信号与系统", layer: 3, x: 1020 },
        { id: "advanced_7", name: "电磁场理论", layer: 3, x: 1180 },

        // 第5层：数理基础知识
        { id: "math_1", name: "高等数学", layer: 4, x: 200 },
        { id: "math_2", name: "高等代数", layer: 4, x: 350 },
        { id: "math_3", name: "概率论与数理统计", layer: 4, x: 550 },
        { id: "math_4", name: "大学物理", layer: 4, x: 750 },
        { id: "math_5", name: "大学物理实验", layer: 4, x: 950 },
        { id: "math_6", name: "复变函数", layer: 4, x: 1100 },
        { id: "math_7", name: "离散数学", layer: 4, x: 1250 }
    ],

    // 连接关系（从下层指向上层）
    links: [
        // 数理基础 -> 高阶基础
        { source: "math_1", target: "advanced_1" },
        { source: "math_1", target: "advanced_5" },
        { source: "math_1", target: "advanced_6" },
        { source: "math_2", target: "advanced_1" },
        { source: "math_2", target: "advanced_2" },
        { source: "math_3", target: "advanced_3" },
        { source: "math_3", target: "advanced_4" },
        { source: "math_3", target: "advanced_6" },
        { source: "math_4", target: "advanced_5" },
        { source: "math_4", target: "advanced_7" },
        { source: "math_5", target: "advanced_5" },
        { source: "math_6", target: "advanced_6" },
        { source: "math_6", target: "advanced_7" },
        { source: "math_7", target: "advanced_2" },
        { source: "math_7", target: "advanced_4" },

        // 高阶基础 -> 专业课程
        { source: "advanced_1", target: "course_3" },
        { source: "advanced_1", target: "course_5" },
        { source: "advanced_1", target: "course_7" },
        { source: "advanced_2", target: "course_3" },
        { source: "advanced_2", target: "course_8" },
        { source: "advanced_3", target: "course_8" },
        { source: "advanced_4", target: "course_8" },
        { source: "advanced_4", target: "course_7" },
        { source: "advanced_5", target: "course_1" },
        { source: "advanced_5", target: "course_2" },
        { source: "advanced_5", target: "course_6" },
        { source: "advanced_6", target: "course_2" },
        { source: "advanced_6", target: "course_3" },
        { source: "advanced_6", target: "course_4" },
        { source: "advanced_6", target: "course_5" },
        { source: "advanced_6", target: "course_6" },
        { source: "advanced_7", target: "course_1" },
        { source: "advanced_7", target: "course_2" },
        { source: "advanced_7", target: "course_4" },

        // 专业课程 -> 问题图谱
        { source: "course_1", target: "problem_1" },
        { source: "course_1", target: "problem_4" },
        { source: "course_2", target: "problem_1" },
        { source: "course_2", target: "problem_2" },
        { source: "course_2", target: "problem_4" },
        { source: "course_3", target: "problem_2" },
        { source: "course_3", target: "problem_3" },
        { source: "course_4", target: "problem_3" },
        { source: "course_4", target: "problem_4" },
        { source: "course_5", target: "problem_3" },
        { source: "course_5", target: "problem_5" },
        { source: "course_6", target: "problem_5" },
        { source: "course_7", target: "problem_6" },
        { source: "course_7", target: "problem_7" },
        { source: "course_8", target: "problem_6" },
        { source: "course_8", target: "problem_7" },

        // 问题图谱 -> 能力图谱
        { source: "problem_1", target: "ability_1" },
        { source: "problem_1", target: "ability_3" },
        { source: "problem_2", target: "ability_1" },
        { source: "problem_2", target: "ability_2" },
        { source: "problem_3", target: "ability_2" },
        { source: "problem_3", target: "ability_4" },
        { source: "problem_4", target: "ability_1" },
        { source: "problem_4", target: "ability_3" },
        { source: "problem_5", target: "ability_3" },
        { source: "problem_5", target: "ability_5" },
        { source: "problem_6", target: "ability_4" },
        { source: "problem_6", target: "ability_5" },
        { source: "problem_7", target: "ability_4" },
        { source: "problem_7", target: "ability_5" }
    ]
};

// 导出数据
if (typeof module !== 'undefined' && module.exports) {
    module.exports = graphData;
}
