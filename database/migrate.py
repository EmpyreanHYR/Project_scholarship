"""
数据库迁移和建表模块
提供自动建表和数据库迁移功能
不会影响现有业务逻辑
"""

import logging
from sqlalchemy import inspect
from .connection import get_engine, check_database_available
from .models import Base, ReviewBatch, Student, Application, Review, AuditLog

# 配置日志
logger = logging.getLogger(__name__)


def create_all_tables(drop_existing=False):
    """
    创建所有数据表
    
    参数:
        drop_existing: bool, 是否先删除已存在的表（危险操作！）
    
    返回:
        dict: {
            'success': bool,
            'message': str,
            'tables_created': list,
            'error': str
        }
    """
    result = {
        'success': False,
        'message': '',
        'tables_created': [],
        'error': None
    }
    
    # 检查数据库是否可用
    if not check_database_available():
        result['message'] = '数据库未启用或不可用，无法创建表'
        logger.warning(result['message'])
        return result
    
    try:
        engine = get_engine()
        if engine is None:
            result['message'] = '无法获取数据库引擎'
            logger.error(result['message'])
            return result
        
        # 删除已存在的表（如果指定）
        if drop_existing:
            logger.warning("正在删除已存在的表...")
            Base.metadata.drop_all(engine)
            logger.info("已删除所有表")
        
        # 创建所有表
        logger.info("开始创建数据表...")
        Base.metadata.create_all(engine)
        
        # 获取已创建的表列表
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        result['tables_created'] = table_names
        
        result['success'] = True
        result['message'] = f'成功创建 {len(table_names)} 个数据表'
        logger.info(result['message'])
        logger.info(f"已创建的表: {', '.join(table_names)}")
        
    except Exception as e:
        result['error'] = str(e)
        result['message'] = f'创建数据表失败: {e}'
        logger.error(result['message'], exc_info=True)
    
    return result


def drop_all_tables():
    """
    删除所有数据表（危险操作！）
    
    返回:
        dict: {
            'success': bool,
            'message': str,
            'error': str
        }
    """
    result = {
        'success': False,
        'message': '',
        'error': None
    }
    
    if not check_database_available():
        result['message'] = '数据库未启用或不可用'
        logger.warning(result['message'])
        return result
    
    try:
        engine = get_engine()
        if engine is None:
            result['message'] = '无法获取数据库引擎'
            logger.error(result['message'])
            return result
        
        logger.warning("正在删除所有数据表...")
        Base.metadata.drop_all(engine)
        
        result['success'] = True
        result['message'] = '成功删除所有数据表'
        logger.info(result['message'])
        
    except Exception as e:
        result['error'] = str(e)
        result['message'] = f'删除数据表失败: {e}'
        logger.error(result['message'], exc_info=True)
    
    return result


def get_table_info():
    """
    获取数据库中的表信息
    
    返回:
        dict: {
            'success': bool,
            'tables': list,  # 表名列表
            'table_details': dict,  # 每个表的详细信息
            'message': str,
            'error': str
        }
    """
    result = {
        'success': False,
        'tables': [],
        'table_details': {},
        'message': '',
        'error': None
    }
    
    if not check_database_available():
        result['message'] = '数据库未启用或不可用'
        return result
    
    try:
        engine = get_engine()
        if engine is None:
            result['message'] = '无法获取数据库引擎'
            return result
        
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        result['tables'] = table_names
        
        # 获取每个表的详细信息
        for table_name in table_names:
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            pk = inspector.get_pk_constraint(table_name)
            fks = inspector.get_foreign_keys(table_name)
            
            result['table_details'][table_name] = {
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable'],
                        'default': col.get('default'),
                    }
                    for col in columns
                ],
                'primary_key': pk['constrained_columns'] if pk else [],
                'indexes': [idx['name'] for idx in indexes],
                'foreign_keys': [
                    {
                        'name': fk.get('name'),
                        'columns': fk['constrained_columns'],
                        'referred_table': fk['referred_table'],
                        'referred_columns': fk['referred_columns']
                    }
                    for fk in fks
                ]
            }
        
        result['success'] = True
        result['message'] = f'成功获取 {len(table_names)} 个表的信息'
        
    except Exception as e:
        result['error'] = str(e)
        result['message'] = f'获取表信息失败: {e}'
        logger.error(result['message'], exc_info=True)
    
    return result


def check_tables_exist():
    """
    检查数据表是否已经创建
    
    返回:
        dict: {
            'success': bool,
            'all_exist': bool,  # 所有表是否都存在
            'existing_tables': list,  # 已存在的表
            'missing_tables': list,  # 缺失的表
            'message': str
        }
    """
    result = {
        'success': False,
        'all_exist': False,
        'existing_tables': [],
        'missing_tables': [],
        'message': ''
    }
    
    if not check_database_available():
        result['message'] = '数据库未启用或不可用'
        return result
    
    try:
        engine = get_engine()
        if engine is None:
            result['message'] = '无法获取数据库引擎'
            return result
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # 定义期望的表名
        expected_tables = [
            'review_batches',
            'students',
            'applications',
            'reviews',
            'audit_logs'
        ]
        
        result['existing_tables'] = [t for t in expected_tables if t in existing_tables]
        result['missing_tables'] = [t for t in expected_tables if t not in existing_tables]
        result['all_exist'] = len(result['missing_tables']) == 0
        result['success'] = True
        
        if result['all_exist']:
            result['message'] = '所有数据表都已存在'
        else:
            result['message'] = f'缺失 {len(result["missing_tables"])} 个表: {", ".join(result["missing_tables"])}'
        
    except Exception as e:
        result['message'] = f'检查表存在性失败: {e}'
        logger.error(result['message'], exc_info=True)
    
    return result


def init_database_schema():
    """
    初始化数据库schema
    检查表是否存在，如果不存在则创建
    
    返回:
        dict: 初始化结果
    """
    logger.info("开始初始化数据库schema...")
    
    # 检查表是否存在
    check_result = check_tables_exist()
    
    if not check_result['success']:
        return {
            'success': False,
            'message': check_result['message']
        }
    
    # 如果所有表都存在，直接返回
    if check_result['all_exist']:
        logger.info("数据表已存在，无需创建")
        return {
            'success': True,
            'message': '数据表已存在',
            'tables': check_result['existing_tables']
        }
    
    # 创建缺失的表
    logger.info(f"检测到缺失的表，准备创建: {check_result['missing_tables']}")
    create_result = create_all_tables(drop_existing=False)
    
    return create_result


def get_model_summary():
    """
    获取模型摘要信息
    
    返回:
        dict: 模型信息
    """
    return {
        'models': [
            {
                'name': 'ReviewBatch',
                'table': 'review_batches',
                'description': '评审批次表'
            },
            {
                'name': 'Student',
                'table': 'students',
                'description': '学生信息表'
            },
            {
                'name': 'Application',
                'table': 'applications',
                'description': '申请信息表'
            },
            {
                'name': 'Review',
                'table': 'reviews',
                'description': '评审记录表'
            },
            {
                'name': 'AuditLog',
                'table': 'audit_logs',
                'description': '审计日志表'
            }
        ]
    }
