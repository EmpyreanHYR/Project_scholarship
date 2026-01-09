"""
数据库模型定义
使用 SQLAlchemy ORM 定义所有数据表结构
本模块完全独立，不会被业务代码调用
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# 创建基类
Base = declarative_base()


class ReviewBatch(Base):
    """
    评审批次表
    记录每次评审活动的基本信息
    """
    __tablename__ = 'review_batches'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='批次ID')
    
    # 基本信息
    batch_name = Column(String(200), nullable=False, comment='批次名称')
    batch_code = Column(String(50), unique=True, nullable=False, comment='批次编号')
    academic_year = Column(String(20), nullable=False, comment='学年，如2023-2024')
    semester = Column(String(20), nullable=False, comment='学期，如第一学期')
    
    # 时间信息
    start_date = Column(DateTime, comment='评审开始时间')
    end_date = Column(DateTime, comment='评审结束时间')
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 状态信息
    status = Column(String(20), default='draft', comment='状态：draft草稿/active进行中/completed完成/archived已归档')
    
    # 描述信息
    description = Column(Text, comment='批次描述')
    reviewer_name = Column(String(100), comment='评审人姓名')
    
    # 统计信息
    total_students = Column(Integer, default=0, comment='总学生数')
    reviewed_count = Column(Integer, default=0, comment='已评审数量')
    
    # 关联关系
    students = relationship('Student', back_populates='batch', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='batch', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='batch', cascade='all, delete-orphan')
    
    # 索引
    __table_args__ = (
        Index('idx_batch_code', 'batch_code'),
        Index('idx_academic_year', 'academic_year'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
        {'comment': '评审批次表'}
    )
    
    def __repr__(self):
        return f"<ReviewBatch(id={self.id}, batch_name='{self.batch_name}', batch_code='{self.batch_code}')>"


class Student(Base):
    """
    学生信息表
    存储学生基本信息
    """
    __tablename__ = 'students'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='学生记录ID')
    
    # 外键
    batch_id = Column(Integer, ForeignKey('review_batches.id', ondelete='CASCADE'), nullable=False, comment='所属批次ID')
    
    # 学生基本信息
    student_id = Column(String(50), nullable=False, comment='学号')
    name = Column(String(100), nullable=False, comment='姓名')
    class_name = Column(String(100), comment='班级')
    major = Column(String(100), comment='专业')
    grade = Column(String(20), comment='年级')
    
    # 联系信息
    phone = Column(String(20), comment='手机号')
    email = Column(String(100), comment='邮箱')
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    batch = relationship('ReviewBatch', back_populates='students')
    applications = relationship('Application', back_populates='student', cascade='all, delete-orphan')
    reviews = relationship('Review', back_populates='student', cascade='all, delete-orphan')
    
    # 索引和约束
    __table_args__ = (
        Index('idx_student_id', 'student_id'),
        Index('idx_batch_student', 'batch_id', 'student_id'),
        Index('idx_name', 'name'),
        UniqueConstraint('batch_id', 'student_id', name='uq_batch_student'),  # 同一批次中学号唯一
        {'comment': '学生信息表'}
    )
    
    def __repr__(self):
        return f"<Student(id={self.id}, student_id='{self.student_id}', name='{self.name}')>"


class Application(Base):
    """
    申请信息表
    存储学生的奖学金申请信息和加分项目
    """
    __tablename__ = 'applications'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='申请ID')
    
    # 外键
    batch_id = Column(Integer, ForeignKey('review_batches.id', ondelete='CASCADE'), nullable=False, comment='所属批次ID')
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, comment='学生ID')
    
    # 加分项目信息
    project_name = Column(String(200), comment='项目名称')
    project_type = Column(String(100), comment='项目类型')
    project_category = Column(String(100), comment='项目类别')
    project_level = Column(String(50), comment='项目级别')
    
    # 获奖信息
    award_name = Column(String(200), comment='获奖名称')
    award_level = Column(String(50), comment='获奖等级')
    award_rank = Column(String(50), comment='获奖排名')
    award_date = Column(DateTime, comment='获奖时间')
    
    # 分数信息
    points = Column(Float, default=0.0, comment='加分分值')
    base_points = Column(Float, default=0.0, comment='基础分')
    bonus_points = Column(Float, default=0.0, comment='奖励分')
    
    # 证明材料
    certificate_path = Column(String(500), comment='证书文件路径')
    certificate_url = Column(String(500), comment='证书URL')
    
    # 状态信息
    status = Column(String(20), default='pending', comment='状态：pending待审/approved通过/rejected拒绝')
    is_valid = Column(Boolean, default=True, comment='是否有效')
    
    # 备注信息
    remarks = Column(Text, comment='备注说明')
    reviewer_notes = Column(Text, comment='评审备注')
    
    # 时间信息
    submitted_at = Column(DateTime, comment='提交时间')
    reviewed_at = Column(DateTime, comment='评审时间')
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    batch = relationship('ReviewBatch', back_populates='applications')
    student = relationship('Student', back_populates='applications')
    
    # 索引
    __table_args__ = (
        Index('idx_batch_id', 'batch_id'),
        Index('idx_student_id', 'student_id'),
        Index('idx_project_type', 'project_type'),
        Index('idx_status', 'status'),
        Index('idx_submitted_at', 'submitted_at'),
        {'comment': '申请信息表'}
    )
    
    def __repr__(self):
        return f"<Application(id={self.id}, project_name='{self.project_name}', points={self.points})>"


class Review(Base):
    """
    评审记录表
    存储每次评审操作的详细记录
    """
    __tablename__ = 'reviews'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='评审记录ID')
    
    # 外键
    batch_id = Column(Integer, ForeignKey('review_batches.id', ondelete='CASCADE'), nullable=False, comment='所属批次ID')
    student_id = Column(Integer, ForeignKey('students.id', ondelete='CASCADE'), nullable=False, comment='学生ID')
    
    # 评审信息
    reviewer_name = Column(String(100), comment='评审人姓名')
    reviewer_account = Column(String(100), comment='评审人账号')
    
    # 评审结果
    total_points = Column(Float, default=0.0, comment='总分')
    final_result = Column(String(50), comment='最终结果')
    rank = Column(Integer, comment='排名')
    
    # 评审详情（JSON格式存储详细加分项）
    review_details = Column(Text, comment='评审详情JSON')
    
    # 状态信息
    review_status = Column(String(20), default='draft', comment='评审状态：draft草稿/submitted已提交/finalized已确认')
    is_passed = Column(Boolean, comment='是否通过')
    
    # 时间信息
    review_time = Column(DateTime, default=datetime.now, comment='评审时间')
    submit_time = Column(DateTime, comment='提交时间')
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 备注
    comments = Column(Text, comment='评审意见')
    
    # 关联关系
    batch = relationship('ReviewBatch', back_populates='reviews')
    student = relationship('Student', back_populates='reviews')
    
    # 索引
    __table_args__ = (
        Index('idx_batch_id', 'batch_id'),
        Index('idx_student_id', 'student_id'),
        Index('idx_reviewer_account', 'reviewer_account'),
        Index('idx_review_status', 'review_status'),
        Index('idx_review_time', 'review_time'),
        {'comment': '评审记录表'}
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, student_id={self.student_id}, total_points={self.total_points})>"


class AuditLog(Base):
    """
    审计日志表
    记录所有重要操作的日志
    """
    __tablename__ = 'audit_logs'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='日志ID')
    
    # 操作信息
    operation_type = Column(String(50), nullable=False, comment='操作类型：create/update/delete/export/import')
    operation_module = Column(String(50), comment='操作模块')
    operation_action = Column(String(100), comment='操作动作')
    
    # 操作者信息
    operator_name = Column(String(100), comment='操作人姓名')
    operator_account = Column(String(100), comment='操作人账号')
    operator_ip = Column(String(50), comment='操作人IP地址')
    
    # 关联信息
    batch_id = Column(Integer, comment='关联批次ID')
    student_id = Column(Integer, comment='关联学生ID')
    target_id = Column(Integer, comment='目标对象ID')
    target_type = Column(String(50), comment='目标对象类型')
    
    # 操作详情
    old_value = Column(Text, comment='修改前数据JSON')
    new_value = Column(Text, comment='修改后数据JSON')
    change_summary = Column(Text, comment='变更摘要')
    
    # 状态信息
    status = Column(String(20), default='success', comment='操作状态：success成功/failed失败/error错误')
    error_message = Column(Text, comment='错误信息')
    
    # 时间信息
    operation_time = Column(DateTime, default=datetime.now, nullable=False, comment='操作时间')
    
    # 其他信息
    user_agent = Column(String(500), comment='用户代理')
    request_params = Column(Text, comment='请求参数JSON')
    
    # 索引
    __table_args__ = (
        Index('idx_operation_type', 'operation_type'),
        Index('idx_operator_account', 'operator_account'),
        Index('idx_operation_time', 'operation_time'),
        Index('idx_batch_id', 'batch_id'),
        Index('idx_target', 'target_type', 'target_id'),
        {'comment': '审计日志表'}
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, operation_type='{self.operation_type}', operator_account='{self.operator_account}')>"
