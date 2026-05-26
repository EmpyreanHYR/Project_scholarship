"""
数据库集成辅助模块
为主程序提供数据库记录功能的钩子
所有函数都是可选的、非阻塞的
"""

import logging

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入数据库服务（如果不可用也不影响程序运行）
try:
    from database.services import (
        record_excel_import_to_db,
        record_batch_excel_import_to_db,
        record_review_result_to_db,
        record_single_award_review
    )
    from database import check_database_available
    DB_AVAILABLE = True
    logger.info("数据库服务模块加载成功")
except ImportError as e:
    logger.debug(f"数据库服务模块未加载: {e}")
    DB_AVAILABLE = False
    check_database_available = lambda: False
    record_excel_import_to_db = None
    record_batch_excel_import_to_db = None
    record_review_result_to_db = None


def safe_record_single_excel_import(file_path, df, reviewer_account=None, reviewer_name=None):
    """
    安全地记录单个Excel导入到数据库
    所有异常都会被捕获，不影响主程序
    
    参数:
        file_path: Excel文件路径
        df: pandas DataFrame，包含学生和奖项信息
        reviewer_account: 评审人账号
        reviewer_name: 评审人姓名
    """
    if not DB_AVAILABLE or not check_database_available():
        logger.debug("数据库不可用，跳过记录Excel导入")
        return None
    
    try:
        # 提取学生信息（从第一行）
        if df is None or len(df) == 0:
            logger.debug("DataFrame为空，跳过记录")
            return
        
        first_row = df.iloc[0]
        student_info = {
            '学院': first_row.get('学院', ''),
            '姓名': first_row.get('姓名', ''),
            '年级': first_row.get('年级', ''),
            '班级': first_row.get('班级', ''),
            '学号': first_row.get('学号', '')
        }
        
        # 提取奖项数据
        awards_data = []
        for idx, row in df.iterrows():
            awards_data.append({
                '所获奖项名称': row.get('所获奖项名称', ''),
                '获奖时间': row.get('获奖时间', ''),
                '奖项等级': row.get('奖项等级', ''),
                '项目类型': row.get('项目类型', ''),
                '加分': row.get('加分', 0),
                '备注': row.get('备注', '')
            })
        
        # 调用服务层记录
        result = record_excel_import_to_db(
            file_path=file_path,
            student_info=student_info,
            awards_data=awards_data,
            reviewer_account=reviewer_account,
            reviewer_name=reviewer_name
        )
        
        if result['success']:
            logger.info(f"Excel导入已记录到数据库: {student_info['姓名']}")
        else:
            logger.debug(f"Excel导入记录失败: {result['message']}")

        return result
            
    except Exception as e:
        # 捕获所有异常，确保不影响主程序
        logger.error(f"记录Excel导入时发生错误: {e}", exc_info=True)
        return None


def safe_record_batch_excel_import(students_data, reviewer_account=None, reviewer_name=None):
    """
    安全地记录批量Excel导入到数据库
    
    参数:
        students_data: 学生数据字典，格式如主程序中的 students_data
        reviewer_account: 评审人账号
        reviewer_name: 评审人姓名
    """
    if not DB_AVAILABLE or not check_database_available():
        logger.debug("数据库不可用，跳过记录批量Excel导入")
        return None
    
    try:
        if not students_data or len(students_data) == 0:
            logger.debug("学生数据为空，跳过记录")
            return
        
        # 调用服务层记录
        result = record_batch_excel_import_to_db(
            students_data_dict=students_data,
            reviewer_account=reviewer_account,
            reviewer_name=reviewer_name
        )
        
        if result['success']:
            logger.info(f"批量Excel导入已记录到数据库: {result['students_count']}个学生")
        else:
            logger.debug(f"批量Excel导入记录失败: {result['message']}")

        return result
            
    except Exception as e:
        logger.error(f"记录批量Excel导入时发生错误: {e}", exc_info=True)
        return None


def safe_record_review_result(student_info, total_points, review_details,
                              reviewer_account, reviewer_name,
                              batch_id=None, final_result=None, rank=None, comments=None):
    """
    安全地记录评审结果到数据库
    
    参数:
        student_info: 学生信息字典
        total_points: 总分
        review_details: 评审详情
        reviewer_account: 评审人账号
        reviewer_name: 评审人姓名
        batch_id: 批次ID（可选）
        final_result: 最终结果
        rank: 排名
        comments: 评审意见
    """
    if not DB_AVAILABLE or not check_database_available():
        logger.debug("数据库不可用，跳过记录评审结果")
        return None
    
    try:
        # 调用服务层记录
        result = record_review_result_to_db(
            batch_id=batch_id,
            student_info=student_info,
            total_points=total_points,
            review_details=review_details,
            reviewer_account=reviewer_account,
            reviewer_name=reviewer_name,
            final_result=final_result,
            rank=rank,
            comments=comments
        )
        
        if result['success']:
            logger.info(f"评审结果已记录到数据库: {student_info.get('姓名')}")
        else:
            logger.debug(f"评审结果记录失败: {result['message']}")

        return result
            
    except Exception as e:
        logger.error(f"记录评审结果时发生错误: {e}", exc_info=True)
        return None


def safe_record_single_award_review(batch_id, student_info, award_data,
                                    reviewer_account, reviewer_name):
    """
    安全地记录单个奖项的评审结果到数据库
    
    参数:
        batch_id: 批次ID
        student_info: 学生信息字典 {'学号', '姓名', '学院', '班级', '年级'}
        award_data: 奖项信息字典 {'所获奖项名称', '项目类型', '评定等级', '认定情况', '加分', '备注'}
        reviewer_account: 评审人账号
        reviewer_name: 评审人姓名
    
    返回:
        dict: 包含 success, message 等字段
    """
    if not DB_AVAILABLE or not check_database_available():
        logger.debug("数据库不可用，跳过记录奖项评审")
        return None
    
    try:
        result = record_single_award_review(
            batch_id=batch_id,
            student_info=student_info,
            award_data=award_data,
            reviewer_account=reviewer_account,
            reviewer_name=reviewer_name
        )
        
        if result.get('success'):
            logger.info(f"奖项评审已记录到数据库: {student_info.get('姓名')} - {award_data.get('所获奖项名称', '')}")
        else:
            logger.debug(f"奖项评审记录失败: {result.get('message')}")
        
        return result
        
    except Exception as e:
        logger.error(f"记录奖项评审时发生错误: {e}", exc_info=True)
        return None


def is_database_enabled():
    """检查数据库功能是否启用"""
    return DB_AVAILABLE and check_database_available()
