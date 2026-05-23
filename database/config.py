"""
数据库配置模块
从环境变量或配置文件读取数据库连接字符串
"""

import os
import json
import logging
from urllib.parse import quote_plus

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseConfig:
    """数据库配置类"""
    
    def __init__(self):
        # 兼容两种配置文件命名：db_config.json（根目录模板）与 database_config.json（历史遗留）
        # 优先使用 db_config.json
        self.config_files = ["db_config.json", "database_config.json"]
        self.config_file = self.config_files[0]
        self._config = self._load_config()
    
    def _load_config(self):
        """
        从配置文件或环境变量加载数据库配置
        优先级：环境变量 > 配置文件 > 默认值
        """
        config = {
            'enabled': False,  # 默认禁用数据库
            'db_type': 'postgresql',  # 数据库类型：postgresql 或 mysql
            'host': 'localhost',
            'port': 5432,
            'username': '',
            'password': '',
            'database': 'scholarship_db',
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'echo': False  # 是否打印SQL语句
        }
        
        # 尝试从配置文件读取（兼容两种命名）
        for candidate in self.config_files:
            if os.path.exists(candidate):
                try:
                    with open(candidate, 'r', encoding='utf-8') as f:
                        file_config = json.load(f)
                        config.update(file_config)
                        self.config_file = candidate
                        logger.info(f"从配置文件加载数据库配置: {candidate}")
                        break  # 成功加载，不再尝试后续候选文件
                except Exception as e:
                    logger.warning(f"读取数据库配置文件失败: {candidate} -> {e}，尝试下一个候选")
                    continue
        
        # 从环境变量读取（优先级最高）
        env_mapping = {
            'DB_ENABLED': 'enabled',
            'DB_TYPE': 'db_type',
            'DB_HOST': 'host',
            'DB_PORT': 'port',
            'DB_USERNAME': 'username',
            'DB_PASSWORD': 'password',
            'DB_DATABASE': 'database',
            'DB_POOL_SIZE': 'pool_size',
            'DB_MAX_OVERFLOW': 'max_overflow',
            'DB_POOL_TIMEOUT': 'pool_timeout',
            'DB_POOL_RECYCLE': 'pool_recycle',
            'DB_ECHO': 'echo'
        }
        
        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 类型转换
                if config_key == 'enabled' or config_key == 'echo':
                    config[config_key] = env_value.lower() in ('true', '1', 'yes')
                elif config_key == 'port' or config_key in ('pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle'):
                    try:
                        config[config_key] = int(env_value)
                    except ValueError:
                        logger.warning(f"环境变量 {env_key} 值无效: {env_value}")
                else:
                    config[config_key] = env_value
        
        return config
    
    def get_connection_string(self):
        """
        生成数据库连接字符串
        格式：
        - PostgreSQL: postgresql://username:password@host:port/database
        - MySQL: mysql+pymysql://username:password@host:port/database
        """
        if not self._config['enabled']:
            return None
        
        db_type = self._config['db_type'].lower()
        username = self._config['username']
        password = self._config['password']
        host = self._config['host']
        port = self._config['port']
        database = self._config['database']
        
        if db_type == 'postgresql':
            connection_string = f"postgresql://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/{database}"
        elif db_type == 'mysql':
            connection_string = f"mysql+pymysql://{quote_plus(username)}:{quote_plus(password)}@{host}:{port}/{database}"
        else:
            logger.error(f"不支持的数据库类型: {db_type}")
            return None
        
        return connection_string
    
    def get_engine_options(self):
        """获取数据库引擎选项"""
        return {
            'pool_size': self._config['pool_size'],
            'max_overflow': self._config['max_overflow'],
            'pool_timeout': self._config['pool_timeout'],
            'pool_recycle': self._config['pool_recycle'],
            'echo': self._config['echo']
        }
    
    def is_enabled(self):
        """检查数据库是否启用"""
        return self._config['enabled']
    
    def create_sample_config(self):
        """创建示例配置文件"""
        sample_config = {
            'enabled': False,
            'db_type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'username': 'your_username',
            'password': 'your_password',
            'database': 'scholarship_db',
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'echo': False
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=4, ensure_ascii=False)
            logger.info(f"已创建示例配置文件: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"创建示例配置文件失败: {e}")
            return False


# 全局配置实例
db_config = DatabaseConfig()
