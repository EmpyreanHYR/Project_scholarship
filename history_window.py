"""
历史记录查询窗口
提供数据库历史数据的查询和查看功能
完全独立的新窗口，不修改原有UI
新增：数据统计和绘图功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from datetime import datetime
import logging

# 配置日志
logger = logging.getLogger(__name__)

# 尝试导入数据库查询服务
try:
    from database.query_service import QueryService
    from database import check_database_available
    DB_QUERY_AVAILABLE = True
except ImportError:
    DB_QUERY_AVAILABLE = False
    QueryService = None
    check_database_available = lambda: False


class HistoryQueryWindow:
    """历史记录查询窗口"""
    
    def __init__(self, parent):
        """
        初始化历史查询窗口
        
        参数:
            parent: 父窗口
        """
        self.window = tk.Toplevel(parent)
        self.window.title("历史记录查询")
        self.window.geometry("1400x800")
        
        # 检查数据库是否可用
        if not DB_QUERY_AVAILABLE or not check_database_available():
            self.show_db_unavailable()
            return
        
        # 数据存储
        self.current_results = []
        self.selected_batch_id = None
        self.chart_window = None
        
        # 创建UI
        self.create_ui()
    
    def show_db_unavailable(self):
        """显示数据库不可用提示"""
        frame = ttk.Frame(self.window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="数据库功能未启用",
            font=("Arial", 16, "bold")
        ).pack(pady=20)
        
        ttk.Label(
            frame,
            text="数据库功能未启用。\n\n"
                 "请按照以下步骤启用：\n"
                 "1. 创建 db_config.json 配置文件\n"
                 "2. 设置 enabled=true\n"
                 "3. 设置 db_type=sqlite\n"
                 "4. 安装 sqlalchemy: pip install sqlalchemy\n"
                 "5. 初始化数据库",
            justify=tk.LEFT
        ).pack(pady=10)
        
        ttk.Button(
            frame,
            text="关闭",
            command=self.window.destroy
        ).pack(pady=20)
    
    def create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建顶部查询条件区域
        self.create_query_panel(main_frame)
        
        # 创建分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # 创建结果显示区域
        self.create_results_panel(main_frame)
        
        # 创建统计面板
        self.create_statistics_panel(main_frame)
    
    def create_query_panel(self, parent):
        """创建查询条件面板"""
        query_frame = ttk.LabelFrame(parent, text="查询条件", padding="10")
        query_frame.pack(fill=tk.X, pady=5)
        
        # 第一行：查询类型选择
        row1 = ttk.Frame(query_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="查询类型:").pack(side=tk.LEFT, padx=5)
        self.query_type_var = tk.StringVar(value="批次")
        query_types = ["批次", "学生", "申请", "评审记录"]
        self.query_type_combo = ttk.Combobox(
            row1,
            textvariable=self.query_type_var,
            values=query_types,
            state="readonly",
            width=15
        )
        self.query_type_combo.pack(side=tk.LEFT, padx=5)
        self.query_type_combo.bind("<<ComboboxSelected>>", self.on_query_type_changed)
        
        # 第二行：通用筛选条件
        row2 = ttk.Frame(query_frame)
        row2.pack(fill=tk.X, pady=2)
        
        ttk.Label(row2, text="批次ID:").pack(side=tk.LEFT, padx=5)
        self.batch_id_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.batch_id_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="学号:").pack(side=tk.LEFT, padx=5)
        self.student_id_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.student_id_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="姓名:").pack(side=tk.LEFT, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.name_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # 第三行：高级筛选
        row3 = ttk.Frame(query_frame)
        row3.pack(fill=tk.X, pady=2)
        
        ttk.Label(row3, text="学院/专业:").pack(side=tk.LEFT, padx=5)
        self.major_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.major_var, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row3, text="项目类型:").pack(side=tk.LEFT, padx=5)
        self.project_type_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.project_type_var, width=15).pack(side=tk.LEFT, padx=5)
        
        self.points_range_label = ttk.Label(row3, text="分数范围:")
        self.points_range_label.pack(side=tk.LEFT, padx=5)
        self.min_points_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.min_points_var, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Label(row3, text="-").pack(side=tk.LEFT)
        self.max_points_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.max_points_var, width=8).pack(side=tk.LEFT, padx=2)
        
        # 查询按钮
        ttk.Button(row3, text="查询", command=self.execute_query).pack(side=tk.LEFT, padx=10)
        ttk.Button(row3, text="重置", command=self.reset_query).pack(side=tk.LEFT, padx=5)
    
    def create_results_panel(self, parent):
        """创建结果显示面板"""
        results_frame = ttk.LabelFrame(parent, text="查询结果", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建表格
        self.create_results_table(results_frame)
        
        # 操作按钮
        btn_frame = ttk.Frame(results_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)
        
        ttk.Button(btn_frame, text="导出查询结果", command=self.export_to_excel).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="导出完整批次", command=self.export_batch).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="查看详情", command=self.view_details).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="数据统计", command=self.open_statistics_window).pack(side='left', padx=5)

        # 右下角记录数
        self.record_count_label = ttk.Label(btn_frame, text="记录数: 0")
        self.record_count_label.pack(side='right', padx=5)
    
    def create_results_table(self, parent):
        """创建结果表格"""
        # 创建滚动条
        scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL)
        
        # 创建Treeview
        self.results_tree = ttk.Treeview(
            parent,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode='extended'
        )
        
        scrollbar_y.config(command=self.results_tree.yview)
        scrollbar_x.config(command=self.results_tree.xview)
        
        # 布局
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_y.grid(row=0, column=1, sticky='ns')
        scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=0)
        parent.grid_rowconfigure(2, weight=0)
        parent.grid_columnconfigure(0, weight=1)
        
        # 初始化列（默认为批次查询）
        self.setup_batch_columns()
    
    def setup_batch_columns(self):
        """设置批次查询的列"""
        self.results_tree['columns'] = (
            'ID', '批次编号', '批次名称', '学年', '学期', 
            '状态', '评审人', '学生数', '已评数', '创建时间'
        )
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        
        for col in self.results_tree['columns']:
            self.results_tree.column(col, width=100, anchor=tk.W)
            self.results_tree.heading(col, text=col, anchor=tk.W)
    
    def setup_student_columns(self):
        """设置学生查询的列"""
        self.results_tree['columns'] = (
            'ID', '批次ID', '学号', '姓名', '班级', 
            '学院/专业', '年级', '手机', '创建时间'
        )
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        
        for col in self.results_tree['columns']:
            self.results_tree.column(col, width=100, anchor=tk.W)
            self.results_tree.heading(col, text=col, anchor=tk.W)
    
    def setup_application_columns(self):
        """设置申请查询的列"""
        self.results_tree['columns'] = (
            'ID', '学号', '姓名', '项目名称', '项目类型',
            '奖项等级', '加分', '状态', '提交时间'
        )
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        
        for col in self.results_tree['columns']:
            self.results_tree.column(col, width=100, anchor=tk.W)
            self.results_tree.heading(col, text=col, anchor=tk.W)
    
    def setup_review_columns(self):
        """设置评审记录查询的列"""
        self.results_tree['columns'] = (
            'ID', '学号', '姓名', '总分', '截断总分',
            '竞赛类', '科研创新', '外语类',
            '排名', '评审状态', '评审人', '评审时间'
        )
        self.results_tree.column('#0', width=0, stretch=tk.NO)
        
        for col in self.results_tree['columns']:
            self.results_tree.column(col, width=120, anchor=tk.W)
            self.results_tree.heading(col, text=col, anchor=tk.W)
    
    def create_button_panel(self, parent):
        """创建底部按钮面板"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame,
            text="导出到Excel",
            command=self.export_to_excel
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="查看详情",
            command=self.view_details
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="数据统计",
            command=self.open_statistics_window
        ).pack(side=tk.LEFT, padx=5)
        
        # 显示记录数量
        self.record_count_label = ttk.Label(button_frame, text="记录数: 0")
        self.record_count_label.pack(side=tk.RIGHT, padx=5)
    
    def create_statistics_panel(self, parent):
        """创建统计面板"""
        stats_frame = ttk.LabelFrame(parent, text="快速统计", padding="10")
        stats_frame.pack(fill=tk.X, pady=5)
        
        # 统计类型选择
        row1 = ttk.Frame(stats_frame)
        row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(row1, text="统计内容:").pack(side=tk.LEFT, padx=5)
        self.stats_type_var = tk.StringVar(value="批次统计")
        stats_types = ["批次统计", "学生统计", "申请统计", "评审统计"]
        self.stats_type_combo = ttk.Combobox(
            row1,
            textvariable=self.stats_type_var,
            values=stats_types,
            state="readonly",
            width=15
        )
        self.stats_type_combo.pack(side=tk.LEFT, padx=5)
        self.stats_type_combo.bind("<<ComboboxSelected>>", self.on_stats_type_changed)
        
        # 图表类型选择
        ttk.Label(row1, text="图表类型:").pack(side=tk.LEFT, padx=5)
        self.chart_type_var = tk.StringVar(value="柱状图")
        chart_types = ["柱状图", "饼图", "折线图"]
        self.chart_type_combo = ttk.Combobox(
            row1,
            textvariable=self.chart_type_var,
            values=chart_types,
            state="readonly",
            width=10
        )
        self.chart_type_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(row1, text="生成图表", command=self.generate_quick_chart).pack(side=tk.LEFT, padx=10)
        ttk.Button(row1, text="详细统计", command=self.open_statistics_window).pack(side=tk.LEFT, padx=5)
        
        # 统计结果展示区域
        self.stats_text = tk.Text(stats_frame, height=6, width=100)
        self.stats_text.pack(fill=tk.X, pady=5)
        
        # 嵌入图表的Frame
        self.chart_frame = ttk.Frame(stats_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def on_query_type_changed(self, event=None):
        """查询类型改变时的处理"""
        query_type = self.query_type_var.get()
        
        # 清空当前结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 根据类型设置列
        if query_type == "批次":
            self.setup_batch_columns()
            if hasattr(self, 'points_range_label'):
                self.points_range_label.config(text="分数范围:")
        elif query_type == "学生":
            self.setup_student_columns()
            if hasattr(self, 'points_range_label'):
                self.points_range_label.config(text="分数范围:")
        elif query_type == "申请":
            self.setup_application_columns()
            if hasattr(self, 'points_range_label'):
                self.points_range_label.config(text="分数范围:")
        elif query_type == "评审记录":
            self.setup_review_columns()
            if hasattr(self, 'points_range_label'):
                self.points_range_label.config(text="分数范围(截断后总分):")
    
    def on_stats_type_changed(self, event=None):
        """统计类型改变时的处理"""
        self.update_quick_stats()
    
    def update_quick_stats(self):
        """更新快速统计信息"""
        stats_type = self.stats_type_var.get()
        self.stats_text.delete('1.0', tk.END)
        
        try:
            if stats_type == "批次统计":
                batches = QueryService.query_batches(limit=1000)
                total = len(batches)
                reviewed = sum(1 for b in batches if b.get('reviewed_count', 0) > 0)
                pending = total - reviewed
                
                stats_info = f"""批次统计概览:
总批次数: {total}
已评审批次: {reviewed}
待评审批次: {pending}
评审完成率: {reviewed/total*100:.1f}%""" if total > 0 else "暂无批次数据"
                
            elif stats_type == "学生统计":
                students = QueryService.query_students(limit=10000)
                total = len(students)
                
                # 统计学院分布
                majors = {}
                for s in students:
                    major = s.get('major') or '未知'
                    majors[major] = majors.get(major, 0) + 1
                
                stats_info = f"""学生统计概览:
总学生数: {total}
学院/专业分布: {len(majors)} 个"""
                
            elif stats_type == "申请统计":
                apps = QueryService.query_applications(limit=10000)
                total = len(apps)
                
                # 统计项目类型分布
                types = {}
                for a in apps:
                    ptype = a.get('project_type') or '未知'
                    types[ptype] = types.get(ptype, 0) + 1
                
                # 统计状态
                statuses = {}
                for a in apps:
                    status = a.get('status') or '未知'
                    statuses[status] = statuses.get(status, 0) + 1
                
                stats_info = f"""申请统计概览:
总申请数: {total}
项目类型分布: {len(types)} 种
申请状态分布: {len(statuses)} 种"""
                
            elif stats_type == "评审统计":
                reviews = QueryService.query_reviews(limit=10000)
                total = len(reviews)
                
                # 统计平均分
                scores = [r.get('total_points', 0) for r in reviews if r.get('total_points')]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                # 统计截断总分
                capped_scores = [r.get('capped_total', 0) for r in reviews if r.get('capped_total') is not None]
                avg_capped = sum(capped_scores) / len(capped_scores) if capped_scores else 0
                
                stats_info = f"""评审统计概览:
总评审记录: {total}
平均总分: {avg_score:.2f}
平均截断总分: {avg_capped:.2f}"""
            else:
                stats_info = "请选择统计类型"
            
            self.stats_text.insert('1.0', stats_info)
            
        except Exception as e:
            logger.error(f"统计更新失败: {e}", exc_info=True)
            self.stats_text.insert('1.0', f"统计失败: {str(e)}")
    
    def execute_query(self):
        """执行查询"""
        query_type = self.query_type_var.get()
        
        # 清空当前结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.current_results = []
        
        try:
            # 获取查询条件
            batch_id = int(self.batch_id_var.get()) if self.batch_id_var.get() else None
            student_id = self.student_id_var.get() or None
            name = self.name_var.get() or None
            major = self.major_var.get() or None
            project_type = self.project_type_var.get() or None
            min_points = float(self.min_points_var.get()) if self.min_points_var.get() else None
            max_points = float(self.max_points_var.get()) if self.max_points_var.get() else None
            
            # 根据类型执行查询
            if query_type == "批次":
                results = QueryService.query_batches(limit=1000)
                self.display_batch_results(results)
            
            elif query_type == "学生":
                results = QueryService.query_students(
                    batch_id=batch_id,
                    student_id=student_id,
                    name=name,
                    major=major,
                    limit=1000
                )
                self.display_student_results(results)
            
            elif query_type == "申请":
                results = QueryService.query_applications(
                    batch_id=batch_id,
                    project_type=project_type,
                    min_points=min_points,
                    max_points=max_points,
                    limit=1000
                )
                self.display_application_results(results)
            
            elif query_type == "评审记录":
                results = QueryService.query_reviews(
                    batch_id=batch_id,
                    min_points=min_points,
                    max_points=max_points,
                    limit=1000
                )
                self.display_review_results(results)
            
            # 更新记录数
            if hasattr(self, 'record_count_label') and self.record_count_label:
                self.record_count_label.config(text=f"记录数: {len(self.current_results)}")
            
            # 更新快速统计
            self.update_quick_stats()
            
        except Exception as e:
            logger.error(f"查询失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"查询失败: {str(e)}")
    
    def display_batch_results(self, results):
        """显示批次查询结果"""
        self.current_results = results
        for batch in results:
            self.results_tree.insert('', 'end', values=(
                batch['id'],
                batch['batch_code'],
                batch['batch_name'],
                batch['academic_year'],
                batch['semester'],
                batch['status'],
                batch['reviewer_name'] or '',
                batch['total_students'],
                batch['reviewed_count'],
                batch['created_at']
            ))
    
    def display_student_results(self, results):
        """显示学生查询结果"""
        self.current_results = results
        for student in results:
            self.results_tree.insert('', 'end', values=(
                student['id'],
                student['batch_id'],
                student['student_id'],
                student['name'],
                student['class_name'] or '',
                student['major'] or '',
                student['grade'] or '',
                student['phone'] or '',
                student['created_at']
            ))
    
    def display_application_results(self, results):
        """显示申请查询结果"""
        self.current_results = results
        for app in results:
            self.results_tree.insert('', 'end', values=(
                app['id'],
                app['student_number'],
                app['student_name'],
                app['project_name'] or '',
                app['project_type'] or '',
                app['award_level'] or '',
                app['points'],
                app['status'],
                app['submitted_at']
            ))
    
    def display_review_results(self, results):
        """显示评审记录查询结果"""
        self.current_results = results
        for review in results:
            self.results_tree.insert('', 'end', values=(
                review['id'],
                review['student_number'],
                review['student_name'],
                review['total_points'],
                review.get('capped_total') if review.get('capped_total') is not None else '',
                review.get('stat_competition') if review.get('stat_competition') is not None else '',
                review.get('stat_research') if review.get('stat_research') is not None else '',
                review.get('stat_language') if review.get('stat_language') is not None else '',
                review.get('rank') or '',
                review.get('review_status'),
                review.get('reviewer_name') or '',
                review.get('review_time')
            ))
    
    def reset_query(self):
        """重置查询条件"""
        self.batch_id_var.set('')
        self.student_id_var.set('')
        self.name_var.set('')
        self.major_var.set('')
        self.project_type_var.set('')
        self.min_points_var.set('')
        self.max_points_var.set('')
    
    def export_to_excel(self):
        """导出查询结果到Excel"""
        if not self.current_results:
            messagebox.showwarning("提示", "没有可导出的数据")
            return
        
        try:
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"查询结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            # 转换为DataFrame并导出
            df = pd.DataFrame(self.current_results)
            df.to_excel(file_path, index=False)
            
            messagebox.showinfo("成功", f"数据已导出到:\n{file_path}")
            
        except Exception as e:
            logger.error(f"导出失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def view_details(self):
        """查看选中记录的详情"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一条记录")
            return
        
        # 获取选中项的值
        item = self.results_tree.item(selection[0])
        values = item['values']
        columns = list(self.results_tree['columns'])
        
        # 打开详情窗口
        DetailsWindow(self.window, values, columns, self.query_type_var.get(), self.current_results)
    
    def export_batch(self):
        """导出完整批次（多Sheet）"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个批次")
            return
        
        try:
            # 获取选中批次ID
            item = self.results_tree.item(selection[0])
            values = item['values']
            
            # 检查是否在批次查询界面
            if self.query_type_var.get() != 'batch':
                messagebox.showwarning("提示", "请在批次查询界面选择批次后再导出")
                return
            
            batch_id = values[0]  # 第一列是ID
            batch_name = values[2]  # 批次名称
            
            # 选择保存路径
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"批次导出_{batch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            # 导入ExportService
            from database import ExportService
            
            # 执行导出
            result = ExportService.export_batch_to_excel(
                batch_id=batch_id,
                file_path=file_path,
                operator_account='system',
                operator_name='管理员'
            )
            
            if result['success']:
                messagebox.showinfo("成功", result['message'] + f"\n文件路径:\n{file_path}")
            else:
                messagebox.showerror("失败", result['message'])
            
        except Exception as e:
            logger.error(f"批次导出失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"批次导出失败: {str(e)}")
    
    def generate_quick_chart(self):
        """生成快速图表"""
        try:
            # 检查matplotlib是否可用
            try:
                import matplotlib
                matplotlib.use('TkAgg')
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            except ImportError:
                messagebox.showerror("错误", 
                    "matplotlib 未安装，无法显示统计图表。\n"
                    "请运行: pip install matplotlib")
                return
            
            # 清空图表区域
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
            
            stats_type = self.stats_type_var.get()
            chart_type = self.chart_type_var.get()
            
            # 根据统计类型获取数据
            if stats_type == "批次统计":
                batches = QueryService.query_batches(limit=1000)
                if not batches:
                    messagebox.showwarning("提示", "暂无数据可绘图")
                    return
                
                # 准备数据
                labels = [b['batch_name'][:15] for b in batches[:10]]  # 限制显示10个
                values = [b['reviewed_count'] or 0 for b in batches[:10]]
                title = "批次评审进度统计"
                
            elif stats_type == "学生统计":
                students = QueryService.query_students(limit=10000)
                if not students:
                    messagebox.showwarning("提示", "暂无数据可绘图")
                    return
                
                # 统计学院分布
                majors = {}
                for s in students:
                    major = s.get('major') or '未知'
                    majors[major] = majors.get(major, 0) + 1
                
                # 取前10个
                sorted_majors = sorted(majors.items(), key=lambda x: x[1], reverse=True)[:10]
                labels = [m[0][:10] for m in sorted_majors]
                values = [m[1] for m in sorted_majors]
                title = "学生学院分布统计"
                
            elif stats_type == "申请统计":
                apps = QueryService.query_applications(limit=10000)
                if not apps:
                    messagebox.showwarning("提示", "暂无数据可绘图")
                    return
                
                # 统计项目类型分布
                types = {}
                for a in apps:
                    ptype = a.get('project_type') or '未知'
                    types[ptype] = types.get(ptype, 0) + 1
                
                sorted_types = sorted(types.items(), key=lambda x: x[1], reverse=True)[:10]
                labels = [t[0][:10] for t in sorted_types]
                values = [t[1] for t in sorted_types]
                title = "申请项目类型分布"
                
            elif stats_type == "评审统计":
                reviews = QueryService.query_reviews(limit=10000)
                if not reviews:
                    messagebox.showwarning("提示", "暂无数据可绘图")
                    return
                
                # 统计分数分布（优先使用截断总分，无则回退到总分）
                scores = []
                for r in reviews:
                    score = r.get('capped_total')
                    if score is None:
                        score = r.get('total_points')
                    if score is not None and score != '':
                        scores.append(score)
                if not scores:
                    messagebox.showwarning("提示", "暂无分数数据可绘图")
                    return
                
                # 创建分数段
                bins = [0, 2, 4, 6, 8, 10, float('inf')]
                bin_labels = ['0-2', '2-4', '4-6', '6-8', '8-10', '10+']
                bin_counts = pd.cut(scores, bins=bins, labels=bin_labels, include_lowest=True, right=False).value_counts().sort_index()
                labels = [str(label) for label in bin_counts.index]
                values = bin_counts.values.tolist()
                title = "评审分数分布"
            else:
                messagebox.showwarning("提示", "请先选择统计类型")
                return
            
            # 创建图表
            fig = Figure(figsize=(8, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # 配置中文字体
            self._configure_chinese_font(matplotlib)
            
            # 根据图表类型绘制
            if chart_type == "柱状图":
                ax.bar(labels, values, color='steelblue')
                ax.set_title(title)
                ax.set_xlabel('类别')
                ax.set_ylabel('数量')
            elif chart_type == "饼图":
                ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title(title)
            elif chart_type == "折线图":
                ax.plot(labels, values, marker='o', linewidth=2, markersize=8, color='steelblue')
                ax.set_title(title)
                ax.set_xlabel('类别')
                ax.set_ylabel('数量')
            
            # 旋转x轴标签
            ax.tick_params(axis='x', rotation=45)
            
            fig.tight_layout()
            
            # 嵌入图表
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"生成图表失败: {str(e)}")
    
    def _configure_chinese_font(self, matplotlib):
        """尽量选择系统中可用的中文字体，避免图表中文字显示为方框。"""
        import matplotlib.font_manager as font_manager
        
        # 常见中文字体名称
        font_names = [
            'SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong',
            'KaiTi', 'STHeiti', 'STKaiti', 'WenQuanYi Micro Hei',
            'Noto Sans CJK SC', 'Source Han Sans SC', 'Source Han Sans CN',
            'PingFang SC', 'Heiti SC', 'WenQuanYi Zen Hei'
        ]
        
        available_fonts = set(f.name for f in font_manager.fontManager.ttflist)
        
        for font_name in font_names:
            if font_name in available_fonts:
                matplotlib.rcParams['font.family'] = 'sans-serif'
                matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams.get('font.sans-serif', [])
                break
        
        matplotlib.rcParams['axes.unicode_minus'] = False
    
    def open_statistics_window(self):
        """打开详细统计窗口"""
        if not self.current_results:
            messagebox.showwarning("提示", "请先执行查询获取数据")
            return
        
        if self.chart_window and self.chart_window.window.winfo_exists():
            self.chart_window.window.lift()
            return

        # 使用表格当前展示的数据行，避免字典键名与中文列名不一致导致统计读取为空
        table_rows = [self.results_tree.item(item_id).get('values', []) for item_id in self.results_tree.get_children()]
        if not table_rows:
            messagebox.showwarning("提示", "当前结果表无可统计数据")
            return
        
        # 打开新的统计窗口
        self.chart_window = StatisticsChartWindow(self.window, table_rows, self.results_tree['columns'])
    
    def on_close(self):
        """窗口关闭时的处理"""
        if self.chart_window:
            try:
                self.chart_window.window.destroy()
            except Exception:
                pass
        self.window.destroy()


class StatisticsChartWindow:
    """详细统计图表窗口"""
    
    def __init__(self, parent, data, columns):
        """
        初始化统计图表窗口
        
        参数:
            parent: 父窗口
            data: 查询结果数据
            columns: 表格列名
        """
        self.window = tk.Toplevel(parent)
        self.window.title("数据统计与分析")
        self.window.geometry("1200x800")
        
        self.data = data
        self.columns = list(columns)
        self.selected_columns = []
        self.fig = None
        self.canvas = None
        self._figure_cls = None
        self._canvas_cls = None
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧选择面板
        left_frame = ttk.LabelFrame(main_frame, text="数据选择", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        
        self.create_selection_panel(left_frame)
        
        # 右侧图表区域
        right_frame = ttk.LabelFrame(main_frame, text="图表展示", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        self.create_chart_panel(right_frame)
    
    def create_selection_panel(self, parent):
        """创建选择面板"""
        # 说明文字
        ttk.Label(parent, text="选择要统计的列:").pack(anchor=tk.W, pady=5)
        
        # 列选择列表框
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.column_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            yscrollcommand=scrollbar.set,
            height=15
        )
        self.column_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.column_listbox.yview)
        
        # 添加列名
        for col in self.columns:
            self.column_listbox.insert(tk.END, col)
        
        # 按钮区域
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="全选", command=self.select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="取消", command=self.select_none).pack(side=tk.LEFT, padx=2)
        
        # 图表类型选择
        ttk.Label(parent, text="图表类型:").pack(anchor=tk.W, pady=5)
        self.chart_type_var = tk.StringVar(value="柱状图")
        chart_types = ["柱状图", "饼图", "折线图", "散点图"]
        chart_combo = ttk.Combobox(
            parent,
            textvariable=self.chart_type_var,
            values=chart_types,
            state="readonly",
            width=15
        )
        chart_combo.pack(fill=tk.X, pady=5)
        
        # 数据预览
        preview_frame = ttk.LabelFrame(parent, text="数据预览", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.preview_text = tk.Text(preview_frame, height=10, width=35)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # 生成按钮
        ttk.Button(parent, text="生成图表", command=self.generate_chart, style='Accent.TButton').pack(fill=tk.X, pady=10)
        
        # 导出按钮
        ttk.Button(parent, text="导出图表", command=self.export_chart).pack(fill=tk.X, pady=5)
    
    def create_chart_panel(self, parent):
        """创建图表面板"""
        # 图表显示区域
        self.chart_container = ttk.Frame(parent)
        self.chart_container.pack(fill=tk.BOTH, expand=True)
        
        # 提示文字
        self.hint_label = ttk.Label(
            self.chart_container,
            text="请在左侧选择数据列，然后点击'生成图表'",
            font=("Arial", 12)
        )
        self.hint_label.pack(expand=True)
    
    def select_all(self):
        """全选列"""
        self.column_listbox.select_set(0, tk.END)
    
    def select_none(self):
        """取消选择"""
        self.column_listbox.selection_clear(0, tk.END)
    
    def generate_chart(self):
        """生成图表"""
        try:
            # 获取选中的列
            selection = self.column_listbox.curselection()
            if not selection:
                messagebox.showwarning("提示", "请至少选择一列数据")
                return
            
            self.selected_columns = [self.column_listbox.get(i) for i in selection]
            
            # 检查matplotlib
            try:
                import matplotlib
                matplotlib.use('TkAgg')
                from matplotlib.figure import Figure
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            except ImportError:
                messagebox.showerror("错误", 
                    "matplotlib 未安装，无法显示统计图表。\n"
                    "请运行: pip install matplotlib")
                return

            # 保存类引用，供子函数使用，避免局部作用域导致 NameError
            self._figure_cls = Figure
            self._canvas_cls = FigureCanvasTkAgg
            
            # 清空图表区域
            for widget in self.chart_container.winfo_children():
                widget.destroy()
            
            # 准备数据
            df = pd.DataFrame(self.data)
            
            # 配置中文字体
            self._configure_chinese_font(matplotlib)
            
            # 根据选择创建图表
            chart_type = self.chart_type_var.get()
            
            if len(self.selected_columns) == 1:
                # 单列数据 - 绘制分布图
                self._plot_single_column(df, self.selected_columns[0], chart_type)
            else:
                # 多列数据 - 绘制对比图
                self._plot_multi_columns(df, self.selected_columns, chart_type)
            
            # 更新预览
            self.update_preview()
            
        except Exception as e:
            logger.error(f"生成图表失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"生成图表失败: {str(e)}")
    
    def _plot_single_column(self, df, column, chart_type):
        """绘制单列数据图表"""
        # 获取列索引
        col_idx = self.columns.index(column) if column in self.columns else None
        if col_idx is None:
            messagebox.showerror("错误", f"找不到列: {column}")
            return
        
        # 提取数值数据
        data_values = []
        data_labels = []
        
        for item in self.data:
            if isinstance(item, dict):
                value = item.get(column)
            else:
                value = item[col_idx] if col_idx < len(item) else None
            
            if value is not None and value != '':
                try:
                    num_value = float(value)
                    data_values.append(num_value)
                    data_labels.append(str(value)[:20])
                except (ValueError, TypeError):
                    # 非数值数据，统计频次
                    data_labels.append(str(value)[:20])
        
        if not data_values and not data_labels:
            messagebox.showwarning("提示", "所选列没有可用数据")
            return
        
        # 创建图表
        self.fig = self._figure_cls(figsize=(8, 6), dpi=100)
        ax = self.fig.add_subplot(111)
        
        if data_values:
            # 数值数据 - 绘制直方图或分布
            if chart_type == "柱状图":
                # 统计分布
                bins = 10
                bin_counts = pd.cut(data_values, bins=bins, include_lowest=True, right=False).value_counts().sort_index()
                labels = [f"{int(interval.left)}-{int(interval.right)}" for interval in bin_counts.index]
                counts = bin_counts.values.tolist()
                ax.bar(labels, counts, color='steelblue')
                ax.set_xlabel(column)
                ax.set_ylabel('频次')
                ax.set_title(f'{column} 分布统计')
            elif chart_type == "饼图":
                # 统计分布
                bins = 5
                bin_counts = pd.cut(data_values, bins=bins, include_lowest=True, right=False).value_counts().sort_index()
                labels = [f"{int(interval.left)}-{int(interval.right)}" for interval in bin_counts.index]
                counts = bin_counts.values.tolist()
                ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'{column} 分布统计')
            elif chart_type == "折线图":
                # 排序后绘制
                sorted_data = sorted(data_values)
                ax.plot(range(len(sorted_data)), sorted_data, marker='o', color='steelblue')
                ax.set_xlabel('序号')
                ax.set_ylabel(column)
                ax.set_title(f'{column} 趋势图')
            else:  # 散点图
                ax.scatter(range(len(data_values)), data_values, alpha=0.6, color='steelblue')
                ax.set_xlabel('序号')
                ax.set_ylabel(column)
                ax.set_title(f'{column} 散点图')
        else:
            # 非数值数据 - 统计频次
            from collections import Counter
            counter = Counter(data_labels)
            top_items = counter.most_common(15)
            labels = [item[0][:15] for item in top_items]
            counts = [item[1] for item in top_items]
            
            if chart_type == "柱状图":
                ax.bar(labels, counts, color='steelblue')
                ax.set_xlabel(column)
                ax.set_ylabel('频次')
                ax.set_title(f'{column} 频次统计')
            elif chart_type == "饼图":
                ax.pie(counts, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'{column} 频次统计')
            elif chart_type == "折线图":
                ax.plot(labels, counts, marker='o', color='steelblue')
                ax.set_xlabel(column)
                ax.set_ylabel('频次')
                ax.set_title(f'{column} 频次趋势')
            else:
                ax.scatter(labels, counts, alpha=0.6, color='steelblue')
                ax.set_xlabel(column)
                ax.set_ylabel('频次')
                ax.set_title(f'{column} 频次分布')
        
        ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()
        
        # 嵌入图表
        self.canvas = self._canvas_cls(self.fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _plot_multi_columns(self, df, columns, chart_type):
        """绘制多列数据对比图表"""
        # 创建图表
        self.fig = self._figure_cls(figsize=(10, 6), dpi=100)
        ax = self.fig.add_subplot(111)
        
        # 获取列索引
        col_indices = [self.columns.index(col) for col in columns if col in self.columns]
        
        # 提取数据
        data_dict = {col: [] for col in columns}
        for item in self.data:
            for i, col in enumerate(columns):
                if isinstance(item, dict):
                    value = item.get(col)
                else:
                    idx = self.columns.index(col) if col in self.columns else None
                    value = item[idx] if idx is not None and idx < len(item) else None
                
                if value is not None and value != '':
                    try:
                        data_dict[col].append(float(value))
                    except (ValueError, TypeError):
                        data_dict[col].append(0)
                else:
                    data_dict[col].append(0)
        
        # 绘制图表
        x = range(min(len(v) for v in data_dict.values()))
        
        colors = ['steelblue', 'darkorange', 'forestgreen', 'crimson', 'purple', 'brown']
        
        for i, col in enumerate(columns):
            values = data_dict[col][:len(x)]
            color = colors[i % len(colors)]
            
            if chart_type == "柱状图":
                # 多列柱状图
                width = 0.8 / len(columns)
                offset = (i - len(columns)/2 + 0.5) * width
                ax.bar([xi + offset for xi in x], values, width, label=col, color=color)
            elif chart_type == "折线图":
                ax.plot(x, values, marker='o', label=col, color=color, linewidth=2)
            elif chart_type == "散点图":
                ax.scatter(x, values, alpha=0.6, label=col, color=color)
            else:  # 饼图不支持多列
                ax.plot(x, values, marker='o', label=col, color=color, linewidth=2)
        
        if chart_type == "饼图":
            # 饼图只支持单列
            messagebox.showwarning("提示", "饼图仅支持单列数据，将显示第一列")
            return
        
        ax.set_xlabel('序号')
        ax.set_ylabel('数值')
        ax.set_title(f'多列数据对比: {", ".join(columns)}')
        ax.legend(loc='best')
        ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()
        
        # 嵌入图表
        self.canvas = self._canvas_cls(self.fig, master=self.chart_container)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _configure_chinese_font(self, matplotlib):
        """配置中文字体"""
        import matplotlib.font_manager as font_manager
        
        font_names = [
            'SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong',
            'KaiTi', 'STHeiti', 'STKaiti', 'WenQuanYi Micro Hei',
            'Noto Sans CJK SC', 'Source Han Sans SC', 'PingFang SC'
        ]
        
        available_fonts = set(f.name for f in font_manager.fontManager.ttflist)
        
        for font_name in font_names:
            if font_name in available_fonts:
                matplotlib.rcParams['font.family'] = 'sans-serif'
                matplotlib.rcParams['font.sans-serif'] = [font_name] + matplotlib.rcParams.get('font.sans-serif', [])
                break
        
        matplotlib.rcParams['axes.unicode_minus'] = False
    
    def update_preview(self):
        """更新数据预览"""
        self.preview_text.delete('1.0', tk.END)
        
        if not self.selected_columns:
            self.preview_text.insert('1.0', "请选择要统计的列")
            return
        
        preview = f"已选择 {len(self.selected_columns)} 列:\n"
        preview += "-" * 30 + "\n"
        
        for col in self.selected_columns:
            preview += f"• {col}\n"
        
        preview += "-" * 30 + "\n"
        preview += f"共 {len(self.data)} 条记录\n"
        
        # 添加数据样例
        preview += "\n数据样例（前3条）:\n"
        for i, item in enumerate(self.data[:3]):
            if isinstance(item, dict):
                row_data = [str(item.get(col, ''))[:15] for col in self.selected_columns]
            else:
                indices = [self.columns.index(col) for col in self.selected_columns if col in self.columns]
                row_data = [str(item[idx])[:15] if idx < len(item) else '' for idx in indices]
            preview += f"{i+1}. " + " | ".join(row_data) + "\n"
        
        self.preview_text.insert('1.0', preview)
    
    def export_chart(self):
        """导出图表"""
        if not self.fig:
            messagebox.showwarning("提示", "请先生成图表")
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[
                    ("PNG图片", "*.png"),
                    ("PDF文档", "*.pdf"),
                    ("SVG矢量图", "*.svg")
                ],
                initialfile=f"统计图表_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            if not file_path:
                return
            
            self.fig.savefig(file_path, dpi=150, bbox_inches='tight')
            messagebox.showinfo("成功", f"图表已保存到:\n{file_path}")
            
        except Exception as e:
            logger.error(f"导出图表失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"导出图表失败: {str(e)}")


class DetailsWindow:
    """详情查看窗口"""
    
    def __init__(self, parent, values, columns, query_type, all_data):
        """
        初始化详情窗口
        
        参数:
            parent: 父窗口
            values: 选中行的数据
            columns: 列名列表
            query_type: 查询类型
            all_data: 所有数据（用于关联查询）
        """
        self.window = tk.Toplevel(parent)
        self.window.title(f"{query_type}详情")
        self.window.geometry("900x600")
        
        self.values = values
        self.columns = columns
        self.query_type = query_type
        self.all_data = all_data
        
        # 创建UI
        self.create_ui()
    
    def create_ui(self):
        """创建用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 基本信息区域
        info_frame = ttk.LabelFrame(main_frame, text="基本信息", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.create_info_section(info_frame)
        
        # 详细信息区域
        detail_frame = ttk.LabelFrame(main_frame, text="详细信息", padding="10")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.create_detail_section(detail_frame)
        
        # 关联信息区域
        self.create_related_section(main_frame)
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="导出此记录", command=self.export_single_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def create_info_section(self, parent):
        """创建基本信息区域"""
        # 创建两列布局
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=2)
        
        # 标题信息
        title_row = ttk.Frame(parent)
        title_row.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 根据查询类型显示标题
        if self.query_type == "批次":
            title_text = self.values[2] if len(self.values) > 2 else "未知批次"  # 批次名称
            ttk.Label(title_row, text=f"📋 {title_text}", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        elif self.query_type == "学生":
            title_text = f"{self.values[3]} ({self.values[2]})" if len(self.values) > 3 else "未知学生"  # 姓名(学号)
            ttk.Label(title_row, text=f"👤 {title_text}", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        elif self.query_type == "申请":
            title_text = self.values[3] if len(self.values) > 3 else "未知申请"  # 项目名称
            ttk.Label(title_row, text=f"📄 {title_text}", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        elif self.query_type == "评审记录":
            title_text = f"{self.values[2]} - {self.values[3]}" if len(self.values) > 3 else "未知记录"  # 姓名-总分
            ttk.Label(title_row, text=f"📊 {title_text}", font=("Arial", 14, "bold")).pack(anchor=tk.W)
        
        # 基本字段信息
        row = 1
        for col, val in zip(self.columns, self.values):
            # 跳过ID列的详细信息显示
            if col == 'ID' or col == '批次ID':
                continue
            
            ttk.Label(parent, text=f"{col}:", font=("Arial", 10, "bold")).grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=3
            )
            
            # 根据值的内容设置样式
            value_label = ttk.Label(parent, text=str(val) if val else "-", foreground="blue")
            value_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=3)
            
            # 状态特殊处理
            if col == '状态' and val:
                if '已' in str(val) or '通过' in str(val):
                    value_label.config(foreground="green")
                elif '未' in str(val) or '待' in str(val):
                    value_label.config(foreground="orange")
                elif '驳回' in str(val) or '失败' in str(val):
                    value_label.config(foreground="red")
            
            row += 1
    
    def create_detail_section(self, parent):
        """创建详细信息表格"""
        # 创建树形表格
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        
        tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            columns=('字段', '值'),
            show='headings',
            height=10
        )
        
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        
        # 设置列
        tree.heading('字段', text='字段名称')
        tree.heading('值', text='字段值')
        tree.column('字段', width=150, anchor=tk.W)
        tree.column('值', width=500, anchor=tk.W)
        
        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 填充数据
        for col, val in zip(self.columns, self.values):
            display_val = str(val) if val else "(空)"
            tree.insert('', 'end', values=(col, display_val))
    
    def create_related_section(self, parent):
        """创建关联信息区域"""
        # 根据查询类型显示不同的关联信息
        if self.query_type == "批次" and len(self.values) > 0:
            # 批次详情 - 显示该批次下的学生和申请
            batch_id = self.values[0]
            related_frame = ttk.LabelFrame(parent, text="批次关联信息", padding="10")
            related_frame.pack(fill=tk.X, pady=5)
            
            # 查询该批次的学生
            try:
                students = QueryService.query_students(batch_id=batch_id, limit=100)
                if students:
                    ttk.Label(related_frame, text=f"该批次共有 {len(students)} 名学生", 
                             font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
                    
                    # 显示部分学生
                    student_text = "学生列表: " + ", ".join([s.get('name', '') for s in students[:5]])
                    if len(students) > 5:
                        student_text += f" ... 等{len(students)}人"
                    
                    ttk.Label(related_frame, text=student_text, foreground="gray").pack(anchor=tk.W)
            except Exception as e:
                logger.debug(f"加载关联信息失败: {e}")
                ttk.Label(related_frame, text="无法加载关联信息").pack(anchor=tk.W)
        
        elif self.query_type == "学生" and len(self.values) > 0:
            # 学生详情 - 显示该学生的申请
            student_id = self.values[0]  # 学生ID
            batch_id = self.values[1] if len(self.values) > 1 else None
            
            related_frame = ttk.LabelFrame(parent, text="学生关联信息", padding="10")
            related_frame.pack(fill=tk.X, pady=5)
            
            try:
                apps = QueryService.query_applications(batch_id=batch_id, limit=100)
                student_apps = [a for a in apps if a.get('student_number') == self.values[2]]  # 学号
                
                if student_apps:
                    ttk.Label(related_frame, text=f"该学生共有 {len(student_apps)} 条申请记录", 
                             font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
                    
                    # 统计加分
                    total_points = sum([a.get('points', 0) for a in student_apps])
                    ttk.Label(related_frame, text=f"总加分: {total_points}", 
                             foreground="blue").pack(anchor=tk.W)
                else:
                    ttk.Label(related_frame, text="暂无申请记录").pack(anchor=tk.W)
            except Exception as e:
                logger.debug(f"加载关联信息失败: {e}")
                ttk.Label(related_frame, text="无法加载关联信息").pack(anchor=tk.W)
        
        elif self.query_type == "申请" and len(self.values) > 0:
            # 申请详情 - 显示关联的学生和评审信息
            related_frame = ttk.LabelFrame(parent, text="申请关联信息", padding="10")
            related_frame.pack(fill=tk.X, pady=5)
            
            student_name = self.values[2] if len(self.values) > 2 else None  # 学生姓名
            
            if student_name:
                try:
                    reviews = QueryService.query_reviews(limit=100)
                    student_reviews = [r for r in reviews if r.get('student_name') == student_name]
                    
                    if student_reviews:
                        ttk.Label(related_frame, text=f"该学生共有 {len(student_reviews)} 条评审记录", 
                                 font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
                        
                        # 显示最新评审
                        latest = student_reviews[-1]
                        ttk.Label(related_frame, 
                                 text=f"最新评审总分: {latest.get('total_points', 'N/A')}, "
                                      f"截断总分: {latest.get('capped_total', 'N/A')}",
                                 foreground="blue").pack(anchor=tk.W)
                    else:
                        ttk.Label(related_frame, text="暂无评审记录").pack(anchor=tk.W)
                except Exception as e:
                    logger.debug(f"加载关联信息失败: {e}")
                    ttk.Label(related_frame, text="无法加载关联信息").pack(anchor=tk.W)
        
        elif self.query_type == "评审记录" and len(self.values) > 0:
            # 评审详情 - 显示分数构成
            related_frame = ttk.LabelFrame(parent, text="分数构成分析", padding="10")
            related_frame.pack(fill=tk.X, pady=5)
            
            # 提取各类分数
            total = self.values[3] if len(self.values) > 3 else 0  # 总分
            capped = self.values[4] if len(self.values) > 4 else 0  # 截断总分
            competition = self.values[5] if len(self.values) > 5 else 0  # 竞赛类
            research = self.values[6] if len(self.values) > 6 else 0  # 科研创新
            language = self.values[7] if len(self.values) > 7 else 0  # 外语类
            
            # 计算各类占比
            if total and float(total) > 0:
                ttk.Label(related_frame, text="分数构成:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
                
                try:
                    total_val = float(total)
                    comp_pct = float(competition or 0) / total_val * 100 if competition else 0
                    res_pct = float(research or 0) / total_val * 100 if research else 0
                    lang_pct = float(language or 0) / total_val * 100 if language else 0
                    
                    info_text = f"  • 竞赛类: {competition} ({comp_pct:.1f}%)\n"
                    info_text += f"  • 科研创新: {research} ({res_pct:.1f}%)\n"
                    info_text += f"  • 外语类: {language} ({lang_pct:.1f}%)"
                    
                    ttk.Label(related_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
                except Exception as e:
                    logger.debug(f"加载分数构成失败: {e}")
    
    def export_single_record(self):
        """导出单条记录"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"{self.query_type}_详情_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            # 创建DataFrame
            data = {'字段': self.columns, '值': self.values}
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False)
            
            messagebox.showinfo("成功", f"记录已导出到:\n{file_path}")
            
        except Exception as e:
            logger.error(f"导出失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"导出失败: {str(e)}")
