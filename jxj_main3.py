# 导入库
import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import re
import openpyxl
import json
from tkinter import Toplevel
import pkg_resources  # 用于打包时访问资源
import sys
import shutil
from PIL import Image, ImageTk
import time


class LoginManager:
    def __init__(self, root, scholarship_reviewer):
        self.root = root
        self.scholarship_reviewer = scholarship_reviewer
        self.user_data_file = "users.json"
        self.users = self.load_user_data()
        self.failed_attempts = {}  # 记录登录失败次数

    def load_user_data(self):
        if not os.path.exists(self.user_data_file):
            with open(self.user_data_file, "w") as f:
                json.dump({}, f)
        with open(self.user_data_file, "r") as f:
            users = json.load(f)

        # 修正旧的用户数据格式（如果值是字符串，将其转换为嵌套字典）
        for username, data in users.items():
            if isinstance(data, str):  # 如果是旧格式，值是字符串（密码）
                users[username] = {"password": data, "locked": False}

        # 保存修正后的数据（如果有修正）
        with open(self.user_data_file, "w") as f:
            json.dump(users, f)

        return users

    def save_user_data(self):
        with open(self.user_data_file, "w") as f:
            json.dump(self.users, f)

    def register(self):
        """显示注册窗口"""
        register_window = Toplevel(self.root)
        register_window.title("注册")

        tk.Label(register_window, text="用户名:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(register_window, text="密码:").grid(row=1, column=0, padx=5, pady=5)

        username_var = tk.StringVar()
        password_var = tk.StringVar()

        username_entry = tk.Entry(register_window, textvariable=username_var)
        password_entry = tk.Entry(register_window, textvariable=password_var, show="*")
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        def attempt_register():
            username = username_var.get()
            password = password_var.get()
            if not username or not password:
                messagebox.showerror("错误", "用户名和密码不能为空！")
                return
            if username in self.users:
                messagebox.showerror("错误", "用户名已存在")
            else:
                # 确保每个用户数据是嵌套字典结构
                self.users[username] = {"password": password, "locked": False}
                self.save_user_data()
                messagebox.showinfo("成功", "注册成功！")
                register_window.destroy()

        tk.Button(register_window, text="注册", command=attempt_register).grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        """显示登录窗口"""
        login_window = Toplevel(self.root)
        login_window.title("登录")

        tk.Label(login_window, text="用户名:").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(login_window, text="密码:").grid(row=1, column=0, padx=5, pady=5)

        username_var = tk.StringVar()
        password_var = tk.StringVar()

        username_entry = tk.Entry(login_window, textvariable=username_var)
        password_entry = tk.Entry(login_window, textvariable=password_var, show="*")
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        def attempt_login():
            username = username_var.get()
            password = password_var.get()

            if not username or not password:
                messagebox.showerror("错误", "用户名和密码不能为空！")
                return

            if username not in self.users:
                messagebox.showerror("错误", "用户名不存在！")
                return

            user_data = self.users[username]  # 获取用户的数据（字典形式）

            # 如果账户被锁定，且输入的是管理员密码，解锁该账户
            if user_data.get("locked"):
                if password == "deblocking":
                    user_data["locked"] = False
                    self.save_user_data()
                    messagebox.showinfo("成功", f"账户 {username} 已解锁！")
                    login_window.destroy()
                    return
                else:
                    messagebox.showerror("错误", "账户已锁定，且密码错误！")
                    return

            if user_data["password"] == password:
                messagebox.showinfo("成功", f"欢迎，{username}！")
                self.scholarship_reviewer.enable_import_excel()  # 启用导入Excel功能
                self.failed_attempts[username] = 0  # 重置失败次数
                login_window.destroy()
            else:
                self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
                if self.failed_attempts[username] >= 3:
                    user_data["locked"] = True
                    self.save_user_data()
                    messagebox.showerror("错误", "登录失败3次，账户已锁定！")
                else:
                    remaining_attempts = 3 - self.failed_attempts[username]
                    messagebox.showerror("错误", f"密码错误！还有{remaining_attempts}次机会。")

        tk.Button(login_window, text="登录", command=attempt_login).grid(row=2, column=0, columnspan=2, pady=10)

class AboutHelp:
    @staticmethod
    def show_about(root):
        """显示关于窗口"""
        about_window = Toplevel(root)
        about_window.title("关于")
        tk.Label(about_window, text="优秀学生奖学金加分项目评审软件 V3.0", font=("Arial", 14)).pack(pady=10)
        tk.Label(about_window, text="版权所有: 黄耀荣，马荣斌，陈彩蝶，高新雅，王俞欢，张舒一").pack(pady=5)
        # 绑定关闭事件，确保资源释放
        about_window.protocol("WM_DELETE_WINDOW", about_window.destroy)

    @staticmethod
    def show_help(root):
        """显示帮助窗口"""
        help_window = Toplevel(root)
        help_window.title("帮助")
        help_text = """使用说明：
1. 点击“选择文件”按钮加载学生信息。
2. 在奖项表中逐项进行评审。
3. 确认后点击导出按钮生成结果文件。
"""
        tk.Label(help_window, text=help_text, justify=tk.LEFT, padx=10, pady=10).pack()
        # 绑定关闭事件，确保资源释放
        help_window.protocol("WM_DELETE_WINDOW", help_window.destroy)

class ScholarshipReviewer:

    def __init__(self, root):
        self.root = root

        # 获取屏幕的宽度和高度
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 设置窗口大小为屏幕大小
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.is_logged_in = False  # 记录用户登录状态

        # 创建注册、登录、关于、帮助功能
        self.login_manager = LoginManager(root, self)
        # 创建按钮菜单，放置在顶部
        self.create_top_buttons()

        self.default_bg = self.root.cget('bg')  # 保存默认背景色

        # 在加载新数据时初始化 exported 属性
        self.exported = True  # 数据未导入，可直接关闭窗口

        self.root.title("优秀学生奖学金加分项目评审软件 V3.0")

        # 当前选中的Excel数据
        self.df = None
        self.current_file = ""
        
        # 批量导入相关的数据结构
        self.students_data = {}  # 存储所有学生的数据：{学生标识: {'df': DataFrame, 'file_path': str}}
        self.current_student_id = None  # 当前选中的学生标识
        
        # 加分规则管理：保存默认和自定义的加分规则
        self.init_default_scoring_rules()
        self.custom_scoring_rules = None  # 自定义加分规则，为None时使用默认规则

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ========== 新布局：主Frame横向分为左右 ==========
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧Frame（纵向分为上：奖项信息展示区，下：支撑材料展示区）
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右侧Frame（评审界面）
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.Y)

        # 学生选择下拉菜单
        self.student_select_frame = ttk.LabelFrame(left_frame, text="学生选择")
        self.student_select_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        self.student_var = tk.StringVar()
        self.student_dropdown = ttk.Combobox(self.student_select_frame, textvariable=self.student_var, width=40, state='readonly')
        self.student_dropdown.pack(side=tk.LEFT, padx=5, pady=5)
        self.student_dropdown.bind("<<ComboboxSelected>>", self.on_student_select)
        
        # 学生信息展示区
        self.student_info_frame = ttk.LabelFrame(left_frame, text="学生信息")
        self.student_info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.info_labels = {
            "学院": tk.Label(self.student_info_frame, text="学院: "),
            "姓名": tk.Label(self.student_info_frame, text="姓名: "),
            "年级": tk.Label(self.student_info_frame, text="年级: "),
            "班级": tk.Label(self.student_info_frame, text="班级: "),
            "学号": tk.Label(self.student_info_frame, text="学号: "),
        }
        for label in self.info_labels.values():
            label.pack(side=tk.LEFT, padx=5)

        # ========== 奖项信息展示区（表格） ==========  高度减少 ==========
        table_frame = tk.Frame(left_frame)
        table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=10, pady=5)
        self.tree = ttk.Treeview(table_frame, columns=(
            "Award", "Time", "Level", "Project", "Evaluated Level", "Recognition", "Points", "Remarks"),
                                 show="headings", height=10)  # 设置height减少高度
        # 设置每一列的表头和宽度
        self.tree.heading("Award", text="所获奖项名称")
        self.tree.column("Award", width=400)
        self.tree.heading("Time", text="获奖时间")
        self.tree.column("Time", width=150)
        self.tree.heading("Level", text="奖项等级")
        self.tree.column("Level", width=150)
        self.tree.heading("Project", text="项目类型")
        self.tree.column("Project", width=150)
        self.tree.heading("Evaluated Level", text="评定等级")
        self.tree.column("Evaluated Level", width=150)
        self.tree.heading("Recognition", text="认定情况")
        self.tree.column("Recognition", width=150)
        self.tree.heading("Points", text="加分")
        self.tree.column("Points", width=50)
        self.tree.heading("Remarks", text="备注")
        self.tree.column("Remarks", width=250)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # ========== 支撑材料展示区（在表格下方） ========== 位置调整 ==========
        self.material_frame = tk.Frame(left_frame)
        self.material_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.material_label = tk.Label(self.material_frame, text="支撑材料预览区", anchor="center")
        self.material_label.pack(side=tk.TOP, fill=tk.X)
        self.material_canvas = tk.Canvas(self.material_frame, bg="white", height=300)
        self.material_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.material_img = None
        self.material_pdf_btn = None

        # ========== 评审界面放在右侧 ==========
        self.review_frame = ttk.LabelFrame(right_frame, text="评审内容")
        self.review_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=15)

        # 评审内容的各类变量定义
        self.project_type_var = tk.StringVar()
        self.level_var = tk.StringVar()
        self.recognition_var = tk.StringVar()
        self.remarks_var = tk.StringVar()

        def adjust_combobox_width(combobox, max_width=60):
            def on_postcommand(event):
                width = max(max_width, combobox.winfo_reqwidth())
                combobox.config(width=width)

            combobox.bind('<Configure>', on_postcommand)

        # 导入加分详情和重置按钮
        self.import_frame = tk.Frame(self.review_frame)
        self.import_frame.pack(side=tk.TOP, padx=5, pady=5)
        
        self.import_scoring_btn = ttk.Button(self.import_frame, text="导入加分详情", command=self.import_scoring_details)
        self.import_scoring_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_scoring_btn = ttk.Button(self.import_frame, text="重置为默认", command=self.reset_scoring_details)
        self.reset_scoring_btn.pack(side=tk.LEFT, padx=5)

        # 项目类型下拉菜单
        self.project_type_label = tk.Label(self.review_frame, text="项目类型: ")
        self.project_type_label.pack(side=tk.TOP, padx=5)
        self.project_type_dropdown = ttk.Combobox(self.review_frame, textvariable=self.project_type_var, width=40)
        # 初始化时使用默认的项目类型
        self.project_type_dropdown['values'] = self.default_project_types
        self.project_type_dropdown.pack(side=tk.TOP, padx=5)
        adjust_combobox_width(self.project_type_dropdown)

        # 奖项级别下拉菜单
        self.level_label = tk.Label(self.review_frame, text="奖项级别: ")
        self.level_label.pack(side=tk.TOP, padx=5)
        self.level_dropdown = ttk.Combobox(self.review_frame, textvariable=self.level_var, width=40)
        self.level_dropdown.pack(side=tk.TOP, padx=5)
        adjust_combobox_width(self.level_dropdown)

        # 认定情况下拉菜单
        self.recognition_label = tk.Label(self.review_frame, text="认定情况: ")
        self.recognition_label.pack(side=tk.TOP, padx=5)
        self.recognition_dropdown = ttk.Combobox(self.review_frame, textvariable=self.recognition_var, width=40)
        self.recognition_dropdown['values'] = ["认定", "不予认定"]
        self.recognition_dropdown.pack(side=tk.TOP, padx=5)
        self.recognition_dropdown.bind("<<ComboboxSelected>>", self.on_recognition_select)
        adjust_combobox_width(self.recognition_dropdown)

        # 备注下拉菜单，默认禁用，只有在选择“不予认定”时启用
        self.remarks_label = tk.Label(self.review_frame, text="备注: ")
        self.remarks_label.pack(side=tk.TOP, padx=5)
        self.remarks_dropdown = ttk.Combobox(self.review_frame, textvariable=self.remarks_var, state='disabled',
                                             width=40)
        self.remarks_dropdown['values'] = [
            "时间不符",
            "名次不符",
            "该材料不符合本次奖项加分材料认定范围",
            "支撑材料不足，补交后可认定",
            "同一赛事奖项已认定最高分，不予重复加分",
            "线上比赛不符合认定要求",
            "其他（需补充文本内容）"
        ]
        self.remarks_dropdown.pack(side=tk.TOP, padx=5)
        adjust_combobox_width(self.remarks_dropdown)

        # 加分显示标签，初始值为0
        self.points_label = tk.Label(self.review_frame, text="加分: 0")
        self.points_label.pack(side=tk.TOP, padx=5)

        # 确定按钮，点击后将评审内容写入表格的相应行
        self.confirm_btn = ttk.Button(self.review_frame, text="确定", command=self.confirm_review)
        self.confirm_btn.pack(side=tk.TOP, padx=5, pady=10)

        # Excel 导出按钮，点击后保存评审结果到新的 Excel 文件
        self.export_btn = ttk.Button(self.review_frame, text="评审结果导出Excel", command=self.export_excel)
        self.export_btn.pack(side=tk.TOP, padx=5, pady=10)

        # 统计结果导出按钮，点击后统计评审结果到新的 Excel 文件
        self.stats_export_btn = ttk.Button(self.review_frame, text="统计结果导出Excel", command=self.stats_export_excel)
        self.stats_export_btn.pack(side=tk.TOP, padx=5, pady=10)

        # 批量导出按钮
        self.batch_export_btn = ttk.Button(self.review_frame, text="批量评审结果导出", command=self.batch_export_excel)
        self.batch_export_btn.pack(side=tk.TOP, padx=5, pady=10)

        # 批量统计导出按钮
        self.batch_stats_export_btn = ttk.Button(self.review_frame, text="批量统计结果导出", command=self.batch_stats_export_excel)
        self.batch_stats_export_btn.pack(side=tk.TOP, padx=5, pady=10)

        # 当选择项目类型时，动态更新奖项级别的选项
        self.project_type_dropdown.bind("<<ComboboxSelected>>", self.update_award_levels)

    def create_top_buttons(self):
        """创建功能按钮"""
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        register_btn = ttk.Button(top_frame, text="注册", command=self.login_manager.register)
        register_btn.pack(side=tk.LEFT, padx=5, pady=5)
        login_btn = ttk.Button(top_frame, text="登录", command=self.login_manager.login)
        login_btn.pack(side=tk.LEFT, padx=5, pady=5)
        about_btn = ttk.Button(top_frame, text="关于", command=lambda: AboutHelp.show_about(self.root))
        about_btn.pack(side=tk.LEFT, padx=5, pady=5)
        help_btn = ttk.Button(top_frame, text="帮助", command=lambda: AboutHelp.show_help(self.root))
        help_btn.pack(side=tk.LEFT, padx=5, pady=5)
        download_template_btn = ttk.Button(top_frame, text="模板", command=self.download_template)
        download_template_btn.pack(side=tk.LEFT, padx=5, pady=30)
        light_btn = ttk.Button(top_frame, text="浅色模式", command=lambda: self.apply_theme("light"))
        light_btn.pack(side=tk.LEFT, padx=5, pady=5)
        dark_btn = ttk.Button(top_frame, text="深色模式", command=lambda: self.apply_theme("dark"))
        dark_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # ========== 导入Excel文件按钮 ==========
        self.file_btn = ttk.Button(top_frame, text="请选择Excel文件", command=self.load_file)
        self.file_btn.pack(side=tk.LEFT, padx=5, pady=10)
        self.file_btn.config(state=tk.DISABLED)  # 默认禁用，登录后启用

        # ========== 批量导入Excel文件按钮 ==========
        self.batch_file_btn = ttk.Button(top_frame, text="批量导入Excel文件", command=self.batch_load_files)
        self.batch_file_btn.pack(side=tk.LEFT, padx=5, pady=10)
        self.batch_file_btn.config(state=tk.DISABLED)  # 默认禁用，登录后启用

        # ========== 补充导入Excel文件按钮 ==========
        self.supplement_file_btn = ttk.Button(top_frame, text="补充导入Excel文件", command=self.supplement_import_files)
        self.supplement_file_btn.pack(side=tk.LEFT, padx=5, pady=10)
        self.supplement_file_btn.config(state=tk.DISABLED)  # 默认禁用，登录后启用

        # ========== 新增：打开PDF支撑材料按钮 ==========
        self.open_pdf_btn = ttk.Button(top_frame, text="打开PDF支撑材料", command=self.open_selected_pdf)
        self.open_pdf_btn.pack(side=tk.LEFT, padx=5, pady=10)
        self.open_pdf_btn.config(state=tk.NORMAL)

        # ========== 新增：打开Excel文件所在目录按钮 ==========
        self.open_excel_dir_btn = ttk.Button(top_frame, text="打开Excel文件位置", command=self.open_excel_dir)
        self.open_excel_dir_btn.pack(side=tk.LEFT, padx=5, pady=10)
        self.open_excel_dir_btn.config(state=tk.NORMAL)

    def open_selected_pdf(self):
        """在顶部按钮栏打开当前选中行的PDF支撑材料"""
        if not self.current_file:
            messagebox.showerror("错误", "请先导入Excel文件！")
            return
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("错误", "请先在表格中选择一行奖项！")
            return
        award_name = self.tree.item(selected_item)['values'][0]
        base_dir = os.path.dirname(self.current_file)
        safe_award_name = ''.join([c for c in str(award_name) if '\u4e00' <= c <= '\u9fff' or c.isalnum()])
        pdf_path = os.path.join(base_dir, safe_award_name + ".pdf")
        if os.path.exists(pdf_path):
            import webbrowser
            webbrowser.open(pdf_path)
        else:
            messagebox.showerror("错误", "未找到对应的PDF文件！")

    def open_excel_dir(self):
        """打开导入的Excel文件所在目录"""
        if not self.current_file:
            messagebox.showerror("错误", "请先导入Excel文件！")
            return
        import subprocess
        folder = os.path.dirname(os.path.abspath(self.current_file))
        try:
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录: {e}")

    def download_template(self, template_name="template" + ".xlsx"):
        """下载模板文件"""
        # 定义模板文件名
        template_filename = "template.xlsx"

        # 打包时使用 pkg_resources 访问模板文件
        if getattr(sys, 'frozen', False):  # 判断是否为打包后的exe文件
            template_path = pkg_resources.resource_filename(__name__, template_filename)
        else:
            # 在开发环境中直接使用本地路径
            template_path = os.path.join(os.path.dirname(__file__), template_filename)

        # 检查模板文件是否存在
        if not os.path.exists(template_path):
            messagebox.showerror("错误", "模板文件不存在！")
            return

        # 文件保存对话框，用户选择保存位置
        save_path = filedialog.asksaveasfilename(initialfile=template_name, defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])

        if save_path:
            try:
                # 复制模板文件到用户选择的路径
                shutil.copy(template_path, save_path)
                messagebox.showinfo("成功", f"模板文件已保存到: {save_path}")
            except Exception as e:
                messagebox.showerror("错误", f"文件保存失败: {str(e)}")

    def apply_theme(self, theme):
        """应用主题"""
        if theme == "dark":
            self.root.tk_setPalette(background="black" , foreground="white")
        else:
            self.root.tk_setPalette(background=self.default_bg, foreground="black")

    def enable_import_excel(self):
        """启用导入Excel功能"""
        self.is_logged_in = True
        self.file_btn.config(state=tk.NORMAL)
        self.batch_file_btn.config(state=tk.NORMAL)
        self.supplement_file_btn.config(state=tk.NORMAL)

    def validate_review_completion(self):
        """校验所有奖项是否审核完毕及备注填写完整，返回(未审核列表, 未备注列表)"""
        unreviewed_awards = []
        incomplete_remarks = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            recognition = values[5] if len(values) > 5 else None
            remarks = values[7] if len(values) > 7 else None
            if not recognition:
                unreviewed_awards.append(values[0])
            if remarks == "请填写备注":
                incomplete_remarks.append(values[0])
        return unreviewed_awards, incomplete_remarks

    def load_file(self):
        """打开文件选择对话框，并读取Excel文件"""
        if not self.is_logged_in:
            messagebox.showerror("错误", "请先登录！")
            return

        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            self.load_excel_data(file_path)

    def batch_load_files(self):
        """批量导入多个Excel文件"""
        if not self.is_logged_in:
            messagebox.showerror("错误", "请先登录！")
            return

        file_paths = filedialog.askopenfilenames(
            title="选择多个Excel文件",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if file_paths:
            self.batch_load_excel_data(file_paths)

    def supplement_import_files(self):
        """补充导入Excel文件 - 在现有数据基础上添加新的学生文件"""
        if not self.is_logged_in:
            messagebox.showerror("错误", "请先登录！")
            return

        # 选择要补充的文件
        file_paths = filedialog.askopenfilenames(
            title="选择要补充导入的Excel文件",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if not file_paths:
            return

        # 情况1：当前是单个文件模式，转换为批量模式
        if self.df is not None and not self.students_data:
            # 先将当前单个文件数据转换为批量数据结构
            self.convert_single_to_batch_mode()
        
        # 情况2：已经是批量模式或刚转换为批量模式，补充新文件
        self.supplement_batch_load_excel_data(file_paths)

    def load_excel_data(self, excel_path):
        """加载Excel文件并将数据添加到表格中"""
        # 清空之前的数据
        self.tree.delete(*self.tree.get_children())  # 清空表格中的内容
        self.df = None  # 清空之前的df数据

        # 加载新的Excel文件
        self.df = pd.read_excel(excel_path)
        
        # 添加评审相关的列（如果不存在的话）
        review_columns = ['项目类型', '评定等级', '认定情况', '加分', '备注']
        for col in review_columns:
            if col not in self.df.columns:
                self.df[col] = ''
                
        self.current_file = excel_path  # 关键：记录当前excel文件路径，供支撑材料查找

        # 在成功加载数据时更新状态
        self.exported = False  # 数据未导出
        messagebox.showinfo("成功", f"文件已加载: {excel_path}")

        #加载学生基本信息
        for idx, row in self.df.iterrows():
            # 显示学生基本信息
            self.info_labels["学院"].config(text=f"学院: {row['学院']}")
            self.info_labels["姓名"].config(text=f"姓名: {row['姓名']}")
            self.info_labels["年级"].config(text=f"年级: {row['年级']}")
            self.info_labels["班级"].config(text=f"班级: {row['班级']}")
            self.info_labels["学号"].config(text=f"学号: {row['学号']}")

            # 添加每行奖项信息到表格中
            self.tree.insert("", "end", values=(row['所获奖项名称'], row['获奖时间'], row['奖项等级'], "", "", "", ""))

    def batch_load_excel_data(self, file_paths):
        """批量加载多个Excel文件并将数据添加到学生数据字典中"""
        success_count = 0
        error_files = []
        
        # 清空之前的数据
        self.students_data = {}
        self.current_student_id = None
        self.tree.delete(*self.tree.get_children())
        
        for file_path in file_paths:
            try:
                # 加载Excel文件
                df = pd.read_excel(file_path)
                
                # 验证必要的列是否存在
                required_columns = ['学院', '姓名', '年级', '班级', '学号', '所获奖项名称', '获奖时间', '奖项等级']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    error_files.append(f"{os.path.basename(file_path)}: 缺少列 {missing_columns}")
                    continue
                
                # 添加评审相关的列（如果不存在的话）
                review_columns = ['项目类型', '评定等级', '认定情况', '加分', '备注']
                for col in review_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # 获取学生基本信息（取第一行）
                student_info = df.iloc[0]
                student_id = f"{student_info['学院']}_{student_info['姓名']}_{student_info['年级']}_{student_info['班级']}_{student_info['学号']}"
                
                # 检查是否有重复学生
                if student_id in self.students_data:
                    error_files.append(f"{os.path.basename(file_path)}: 学生信息重复")
                    continue
                
                # 存储学生数据
                self.students_data[student_id] = {
                    'df': df,
                    'file_path': file_path,
                    'student_info': {
                        '学院': student_info['学院'],
                        '姓名': student_info['姓名'],
                        '年级': student_info['年级'],
                        '班级': student_info['班级'],
                        '学号': student_info['学号']
                    }
                }
                success_count += 1
                
            except Exception as e:
                error_files.append(f"{os.path.basename(file_path)}: {str(e)}")
        
        # 更新学生选择下拉菜单
        if self.students_data:
            student_names = []
            for student_id, data in self.students_data.items():
                info = data['student_info']
                display_name = f"{info['姓名']} - {info['学院']} - {info['班级']}"
                student_names.append(display_name)
            
            self.student_dropdown['values'] = student_names
            
            # 默认选择第一个学生
            if student_names:
                self.student_dropdown.current(0)
                self.on_student_select()
        
        # 显示导入结果
        result_message = f"成功导入 {success_count} 个学生文件"
        if error_files:
            result_message += f"\n\n导入失败的文件：\n" + "\n".join(error_files)
        
        if success_count > 0:
            messagebox.showinfo("批量导入结果", result_message)
            self.exported = False  # 数据未导出
        else:
            messagebox.showerror("批量导入失败", result_message)

    def convert_single_to_batch_mode(self):
        """将当前单个文件模式转换为批量处理模式"""
        if self.df is None or self.current_file is None:
            return
        
        # 获取当前学生的基本信息
        student_info = self.df.iloc[0]
        student_id = f"{student_info['学院']}_{student_info['姓名']}_{student_info['年级']}_{student_info['班级']}_{student_info['学号']}"
        
        # 确保DataFrame包含所有必要的评审列
        review_columns = ['项目类型', '评定等级', '认定情况', '加分', '备注']
        for col in review_columns:
            if col not in self.df.columns:
                self.df[col] = ''
        
        # 将当前数据转存到students_data结构中
        self.students_data = {
            student_id: {
                'df': self.df.copy(),
                'file_path': self.current_file,
                'student_info': {
                    '学院': student_info['学院'],
                    '姓名': student_info['姓名'],
                    '年级': student_info['年级'],
                    '班级': student_info['班级'],
                    '学号': student_info['学号']
                }
            }
        }
        self.current_student_id = student_id
        
        # 更新学生选择下拉菜单
        info = self.students_data[student_id]['student_info']
        display_name = f"{info['姓名']} - {info['学院']} - {info['班级']}"
        self.student_dropdown['values'] = [display_name]
        self.student_dropdown.current(0)

    def supplement_batch_load_excel_data(self, file_paths):
        """补充加载Excel文件到现有的学生数据中"""
        success_count = 0
        error_files = []
        skipped_files = []
        
        for file_path in file_paths:
            try:
                # 加载Excel文件
                df = pd.read_excel(file_path)
                
                # 验证必要的列是否存在
                required_columns = ['学院', '姓名', '年级', '班级', '学号', '所获奖项名称', '获奖时间', '奖项等级']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    error_files.append(f"{os.path.basename(file_path)}: 缺少列 {missing_columns}")
                    continue
                
                # 添加评审相关的列（如果不存在的话）
                review_columns = ['项目类型', '评定等级', '认定情况', '加分', '备注']
                for col in review_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # 获取学生基本信息（取第一行）
                student_info = df.iloc[0]
                student_id = f"{student_info['学院']}_{student_info['姓名']}_{student_info['年级']}_{student_info['班级']}_{student_info['学号']}"
                
                # 检查是否有重复学生
                if student_id in self.students_data:
                    skipped_files.append(f"{os.path.basename(file_path)}: 学生信息已存在，跳过")
                    continue
                
                # 存储学生数据
                self.students_data[student_id] = {
                    'df': df,
                    'file_path': file_path,
                    'student_info': {
                        '学院': student_info['学院'],
                        '姓名': student_info['姓名'],
                        '年级': student_info['年级'],
                        '班级': student_info['班级'],
                        '学号': student_info['学号']
                    }
                }
                success_count += 1
                
            except Exception as e:
                error_files.append(f"{os.path.basename(file_path)}: {str(e)}")
        
        # 更新学生选择下拉菜单
        if self.students_data:
            student_names = []
            for student_id, data in self.students_data.items():
                info = data['student_info']
                display_name = f"{info['姓名']} - {info['学院']} - {info['班级']}"
                student_names.append(display_name)
        
            self.student_dropdown['values'] = student_names
        
        # 显示补充导入结果
        result_message = f"成功补充导入 {success_count} 个学生文件"
        if skipped_files:
            result_message += f"\n\n跳过的重复文件：\n" + "\n".join(skipped_files)
        if error_files:
            result_message += f"\n\n导入失败的文件：\n" + "\n".join(error_files)
        
        if success_count > 0:
            messagebox.showinfo("补充导入结果", result_message)
            self.exported = False  # 数据未导出
        else:
            if skipped_files and not error_files:
                messagebox.showinfo("补充导入结果", result_message)
            else:
                messagebox.showerror("补充导入失败", result_message)

    def on_student_select(self, event=None):
        """当用户选择不同学生时，切换显示的数据"""
        selected_display_name = self.student_var.get()
        if not selected_display_name:
            return
        
        # 如果有当前学生数据，先保存当前的评审进度
        if self.current_student_id and self.df is not None:
            self.students_data[self.current_student_id]['df'] = self.df.copy()
        
        # 根据显示名称找到对应的学生ID
        for student_id, data in self.students_data.items():
            info = data['student_info']
            display_name = f"{info['姓名']} - {info['学院']} - {info['班级']}"
            if display_name == selected_display_name:
                self.current_student_id = student_id
                break
        
        if self.current_student_id:
            # 更新当前数据
            student_data = self.students_data[self.current_student_id]
            self.df = student_data['df'].copy()  # 使用copy()确保数据独立
            self.current_file = student_data['file_path']
            
            # 更新学生信息显示
            info = student_data['student_info']
            self.info_labels["学院"].config(text=f"学院: {info['学院']}")
            self.info_labels["姓名"].config(text=f"姓名: {info['姓名']}")
            self.info_labels["年级"].config(text=f"年级: {info['年级']}")
            self.info_labels["班级"].config(text=f"班级: {info['班级']}")
            self.info_labels["学号"].config(text=f"学号: {info['学号']}")
            
            # 清空并重新加载表格数据
            self.tree.delete(*self.tree.get_children())
            for idx, row in self.df.iterrows():
                # 从DataFrame中获取评审数据，如果存在的话
                project_type = row.get('项目类型', '')
                level = row.get('评定等级', '')
                recognition = row.get('认定情况', '')
                points = row.get('加分', '')
                remarks = row.get('备注', '')
                
                self.tree.insert("", "end", values=(
                    row['所获奖项名称'], row['获奖时间'], row['奖项等级'], 
                    project_type, level, recognition, points, remarks
                ))


    def on_select(self, event):
        """当用户点击表格中的一行时，更新右侧的评审界面，并显示奖项支撑材料"""
        selected_item = self.tree.selection()
        if selected_item:
            # 获取所选行的数据
            selected_values = self.tree.item(selected_item)['values']

            # 这里更新评审界面对应的输入框或标签
            award_name = selected_values[0]  # 奖项名称
            level = selected_values[2]  # 奖项等级

            # 将奖项名称和等级显示在评审界面上
            self.project_type_var.set("")  # 清空项目类型选择
            self.level_var.set("")  # 不默认显示读取的Excel的奖项等级
            self.recognition_var.set("")  # 清空认定情况选择
            self.remarks_var.set("")  # 清空备注选择
            self.points_label.config(text="加分: 0")  # 重置加分为0

            # 新增：查找并显示奖项支撑材料
            self.show_award_material(award_name)

    def show_award_material(self, award_name):
        """查找并显示与奖项名称相关的图片或pdf文件"""
        # 清空canvas和pdf按钮
        self.material_canvas.delete("all")
        if self.material_pdf_btn:
            self.material_pdf_btn.destroy()
            self.material_pdf_btn = None
        if not self.current_file:
            return
        base_dir = os.path.dirname(self.current_file)
        safe_award_name = ''.join([c for c in str(award_name) if '\u4e00' <= c <= '\u9fff' or c.isalnum()])
        # 优先查找图片
        for ext in [".jpg", ".jpeg", ".png"]:
            file_path = os.path.join(base_dir, safe_award_name + ext)
            if os.path.exists(file_path):
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(file_path)
                    img.thumbnail((400, 300))
                    self.material_img = ImageTk.PhotoImage(img)
                    self.material_canvas.create_image(200, 150, image=self.material_img)
                    return
                except Exception as e:
                    self.material_canvas.create_text(200, 150, text=f"图片加载失败: {e}")
                    return
        # 查找pdf
        pdf_path = os.path.join(base_dir, safe_award_name + ".pdf")
        if os.path.exists(pdf_path):
            def open_pdf():
                import webbrowser
                webbrowser.open(pdf_path)
            self.material_pdf_btn = tk.Button(self.material_frame, text="打开PDF支撑材料", command=open_pdf)
            self.material_pdf_btn.pack(side=tk.TOP, pady=10)
            self.material_canvas.create_text(200, 150, text="点击上方按钮打开PDF文件")
            return
        self.material_canvas.create_text(200, 150, text="未找到相关支撑材料（图片或PDF）")

    def update_award_levels(self, event=None):
        """根据选择的项目类型，动态更新奖项级别下拉列表的选项"""
        project_type = self.project_type_var.get()
        level_mapping = self.get_current_level_mapping()
        
        if project_type in level_mapping:
            self.level_dropdown['values'] = level_mapping[project_type]
        else:
            self.level_dropdown['values'] = []
            
        self.level_var.set("")  # 清空选择

    def on_recognition_select(self, event=None):
        """当用户选择认定情况时，启用或禁用备注下拉菜单"""
        if self.recognition_var.get() == "不予认定":
            self.remarks_dropdown.config(state='readonly')  # 启用备注选择
            # 备注必须填写，所以这里设置为不能为空
            self.remarks_var.set("请填写备注")
        else:
            self.remarks_dropdown.config(state='disabled')  # 禁用备注选择
            self.remarks_var.set("")  # 清空备注选择

    def calculate_points(self, project_type, level):
        """根据项目类型和级别计算加分"""
        # 获取当前使用的加分字典
        points_dict = self.get_current_points_dict()
        
        # 查找对应的加分值
        if project_type in points_dict and level in points_dict[project_type]:
            return points_dict[project_type][level]
        return 0  # 如果没有找到对应的加分项，返回0分

    def confirm_review(self):
        """确认评审结果并更新表格"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("错误", "请先选择一行进行评审")
            return

        # 检查是否有学生数据
        if not self.df is not None and not self.students_data:
            messagebox.showerror("错误", "请先导入学生数据")
            return

        if selected_item:
            # 获取当前选中的行号
            selected_idx = self.tree.index(selected_item[0])
            # 获取用户输入的内容
            project_type = self.project_type_var.get()
            level = self.level_var.get()
            recognition = self.recognition_var.get()
            remarks = self.remarks_var.get()

            # 如果认定情况为“不予认定”，则必须有备注
            if recognition == "不予认定" and not remarks:
                messagebox.showerror("错误", "请填写备注信息")
                return  # 退出方法，不更新表格

            # 如果认定情况为“认定”，则项目类型和评定等级不能为空
            if recognition == "认定" and (not project_type or not level):
                messagebox.showerror("错误", "项目类型和评定等级不能为空")
                return  # 退出方法，不更新表格

            if recognition == "认定":
                points = self.calculate_points(project_type, level)
            else:
                points = 0

            # 更新 TreeView 的选中行
            self.tree.item(selected_item, values=(
                self.tree.item(selected_item, "values")[0],  # 奖项名称
                self.tree.item(selected_item, "values")[1],  # 获奖时间
                self.tree.item(selected_item, "values")[2],  # 奖项等级
                project_type,  # 项目类型
                level,  # 评定等级
                recognition,  # 认定情况
                points,  # 加分
                remarks  # 备注
            ))

            # 更新 DataFrame 中的数据
            self.df.loc[selected_idx, '项目类型'] = project_type
            self.df.loc[selected_idx, '评定等级'] = level
            self.df.loc[selected_idx, '认定情况'] = recognition
            self.df.loc[selected_idx, '加分'] = points
            self.df.loc[selected_idx, '备注'] = remarks

            # 如果是批量导入模式，同时更新students_data中的数据
            if self.students_data and self.current_student_id:
                self.students_data[self.current_student_id]['df'] = self.df.copy()

            # 更新界面的加分显示

            # 计算加分
            points = self.calculate_points(project_type, level)

            # 如果认定情况为“不予认定”，则加分为0
            if recognition == "不予认定":
                points = 0

            # 获取当前选中行的索引
            index = self.tree.index(selected_item)
            award_name = self.tree.item(selected_item)['values'][0]  # 奖项名称

            self.points_label.config(text=f"加分: {points}")  # 更新加分显示

            # 更新表格
            self.tree.item(selected_item, values=(
                award_name,
                self.tree.item(selected_item)['values'][1],  # 保持获奖时间不变
                self.tree.item(selected_item)['values'][2],  # 保持奖项等级不变
                project_type,
                level,
                recognition,
                points,
                remarks
            ))

            # 自动选择下一行
            self.select_next_item(index)

    def select_next_item(self, current_index):
        """选择下一行，如果没有则从头开始检查未评审的行"""
        next_index = current_index + 1

        # 检查是否到达最后一行
        if next_index >= len(self.tree.get_children()):
            next_index = 0  # 如果到达最后一行，则从头开始

        # 从当前索引或头开始，寻找未评审的行
        for i in range(next_index, len(self.tree.get_children())):
            item = self.tree.get_children()[i]
            recognition = self.tree.item(item)['values'][5]  # 认定情况的列索引
            if recognition == "":  # 如果认定情况为空，则选中该行
                self.tree.selection_set(item)
                self.tree.focus(item)
                return

        # 如果从当前位置没有找到未评审的，则从头开始查找
        for i in range(0, next_index):
            item = self.tree.get_children()[i]
            recognition = self.tree.item(item)['values'][5]  # 认定情况的列索引
            if recognition == "":  # 如果认定情况为空，则选中该行
                self.tree.selection_set(item)
                self.tree.focus(item)
                return

    def on_closing(self):
        """当用户尝试关闭窗口时，检查是否有未导出的数据"""
        if not self.exported:  # 如果数据未导出
            if messagebox.askokcancel("未导出数据", "你还有未导出的评审结果，确定要关闭吗？"):
                self.root.destroy()  # 用户确认后关闭窗口
        else:
            self.root.destroy()  # 如果数据已导出，直接关闭窗口

    def export_excel(self):
        """导出当前学生的评审结果到新的Excel文件"""
        # 检查是否有数据
        if self.df is None and not self.students_data:
            messagebox.showerror("错误", "没有可导出的数据！")
            return
        
        # 如果是批量导入模式但没有选中学生
        if self.students_data and not self.current_student_id:
            messagebox.showerror("错误", "请先选择要导出的学生！")
            return
        
        # 获取当前数据
        current_df = self.df
        if self.students_data and self.current_student_id:
            current_df = self.students_data[self.current_student_id]['df']
        
        if current_df is not None:
            unreviewed_awards, incomplete_remarks = self.validate_review_completion()
            if unreviewed_awards or incomplete_remarks:
                error_message = ""
                if unreviewed_awards:
                    error_message += f"以下奖项未完成审核：\n{', '.join(map(str,unreviewed_awards))}\n"
                if incomplete_remarks:
                    error_message += f"以下奖项需要填写备注：\n{', '.join(map(str,incomplete_remarks))}\n"
                messagebox.showerror("错误", error_message + "请先完成所有奖项的审核。")
                return

            # 获取当前选中学生的基本信息
            basic_info = {
                "学院": self.info_labels["学院"].cget("text").split(": ")[1],
                "姓名": self.info_labels["姓名"].cget("text").split(": ")[1],
                "年级": self.info_labels["年级"].cget("text").split(": ")[1],
                "班级": self.info_labels["班级"].cget("text").split(": ")[1],
                "学号": self.info_labels["学号"].cget("text").split(": ")[1]
            }

            export_data = []
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                # 将基本信息添加到每一行的前面
                row_data = [basic_info["学院"], basic_info["姓名"], basic_info["年级"], basic_info["班级"],
                            basic_info["学号"]] + list(values)
                export_data.append(row_data)

            # 导出Excel的逻辑
            # 获取学生信息
            student_info = current_df.iloc[0][['学院', '姓名', '年级', '班级', '学号']]
            file_name = "_".join(student_info.astype(str)) + ".xlsx"

            # 导出Excel的数据内容
            df_export = pd.DataFrame(export_data,
                                     columns=["学院", "姓名", "年级", "班级", "学号", "所获奖项名称", "获奖时间",
                                              "奖项等级", "项目类型", "评定等级", "认定情况", "加分", "备注"])

            # 设置文件默认保存名格式，“学院_姓名_年级_班级_学号.xlsx”
            save_path = filedialog.asksaveasfilename(initialfile=file_name, defaultextension=".xlsx",
                                                         filetypes=[("Excel files", "*.xlsx")])
            if not save_path:
                messagebox.showerror("错误", "文件路径未选择！")
                return  # 终止函数的执行

            df_export.to_excel(save_path, index=False)
            messagebox.showinfo("成功", f"Excel文件导出成功！导出至{save_path}")
            self.exported = True

        else:
            messagebox.showerror("错误", "没有可导出的数据！")

    def stats_export_excel(self):
        """导出当前学生的统计结果到新的Excel文件"""
        # 检查是否有数据
        if self.df is None and not self.students_data:
            messagebox.showerror("错误", "没有可导出的数据！")
            return
        
        # 如果是批量导入模式但没有选中学生
        if self.students_data and not self.current_student_id:
            messagebox.showerror("错误", "请先选择要导出的学生！")
            return
        
        # 获取当前数据
        current_df = self.df
        if self.students_data and self.current_student_id:
            current_df = self.students_data[self.current_student_id]['df']
        
        if current_df is not None:
            unreviewed_awards, incomplete_remarks = self.validate_review_completion()
            if unreviewed_awards or incomplete_remarks:
                error_message = ""
                if unreviewed_awards:
                    error_message += f"以下奖项未完成审核：\n{', '.join(map(str, unreviewed_awards))}\n"
                if incomplete_remarks:
                    error_message += f"以下奖项需要填写备注：\n{', '.join(map(str, incomplete_remarks))}\n"
                messagebox.showerror("错误", error_message + "请先完成所有奖项的审核。")
                return

            # 动态获取项目类型
            if self.custom_scoring_rules and 'project_types' in self.custom_scoring_rules:
                project_types = self.custom_scoring_rules['project_types']
            else:
                project_types = ["竞赛类加分", "科研创新类加分", "外语类加分"]

            # 初始化统计字典
            statistics = {ptype: 0 for ptype in project_types}

            # 遍历表格，按项目类型统计总分
            for _, row in current_df.iterrows():
                project_type = row.get("项目类型", "")
                points = row.get("加分", 0)
                if project_type in statistics:
                    statistics[project_type] += points

            # 限制每类总分最大为自定义上限或6分
            for key in statistics:
                max_score = 6
                if self.custom_scoring_rules and 'max_dict' in self.custom_scoring_rules:
                    max_score = self.custom_scoring_rules['max_dict'].get(key, 6)
                statistics[key] = min(statistics[key], max_score)

            # 获取当前选中学生的基本信息
            basic_info = {
                "学院": self.info_labels["学院"].cget("text").split(": ")[1],
                "姓名": self.info_labels["姓名"].cget("text").split(": ")[1],
                "年级": self.info_labels["年级"].cget("text").split(": ")[1],
                "班级": self.info_labels["班级"].cget("text").split(": ")[1],
                "学号": self.info_labels["学号"].cget("text").split(": ")[1]
            }

            # 构建导出的行数据（动态项目类型）
            export_row = [
                basic_info["学院"],
                basic_info["姓名"],
                basic_info["年级"],
                basic_info["班级"],
                basic_info["学号"]
            ] + [statistics[ptype] for ptype in project_types]

            # 定义列名
            columns = ["学院", "姓名", "年级", "班级", "学号"] + project_types

            # 设置文件默认保存名格式，“学院_姓名_年级_班级_学号.xlsx”
            file_name = f"{basic_info['学院']}_{basic_info['姓名']}_{basic_info['年级']}_{basic_info['班级']}_{basic_info['学号']}_统计.xlsx"
            save_path = filedialog.asksaveasfilename(initialfile=file_name, defaultextension=".xlsx",
                                                     filetypes=[("Excel files", "*.xlsx")])
            if not save_path:
                messagebox.showerror("错误", "文件路径未选择！")
                return  # 终止函数的执行

            # 创建导出 DataFrame 并保存为 Excel
            df_export = pd.DataFrame([export_row], columns=columns)
            df_export.to_excel(save_path, index=False)
            messagebox.showinfo("成功", f"Excel文件导出成功！导出至{save_path}")
            self.exported = True

        else:
            messagebox.showerror("错误", "没有可导出的数据！")

    def batch_export_excel(self):
        """批量导出所有学生的评审结果到Excel文件"""
        if not self.students_data:
            messagebox.showerror("错误", "请先导入学生数据！")
            return
        
        # 先保存当前学生的评审进度
        if self.current_student_id and self.df is not None:
            self.students_data[self.current_student_id]['df'] = self.df.copy()
        
        # 检查是否所有学生都完成了评审
        unfinished_students = []
        for student_id, data in self.students_data.items():
            df = data['df']
            # 检查是否有未评审的项目
            unreviewed_count = 0
            for idx, row in df.iterrows():
                if pd.isna(df.loc[idx, '认定情况']) or df.loc[idx, '认定情况'] == '':
                    unreviewed_count += 1
            
            if unreviewed_count > 0:
                info = data['student_info']
                unfinished_students.append(f"{info['姓名']} - {info['学院']} - {info['班级']} (剩余{unreviewed_count}项未评审)")
        
        if unfinished_students:
            result = messagebox.askyesno("未完成评审", 
                f"以下学生还有未完成的评审：\n" + "\n".join(unfinished_students) + 
                "\n\n是否继续导出？")
            if not result:
                return
        
        # 选择保存目录
        save_dir = filedialog.askdirectory(title="选择批量导出的保存目录")
        if not save_dir:
            return
        
        success_count = 0
        error_files = []
        
        for student_id, data in self.students_data.items():
            try:
                df = data['df']
                info = data['student_info']
                
                # 准备导出数据
                export_data = []
                for idx, row in df.iterrows():
                    # 构建行数据，安全地获取评审数据
                    project_type = row.get('项目类型', '') if '项目类型' in df.columns else ''
                    level = row.get('评定等级', '') if '评定等级' in df.columns else ''
                    recognition = row.get('认定情况', '') if '认定情况' in df.columns else ''
                    points = row.get('加分', '') if '加分' in df.columns else ''
                    remarks = row.get('备注', '') if '备注' in df.columns else ''
                    
                    row_data = [
                        info['学院'], info['姓名'], info['年级'], info['班级'], info['学号'],
                        row['所获奖项名称'], row['获奖时间'], row['奖项等级'],
                        project_type, level, recognition, points, remarks
                    ]
                    export_data.append(row_data)
                
                # 创建DataFrame
                df_export = pd.DataFrame(export_data,
                    columns=["学院", "姓名", "年级", "班级", "学号", "所获奖项名称", "获奖时间",
                             "奖项等级", "项目类型", "评定等级", "认定情况", "加分", "备注"])
                
                # 生成文件名
                file_name = f"{info['学院']}_{info['姓名']}_{info['年级']}_{info['班级']}_{info['学号']}.xlsx"
                save_path = os.path.join(save_dir, file_name)
                
                # 保存文件
                df_export.to_excel(save_path, index=False)
                success_count += 1
                
            except Exception as e:
                error_files.append(f"{student_id}: {str(e)}")
        
        # 显示结果
        result_message = f"成功导出 {success_count} 个学生的评审结果到：\n{save_dir}"
        if error_files:
            result_message += f"\n\n导出失败的学生：\n" + "\n".join(error_files)
        
        if success_count > 0:
            messagebox.showinfo("批量导出完成", result_message)
            self.exported = True
        else:
            messagebox.showerror("批量导出失败", result_message)

    def batch_stats_export_excel(self):
        """批量导出所有学生的统计结果到Excel文件"""
        if not self.students_data:
            messagebox.showerror("错误", "请先导入学生数据！")
            return
        
        # 先保存当前学生的评审进度
        if self.current_student_id and self.df is not None:
            self.students_data[self.current_student_id]['df'] = self.df.copy()
        
        # 检查是否所有学生都完成了评审
        unfinished_students = []
        for student_id, data in self.students_data.items():
            df = data['df']
            # 检查是否有未评审的项目
            unreviewed_count = 0
            for idx, row in df.iterrows():
                if pd.isna(df.loc[idx, '认定情况']) or df.loc[idx, '认定情况'] == '':
                    unreviewed_count += 1
            
            if unreviewed_count > 0:
                info = data['student_info']
                unfinished_students.append(f"{info['姓名']} - {info['学院']} - {info['班级']} (剩余{unreviewed_count}项未评审)")
        
        if unfinished_students:
            result = messagebox.askyesno("未完成评审", 
                f"以下学生还有未完成的评审：\n" + "\n".join(unfinished_students) + 
                "\n\n是否继续导出？")
            if not result:
                return
        
        # 选择保存文件
        save_path = filedialog.asksaveasfilename(
            title="保存批量统计结果",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        if not save_path:
            return
        
        # 准备统计数据
        all_stats_data = []
        project_types = ["竞赛类加分", "科研创新类加分", "外语类加分"]
        
        for student_id, data in self.students_data.items():
            try:
                df = data['df']
                info = data['student_info']
                
                # 初始化统计字典
                statistics = {ptype: 0 for ptype in project_types}
                
                # 统计各类加分
                for idx, row in df.iterrows():
                    project_type = row.get('项目类型', '') if '项目类型' in df.columns else ''
                    points = row.get('加分', 0) if '加分' in df.columns else 0
                    
                    if project_type in statistics:
                        try:
                            points_value = float(points) if points else 0
                            statistics[project_type] += points_value
                        except (ValueError, TypeError):
                            pass
                
                # 限制每类总分最大为自定义上限或6分
                for key in statistics:
                    max_score = 6
                    if self.custom_scoring_rules and 'max_dict' in self.custom_scoring_rules:
                        max_score = self.custom_scoring_rules['max_dict'].get(key, 6)
                    statistics[key] = min(statistics[key], max_score)
                
                # 构建统计行数据
                stats_row = [
                    info['学院'], info['姓名'], info['年级'], info['班级'], info['学号']
                ] + [statistics[ptype] for ptype in project_types]
                all_stats_data.append(stats_row)
            except Exception as e:
                print(f"处理学生 {student_id} 时出错: {e}")
        # 创建统计DataFrame
        columns = ["学院", "姓名", "年级", "班级", "学号"] + project_types
        df_stats = pd.DataFrame(all_stats_data, columns=columns)
        
        try:
            # 保存统计结果
            df_stats.to_excel(save_path, index=False)
            messagebox.showinfo("成功", f"批量统计结果已导出到：\n{save_path}")
            self.exported = True
        except Exception as e:
            messagebox.showerror("导出失败", f"保存文件时出错：{str(e)}")

    def init_default_scoring_rules(self):
        """初始化默认的加分规则"""
        self.default_project_types = ["竞赛类加分", "科研创新类加分", "外语类加分"]
        
        self.default_level_mapping = {
            "竞赛类加分": [
                "国家级一等奖", "国家级二等奖", "国家级三等奖",
                "省级一等奖", "省级二等奖", "省级三等奖",
                "市级一等奖", "市级二等奖", "市级三等奖",
                "校级一等奖", "校级二等奖", "校级三等奖",
                "院级一等奖", "院级二等奖", "院级三等奖"
            ],
            "科研创新类加分": [
                "国家级立项主持人", "国家级立项学生成员",
                "省级重点立项主持人", "省级重点立项学生成员",
                "省级一般立项主持人", "省级一般立项学生成员",
                "校级立项主持人", "校级立项学生成员",
                "SCI论文一作", "SCI论文二作", "SCI论文三作",
                "核心期刊论文一作", "核心期刊论文二作", "核心期刊论文三作",
                "普通期刊论文一作", "普通期刊论文二作", "普通期刊论文三作",
                "版权著作",
                "发明专利一作", "发明专利二作", "发明专利三作",
                "实用新型专利一作", "实用新型专利二作", "实用新型专利三作",
                "外观专利一作", "外观专利二作", "外观专利三作",
            ],
            "外语类加分": [
                "大学英语四级（CET4）", "大学英语六级（CET6）",
                "英语专业四级（TEM4）", "英语专业八级（TEM8）",
                "雅思（IELTS）",
                "托福（TOEFL）",
                "剑桥英语考试（Cambridge English Exams）",
                "培生英语考试（Pearson Test of English Academic, PTE Academic）",
                "GRE（Graduate Record Examination）",
                "GMAT（Graduate Management Admission Test）",
                "其他符合外语类加分项目（2分）",
                "其他符合外语类加分项目（1分）",
            ]
        }
        
        self.default_points_dict = {
            "竞赛类加分": {
                "国家级一等奖": 6, "国家级二等奖": 4, "国家级三等奖": 3,
                "省级一等奖": 5, "省级二等奖": 3, "省级三等奖": 2,
                "市级一等奖": 3, "市级二等奖": 2, "市级三等奖": 1,
                "校级一等奖": 2, "校级二等奖": 1, "校级三等奖": 0.5,
                "院级一等奖": 1, "院级二等奖": 0.5, "院级三等奖": 0.3
            },
            "科研创新类加分": {
                "国家级立项主持人": 6, "国家级立项学生成员": 4,
                "省级重点立项主持人": 5, "省级重点立项学生成员": 3,
                "省级一般立项主持人": 3, "省级一般立项学生成员": 2,
                "校级立项主持人": 2, "校级立项学生成员": 1,
                "SCI论文一作": 6, "SCI论文二作": 4, "SCI论文三作": 3,
                "核心期刊论文一作": 3, "核心期刊论文二作": 2, "核心期刊论文三作": 1,
                "普通期刊论文一作": 2, "普通期刊论文二作": 1, "普通期刊论文三作": 0.5,
                "版权著作": 1,
                "发明专利一作": 6, "发明专利二作": 4, "发明专利三作": 3,
                "实用新型专利一作": 2, "实用新型专利二作": 1, "实用新型专利三作": 0.5,
                "外观专利一作": 2, "外观专利二作": 1, "外观专利三作": 0.5,
            },
            "外语类加分": {
                "大学英语四级（CET4）": 1, "大学英语六级（CET6）": 2,
                "英语专业四级（TEM4）": 1, "英语专业八级（TEM8）": 2,
                "雅思（IELTS）": 2,
                "托福（TOEFL）": 2,
                "剑桥英语考试（Cambridge English Exams）": 2,
                "培生英语考试（Pearson Test of English Academic）": 2,
                "GRE（Graduate Record Examination）": 2,
                "GMAT（Graduate Management Admission Test）": 2,
                "其他符合外语类加分项目（2分）": 2,
                "其他符合外语类加分项目（1分）": 1
            }
        }

    def import_scoring_details(self):
        """导入加分详情xlsx文件"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择加分详情Excel文件",
                filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls")]
            )
            
            if not file_path:
                return
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 检查文件格式
            if len(df.columns) < 3:
                messagebox.showerror("错误", "文件格式不正确！请确保文件包含三列：项目类型、奖项级别、加分")
                return
            
            # 获取列名（可能是中文或其他语言）
            col_names = df.columns.tolist()
            project_type_col = col_names[0]
            level_col = col_names[1] 
            points_col = col_names[2]
            
            # 构建自定义加分规则
            custom_project_types = df[project_type_col].dropna().unique().tolist()
            custom_level_mapping = {}
            custom_points_dict = {}
            
            for project_type in custom_project_types:
                # 获取该项目类型下的所有奖项级别
                type_data = df[df[project_type_col] == project_type]
                levels = type_data[level_col].dropna().unique().tolist()
                custom_level_mapping[project_type] = levels
                
                # 构建加分映射
                custom_points_dict[project_type] = {}
                for _, row in type_data.iterrows():
                    level = row[level_col]
                    points = row[points_col]
                    if pd.notna(level) and pd.notna(points):
                        try:
                            custom_points_dict[project_type][level] = float(points)
                        except ValueError:
                            messagebox.showwarning("警告", f"无法解析加分值: {points}，将设为0")
                            custom_points_dict[project_type][level] = 0
            
            # 检查是否有加分上限列
            max_col = col_names[3] if len(col_names) >= 4 else None
            custom_max_dict = {}
            if max_col:
                for project_type in custom_project_types:
                    # 取该类型下的第一个非空上限
                    type_data = df[df[project_type_col] == project_type]
                    max_val = type_data[max_col].dropna()
                    if not max_val.empty:
                        try:
                            custom_max_dict[project_type] = float(max_val.iloc[0])
                        except Exception:
                            custom_max_dict[project_type] = 6  # 解析失败默认6分
                    else:
                        custom_max_dict[project_type] = 6
            else:
                for project_type in custom_project_types:
                    custom_max_dict[project_type] = 6

            # 更新自定义规则
            self.custom_scoring_rules = {
                'project_types': custom_project_types,
                'level_mapping': custom_level_mapping,
                'points_dict': custom_points_dict,
                'max_dict': custom_max_dict
            }
            
            # 更新界面
            self.update_scoring_interface()
            
            messagebox.showinfo("成功", f"成功导入加分详情！\n共导入 {len(custom_project_types)} 个项目类型")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    def reset_scoring_details(self):
        """重置为默认的加分规则"""
        self.custom_scoring_rules = None
        self.update_scoring_interface()
        messagebox.showinfo("成功", "已重置为默认加分规则")

    def update_scoring_interface(self):
        """根据当前加分规则更新界面"""
        # 获取当前使用的规则
        if self.custom_scoring_rules:
            project_types = self.custom_scoring_rules['project_types']
        else:
            project_types = self.default_project_types
        
        # 更新项目类型下拉菜单
        self.project_type_dropdown['values'] = project_types
        
        # 清空当前选择
        self.project_type_var.set("")
        self.level_var.set("")
        self.level_dropdown['values'] = []
        
        # 重置加分显示
        self.points_label.config(text="加分: 0")

    def get_current_level_mapping(self):
        """获取当前使用的奖项级别映射"""
        if self.custom_scoring_rules:
            return self.custom_scoring_rules['level_mapping']
        else:
            return self.default_level_mapping

    def get_current_points_dict(self):
        """获取当前使用的加分字典"""
        if self.custom_scoring_rules:
            return self.custom_scoring_rules['points_dict']
        else:
            return self.default_points_dict


if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    app = ScholarshipReviewer(root)

    # 加载图标
    icon_path = "logo.ico"
    icon_image = ImageTk.PhotoImage(file=icon_path)
    # 设置窗口 Logo
    root.iconphoto(False, icon_image)

    class CustomToplevel(Toplevel):
        def __init__(self, master=None, icon=None, **kwargs):
            super().__init__(master, **kwargs)
            if icon:
                self.iconphoto(False, icon)  # 自动设置图标


    # 使用封装的弹窗类
    def create_popup():
        popup = CustomToplevel(root, icon=icon_image)
        popup.title("统一图标的弹窗")
        popup.geometry("512*512")

        # 添加内容
        label = tk.Label(popup, text="这是一个统一图标的弹窗")
        label.pack(pady=20)

        button_close = tk.Button(popup, text="关闭", command=popup.destroy)
        button_close.pack(pady=10)

    # 窗口主循环
    root.mainloop()
