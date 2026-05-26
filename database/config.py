"""
数据库配置模块
SQLite 数据库连接配置
"""

import os
import json
import logging

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置类"""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.config_file = "db_config.json"
        # 项目根目录
        self._project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._config = self._load_config()
    
    def _load_config(self):
        """
        从配置文件加载数据库配置
        """
        config = {
            'enabled': True,  # 默认启用数据库
            'db_type': 'sqlite',  # 数据库类型
            'database': 'data/scholarship.db',  # SQLite 数据库文件路径
            'echo': False  # 是否打印SQL语句
        }
        
        # 尝试从配置文件读取
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    logger.info(f"从配置文件加载数据库配置: {self.config_file}")
            except Exception as e:
                logger.warning(f"读取数据库配置文件失败: {e}")
        
        return config
    
    def get_connection_string(self):
        """
        生成数据库连接字符串
        格式: sqlite:///absolute/path/to/data.db
        """
        if not self._config['enabled']:
            return None
        
        database = self._config['database']
        
        # SQLite：数据库文件存储在项目根目录下
        if os.path.isabs(database):
            db_path = database
        else:
            db_path = os.path.join(self._project_root, database)
        
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"已创建数据库目录: {db_dir}")
            except Exception as e:
                logger.warning(f"创建数据库目录失败: {e}")
        
        # 使用正斜杠路径
        db_path_posix = db_path.replace('\\', '/')
        return f"sqlite:///{db_path_posix}"
    
    def get_engine_options(self):
        """获取数据库引擎选项"""
        return {
            'echo': self._config['echo'],
            'connect_args': {'check_same_thread': False}
        }
    
    def is_enabled(self):
        """检查数据库是否启用"""
        return self._config['enabled']


# 全局配置实例
db_config = DatabaseConfig()