# 文件名: init_db.py
import sqlite3

def init_db():
    # 1. 连接数据库 (如果不存在会自动创建)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # 2. 创建节点表 (Nodes)
    # id: 唯一标识
    # name: 显示名称
    # group_level: 1-6 代表六个层级
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            name TEXT,
            group_level INTEGER
        )
    ''')

    # 3. 创建关系表 (Edges)
    # source: 起点ID, target: 终点ID
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            source TEXT,
            target TEXT
        )
    ''')

    # 4. 插入测试数据 (模拟6层结构)
    # 第1层: 课程
    # 第2层: 章
    # 第3层: 节
    # 第4层: 知识点
    # 第5层: 子概念
    # 第6层: 题目
    
    nodes_data = [
        # 第1层 - 课程
        ('course1', '通信工程', 1),
        ('course2', '信号与系统', 1),
        
        # 第2层 - 章
        ('ch1', '第一章：信号概述', 2),
        ('ch2', '第二章：系统分析', 2),
        ('ch3', '第三章：频域分析', 2),
        ('ch4', '第四章：时域分析', 2),
        
        # 第3层 - 节
        ('sec1', '1.1 信号分类', 3),
        ('sec2', '1.2 信号运算', 3),
        ('sec3', '2.1 系统特性', 3),
        ('sec4', '2.2 系统响应', 3),
        ('sec5', '3.1 傅里叶变换', 3),
        ('sec6', '3.2 拉普拉斯变换', 3),
        ('sec7', '4.1 卷积运算', 3),
        ('sec8', '4.2 微分方程', 3),
        
        # 第4层 - 知识点
        ('kp1', '连续信号', 4),
        ('kp2', '离散信号', 4),
        ('kp3', '奇异信号', 4),
        ('kp4', '信号平移', 4),
        ('kp5', '信号尺度变换', 4),
        ('kp6', '线性系统', 4),
        ('kp7', '时不变系统', 4),
        ('kp8', '零输入响应', 4),
        ('kp9', '零状态响应', 4),
        ('kp10', 'FT性质', 4),
        ('kp11', 'FT应用', 4),
        ('kp12', 'LT性质', 4),
        ('kp13', 'LT应用', 4),
        ('kp14', '卷积定理', 4),
        ('kp15', '卷积计算', 4),
        ('kp16', '常系数微分方程', 4),
        
        # 第5层 - 子概念
        ('sub1', '冲激函数δ(t)', 5),
        ('sub2', '阶跃函数u(t)', 5),
        ('sub3', '斜坡函数', 5),
        ('sub4', '时移性质', 5),
        ('sub5', '频移性质', 5),
        ('sub6', '卷积性质', 5),
        ('sub7', '初值定理', 5),
        ('sub8', '终值定理', 5),
        ('sub9', '图解法', 5),
        ('sub10', '解析法', 5),
        ('sub11', '齐次解', 5),
        ('sub12', '特解', 5),
        
        # 第6层 - 题目
        ('q1', '题目：求δ(2t-1)的值', 6),
        ('q2', '题目：画出u(t-2)波形', 6),
        ('q3', '题目：求信号的傅里叶变换', 6),
        ('q4', '题目：利用时移性质求FT', 6),
        ('q5', '题目：求卷积x(t)*h(t)', 6),
        ('q6', '题目：用图解法求卷积', 6),
        ('q7', '题目：求系统的冲激响应', 6),
        ('q8', '题目：求微分方程的解', 6),
        ('q9', '题目：判断系统稳定性', 6),
        ('q10', '题目：求拉普拉斯变换', 6),
    ]
    
    links_data = [
        # 课程 -> 章
        ('course1', 'ch1'),
        ('course1', 'ch2'),
        ('course2', 'ch3'),
        ('course2', 'ch4'),
        
        # 章 -> 节
        ('ch1', 'sec1'),
        ('ch1', 'sec2'),
        ('ch2', 'sec3'),
        ('ch2', 'sec4'),
        ('ch3', 'sec5'),
        ('ch3', 'sec6'),
        ('ch4', 'sec7'),
        ('ch4', 'sec8'),
        
        # 节 -> 知识点
        ('sec1', 'kp1'),
        ('sec1', 'kp2'),
        ('sec1', 'kp3'),
        ('sec2', 'kp4'),
        ('sec2', 'kp5'),
        ('sec3', 'kp6'),
        ('sec3', 'kp7'),
        ('sec4', 'kp8'),
        ('sec4', 'kp9'),
        ('sec5', 'kp10'),
        ('sec5', 'kp11'),
        ('sec6', 'kp12'),
        ('sec6', 'kp13'),
        ('sec7', 'kp14'),
        ('sec7', 'kp15'),
        ('sec8', 'kp16'),
        
        # 知识点 -> 子概念
        ('kp3', 'sub1'),
        ('kp3', 'sub2'),
        ('kp3', 'sub3'),
        ('kp10', 'sub4'),
        ('kp10', 'sub5'),
        ('kp14', 'sub6'),
        ('kp12', 'sub7'),
        ('kp12', 'sub8'),
        ('kp15', 'sub9'),
        ('kp15', 'sub10'),
        ('kp16', 'sub11'),
        ('kp16', 'sub12'),
        
        # 子概念 -> 题目
        ('sub1', 'q1'),
        ('sub2', 'q2'),
        ('sub4', 'q3'),
        ('sub5', 'q4'),
        ('sub6', 'q5'),
        ('sub9', 'q6'),
        ('sub10', 'q7'),
        ('sub11', 'q8'),
        ('sub12', 'q9'),
        ('sub8', 'q10'),
    ]

    # 清空旧数据
    cursor.execute('DELETE FROM nodes')
    cursor.execute('DELETE FROM links')
    
    cursor.executemany('INSERT OR IGNORE INTO nodes VALUES (?,?,?)', nodes_data)
    cursor.executemany('INSERT OR IGNORE INTO links VALUES (?,?)', links_data)

    conn.commit()
    conn.close()
    print("数据库初始化完成！文件名为 database.db")
    print(f"已插入 {len(nodes_data)} 个节点和 {len(links_data)} 条连接")

if __name__ == '__main__':
    init_db()
