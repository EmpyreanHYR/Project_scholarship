"""
数据库模块
提供数据库连接和会话管理功能
本模块完全独立，不影响任何现有功能
"""

from .connection import get_session, session_scope, get_engine, check_database_available
from .migrate import (
    create_all_tables, 
    drop_all_tables, 
    get_table_info, 
    check_tables_exist,
    init_database_schema,
    get_model_summary
)
from .dao import ReviewBatchDAO, StudentDAO, ApplicationDAO, ReviewDAO, AuditLogDAO
from .query_service import QueryService
from .export_service import ExportService

__all__ = [
    'get_session', 
    'session_scope', 
    'get_engine', 
    'check_database_available',
    'create_all_tables',
    'drop_all_tables',
    'get_table_info',
    'check_tables_exist',
    'init_database_schema',
    'get_model_summary',
    'ReviewBatchDAO',
    'StudentDAO',
    'ApplicationDAO',
    'ReviewDAO',
    'AuditLogDAO',
    'QueryService',
    'ExportService'
]
