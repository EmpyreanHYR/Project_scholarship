"""
数据库导出服务
提供从数据库导出Excel的功能
"""

import logging
import pandas as pd
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from .query_service import QueryService
from .dao import AuditLogDAO
from .connection import check_database_available

# 配置日志
logger = logging.getLogger(__name__)


class ExportService:
    """导出服务类"""
    
    @staticmethod
    def export_batch_to_excel(batch_id, file_path, operator_account=None, operator_name=None):
        """
        导出完整批次到Excel（包含多个Sheet）
        
        参数:
            batch_id: 批次ID
            file_path: 导出文件路径
            operator_account: 操作人账号
            operator_name: 操作人姓名
        
        返回:
            dict: {
                'success': bool,
                'message': str,
                'file_path': str
            }
        """
        result = {
            'success': False,
            'message': '',
            'file_path': file_path
        }
        
        if not check_database_available():
            result['message'] = '数据库未启用'
            return result
        
        try:
            # 获取批次详情
            batch_details = QueryService.get_batch_with_details(batch_id)
            if not batch_details:
                result['message'] = '批次不存在'
                return result
            
            batch_info = batch_details['batch_info']
            
            # 创建Excel writer
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Sheet 1: 批次汇总
                summary_data = [{
                    '批次编号': batch_info['batch_code'],
                    '批次名称': batch_info['batch_name'],
                    '学年': batch_info['academic_year'],
                    '学期': batch_info['semester'],
                    '状态': batch_info['status'],
                    '评审人': batch_info['reviewer_name'],
                    '总学生数': batch_info['total_students'],
                    '已评审数': batch_info['reviewed_count'],
                    '创建时间': batch_info['created_at'],
                    '导出时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='批次汇总', index=False)
                
                # Sheet 2: 学生列表
                if batch_details['students']:
                    df_students = pd.DataFrame(batch_details['students'])
                    df_students.to_excel(writer, sheet_name='学生列表', index=False)
                
                # Sheet 3: 评审结果
                if batch_details['reviews']:
                    df_reviews = pd.DataFrame(batch_details['reviews'])
                    df_reviews.to_excel(writer, sheet_name='评审结果', index=False)
                
                # Sheet 4: 详细申请记录
                applications = QueryService.query_applications(batch_id=batch_id, limit=10000)
                if applications:
                    df_apps = pd.DataFrame(applications)
                    df_apps.to_excel(writer, sheet_name='申请详情', index=False)
            
            # 记录审计日志
            AuditLogDAO.log_operation(
                operation_type='export',
                operation_action=f'导出批次Excel: {batch_info["batch_name"]}',
                operator_account=operator_account or 'system',
                operator_name=operator_name,
                batch_id=batch_id,
                new_value={'file_path': file_path},
                status='success'
            )
            
            result['success'] = True
            result['message'] = f'成功导出批次数据，包含{len(batch_details["students"])}个学生'
            logger.info(f"批次导出成功: {batch_info['batch_name']}")
            
        except Exception as e:
            result['message'] = f'导出失败: {str(e)}'
            logger.error(result['message'], exc_info=True)
            
            # 记录失败日志
            try:
                AuditLogDAO.log_operation(
                    operation_type='export',
                    operation_action='导出批次Excel',
                    operator_account=operator_account or 'system',
                    operator_name=operator_name,
                    batch_id=batch_id,
                    status='failed',
                    error_message=result['message']
                )
            except:
                pass
        
        return result
    
    @staticmethod
    def export_query_results_to_excel(results, file_path, sheet_name='查询结果',
                                     operator_account=None, operator_name=None):
        """
        导出查询结果到Excel
        
        参数:
            results: 查询结果列表（字典列表）
            file_path: 导出文件路径
            sheet_name: Sheet名称
            operator_account: 操作人账号
            operator_name: 操作人姓名
        
        返回:
            dict: {
                'success': bool,
                'message': str,
                'file_path': str
            }
        """
        result = {
            'success': False,
            'message': '',
            'file_path': file_path
        }
        
        if not results:
            result['message'] = '没有数据可导出'
            return result
        
        try:
            # 转换为DataFrame并导出
            df = pd.DataFrame(results)
            df.to_excel(file_path, sheet_name=sheet_name, index=False)
            
            # 记录审计日志
            if check_database_available():
                AuditLogDAO.log_operation(
                    operation_type='export',
                    operation_action=f'导出查询结果: {len(results)}条记录',
                    operator_account=operator_account or 'system',
                    operator_name=operator_name,
                    new_value={'file_path': file_path, 'count': len(results)},
                    status='success'
                )
            
            result['success'] = True
            result['message'] = f'成功导出{len(results)}条记录'
            logger.info(f"查询结果导出成功: {len(results)}条")
            
        except Exception as e:
            result['message'] = f'导出失败: {str(e)}'
            logger.error(result['message'], exc_info=True)
        
        return result
    
    @staticmethod
    def export_reviews_with_statistics(batch_id, file_path, operator_account=None, operator_name=None):
        """
        导出评审结果并包含统计信息
        
        参数:
            batch_id: 批次ID
            file_path: 导出文件路径
            operator_account: 操作人账号
            operator_name: 操作人姓名
        
        返回:
            dict: 导出结果
        """
        result = {
            'success': False,
            'message': '',
            'file_path': file_path
        }
        
        if not check_database_available():
            result['message'] = '数据库未启用'
            return result
        
        try:
            # 获取评审记录
            reviews = QueryService.query_reviews(batch_id=batch_id, limit=10000)
            if not reviews:
                result['message'] = '没有评审记录'
                return result
            
            # 创建Excel writer
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Sheet 1: 评审结果
                df_reviews = pd.DataFrame(reviews)
                df_reviews = df_reviews.sort_values('total_points', ascending=False)
                df_reviews.to_excel(writer, sheet_name='评审结果', index=False)
                
                # Sheet 2: 统计信息
                stats_data = {
                    '总人数': [len(reviews)],
                    '最高分': [max([r['total_points'] for r in reviews])],
                    '最低分': [min([r['total_points'] for r in reviews])],
                    '平均分': [sum([r['total_points'] for r in reviews]) / len(reviews)],
                    '已完成评审': [len([r for r in reviews if r['review_status'] == 'submitted'])],
                    '导出时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                }
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='统计信息', index=False)
            
            result['success'] = True
            result['message'] = f'成功导出{len(reviews)}条评审记录'
            logger.info(f"评审结果导出成功: {len(reviews)}条")
            
        except Exception as e:
            result['message'] = f'导出失败: {str(e)}'
            logger.error(result['message'], exc_info=True)
        
        return result
