"""
数据库连接模块
提供数据库引擎创建、会话管理和连接检查功能
所有异常都会被捕获并记录，不会影响主程序运行
"""

import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
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
    不会抛出异常，确保不影响主程序
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
        
        # 测试连接
        with _engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        _database_available = True
        logger.info("数据库引擎创建成功")
        
    except ImportError as e:
        logger.warning(f"数据库驱动未安装: {e}")
        logger.warning("提示：PostgreSQL需要安装 psycopg2，MySQL需要安装 pymysql")
        _database_available = False
        return None
    
    except SQLAlchemyError as e:
        logger.warning(f"数据库连接失败: {e}")
        _database_available = False
        return None
    
    except Exception as e:
        logger.error(f"创建数据库引擎时发生未知错误: {e}")
        _database_available = False
        return None
    
    return _engine


def _get_session_factory():
    """
    获取Session工厂
    内部使用，不对外暴露
    """
    global _Session
    
    if _Session is not None:
        return _Session
    
    engine = get_engine()
    if engine is None:
        return None
    
    try:
        # 创建线程安全的Session工厂
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
    
    使用示例:
        session = get_session()
        if session:
            try:
                # 执行数据库操作
                pass
            finally:
                session.close()
    
    注意：
        - 使用完毕后需要手动关闭会话
        - 建议使用 session_scope() 上下文管理器
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
    
    使用示例:
        from database import session_scope
        
        with session_scope() as session:
            if session:
                # 执行数据库操作
                result = session.execute(text("SELECT * FROM users"))
                # 会自动提交
    
    特性:
        - 自动提交成功的事务
        - 自动回滚失败的事务
        - 自动关闭会话
        - 异常不会向上传播，只记录日志
    """
    session = get_session()
    
    if session is None:
        # 数据库不可用，yield None
        logger.debug("数据库不可用，跳过数据库操作")
        yield None
        return
    
    try:
        yield session
        session.commit()
        logger.debug("数据库事务提交成功")
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"数据库操作失败，已回滚: {e}")
    except Exception as e:
        session.rollback()
        logger.error(f"数据库会话发生未知错误，已回滚: {e}")
    finally:
        session.close()
        logger.debug("数据库会话已关闭")


def check_database_available():
    """
    检查数据库是否可用
    
    返回:
        bool: 数据库可用返回 True，否则返回 False
    
    使用示例:
        from database import check_database_available
        
        if check_database_available():
            print("数据库可用")
        else:
            print("数据库不可用，使用本地文件存储")
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
    
    使用场景:
        - 配置文件更新后
        - 数据库连接断开需要重连
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


# 模块清理
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
