"""
业务服务层
提供Excel导入和评审结果的数据库记录功能
所有函数都是附加式的，不修改原有业务逻辑
"""

import logging
from datetime import datetime
from .dao import ReviewBatchDAO, StudentDAO, ApplicationDAO, ReviewDAO, AuditLogDAO
from .connection import check_database_available

# 配置日志
logger = logging.getLogger(__name__)


def record_excel_import_to_db(file_path, student_info, awards_data, batch_name=None, 
                              reviewer_account=None, reviewer_name=None):
    """
    将Excel导入的数据记录到数据库
    这是一个旁路函数，不影响原有导入逻辑
    
    参数:
        file_path: Excel文件路径
        student_info: 学生基本信息字典 {'学院', '姓名', '年级', '班级', '学号'}
        awards_data: 奖项数据列表，每项包含 {'所获奖项名称', '获奖时间', '奖项等级', ...}
        batch_name: 批次名称（可选）
        reviewer_account: 评审人账号
        reviewer_name: 评审人姓名
    
    返回:
        dict: {
            'success': bool,
            'batch_id': int,
            'student_db_id': int,
            'applications_count': int,
            'message': str
        }
    """
    result = {
        'success': False,
        'batch_id': None,
        'student_db_id': None,
        'applications_count': 0,
        'message': ''
    }
    
    # 检查数据库是否可用
    if not check_database_available():
        logger.debug("数据库不可用，跳过记录导入数据")
        result['message'] = '数据库未启用'
        return result
    
    try:
        # 1. 生成批次编号和名称
        now = datetime.now()
        if not batch_name:
            batch_name = f"导入_{now.strftime('%Y%m%d_%H%M%S')}"
        
        batch_code = f"BATCH_{now.strftime('%Y%m%d%H%M%S')}_{student_info.get('学号', 'unknown')}"
        academic_year = f"{now.year}-{now.year+1}"
        semester = "第一学期" if now.month >= 9 or now.month <= 2 else "第二学期"
        
        # 2. 创建评审批次
        batch_id = ReviewBatchDAO.create_batch(
            batch_code=batch_code,
            batch_name=batch_name,
            academic_year=academic_year,
            semester=semester,
            reviewer_name=reviewer_name,
            description=f"从文件导入: {file_path}"
        )
        
        if not batch_id:
            result['message'] = '创建批次失败'
            return result
        
        result['batch_id'] = batch_id
        
        # 3. 创建或获取学生记录
        student_db_id = StudentDAO.create_or_get_student(
            batch_id=batch_id,
            student_id=student_info.get('学号', ''),
            name=student_info.get('姓名', ''),
            class_name=student_info.get('班级', ''),
            major=student_info.get('学院', ''),
            grade=student_info.get('年级', '')
        )
        
        if not student_db_id:
            result['message'] = '创建学生记录失败'
            return result
        
        result['student_db_id'] = student_db_id
        
        # 4. 创建申请记录（奖项）
        applications_count = 0
        for award in awards_data:
            # 解析获奖时间
            award_date = None
            if award.get('获奖时间'):
                try:
                    award_time_str = str(award['获奖时间'])
                    # 尝试解析不同格式的日期
                    if '-' in award_time_str:
                        award_date = datetime.strptime(award_time_str, '%Y-%m-%d')
                    elif '/' in award_time_str:
                        award_date = datetime.strptime(award_time_str, '%Y/%m/%d')
                except:
                    pass
            
            app_id = ApplicationDAO.create_application(
                batch_id=batch_id,
                student_db_id=student_db_id,
                project_name=award.get('所获奖项名称', ''),
                award_level=award.get('奖项等级', ''),
                award_date=award_date,
                points=float(award.get('加分', 0) or 0),
                project_type=award.get('项目类型', ''),
                award_name=award.get('所获奖项名称', ''),
                remarks=award.get('备注', '')
            )
            
            if app_id:
                applications_count += 1
        
        result['applications_count'] = applications_count
        
        # 5. 记录审计日志
        AuditLogDAO.log_operation(
            operation_type='import',
            operation_action=f'导入Excel文件',
            operator_account=reviewer_account or 'system',
            operator_name=reviewer_name,
            batch_id=batch_id,
            student_id=student_db_id,
            new_value={
                'file_path': file_path,
                'student_info': student_info,
                'awards_count': applications_count
            },
            status='success'
        )
        
        result['success'] = True
        result['message'] = f'成功记录{applications_count}个申请项目'
        logger.info(f"Excel导入记录到数据库: 学生={student_info.get('姓名')}, 项目数={applications_count}")
        
    except Exception as e:
        result['message'] = f'记录导入数据失败: {str(e)}'
        logger.error(result['message'], exc_info=True)
        
        # 记录失败日志
        try:
            AuditLogDAO.log_operation(
                operation_type='import',
                operation_action='导入Excel文件',
                operator_account=reviewer_account or 'system',
                operator_name=reviewer_name,
                status='failed',
                error_message=result['message']
            )
        except:
            pass
    
    return result


def record_batch_excel_import_to_db(students_data_dict, batch_name=None,
                                    reviewer_account=None, reviewer_name=None):
    """
    将批量Excel导入的数据记录到数据库
    
    参数:
        students_data_dict: 学生数据字典，格式如主程序中的 students_data
        batch_name: 批次名称
        reviewer_account: 评审人账号
        reviewer_name: 评审人姓名
    
    返回:
        dict: {
            'success': bool,
            'batch_id': int,
            'students_count': int,
            'applications_count': int,
            'message': str
        }
    """
    result = {
        'success': False,
        'batch_id': None,
        'students_count': 0,
        'applications_count': 0,
        'message': ''
    }
    
    if not check_database_available():
        logger.debug("数据库不可用，跳过批量导入记录")
        result['message'] = '数据库未启用'
        return result
    
    try:
        # 1. 创建统一的批次
        now = datetime.now()
        if not batch_name:
            batch_name = f"批量导入_{now.strftime('%Y%m%d_%H%M%S')}"
        
        batch_code = f"BATCH_{now.strftime('%Y%m%d%H%M%S')}_MULTI"
        academic_year = f"{now.year}-{now.year+1}"
        semester = "第一学期" if now.month >= 9 or now.month <= 2 else "第二学期"
        
        batch_id = ReviewBatchDAO.create_batch(
            batch_code=batch_code,
            batch_name=batch_name,
            academic_year=academic_year,
            semester=semester,
            reviewer_name=reviewer_name,
            description=f"批量导入，包含{len(students_data_dict)}个学生"
        )
        
        if not batch_id:
            result['message'] = '创建批次失败'
            return result
        
        result['batch_id'] = batch_id
        students_count = 0
        applications_count = 0
        
        # 2. 遍历每个学生
        for student_id, student_data in students_data_dict.items():
            student_info = student_data['student_info']
            df = student_data['df']
            
            # 创建学生记录
            student_db_id = StudentDAO.create_or_get_student(
                batch_id=batch_id,
                student_id=student_info.get('学号', ''),
                name=student_info.get('姓名', ''),
                class_name=student_info.get('班级', ''),
                major=student_info.get('学院', ''),
                grade=student_info.get('年级', '')
            )
            
            if not student_db_id:
                logger.warning(f"创建学生记录失败: {student_info.get('姓名')}")
                continue
            
            students_count += 1
            
            # 3. 创建申请记录
            for idx, row in df.iterrows():
                try:
                    # 解析获奖时间
                    award_date = None
                    if '获奖时间' in row and row['获奖时间']:
                        try:
                            award_time_str = str(row['获奖时间'])
                            if '-' in award_time_str:
                                award_date = datetime.strptime(award_time_str, '%Y-%m-%d')
                            elif '/' in award_time_str:
                                award_date = datetime.strptime(award_time_str, '%Y/%m/%d')
                        except:
                            pass
                    
                    app_id = ApplicationDAO.create_application(
                        batch_id=batch_id,
                        student_db_id=student_db_id,
                        project_name=row.get('所获奖项名称', ''),
                        award_level=row.get('奖项等级', ''),
                        award_date=award_date,
                        points=float(row.get('加分', 0) or 0),
                        project_type=row.get('项目类型', ''),
                        award_name=row.get('所获奖项名称', ''),
                        remarks=row.get('备注', '')
                    )
                    
                    if app_id:
                        applications_count += 1
                        
                except Exception as e:
                    logger.warning(f"创建申请记录失败: {e}")
                    continue
        
        result['students_count'] = students_count
        result['applications_count'] = applications_count
        
        # 4. 记录审计日志
        AuditLogDAO.log_operation(
            operation_type='import',
            operation_action='批量导入Excel文件',
            operator_account=reviewer_account or 'system',
            operator_name=reviewer_name,
            batch_id=batch_id,
            new_value={
                'students_count': students_count,
                'applications_count': applications_count
            },
            status='success'
        )
        
        result['success'] = True
        result['message'] = f'成功记录{students_count}个学生，{applications_count}个申请项目'
        logger.info(f"批量Excel导入记录到数据库: 学生数={students_count}, 项目数={applications_count}")
        
    except Exception as e:
        result['message'] = f'记录批量导入数据失败: {str(e)}'
        logger.error(result['message'], exc_info=True)
    
    return result


def record_review_result_to_db(batch_id, student_info, total_points, review_details,
                               reviewer_account, reviewer_name, final_result=None,
                               rank=None, comments=None):
    """
    将评审结果记录到数据库（幂等操作）
    
    参数:
        batch_id: 批次ID（如果为None，尝试查找或创建）
        student_info: 学生信息字典
        total_points: 总分
        review_details: 评审详情（字典或列表）
        reviewer_account: 评审人账号
        reviewer_name: 评审人姓名
        final_result: 最终结果
        rank: 排名
        comments: 评审意见
    
    返回:
        dict: {
            'success': bool,
            'review_id': int,
            'message': str
        }
    """
    result = {
        'success': False,
        'review_id': None,
        'message': ''
    }
    
    if not check_database_available():
        logger.debug("数据库不可用，跳过记录评审结果")
        result['message'] = '数据库未启用'
        return result
    
    try:
        # 1. 确保有批次ID
        if not batch_id:
            # 尝试创建临时批次
            now = datetime.now()
            batch_code = f"REVIEW_{now.strftime('%Y%m%d%H%M%S')}_{student_info.get('学号', 'unknown')}"
            batch_id = ReviewBatchDAO.create_batch(
                batch_code=batch_code,
                batch_name=f"评审_{now.strftime('%Y%m%d_%H%M%S')}",
                academic_year=f"{now.year}-{now.year+1}",
                semester="第一学期" if now.month >= 9 or now.month <= 2 else "第二学期",
                reviewer_name=reviewer_name
            )
        
        if not batch_id:
            result['message'] = '无法获取或创建批次'
            return result
        
        # 2. 获取学生数据库ID
        student_db_id = StudentDAO.create_or_get_student(
            batch_id=batch_id,
            student_id=student_info.get('学号', ''),
            name=student_info.get('姓名', ''),
            class_name=student_info.get('班级', ''),
            major=student_info.get('学院', ''),
            grade=student_info.get('年级', '')
        )
        
        if not student_db_id:
            result['message'] = '无法获取学生记录'
            return result
        
        # 3. 创建或更新评审记录
        review_id = ReviewDAO.create_or_update_review(
            batch_id=batch_id,
            student_db_id=student_db_id,
            reviewer_name=reviewer_name,
            reviewer_account=reviewer_account,
            total_points=total_points,
            review_details=review_details,
            final_result=final_result,
            rank=rank,
            comments=comments
        )
        
        if not review_id:
            result['message'] = '创建/更新评审记录失败'
            return result
        
        result['review_id'] = review_id
        
        # 4. 记录审计日志
        AuditLogDAO.log_operation(
            operation_type='update',
            operation_action='保存评审结果',
            operator_account=reviewer_account,
            operator_name=reviewer_name,
            batch_id=batch_id,
            student_id=student_db_id,
            new_value={
                'total_points': total_points,
                'final_result': final_result,
                'rank': rank
            },
            status='success'
        )
        
        result['success'] = True
        result['message'] = '评审结果已记录'
        logger.info(f"评审结果记录到数据库: 学生={student_info.get('姓名')}, 总分={total_points}")
        
    except Exception as e:
        result['message'] = f'记录评审结果失败: {str(e)}'
        logger.error(result['message'], exc_info=True)
    
    return result
