"""
数据库初始化模块
提供数据库初始化和健康检查功能
"""

import logging
from sqlalchemy import text
from .connection import get_engine, check_database_available, session_scope

# 配置日志
logger = logging.getLogger(__name__)


def init_database():
    """
    初始化数据库
    检查数据库连接并记录状态
    
    返回:
        bool: 初始化成功返回 True，失败返回 False
    """
    logger.info("正在初始化数据库模块...")
    
    # 检查数据库是否可用
    if not check_database_available():
        logger.info("数据库未启用，程序将正常运行（不使用数据库功能）")
        return False
    
    try:
        # 测试数据库连接
        with session_scope() as session:
            if session:
                result = session.execute(text("SELECT 1"))
                logger.info("数据库连接测试成功")
                return True
            else:
                logger.warning("数据库会话创建失败")
                return False
    
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def health_check():
    """
    数据库健康检查
    检查数据库连接是否正常
    
    返回:
        dict: 包含健康检查结果的字典
        {
            'available': bool,  # 数据库是否可用
            'status': str,      # 状态描述
            'message': str      # 详细信息
        }
    """
    result = {
        'available': False,
        'status': 'unavailable',
        'message': ''
    }
    
    if not check_database_available():
        result['message'] = '数据库未启用或不可用'
        return result
    
    try:
        with session_scope() as session:
            if session:
                session.execute(text("SELECT 1"))
                result['available'] = True
                result['status'] = 'healthy'
                result['message'] = '数据库连接正常'
            else:
                result['message'] = '无法创建数据库会话'
    
    except Exception as e:
        result['message'] = f'数据库健康检查失败: {str(e)}'
        logger.error(result['message'])
    
    return result


def get_database_info():
    """
    获取数据库信息
    
    返回:
        dict: 包含数据库信息的字典
        {
            'enabled': bool,        # 是否启用
            'available': bool,      # 是否可用
            'type': str,           # 数据库类型
            'version': str         # 数据库版本
        }
    """
    from .config import db_config
    
    info = {
        'enabled': db_config.is_enabled(),
        'available': False,
        'type': 'sqlite',
        'version': '3.x (Python内置)'
    }
    
    if not info['enabled']:
        return info
    
    info['available'] = check_database_available()
    
    if info['available']:
        try:
            with session_scope() as session:
                if session:
                    result = session.execute(text("SELECT sqlite_version()"))
                    info['version'] = f"SQLite {result.scalar()}"
        except Exception as e:
            logger.warning(f"获取数据库版本信息失败: {e}")
    
    return info