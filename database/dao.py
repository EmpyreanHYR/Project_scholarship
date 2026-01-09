"""
数据访问层（DAO - Data Access Object）
提供数据库操作的高级接口
所有数据库异常都会被捕获，不影响主程序
"""

import logging
import json
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from .connection import session_scope, check_database_available
from .models import ReviewBatch, Student, Application, Review, AuditLog

# 配置日志
logger = logging.getLogger(__name__)


class ReviewBatchDAO:
    """评审批次数据访问对象"""
    
    @staticmethod
    def create_batch(batch_code, batch_name, academic_year, semester, 
                    reviewer_name=None, description=None):
        """
        创建评审批次
        
        参数:
            batch_code: 批次编号（唯一）
            batch_name: 批次名称
            academic_year: 学年
            semester: 学期
            reviewer_name: 评审人姓名
            description: 批次描述
        
        返回:
            批次ID，如果失败返回 None
        """
        if not check_database_available():
            logger.debug("数据库不可用，跳过创建批次")
            return None
        
        try:
            with session_scope() as session:
                if session is None:
                    return None
                
                # 检查是否已存在
                existing = session.query(ReviewBatch).filter_by(batch_code=batch_code).first()
                if existing:
                    logger.info(f"批次已存在: {batch_code}")
                    return existing.id
                
                # 创建新批次
                batch = ReviewBatch(
                    batch_code=batch_code,
                    batch_name=batch_name,
                    academic_year=academic_year,
                    semester=semester,
                    reviewer_name=reviewer_name,
                    description=description,
                    status='active'
                )
                session.add(batch)
                session.flush()  # 获取ID
                
                batch_id = batch.id
                logger.info(f"创建批次成功: {batch_name} (ID: {batch_id})")
                return batch_id
                
        except Exception as e:
            logger.error(f"创建批次失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def get_batch_by_code(batch_code):
        """根据批次编号获取批次"""
        if not check_database_available():
            return None
        
        try:
            with session_scope() as session:
                if session is None:
                    return None
                
                batch = session.query(ReviewBatch).filter_by(batch_code=batch_code).first()
                if batch:
                    return {
                        'id': batch.id,
                        'batch_code': batch.batch_code,
                        'batch_name': batch.batch_name,
                        'academic_year': batch.academic_year,
                        'semester': batch.semester,
                        'status': batch.status
                    }
                return None
                
        except Exception as e:
            logger.error(f"获取批次失败: {e}")
            return None


class StudentDAO:
    """学生数据访问对象"""
    
    @staticmethod
    def create_or_get_student(batch_id, student_id, name, class_name=None, 
                             major=None, grade=None, phone=None, email=None):
        """
        创建或获取学生记录
        
        返回:
            学生数据库ID，如果失败返回 None
        """
        if not check_database_available():
            return None
        
        try:
            with session_scope() as session:
                if session is None:
                    return None
                
                # 查找是否已存在
                existing = session.query(Student).filter(
                    and_(
                        Student.batch_id == batch_id,
                        Student.student_id == student_id
                    )
                ).first()
                
                if existing:
                    # 更新基本信息
                    existing.name = name
                    existing.class_name = class_name
                    existing.major = major
                    existing.grade = grade
                    existing.phone = phone
                    existing.email = email
                    session.flush()
                    return existing.id
                
                # 创建新学生
                student = Student(
                    batch_id=batch_id,
                    student_id=student_id,
                    name=name,
                    class_name=class_name,
                    major=major,
                    grade=grade,
                    phone=phone,
                    email=email
                )
                session.add(student)
                session.flush()
                
                logger.info(f"创建学生成功: {name} ({student_id})")
                return student.id
                
        except Exception as e:
            logger.error(f"创建/获取学生失败: {e}", exc_info=True)
            return None


class ApplicationDAO:
    """申请数据访问对象"""
    
    @staticmethod
    def create_application(batch_id, student_db_id, project_name, award_level=None,
                          award_date=None, points=0.0, project_type=None,
                          award_name=None, certificate_path=None, remarks=None):
        """
        创建申请记录
        
        返回:
            申请ID，如果失败返回 None
        """
        if not check_database_available():
            return None
        
        try:
            with session_scope() as session:
                if session is None:
                    return None
                
                application = Application(
                    batch_id=batch_id,
                    student_id=student_db_id,
                    project_name=project_name,
                    project_type=project_type,
                    award_name=award_name,
                    award_level=award_level,
                    award_date=award_date,
                    points=points,
                    certificate_path=certificate_path,
                    remarks=remarks,
                    status='pending',
                    submitted_at=datetime.now()
                )
                session.add(application)
                session.flush()
                
                logger.debug(f"创建申请成功: {project_name}")
                return application.id
                
        except Exception as e:
            logger.error(f"创建申请失败: {e}", exc_info=True)
            return None


class ReviewDAO:
    """评审记录数据访问对象"""
    
    @staticmethod
    def create_or_update_review(batch_id, student_db_id, reviewer_name, 
                                reviewer_account, total_points, review_details=None,
                                final_result=None, rank=None, comments=None):
        """
        创建或更新评审记录（幂等操作）
        
        返回:
            评审ID，如果失败返回 None
        """
        if not check_database_available():
            return None
        
        try:
            with session_scope() as session:
                if session is None:
                    return None
                
                # 查找是否已存在该学生在该批次的评审记录
                existing = session.query(Review).filter(
                    and_(
                        Review.batch_id == batch_id,
                        Review.student_id == student_db_id
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.reviewer_name = reviewer_name
                    existing.reviewer_account = reviewer_account
                    existing.total_points = total_points
                    if review_details:
                        existing.review_details = json.dumps(review_details, ensure_ascii=False)
                    existing.final_result = final_result
                    existing.rank = rank
                    existing.comments = comments
                    existing.review_time = datetime.now()
                    existing.review_status = 'submitted'
                    session.flush()
                    
                    logger.info(f"更新评审记录: 学生ID={student_db_id}, 总分={total_points}")
                    return existing.id
                
                # 创建新记录
                review = Review(
                    batch_id=batch_id,
                    student_id=student_db_id,
                    reviewer_name=reviewer_name,
                    reviewer_account=reviewer_account,
                    total_points=total_points,
                    review_details=json.dumps(review_details, ensure_ascii=False) if review_details else None,
                    final_result=final_result,
                    rank=rank,
                    comments=comments,
                    review_status='submitted',
                    review_time=datetime.now()
                )
                session.add(review)
                session.flush()
                
                logger.info(f"创建评审记录: 学生ID={student_db_id}, 总分={total_points}")
                return review.id
                
        except Exception as e:
            logger.error(f"创建/更新评审记录失败: {e}", exc_info=True)
            return None


class AuditLogDAO:
    """审计日志数据访问对象"""
    
    @staticmethod
    def log_operation(operation_type, operation_action, operator_account,
                     operator_name=None, batch_id=None, student_id=None,
                     old_value=None, new_value=None, status='success',
                     error_message=None):
        """
        记录操作日志
        
        参数:
            operation_type: 操作类型 (create/update/delete/export/import)
            operation_action: 操作动作描述
            operator_account: 操作人账号
            operator_name: 操作人姓名
            batch_id: 关联批次ID
            student_id: 关联学生ID
            old_value: 修改前数据
            new_value: 修改后数据
            status: 操作状态
            error_message: 错误信息
        """
        if not check_database_available():
            return None
        
        try:
            with session_scope() as session:
                if session is None:
                    return None
                
                log = AuditLog(
                    operation_type=operation_type,
                    operation_action=operation_action,
                    operator_account=operator_account,
                    operator_name=operator_name,
                    batch_id=batch_id,
                    student_id=student_id,
                    old_value=json.dumps(old_value, ensure_ascii=False) if old_value else None,
                    new_value=json.dumps(new_value, ensure_ascii=False) if new_value else None,
                    status=status,
                    error_message=error_message,
                    operation_time=datetime.now()
                )
                session.add(log)
                session.flush()
                
                return log.id
                
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")
            return None
