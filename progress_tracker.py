"""
奖学金评审软件 - 评审进度追踪模块

功能：
1. 可视化评审进度面板
2. 多维度进度统计
3. 进度预测和提醒
4. 进度导出和报告
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReviewProgressTracker:
    """评审进度追踪器"""
    
    def __init__(self):
        """初始化进度追踪器"""
        self.progress_data = {
            'total_students': 0,
            'total_awards': 0,
            'reviewed_awards': 0,
            'approved_awards': 0,
            'rejected_awards': 0,
            'start_time': None,
            'last_update_time': None,
            'student_progress': {},  # {student_id: {total: int, reviewed: int, approved: int, rejected: int}}
            'daily_progress': {},    # {date: {reviewed: int, approved: int, rejected: int}}
            'review_history': []     # [{timestamp, student_id, award_name, decision, reviewer}]
        }
    
    def initialize(self, students_data):
        """初始化进度数据
        
        Args:
            students_data: 学生数据字典 {student_id: {'df': DataFrame, 'student_info': dict}}
        """
        self.progress_data['total_students'] = len(students_data)
        self.progress_data['start_time'] = datetime.now().isoformat()
        
        total_awards = 0
        for student_id, data in students_data.items():
            df = data.get('df')
            if df is not None:
                student_awards = len(df)
                total_awards += student_awards
                
                self.progress_data['student_progress'][student_id] = {
                    'total': student_awards,
                    'reviewed': 0,
                    'approved': 0,
                    'rejected': 0,
                    'student_info': data.get('student_info', {})
                }
        
        self.progress_data['total_awards'] = total_awards
        logger.info(f"进度追踪初始化完成: {len(students_data)} 名学生, {total_awards} 个奖项")
    
    def record_review(self, student_id, award_name, decision, reviewer=None):
        """记录评审结果
        
        Args:
            student_id: 学生ID
            award_name: 奖项名称
            decision: 评审决定（认定/不予认定）
            reviewer: 评审人
        """
        timestamp = datetime.now()
        date_str = timestamp.strftime("%Y-%m-%d")
        
        # 更新总体进度
        self.progress_data['reviewed_awards'] += 1
        if decision == "认定":
            self.progress_data['approved_awards'] += 1
        else:
            self.progress_data['rejected_awards'] += 1
        
        # 更新学生进度
        if student_id in self.progress_data['student_progress']:
            student_prog = self.progress_data['student_progress'][student_id]
            student_prog['reviewed'] += 1
            if decision == "认定":
                student_prog['approved'] += 1
            else:
                student_prog['rejected'] += 1
        
        # 更新每日进度
        if date_str not in self.progress_data['daily_progress']:
            self.progress_data['daily_progress'][date_str] = {
                'reviewed': 0,
                'approved': 0,
                'rejected': 0
            }
        
        daily = self.progress_data['daily_progress'][date_str]
        daily['reviewed'] += 1
        if decision == "认定":
            daily['approved'] += 1
        else:
            daily['rejected'] += 1
        
        # 记录评审历史
        self.progress_data['review_history'].append({
            'timestamp': timestamp.isoformat(),
            'student_id': student_id,
            'award_name': award_name,
            'decision': decision,
            'reviewer': reviewer or '未知'
        })
        
        # 更新最后更新时间
        self.progress_data['last_update_time'] = timestamp.isoformat()
        
        logger.debug(f"记录评审: {student_id} - {award_name} - {decision}")
    
    def get_progress_summary(self):
        """获取进度摘要
        
        Returns:
            dict: 进度摘要数据
        """
        total = self.progress_data['total_awards']
        reviewed = self.progress_data['reviewed_awards']
        approved = self.progress_data['approved_awards']
        rejected = self.progress_data['rejected_awards']
        
        # 计算进度百分比
        progress_percent = (reviewed / total * 100) if total > 0 else 0
        approval_rate = (approved / reviewed * 100) if reviewed > 0 else 0
        
        # 计算预计完成时间
        estimated_completion = self._estimate_completion_time()
        
        # 计算今日进度
        today = datetime.now().strftime("%Y-%m-%d")
        today_progress = self.progress_data['daily_progress'].get(today, {
            'reviewed': 0,
            'approved': 0,
            'rejected': 0
        })
        
        return {
            'total_students': self.progress_data['total_students'],
            'total_awards': total,
            'reviewed_awards': reviewed,
            'approved_awards': approved,
            'rejected_awards': rejected,
            'remaining_awards': total - reviewed,
            'progress_percent': progress_percent,
            'approval_rate': approval_rate,
            'estimated_completion': estimated_completion,
            'today_progress': today_progress,
            'start_time': self.progress_data['start_time'],
            'last_update_time': self.progress_data['last_update_time']
        }
    
    def get_student_progress(self, student_id):
        """获取单个学生的进度
        
        Args:
            student_id: 学生ID
            
        Returns:
            dict: 学生进度数据
        """
        return self.progress_data['student_progress'].get(student_id, {})
    
    def get_all_student_progress(self):
        """获取所有学生的进度
        
        Returns:
            dict: 所有学生进度数据
        """
        return self.progress_data['student_progress']
    
    def get_daily_progress(self, days=7):
        """获取每日进度
        
        Args:
            days: 获取最近几天的数据
            
        Returns:
            dict: 每日进度数据
        """
        daily = self.progress_data['daily_progress']
        
        # 只返回最近几天的数据
        sorted_dates = sorted(daily.keys(), reverse=True)[:days]
        return {date: daily[date] for date in sorted_dates}
    
    def get_review_history(self, limit=100):
        """获取评审历史
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            list: 评审历史记录
        """
        return self.progress_data['review_history'][-limit:]
    
    def _estimate_completion_time(self):
        """预估完成时间
        
        Returns:
            str: 预计完成时间，如果无法预估则返回 None
        """
        if not self.progress_data['start_time'] or self.progress_data['reviewed_awards'] == 0:
            return None
        
        start_time = datetime.fromisoformat(self.progress_data['start_time'])
        now = datetime.now()
        
        # 计算已用时间
        elapsed = (now - start_time).total_seconds()
        
        # 计算平均每个奖项的评审时间
        avg_time_per_award = elapsed / self.progress_data['reviewed_awards']
        
        # 计算剩余时间
        remaining_awards = self.progress_data['total_awards'] - self.progress_data['reviewed_awards']
        remaining_time = avg_time_per_award * remaining_awards
        
        # 预计完成时间
        estimated_time = now + timedelta(seconds=remaining_time)
        
        return estimated_time.strftime("%Y-%m-%d %H:%M")
    
    def export_progress(self, file_path):
        """导出进度数据
        
        Args:
            file_path: 导出文件路径
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, ensure_ascii=False, indent=2)
            logger.info(f"进度数据已导出: {file_path}")
        except Exception as e:
            logger.error(f"导出进度数据失败: {e}")
            raise
    
    def import_progress(self, file_path):
        """导入进度数据
        
        Args:
            file_path: 导入文件路径
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.progress_data = json.load(f)
            logger.info(f"进度数据已导入: {file_path}")
        except Exception as e:
            logger.error(f"导入进度数据失败: {e}")
            raise


class ProgressDashboard:
    """评审进度仪表盘"""
    
    def __init__(self, parent, progress_tracker):
        """初始化进度仪表盘
        
        Args:
            parent: 父窗口
            progress_tracker: ReviewProgressTracker 实例
        """
        self.parent = parent
        self.tracker = progress_tracker
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("评审进度追踪")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        # 创建界面
        self._create_ui()
        
        # 刷新数据
        self._refresh_data()
    
    def _create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="评审进度仪表盘", font=("Arial", 16, "bold")).pack(pady=(0, 15))
        
        # 概览卡片框架
        cards_frame = ttk.Frame(main_frame)
        cards_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 创建概览卡片
        self._create_card(cards_frame, "总学生数", "0", 0, 0)
        self._create_card(cards_frame, "总奖项数", "0", 0, 1)
        self._create_card(cards_frame, "已评审", "0", 0, 2)
        self._create_card(cards_frame, "待评审", "0", 0, 3)
        
        self._create_card(cards_frame, "完成率", "0%", 1, 0)
        self._create_card(cards_frame, "认定率", "0%", 1, 1)
        self._create_card(cards_frame, "今日评审", "0", 1, 2)
        self._create_card(cards_frame, "预计完成", "N/A", 1, 3)
        
        # 进度条框架
        progress_frame = ttk.LabelFrame(main_frame, text="总体进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack()
        
        # 学生进度表格
        table_frame = ttk.LabelFrame(main_frame, text="学生进度明细", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建 Treeview
        columns = ("学号", "姓名", "总奖项", "已评审", "认定", "不予认定", "完成率")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        
        self.tree.column("学号", width=120)
        self.tree.column("姓名", width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Button(btn_frame, text="刷新", command=self._refresh_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="导出进度", command=self._export_progress).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="查看历史", command=self._show_history).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT)
    
    def _create_card(self, parent, title, value, row, col):
        """创建概览卡片"""
        card = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        card.grid(row=row, column=col, padx=5, pady=5, sticky=tk.NSEW)
        
        parent.columnconfigure(col, weight=1)
        
        ttk.Label(card, text=title, font=("Arial", 10)).pack(pady=(10, 5))
        
        value_label = ttk.Label(card, text=value, font=("Arial", 18, "bold"))
        value_label.pack(pady=(0, 10))
        
        # 保存标签引用以便更新
        setattr(self, f"card_{row}_{col}", value_label)
    
    def _refresh_data(self):
        """刷新数据"""
        summary = self.tracker.get_progress_summary()
        
        # 更新概览卡片
        self.card_0_0.config(text=str(summary['total_students']))
        self.card_0_1.config(text=str(summary['total_awards']))
        self.card_0_2.config(text=str(summary['reviewed_awards']))
        self.card_0_3.config(text=str(summary['remaining_awards']))
        
        self.card_1_0.config(text=f"{summary['progress_percent']:.1f}%")
        self.card_1_1.config(text=f"{summary['approval_rate']:.1f}%")
        self.card_1_2.config(text=str(summary['today_progress']['reviewed']))
        self.card_1_3.config(text=summary['estimated_completion'] or "N/A")
        
        # 更新进度条
        self.progress_bar['value'] = summary['progress_percent']
        self.progress_label.config(text=f"{summary['progress_percent']:.1f}%")
        
        # 更新学生进度表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        all_student_progress = self.tracker.get_all_student_progress()
        for student_id, progress in all_student_progress.items():
            total = progress['total']
            reviewed = progress['reviewed']
            approved = progress['approved']
            rejected = progress['rejected']
            
            # 计算完成率
            completion_rate = (reviewed / total * 100) if total > 0 else 0
            
            # 获取学生信息
            student_info = progress.get('student_info', {})
            name = student_info.get('姓名', '未知')
            
            self.tree.insert("", "end", values=(
                student_id,
                name,
                total,
                reviewed,
                approved,
                rejected,
                f"{completion_rate:.1f}%"
            ))
    
    def _export_progress(self):
        """导出进度"""
        file_path = filedialog.asksaveasfilename(
            title="导出进度数据",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.tracker.export_progress(file_path)
            messagebox.showinfo("成功", f"进度数据已导出到：\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{e}")
    
    def _show_history(self):
        """显示评审历史"""
        history_window = tk.Toplevel(self.window)
        history_window.title("评审历史记录")
        history_window.geometry("700x400")
        
        # 创建 Treeview
        columns = ("时间", "学号", "奖项", "决定", "评审人")
        tree = ttk.Treeview(history_window, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("时间", width=150)
        tree.column("学号", width=100)
        tree.column("奖项", width=200)
        tree.column("决定", width=100)
        tree.column("评审人", width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(history_window, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))
        
        # 加载历史记录
        history = self.tracker.get_review_history(limit=500)
        for record in reversed(history):
            # 格式化时间
            timestamp = record.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            
            tree.insert("", "end", values=(
                timestamp,
                record.get('student_id', ''),
                record.get('award_name', ''),
                record.get('decision', ''),
                record.get('reviewer', '')
            ))


class ProgressReportGenerator:
    """进度报告生成器"""
    
    def __init__(self, progress_tracker):
        """初始化报告生成器
        
        Args:
            progress_tracker: ReviewProgressTracker 实例
        """
        self.tracker = progress_tracker
    
    def generate_text_report(self):
        """生成文本报告
        
        Returns:
            str: 文本报告内容
        """
        summary = self.tracker.get_progress_summary()
        daily_progress = self.tracker.get_daily_progress(days=7)
        
        report = []
        report.append("=" * 60)
        report.append("奖学金评审进度报告")
        report.append("=" * 60)
        report.append("")
        
        # 概览
        report.append("【概览】")
        report.append(f"总学生数：{summary['total_students']}")
        report.append(f"总奖项数：{summary['total_awards']}")
        report.append(f"已评审数：{summary['reviewed_awards']}")
        report.append(f"待评审数：{summary['remaining_awards']}")
        report.append(f"完成率：{summary['progress_percent']:.1f}%")
        report.append(f"认定率：{summary['approval_rate']:.1f}%")
        report.append("")
        
        # 今日进度
        report.append("【今日进度】")
        today = summary['today_progress']
        report.append(f"评审数：{today['reviewed']}")
        report.append(f"认定数：{today['approved']}")
        report.append(f"不予认定数：{today['rejected']}")
        report.append("")
        
        # 近期进度
        report.append("【近7日进度】")
        for date, progress in sorted(daily_progress.items()):
            report.append(f"{date}: 评审 {progress['reviewed']} 个, "
                         f"认定 {progress['approved']} 个, "
                         f"不予认定 {progress['rejected']} 个")
        report.append("")
        
        # 学生进度
        report.append("【学生进度】")
        all_progress = self.tracker.get_all_student_progress()
        for student_id, progress in all_progress.items():
            student_info = progress.get('student_info', {})
            name = student_info.get('姓名', '未知')
            total = progress['total']
            reviewed = progress['reviewed']
            completion = (reviewed / total * 100) if total > 0 else 0
            
            report.append(f"{student_id} ({name}): "
                         f"{reviewed}/{total} ({completion:.1f}%)")
        
        report.append("")
        report.append("=" * 60)
        report.append(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, file_path):
        """保存报告到文件
        
        Args:
            file_path: 文件路径
        """
        report = self.generate_text_report()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"进度报告已保存: {file_path}")


# 集成示例
class ProgressTrackerMixin:
    """进度追踪混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progress_tracker = ReviewProgressTracker()
    
    def _initialize_progress_tracker(self, students_data):
        """初始化进度追踪器"""
        self.progress_tracker.initialize(students_data)
    
    def _record_review_to_tracker(self, student_id, award_name, decision, reviewer=None):
        """记录评审结果到追踪器"""
        self.progress_tracker.record_review(student_id, award_name, decision, reviewer)
    
    def open_progress_dashboard(self):
        """打开进度仪表盘"""
        ProgressDashboard(self.root, self.progress_tracker)


# 使用示例
if __name__ == "__main__":
    # 测试进度追踪器
    tracker = ReviewProgressTracker()
    
    # 模拟学生数据
    students_data = {
        '001': {'df': None, 'student_info': {'姓名': '张三'}},
        '002': {'df': None, 'student_info': {'姓名': '李四'}},
    }
    
    # 初始化
    tracker.initialize(students_data)
    
    # 模拟评审
    tracker.record_review('001', '数学竞赛一等奖', '认定', '王老师')
    tracker.record_review('001', '英语竞赛二等奖', '不予认定', '王老师')
    tracker.record_review('002', '科研项目', '认定', '李老师')
    
    # 获取进度摘要
    summary = tracker.get_progress_summary()
    print(f"进度摘要: {summary}")
    
    # 生成报告
    report_gen = ProgressReportGenerator(tracker)
    report = report_gen.generate_text_report()
    print(report)
    
    print("测试完成！")
