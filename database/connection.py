"""
数据库连接模块
提供 SQLite 数据库引擎创建和会话管理功能
"""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, scoped_session

from .config import db_config

# 配置日志
logger = logging.getLogger(__name__)

# 全局变量
_engine = None
_Session = None
_database_available = False


def get_engine():
    """
    获取数据库引擎
    如果数据库未启用或连接失败，返回 None
    """
    global _engine, _database_available
    
    # 如果已经初始化过，直接返回
    if _engine is not None:
        return _engine
    
    # 检查数据库是否启用
    if not db_config.is_enabled():
        logger.info("数据库功能未启用")
        return None
    
    try:
        # 获取连接字符串
        connection_string = db_config.get_connection_string()
        if not connection_string:
            logger.warning("无法获取数据库连接字符串")
            return None
        
        # 创建引擎
        engine_options = db_config.get_engine_options()
        _engine = create_engine(connection_string, **engine_options)
        
        # SQLite：启用外键约束
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        # 测试连接
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        _database_available = True
        logger.info("数据库引擎创建成功")
        
    except Exception as e:
        logger.error(f"创建数据库引擎失败: {e}")
        _database_available = False
        return None
    
    return _engine


def _get_session_factory():
    """
    获取Session工厂
    """
    global _Session
    
    if _Session is not None:
        return _Session
    
    engine = get_engine()
    if engine is None:
        return None
    
    try:
        session_factory = sessionmaker(bind=engine)
        _Session = scoped_session(session_factory)
        logger.info("数据库Session工厂创建成功")
    except Exception as e:
        logger.error(f"创建Session工厂失败: {e}")
        return None
    
    return _Session


def get_session():
    """
    获取数据库会话对象
    
    返回:
        Session对象，如果数据库不可用则返回 None
    """
    Session = _get_session_factory()
    if Session is None:
        return None
    
    try:
        return Session()
    except Exception as e:
        logger.error(f"创建数据库会话失败: {e}")
        return None


@contextmanager
def session_scope():
    """
    数据库会话上下文管理器
    自动处理会话的提交、回滚和关闭
    """
    session = get_session()
    
    if session is None:
        logger.debug("数据库不可用，跳过数据库操作")
        yield None
        return
    
    try:
        yield session
        session.commit()
        logger.debug("数据库事务提交成功")
    except Exception as e:
        session.rollback()
        logger.error(f"数据库操作失败，已回滚: {e}")
    finally:
        session.close()
        logger.debug("数据库会话已关闭")


def check_database_available():
    """
    检查数据库是否可用
    
    返回:
        bool: 数据库可用返回 True，否则返回 False
    """
    global _database_available
    
    # 如果已经检查过，直接返回结果
    if _engine is not None:
        return _database_available
    
    # 尝试获取引擎（会进行连接测试）
    engine = get_engine()
    return engine is not None


def reset_database_connection():
    """
    重置数据库连接
    用于重新加载配置或重新连接数据库
    """
    global _engine, _Session, _database_available
    
    try:
        if _Session is not None:
            _Session.remove()
            _Session = None
        
        if _engine is not None:
            _engine.dispose()
            _engine = None
        
        _database_available = False
        logger.info("数据库连接已重置")
    except Exception as e:
        logger.error(f"重置数据库连接时发生错误: {e}")


def cleanup():
    """
    清理数据库资源
    在程序退出时调用
    """
    global _engine, _Session
    
    try:
        if _Session is not None:
            _Session.remove()
        
        if _engine is not None:
            _engine.dispose()
        
        logger.info("数据库资源已清理")
    except Exception as e:
        logger.error(f"清理数据库资源时发生错误: {e}")