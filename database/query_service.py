"""
数据库查询服务
提供历史记录查询功能
只读操作，不修改数据
"""

import logging
import json
from datetime import datetime
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import joinedload

from .connection import session_scope, check_database_available
from .models import ReviewBatch, Student, Application, Review, AuditLog

# 配置日志
logger = logging.getLogger(__name__)


class QueryService:
    """查询服务类"""
    
    @staticmethod
    def query_batches(academic_year=None, semester=None, status=None, limit=100):
        """
        查询评审批次
        
        参数:
            academic_year: 学年筛选
            semester: 学期筛选
            status: 状态筛选
            limit: 返回数量限制
        
        返回:
            list: 批次列表
        """
        if not check_database_available():
            return []
        
        try:
            with session_scope() as session:
                if session is None:
                    return []
                
                query = session.query(ReviewBatch)
                
                # 应用筛选条件
                if academic_year:
                    query = query.filter(ReviewBatch.academic_year == academic_year)
                if semester:
                    query = query.filter(ReviewBatch.semester == semester)
                if status:
                    query = query.filter(ReviewBatch.status == status)
                
                # 按创建时间倒序
                query = query.order_by(desc(ReviewBatch.created_at))
                
                # 限制数量
                if limit:
                    query = query.limit(limit)
                
                batches = query.all()
                
                # 转换为字典
                result = []
                for batch in batches:
                    result.append({
                        'id': batch.id,
                        'batch_code': batch.batch_code,
                        'batch_name': batch.batch_name,
                        'academic_year': batch.academic_year,
                        'semester': batch.semester,
                        'status': batch.status,
                        'reviewer_name': batch.reviewer_name,
                        'total_students': batch.total_students,
                        'reviewed_count': batch.reviewed_count,
                        'created_at': batch.created_at.strftime('%Y-%m-%d %H:%M:%S') if batch.created_at else '',
                        'description': batch.description
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"查询批次失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def query_students(batch_id=None, student_id=None, name=None, major=None, 
                      grade=None, limit=1000):
        """
        查询学生记录
        
        返回:
            list: 学生列表
        """
        if not check_database_available():
            return []
        
        try:
            with session_scope() as session:
                if session is None:
                    return []
                
                query = session.query(Student)
                
                # 应用筛选条件
                if batch_id:
                    query = query.filter(Student.batch_id == batch_id)
                if student_id:
                    query = query.filter(Student.student_id.like(f'%{student_id}%'))
                if name:
                    query = query.filter(Student.name.like(f'%{name}%'))
                if major:
                    query = query.filter(Student.major.like(f'%{major}%'))
                if grade:
                    query = query.filter(Student.grade.like(f'%{grade}%'))
                
                # 限制数量
                if limit:
                    query = query.limit(limit)
                
                students = query.all()
                
                # 转换为字典
                result = []
                for student in students:
                    result.append({
                        'id': student.id,
                        'batch_id': student.batch_id,
                        'student_id': student.student_id,
                        'name': student.name,
                        'class_name': student.class_name,
                        'major': student.major,
                        'grade': student.grade,
                        'phone': student.phone,
                        'email': student.email,
                        'created_at': student.created_at.strftime('%Y-%m-%d %H:%M:%S') if student.created_at else ''
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"查询学生失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def query_applications(batch_id=None, student_db_id=None, project_type=None,
                          status=None, min_points=None, max_points=None,
                          start_date=None, end_date=None, limit=1000):
        """
        查询申请记录
        
        返回:
            list: 申请列表
        """
        if not check_database_available():
            return []
        
        try:
            with session_scope() as session:
                if session is None:
                    return []
                
                query = session.query(Application).join(Student)
                
                # 应用筛选条件
                if batch_id:
                    query = query.filter(Application.batch_id == batch_id)
                if student_db_id:
                    query = query.filter(Application.student_id == student_db_id)
                if project_type:
                    query = query.filter(Application.project_type.like(f'%{project_type}%'))
                if status:
                    query = query.filter(Application.status == status)
                if min_points is not None:
                    query = query.filter(Application.points >= min_points)
                if max_points is not None:
                    query = query.filter(Application.points <= max_points)
                if start_date:
                    query = query.filter(Application.created_at >= start_date)
                if end_date:
                    query = query.filter(Application.created_at <= end_date)
                
                # 限制数量
                if limit:
                    query = query.limit(limit)
                
                applications = query.all()
                
                # 转换为字典
                result = []
                for app in applications:
                    result.append({
                        'id': app.id,
                        'batch_id': app.batch_id,
                        'student_id': app.student_id,
                        'student_name': app.student.name,
                        'student_number': app.student.student_id,
                        'project_name': app.project_name,
                        'project_type': app.project_type,
                        'award_level': app.award_level,
                        'points': app.points,
                        'status': app.status,
                        'submitted_at': app.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if app.submitted_at else '',
                        'created_at': app.created_at.strftime('%Y-%m-%d %H:%M:%S') if app.created_at else ''
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"查询申请失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def query_reviews(batch_id=None, student_db_id=None, reviewer_account=None,
                     min_points=None, max_points=None, review_status=None,
                     start_date=None, end_date=None, limit=1000):
        """
        查询评审记录
        
        返回:
            list: 评审记录列表
        """
        if not check_database_available():
            return []
        
        try:
            with session_scope() as session:
                if session is None:
                    return []
                
                query = session.query(Review).join(Student)
                
                # 应用筛选条件
                if batch_id:
                    query = query.filter(Review.batch_id == batch_id)
                if student_db_id:
                    query = query.filter(Review.student_id == student_db_id)
                if reviewer_account:
                    query = query.filter(Review.reviewer_account.like(f'%{reviewer_account}%'))
                if min_points is not None:
                    query = query.filter(Review.total_points >= min_points)
                if max_points is not None:
                    query = query.filter(Review.total_points <= max_points)
                if review_status:
                    query = query.filter(Review.review_status == review_status)
                if start_date:
                    query = query.filter(Review.review_time >= start_date)
                if end_date:
                    query = query.filter(Review.review_time <= end_date)
                
                # 按评审时间倒序
                query = query.order_by(desc(Review.review_time))
                
                # 限制数量
                if limit:
                    query = query.limit(limit)
                
                reviews = query.all()
                
                # 转换为字典
                result = []
                for review in reviews:
                    result.append({
                        'id': review.id,
                        'batch_id': review.batch_id,
                        'student_id': review.student_id,
                        'student_name': review.student.name,
                        'student_number': review.student.student_id,
                        'reviewer_name': review.reviewer_name,
                        'reviewer_account': review.reviewer_account,
                        'total_points': review.total_points,
                        'final_result': review.final_result,
                        'rank': review.rank,
                        'review_status': review.review_status,
                        'review_time': review.review_time.strftime('%Y-%m-%d %H:%M:%S') if review.review_time else '',
                        'comments': review.comments
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"查询评审记录失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def get_batch_with_details(batch_id):
        """
        获取批次及其详细信息（包含学生和评审）
        
        返回:
            dict: 批次详情
        """
        if not check_database_available():
            return None
        
        try:
            with session_scope() as session:
                if session is None:
                    return None
                
                batch = session.query(ReviewBatch).filter_by(id=batch_id).first()
                if not batch:
                    return None
                
                # 获取批次信息
                result = {
                    'batch_info': {
                        'id': batch.id,
                        'batch_code': batch.batch_code,
                        'batch_name': batch.batch_name,
                        'academic_year': batch.academic_year,
                        'semester': batch.semester,
                        'status': batch.status,
                        'reviewer_name': batch.reviewer_name,
                        'total_students': batch.total_students,
                        'reviewed_count': batch.reviewed_count,
                        'created_at': batch.created_at.strftime('%Y-%m-%d %H:%M:%S') if batch.created_at else ''
                    },
                    'students': [],
                    'reviews': []
                }
                
                # 获取学生列表
                students = session.query(Student).filter_by(batch_id=batch_id).all()
                for student in students:
                    result['students'].append({
                        'id': student.id,
                        'student_id': student.student_id,
                        'name': student.name,
                        'class_name': student.class_name,
                        'major': student.major,
                        'grade': student.grade
                    })
                
                # 获取评审记录
                reviews = session.query(Review).join(Student).filter(Review.batch_id == batch_id).all()
                for review in reviews:
                    result['reviews'].append({
                        'student_name': review.student.name,
                        'student_number': review.student.student_id,
                        'total_points': review.total_points,
                        'rank': review.rank,
                        'review_status': review.review_status,
                        'review_time': review.review_time.strftime('%Y-%m-%d %H:%M:%S') if review.review_time else ''
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"获取批次详情失败: {e}", exc_info=True)
            return None
