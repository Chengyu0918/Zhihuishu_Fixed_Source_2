#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识图谱系统 - 主启动程序
系统启动与环境预检模块
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 系统配置
DATABASE_PATH = 'database.db'
DATA_DIR = 'data'
DATAJSON_DIR = 'datajson'

# 数据库Schema定义（预期的表结构）
EXPECTED_TABLES = {
    'nodes': ['id', 'name', 'layer', 'category'],
    'edges': ['id', 'source_id', 'target_id', 'relation_type', 'weight'],
}

# 支持的数据文件格式
SUPPORTED_DATA_FORMATS = ['.xlsx', '.xls', '.json', '.csv']


class SystemChecker:
    """系统环境检查器"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        
    def log_info(self, message):
        """记录信息"""
        self.info.append(message)
        logger.info(message)
        
    def log_warning(self, message):
        """记录警告"""
        self.warnings.append(message)
        logger.warning(message)
        
    def log_error(self, message):
        """记录错误"""
        self.errors.append(message)
        logger.error(message)
        
    def check_database_connection(self):
        """测试数据库连接"""
        self.log_info("=" * 50)
        self.log_info("开始数据库连接测试...")
        
        if not os.path.exists(DATABASE_PATH):
            self.log_error(f"数据库文件不存在: {DATABASE_PATH}")
            return False
            
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # 测试基本查询
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            self.log_info(f"SQLite 版本: {version}")
            
            # 检查数据库文件大小
            db_size = os.path.getsize(DATABASE_PATH)
            self.log_info(f"数据库文件大小: {db_size / 1024:.2f} KB")
            
            conn.close()
            self.log_info("✓ 数据库连接测试通过")
            return True
            
        except sqlite3.Error as e:
            self.log_error(f"数据库连接失败: {e}")
            return False
            
    def check_schema_integrity(self):
        """校验Schema完整性"""
        self.log_info("=" * 50)
        self.log_info("开始Schema完整性校验...")
        
        if not os.path.exists(DATABASE_PATH):
            self.log_error("无法校验Schema: 数据库文件不存在")
            return False
            
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            self.log_info(f"检测到 {len(existing_tables)} 个数据表")
            
            schema_valid = True
            
            for table_name, expected_columns in EXPECTED_TABLES.items():
                if table_name not in existing_tables:
                    self.log_error(f"缺少必要的表: {table_name}")
                    schema_valid = False
                    continue
                    
                # 检查表的列
                cursor.execute(f"PRAGMA table_info({table_name})")
                actual_columns = {row[1] for row in cursor.fetchall()}
                
                missing_columns = set(expected_columns) - actual_columns
                if missing_columns:
                    self.log_warning(f"表 {table_name} 缺少列: {missing_columns}")
                    
                # 统计表中的记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                self.log_info(f"  - 表 {table_name}: {count} 条记录")
                
            # 检查额外的表
            extra_tables = existing_tables - set(EXPECTED_TABLES.keys()) - {'sqlite_sequence'}
            if extra_tables:
                self.log_info(f"检测到额外的表: {extra_tables}")
                for table in extra_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.log_info(f"  - 表 {table}: {count} 条记录")
                    
            conn.close()
            
            if schema_valid:
                self.log_info("✓ Schema完整性校验通过")
            return schema_valid
            
        except sqlite3.Error as e:
            self.log_error(f"Schema校验失败: {e}")
            return False
            
    def check_data_files(self):
        """检查数据文件格式"""
        self.log_info("=" * 50)
        self.log_info("开始数据文件格式检查...")
        
        total_files = 0
        valid_files = 0
        file_stats = {}
        
        # 检查data目录
        if os.path.exists(DATA_DIR):
            for root, dirs, files in os.walk(DATA_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    ext = os.path.splitext(file)[1].lower()
                    
                    if ext in SUPPORTED_DATA_FORMATS:
                        total_files += 1
                        valid_files += 1
                        file_stats[ext] = file_stats.get(ext, 0) + 1
                    elif ext and not file.startswith('.'):
                        total_files += 1
                        self.log_warning(f"不支持的文件格式: {file_path}")
        else:
            self.log_warning(f"数据目录不存在: {DATA_DIR}")
            
        # 检查datajson目录
        if os.path.exists(DATAJSON_DIR):
            for file in os.listdir(DATAJSON_DIR):
                file_path = os.path.join(DATAJSON_DIR, file)
                if os.path.isfile(file_path):
                    ext = os.path.splitext(file)[1].lower()
                    if ext == '.json':
                        total_files += 1
                        valid_files += 1
                        file_stats[ext] = file_stats.get(ext, 0) + 1
        else:
            self.log_warning(f"JSON数据目录不存在: {DATAJSON_DIR}")
            
        self.log_info(f"检测到数据文件总数: {total_files}")
        self.log_info(f"有效数据文件数量: {valid_files}")
        
        if file_stats:
            self.log_info("文件类型统计:")
            for ext, count in sorted(file_stats.items()):
                self.log_info(f"  - {ext}: {count} 个文件")
                
        self.log_info("✓ 数据文件格式检查完成")
        return valid_files > 0
        
    def check_dependencies(self):
        """检查Python依赖"""
        self.log_info("=" * 50)
        self.log_info("开始依赖检查...")
        
        required_modules = [
            ('flask', 'Flask Web框架'),
            ('openpyxl', 'Excel文件处理'),
            ('sqlite3', 'SQLite数据库'),
        ]
        
        optional_modules = [
            ('pandas', 'Pandas数据处理'),
            ('numpy', 'NumPy数值计算'),
        ]
        
        all_required_present = True
        
        for module_name, description in required_modules:
            try:
                __import__(module_name)
                self.log_info(f"  ✓ {module_name} ({description})")
            except ImportError:
                self.log_error(f"  ✗ {module_name} ({description}) - 未安装")
                all_required_present = False
                
        for module_name, description in optional_modules:
            try:
                __import__(module_name)
                self.log_info(f"  ✓ {module_name} ({description}) [可选]")
            except ImportError:
                self.log_warning(f"  - {module_name} ({description}) [可选] - 未安装")
                
        if all_required_present:
            self.log_info("✓ 必要依赖检查通过")
        return all_required_present
        
    def run_all_checks(self):
        """运行所有检查"""
        self.log_info("=" * 50)
        self.log_info("知识图谱系统 - 环境预检")
        self.log_info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_info(f"工作目录: {os.getcwd()}")
        self.log_info(f"Python版本: {sys.version}")
        
        results = {
            '依赖检查': self.check_dependencies(),
            '数据库连接': self.check_database_connection(),
            'Schema完整性': self.check_schema_integrity(),
            '数据文件': self.check_data_files(),
        }
        
        self.log_info("=" * 50)
        self.log_info("环境预检结果汇总:")
        
        all_passed = True
        for check_name, passed in results.items():
            status = "✓ 通过" if passed else "✗ 失败"
            self.log_info(f"  {check_name}: {status}")
            if not passed:
                all_passed = False
                
        if self.warnings:
            self.log_info(f"\n警告数量: {len(self.warnings)}")
            
        if self.errors:
            self.log_info(f"错误数量: {len(self.errors)}")
            
        self.log_info("=" * 50)
        
        if all_passed:
            self.log_info("✓ 系统环境预检全部通过，可以正常启动")
        else:
            self.log_error("✗ 系统环境预检存在问题，请检查上述错误")
            
        return all_passed


def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("    知识图谱系统 - 启动中...")
    print("=" * 50 + "\n")
    
    # 创建检查器并运行所有检查
    checker = SystemChecker()
    all_passed = checker.run_all_checks()
    
    if all_passed:
        print("\n系统初始化完成，环境预检通过。")
        print("如需启动Web服务，请运行: python app.py\n")
        return 0
    else:
        print("\n系统初始化失败，请检查上述错误信息。\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
