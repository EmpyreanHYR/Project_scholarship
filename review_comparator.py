"""
奖学金评审软件 - 评审结果对比分析模块

功能：
1. 不同批次评审结果对比
2. 学生历史评审对比
3. 评审趋势分析
4. 统计报表生成
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import pandas as pd

logger = logging.getLogger(__name__)


class ReviewComparator:
    """评审结果对比器"""
    
    def __init__(self):
        """初始化对比器"""
        self.batches = {}  # {batch_id: batch_data}
    
    def add_batch(self, batch_id, batch_data, description=""):
        """添加评审批次
        
        Args:
            batch_id: 批次ID
            batch_data: 批次数据 {student_id: {awards: [], total_score: float}}
            description: 批次描述
        """
        self.batches[batch_id] = {
            'data': batch_data,
            'description': description,
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"添加评审批次: {batch_id}")
    
    def compare_batches(self, batch_id1, batch_id2):
        """对比两个批次的评审结果
        
        Args:
            batch_id1: 第一个批次ID
            batch_id2: 第二个批次ID
            
        Returns:
            dict: 对比结果
        """
        if batch_id1 not in self.batches or batch_id2 not in self.batches:
            raise ValueError("批次不存在")
        
        batch1 = self.batches[batch_id1]['data']
        batch2 = self.batches[batch_id2]['data']
        
        comparison = {
            'batch1': batch_id1,
            'batch2': batch_id2,
            'students': {},
            'summary': {
                'total_students_batch1': len(batch1),
                'total_students_batch2': len(batch2),
                'common_students': 0,
                'score_changes': [],
                'new_students': [],
                'removed_students': []
            }
        }
        
        # 获取共同学生
        common_students = set(batch1.keys()) & set(batch2.keys())
        comparison['summary']['common_students'] = len(common_students)
        
        # 获取新增和移除的学生
        new_students = set(batch2.keys()) - set(batch1.keys())
        removed_students = set(batch1.keys()) - set(batch2.keys())
        
        comparison['summary']['new_students'] = list(new_students)
        comparison['summary']['removed_students'] = list(removed_students)
        
        # 对比共同学生的成绩变化
        for student_id in common_students:
            student1 = batch1[student_id]
            student2 = batch2[student_id]
            
            score1 = student1.get('total_score', 0)
            score2 = student2.get('total_score', 0)
            score_change = score2 - score1
            
            comparison['students'][student_id] = {
                'score1': score1,
                'score2': score2,
                'score_change': score_change,
                'awards1': student1.get('awards', []),
                'awards2': student2.get('awards', [])
            }
            
            comparison['summary']['score_changes'].append({
                'student_id': student_id,
                'score_change': score_change
            })
        
        # 计算统计信息
        if comparison['summary']['score_changes']:
            changes = [s['score_change'] for s in comparison['summary']['score_changes']]
            comparison['summary']['avg_score_change'] = sum(changes) / len(changes)
            comparison['summary']['max_score_change'] = max(changes)
            comparison['summary']['min_score_change'] = min(changes)
        
        return comparison
    
    def get_student_history(self, student_id):
        """获取学生的历史评审记录
        
        Args:
            student_id: 学生ID
            
        Returns:
            list: 历史记录列表
        """
        history = []
        
        for batch_id, batch_info in self.batches.items():
            batch_data = batch_info['data']
            if student_id in batch_data:
                student_data = batch_data[student_id]
                history.append({
                    'batch_id': batch_id,
                    'description': batch_info['description'],
                    'timestamp': batch_info['timestamp'],
                    'total_score': student_data.get('total_score', 0),
                    'awards': student_data.get('awards', [])
                })
        
        # 按时间排序
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        return history
    
    def get_batch_statistics(self, batch_id):
        """获取批次统计信息
        
        Args:
            batch_id: 批次ID
            
        Returns:
            dict: 统计信息
        """
        if batch_id not in self.batches:
            raise ValueError("批次不存在")
        
        batch_data = self.batches[batch_id]['data']
        
        # 计算统计信息
        scores = [student.get('total_score', 0) for student in batch_data.values()]
        
        if not scores:
            return {
                'batch_id': batch_id,
                'student_count': 0,
                'total_score': 0,
                'avg_score': 0,
                'max_score': 0,
                'min_score': 0,
                'score_distribution': {}
            }
        
        # 分数分布
        distribution = defaultdict(int)
        for score in scores:
            # 按 10 分段统计
            bracket = f"{int(score // 10) * 10}-{int(score // 10) * 10 + 9}"
            distribution[bracket] += 1
        
        return {
            'batch_id': batch_id,
            'student_count': len(scores),
            'total_score': sum(scores),
            'avg_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'score_distribution': dict(distribution)
        }
    
    def export_comparison(self, comparison, file_path):
        """导出对比结果
        
        Args:
            comparison: 对比结果
            file_path: 导出文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, ensure_ascii=False, indent=2)
            logger.info(f"对比结果已导出: {file_path}")
        except Exception as e:
            logger.error(f"导出对比结果失败: {e}")
            raise
    
    def save_batches(self, file_path):
        """保存所有批次数据
        
        Args:
            file_path: 保存文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.batches, f, ensure_ascii=False, indent=2)
            logger.info(f"批次数据已保存: {file_path}")
        except Exception as e:
            logger.error(f"保存批次数据失败: {e}")
            raise
    
    def load_batches(self, file_path):
        """加载批次数据
        
        Args:
            file_path: 加载文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.batches = json.load(f)
            logger.info(f"批次数据已加载: {file_path}")
        except Exception as e:
            logger.error(f"加载批次数据失败: {e}")
            raise


class ComparisonDialog:
    """对比分析对话框"""
    
    def __init__(self, parent, comparator):
        """初始化对比对话框
        
        Args:
            parent: 父窗口
            comparator: ReviewComparator 实例
        """
        self.parent = parent
        self.comparator = comparator
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("评审结果对比分析")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        
        # 创建界面
        self._create_ui()
        
        # 刷新批次列表
        self._refresh_batch_list()
    
    def _create_ui(self):
        """创建界面"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="评审结果对比分析", font=("Arial", 16, "bold")).pack(pady=(0, 15))
        
        # 批次选择框架
        select_frame = ttk.LabelFrame(main_frame, text="选择批次", padding="10")
        select_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 批次1选择
        batch1_frame = ttk.Frame(select_frame)
        batch1_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(batch1_frame, text="批次1:").pack(side=tk.LEFT, padx=(0, 10))
        self.batch1_var = tk.StringVar()
        self.batch1_combo = ttk.Combobox(batch1_frame, textvariable=self.batch1_var, state='readonly', width=40)
        self.batch1_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 批次2选择
        batch2_frame = ttk.Frame(select_frame)
        batch2_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(batch2_frame, text="批次2:").pack(side=tk.LEFT, padx=(0, 10))
        self.batch2_var = tk.StringVar()
        self.batch2_combo = ttk.Combobox(batch2_frame, textvariable=self.batch2_var, state='readonly', width=40)
        self.batch2_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 按钮
        btn_frame = ttk.Frame(select_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="对比分析", command=self._compare_batches).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="查看统计", command=self._show_statistics).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="导出结果", command=self._export_comparison).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="加载数据", command=self._load_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="保存数据", command=self._save_data).pack(side=tk.LEFT)
        
        # 结果显示框架
        result_frame = ttk.LabelFrame(main_frame, text="对比结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建 Notebook 用于显示不同类型的对比结果
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 概览标签页
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="概览")
        self._create_overview_tab(overview_frame)
        
        # 学生详情标签页
        students_frame = ttk.Frame(self.notebook)
        self.notebook.add(students_frame, text="学生详情")
        self._create_students_tab(students_frame)
        
        # 分数变化标签页
        changes_frame = ttk.Frame(self.notebook)
        self.notebook.add(changes_frame, text="分数变化")
        self._create_changes_tab(changes_frame)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var).pack(fill=tk.X, pady=(10, 0))
    
    def _create_overview_tab(self, parent):
        """创建概览标签页"""
        # 使用 Text 组件显示概览信息
        self.overview_text = tk.Text(parent, wrap=tk.WORD, height=20)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.overview_text.yview)
        self.overview_text.configure(yscrollcommand=scrollbar.set)
        
        self.overview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_students_tab(self, parent):
        """创建学生详情标签页"""
        # 创建 Treeview
        columns = ("学号", "批次1分数", "批次2分数", "分数变化", "变化率")
        self.students_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.students_tree.heading(col, text=col)
            self.students_tree.column(col, width=100, anchor=tk.CENTER)
        
        self.students_tree.column("学号", width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=scrollbar.set)
        
        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_changes_tab(self, parent):
        """创建分数变化标签页"""
        # 创建 Treeview
        columns = ("学号", "分数变化", "变化类型", "变化幅度")
        self.changes_tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.changes_tree.heading(col, text=col)
            self.changes_tree.column(col, width=100, anchor=tk.CENTER)
        
        self.changes_tree.column("学号", width=120)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.changes_tree.yview)
        self.changes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.changes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _refresh_batch_list(self):
        """刷新批次列表"""
        batch_ids = list(self.comparator.batches.keys())
        
        # 创建显示列表
        batch_list = []
        for batch_id in batch_ids:
            batch_info = self.comparator.batches[batch_id]
            description = batch_info.get('description', '')
            timestamp = batch_info.get('timestamp', '')
            
            # 格式化时间
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass
            
            display_text = f"{batch_id}"
            if description:
                display_text += f" - {description}"
            if timestamp:
                display_text += f" ({timestamp})"
            
            batch_list.append(display_text)
        
        self.batch1_combo['values'] = batch_list
        self.batch2_combo['values'] = batch_list
        
        if batch_list:
            self.batch1_combo.current(0)
            if len(batch_list) > 1:
                self.batch2_combo.current(1)
    
    def _compare_batches(self):
        """对比批次"""
        batch1_text = self.batch1_var.get()
        batch2_text = self.batch2_var.get()
        
        if not batch1_text or not batch2_text:
            messagebox.showwarning("警告", "请选择两个批次！")
            return
        
        # 提取批次ID
        batch1_id = batch1_text.split(" - ")[0].strip()
        batch2_id = batch2_text.split(" - ")[0].strip()
        
        if batch1_id == batch2_id:
            messagebox.showwarning("警告", "请选择不同的批次！")
            return
        
        try:
            # 执行对比
            comparison = self.comparator.compare_batches(batch1_id, batch2_id)
            self.current_comparison = comparison
            
            # 更新概览
            self._update_overview(comparison)
            
            # 更新学生详情
            self._update_students(comparison)
            
            # 更新分数变化
            self._update_changes(comparison)
            
            self.status_var.set(f"对比完成: {batch1_id} vs {batch2_id}")
            
        except Exception as e:
            messagebox.showerror("错误", f"对比失败：{e}")
    
    def _update_overview(self, comparison):
        """更新概览显示"""
        self.overview_text.delete(1.0, tk.END)
        
        summary = comparison['summary']
        
        text = "=" * 60 + "\n"
        text += "评审结果对比分析报告\n"
        text += "=" * 60 + "\n\n"
        
        text += f"批次1: {comparison['batch1']}\n"
        text += f"批次2: {comparison['batch2']}\n\n"
        
        text += "【基本统计】\n"
        text += f"批次1学生数: {summary['total_students_batch1']}\n"
        text += f"批次2学生数: {summary['total_students_batch2']}\n"
        text += f"共同学生数: {summary['common_students']}\n"
        text += f"新增学生数: {len(summary['new_students'])}\n"
        text += f"移除学生数: {len(summary['removed_students'])}\n\n"
        
        if summary.get('avg_score_change') is not None:
            text += "【分数变化统计】\n"
            text += f"平均分数变化: {summary['avg_score_change']:.2f}\n"
            text += f"最大分数增加: {summary['max_score_change']:.2f}\n"
            text += f"最大分数减少: {summary['min_score_change']:.2f}\n\n"
        
        if summary['new_students']:
            text += "【新增学生】\n"
            for student_id in summary['new_students']:
                text += f"  • {student_id}\n"
            text += "\n"
        
        if summary['removed_students']:
            text += "【移除学生】\n"
            for student_id in summary['removed_students']:
                text += f"  • {student_id}\n"
            text += "\n"
        
        text += "=" * 60 + "\n"
        text += f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += "=" * 60
        
        self.overview_text.insert(1.0, text)
    
    def _update_students(self, comparison):
        """更新学生详情"""
        # 清空表格
        for item in self.students_tree.get_children():
            self.students_tree.delete(item)
        
        # 添加数据
        for student_id, student_data in comparison['students'].items():
            score1 = student_data['score1']
            score2 = student_data['score2']
            score_change = student_data['score_change']
            
            # 计算变化率
            if score1 > 0:
                change_rate = (score_change / score1) * 100
            else:
                change_rate = 0 if score_change == 0 else float('inf')
            
            self.students_tree.insert("", "end", values=(
                student_id,
                f"{score1:.2f}",
                f"{score2:.2f}",
                f"{score_change:+.2f}",
                f"{change_rate:+.1f}%"
            ))
    
    def _update_changes(self, comparison):
        """更新分数变化"""
        # 清空表格
        for item in self.changes_tree.get_children():
            self.changes_tree.delete(item)
        
        # 添加数据
        for change in comparison['summary']['score_changes']:
            student_id = change['student_id']
            score_change = change['score_change']
            
            # 确定变化类型
            if score_change > 0:
                change_type = "增加"
                change_magnitude = "显著" if score_change > 5 else "轻微"
            elif score_change < 0:
                change_type = "减少"
                change_magnitude = "显著" if score_change < -5 else "轻微"
            else:
                change_type = "不变"
                change_magnitude = "-"
            
            self.changes_tree.insert("", "end", values=(
                student_id,
                f"{score_change:+.2f}",
                change_type,
                change_magnitude
            ))
    
    def _show_statistics(self):
        """显示统计信息"""
        batch_text = self.batch1_var.get()
        if not batch_text:
            messagebox.showwarning("警告", "请选择批次！")
            return
        
        batch_id = batch_text.split(" - ")[0].strip()
        
        try:
            stats = self.comparator.get_batch_statistics(batch_id)
            
            # 创建统计窗口
            stats_window = tk.Toplevel(self.dialog)
            stats_window.title(f"批次统计 - {batch_id}")
            stats_window.geometry("400x300")
            
            # 显示统计信息
            text = tk.Text(stats_window, wrap=tk.WORD, padding=10)
            text.pack(fill=tk.BOTH, expand=True)
            
            stats_text = "=" * 40 + "\n"
            stats_text += f"批次统计: {batch_id}\n"
            stats_text += "=" * 40 + "\n\n"
            stats_text += f"学生数量: {stats['student_count']}\n"
            stats_text += f"总分: {stats['total_score']:.2f}\n"
            stats_text += f"平均分: {stats['avg_score']:.2f}\n"
            stats_text += f"最高分: {stats['max_score']:.2f}\n"
            stats_text += f"最低分: {stats['min_score']:.2f}\n\n"
            
            stats_text += "【分数分布】\n"
            for bracket, count in sorted(stats['score_distribution'].items()):
                stats_text += f"  {bracket}: {count} 人\n"
            
            text.insert(1.0, stats_text)
            
        except Exception as e:
            messagebox.showerror("错误", f"获取统计信息失败：{e}")
    
    def _export_comparison(self):
        """导出对比结果"""
        if not hasattr(self, 'current_comparison'):
            messagebox.showwarning("警告", "请先执行对比分析！")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="导出对比结果",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.comparator.export_comparison(self.current_comparison, file_path)
            messagebox.showinfo("成功", f"对比结果已导出到：\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{e}")
    
    def _load_data(self):
        """加载数据"""
        file_path = filedialog.askopenfilename(
            title="加载批次数据",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.comparator.load_batches(file_path)
            self._refresh_batch_list()
            messagebox.showinfo("成功", "数据加载成功！")
        except Exception as e:
            messagebox.showerror("错误", f"加载失败：{e}")
    
    def _save_data(self):
        """保存数据"""
        file_path = filedialog.asksaveasfilename(
            title="保存批次数据",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.comparator.save_batches(file_path)
            messagebox.showinfo("成功", f"数据已保存到：\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")


class ReviewTrendAnalyzer:
    """评审趋势分析器"""
    
    def __init__(self, comparator):
        """初始化趋势分析器
        
        Args:
            comparator: ReviewComparator 实例
        """
        self.comparator = comparator
    
    def analyze_trends(self, student_id=None):
        """分析评审趋势
        
        Args:
            student_id: 学生ID（可选，分析特定学生）
            
        Returns:
            dict: 趋势分析结果
        """
        if student_id:
            return self._analyze_student_trend(student_id)
        else:
            return self._analyze_overall_trend()
    
    def _analyze_student_trend(self, student_id):
        """分析单个学生的趋势"""
        history = self.comparator.get_student_history(student_id)
        
        if len(history) < 2:
            return {
                'student_id': student_id,
                'trend': 'insufficient_data',
                'message': '数据不足，无法分析趋势'
            }
        
        # 提取分数序列
        scores = [h['total_score'] for h in history]
        
        # 计算趋势
        if len(scores) >= 2:
            recent_change = scores[0] - scores[1]  # 最近一次变化
            avg_change = sum(scores[i] - scores[i+1] for i in range(len(scores)-1)) / (len(scores)-1)
            
            if recent_change > 0:
                trend = 'improving'
                trend_desc = '呈上升趋势'
            elif recent_change < 0:
                trend = 'declining'
                trend_desc = '呈下降趋势'
            else:
                trend = 'stable'
                trend_desc = '保持稳定'
        else:
            trend = 'unknown'
            trend_desc = '无法确定趋势'
            recent_change = 0
            avg_change = 0
        
        return {
            'student_id': student_id,
            'trend': trend,
            'trend_description': trend_desc,
            'recent_change': recent_change,
            'avg_change': avg_change,
            'history_count': len(history),
            'latest_score': scores[0] if scores else 0,
            'history': history
        }
    
    def _analyze_overall_trend(self):
        """分析整体趋势"""
        all_students = set()
        
        # 收集所有学生
        for batch_info in self.comparator.batches.values():
            all_students.update(batch_info['data'].keys())
        
        # 分析每个学生的趋势
        trends = {
            'improving': [],
            'declining': [],
            'stable': [],
            'insufficient_data': []
        }
        
        for student_id in all_students:
            trend_result = self._analyze_student_trend(student_id)
            trend = trend_result['trend']
            trends[trend].append(student_id)
        
        # 计算统计
        total_students = len(all_students)
        improving_count = len(trends['improving'])
        declining_count = len(trends['declining'])
        stable_count = len(trends['stable'])
        
        return {
            'total_students': total_students,
            'improving_count': improving_count,
            'declining_count': declining_count,
            'stable_count': stable_count,
            'improving_rate': (improving_count / total_students * 100) if total_students > 0 else 0,
            'declining_rate': (declining_count / total_students * 100) if total_students > 0 else 0,
            'trends': trends
        }


# 使用示例
if __name__ == "__main__":
    # 测试对比器
    comparator = ReviewComparator()
    
    # 模拟批次数据
    batch1_data = {
        '001': {'total_score': 85, 'awards': ['数学竞赛一等奖']},
        '002': {'total_score': 72, 'awards': ['英语竞赛二等奖']},
        '003': {'total_score': 90, 'awards': ['科研项目']}
    }
    
    batch2_data = {
        '001': {'total_score': 92, 'awards': ['数学竞赛一等奖', '科研项目']},
        '002': {'total_score': 68, 'awards': ['英语竞赛二等奖']},
        '004': {'total_score': 78, 'awards': ['创新大赛']}
    }
    
    # 添加批次
    comparator.add_batch('2024春季', batch1_data, '2024年春季评审')
    comparator.add_batch('2024秋季', batch2_data, '2024年秋季评审')
    
    # 对比批次
    comparison = comparator.compare_batches('2024春季', '2024秋季')
    print("对比结果:", comparison)
    
    # 获取统计信息
    stats = comparator.get_batch_statistics('2024春季')
    print("批次统计:", stats)
    
    # 趋势分析
    analyzer = ReviewTrendAnalyzer(comparator)
    trend = analyzer.analyze_trends('001')
    print("学生趋势:", trend)
    
    overall_trend = analyzer.analyze_trends()
    print("整体趋势:", overall_trend)
    
    print("测试完成！")
