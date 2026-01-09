"""
历史记录查询窗口
提供数据库历史数据的查询和查看功能
完全独立的新窗口，不修改原有UI
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
        self.window.geometry("1200x700")
        
        # 检查数据库是否可用
        if not DB_QUERY_AVAILABLE or not check_database_available():
            self.show_db_unavailable()
            return
        
        # 数据存储
        self.current_results = []
        self.selected_batch_id = None
        
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
            text="历史记录查询功能需要启用数据库。\n\n"
                 "请按照以下步骤启用：\n"
                 "1. 创建 database_config.json 配置文件\n"
                 "2. 设置 enabled=true\n"
                 "3. 配置数据库连接信息\n"
                 "4. 安装数据库驱动（psycopg2或pymysql）",
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
        
        # 创建底部按钮区域
        self.create_button_panel(main_frame)
    
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
        
        ttk.Label(row3, text="分数范围:").pack(side=tk.LEFT, padx=5)
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
        btn_frame.pack(pady=5, fill='x')
        
        ttk.Button(btn_frame, text="导出查询结果", command=self.export_to_excel).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="导出完整批次", command=self.export_batch).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="查看详情", command=self.view_details).pack(side='left', padx=5)
    
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
            'ID', '学号', '姓名', '总分', '排名',
            '评审状态', '评审人', '评审时间'
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
        
        # 显示记录数量
        self.record_count_label = ttk.Label(button_frame, text="记录数: 0")
        self.record_count_label.pack(side=tk.RIGHT, padx=5)
    
    def on_query_type_changed(self, event=None):
        """查询类型改变时的处理"""
        query_type = self.query_type_var.get()
        
        # 清空当前结果
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 根据类型设置列
        if query_type == "批次":
            self.setup_batch_columns()
        elif query_type == "学生":
            self.setup_student_columns()
        elif query_type == "申请":
            self.setup_application_columns()
        elif query_type == "评审记录":
            self.setup_review_columns()
    
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
            self.record_count_label.config(text=f"记录数: {len(self.current_results)}")
            
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
                review['rank'] or '',
                review['review_status'],
                review['reviewer_name'] or '',
                review['review_time']
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
        
        # 简单显示详情
        details = "\\n".join([f"{col}: {val}" for col, val in zip(self.results_tree['columns'], values)])
        messagebox.showinfo("详情", details)
    
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
                messagebox.showinfo("成功", result['message'] + f"\\n文件路径:\\n{file_path}")
            else:
                messagebox.showerror("失败", result['message'])
            
        except Exception as e:
            logger.error(f"批次导出失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"批次导出失败: {str(e)}")

