"""
奖学金评审软件 - 增强数据导入模块

功能：
1. CSV 格式导入支持
2. JSON 格式导入支持
3. 数据格式自动检测
4. 数据验证和清洗
5. 批量导入优化
"""

import os
import csv
import json
import logging
import chardet
import pandas as pd
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

logger = logging.getLogger(__name__)


class DataImporter:
    """数据导入器"""
    
    # 支持的文件格式
    SUPPORTED_FORMATS = {
        '.xlsx': 'Excel 2007+',
        '.xls': 'Excel 97-2003',
        '.csv': 'CSV',
        '.json': 'JSON',
        '.txt': 'Text (Tab-separated)'
    }
    
    def __init__(self):
        """初始化数据导入器"""
        self.import_history = []
    
    def import_file(self, file_path, file_format=None):
        """导入文件
        
        Args:
            file_path: 文件路径
            file_format: 文件格式（可选，自动检测）
            
        Returns:
            pandas.DataFrame: 导入的数据
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 自动检测格式
        if file_format is None:
            file_format = file_path.suffix.lower()
        
        # 根据格式选择导入方法
        if file_format in ['.xlsx', '.xls']:
            df = self._import_excel(file_path)
        elif file_format == '.csv':
            df = self._import_csv(file_path)
        elif file_format == '.json':
            df = self._import_json(file_path)
        elif file_format == '.txt':
            df = self._import_text(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")
        
        # 记录导入历史
        self.import_history.append({
            'file_path': str(file_path),
            'file_format': file_format,
            'rows': len(df),
            'columns': len(df.columns),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"文件导入成功: {file_path} ({len(df)} 行, {len(df.columns)} 列)")
        return df
    
    def _import_excel(self, file_path):
        """导入 Excel 文件"""
        try:
            # 尝试读取所有 sheet
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            if len(sheet_names) == 1:
                # 单个 sheet，直接读取
                df = pd.read_excel(file_path, sheet_name=0)
            else:
                # 多个 sheet，让用户选择或读取第一个
                logger.info(f"Excel 文件包含 {len(sheet_names)} 个 sheet: {sheet_names}")
                df = pd.read_excel(file_path, sheet_name=0)
            
            return df
        except Exception as e:
            logger.error(f"导入 Excel 文件失败: {e}")
            raise
    
    def _import_csv(self, file_path):
        """导入 CSV 文件"""
        try:
            # 自动检测编码
            encoding = self._detect_encoding(file_path)
            
            # 尝试不同的分隔符
            separators = [',', ';', '\t', '|']
            df = None
            
            for sep in separators:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep=sep, engine='python')
                    # 检查是否成功解析（多列）
                    if len(df.columns) > 1:
                        break
                except Exception:
                    continue
            
            if df is None:
                # 如果都失败，使用默认逗号分隔
                df = pd.read_csv(file_path, encoding=encoding)
            
            return df
        except Exception as e:
            logger.error(f"导入 CSV 文件失败: {e}")
            raise
    
    def _import_json(self, file_path):
        """导入 JSON 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 支持多种 JSON 格式
            if isinstance(data, list):
                # 列表格式
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # 字典格式
                if 'data' in data:
                    # 嵌套数据格式
                    df = pd.DataFrame(data['data'])
                else:
                    # 单条记录格式
                    df = pd.DataFrame([data])
            else:
                raise ValueError("不支持的 JSON 格式")
            
            return df
        except Exception as e:
            logger.error(f"导入 JSON 文件失败: {e}")
            raise
    
    def _import_text(self, file_path):
        """导入文本文件（Tab 分隔）"""
        try:
            encoding = self._detect_encoding(file_path)
            df = pd.read_csv(file_path, encoding=encoding, sep='\t')
            return df
        except Exception as e:
            logger.error(f"导入文本文件失败: {e}")
            raise
    
    def _detect_encoding(self, file_path):
        """检测文件编码
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件编码
        """
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                result = chardet.detect(raw_data)
                encoding = result['encoding']
                
                # 如果检测失败，使用常见编码
                if encoding is None:
                    encoding = 'utf-8'
                
                logger.debug(f"检测到文件编码: {encoding}")
                return encoding
        except Exception:
            # 默认使用 utf-8
            return 'utf-8'
    
    def validate_data(self, df, required_columns=None):
        """验证数据
        
        Args:
            df: DataFrame
            required_columns: 必需列列表
            
        Returns:
            tuple: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # 检查空数据
        if df.empty:
            errors.append("数据为空")
            return False, errors, warnings
        
        # 检查必需列
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                errors.append(f"缺少必需列: {', '.join(missing_columns)}")
        
        # 检查数据类型
        for col in df.columns:
            # 检查全空列
            if df[col].isna().all():
                warnings.append(f"列 '{col}' 全为空值")
        
        # 检查重复行
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            warnings.append(f"存在 {duplicate_count} 行重复数据")
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def clean_data(self, df, drop_duplicates=True, drop_empty_rows=True):
        """清洗数据
        
        Args:
            df: DataFrame
            drop_duplicates: 是否删除重复行
            drop_empty_rows: 是否删除空行
            
        Returns:
            pandas.DataFrame: 清洗后的数据
        """
        original_rows = len(df)
        
        # 删除重复行
        if drop_duplicates:
            df = df.drop_duplicates()
        
        # 删除空行
        if drop_empty_rows:
            df = df.dropna(how='all')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        cleaned_rows = original_rows - len(df)
        if cleaned_rows > 0:
            logger.info(f"数据清洗完成: 删除 {cleaned_rows} 行")
        
        return df
    
    def get_import_history(self):
        """获取导入历史
        
        Returns:
            list: 导入历史记录
        """
        return self.import_history


class EnhancedImportDialog:
    """增强导入对话框"""
    
    def __init__(self, parent, importer, callback):
        """初始化导入对话框
        
        Args:
            parent: 父窗口
            importer: DataImporter 实例
            callback: 导入完成回调函数
        """
        self.parent = parent
        self.importer = importer
        self.callback = callback
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("导入数据")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建界面
        self._create_ui()
    
    def _create_ui(self):
        """创建界面"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="导入数据文件", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # 支持格式说明
        formats_text = "支持的文件格式：\n"
        for ext, desc in self.importer.SUPPORTED_FORMATS.items():
            formats_text += f"  • {ext} - {desc}\n"
        
        ttk.Label(main_frame, text=formats_text, justify=tk.LEFT).pack(pady=(0, 20))
        
        # 文件选择框架
        file_frame = ttk.LabelFrame(main_frame, text="选择文件", padding="10")
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(file_frame, text="浏览...", command=self._browse_file).pack(side=tk.RIGHT)
        
        # 导入选项框架
        options_frame = ttk.LabelFrame(main_frame, text="导入选项", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 数据验证选项
        self.validate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="导入后验证数据", variable=self.validate_var).pack(anchor=tk.W)
        
        self.clean_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="自动清洗数据（删除空行和重复行）", variable=self.clean_var).pack(anchor=tk.W)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="导入", command=self._import_file).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var).pack(fill=tk.X, pady=(20, 0))
    
    def _browse_file(self):
        """浏览文件"""
        file_types = [
            ("所有支持的格式", "*.xlsx *.xls *.csv *.json *.txt"),
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("JSON files", "*.json"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=file_types
        )
        
        if file_path:
            self.file_path_var.set(file_path)
    
    def _import_file(self):
        """导入文件"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("警告", "请先选择文件！")
            return
        
        try:
            self.status_var.set("正在导入...")
            self.dialog.update()
            
            # 导入文件
            df = self.importer.import_file(file_path)
            
            # 验证数据
            if self.validate_var.get():
                is_valid, errors, warnings = self.importer.validate_data(df)
                
                if errors:
                    messagebox.showerror("验证失败", "数据验证失败：\n" + "\n".join(errors))
                    self.status_var.set("导入失败")
                    return
                
                if warnings:
                    warning_msg = "数据验证警告：\n" + "\n".join(warnings)
                    if not messagebox.askyesno("验证警告", warning_msg + "\n\n是否继续导入？"):
                        self.status_var.set("导入已取消")
                        return
            
            # 清洗数据
            if self.clean_var.get():
                df = self.importer.clean_data(df)
            
            # 调用回调函数
            if self.callback:
                self.callback(df)
            
            self.status_var.set(f"导入成功: {len(df)} 行数据")
            messagebox.showinfo("成功", f"数据导入成功！\n共 {len(df)} 行数据")
            
            # 关闭对话框
            self.dialog.destroy()
            
        except Exception as e:
            self.status_var.set(f"导入失败: {e}")
            messagebox.showerror("错误", f"导入失败：{e}")


class BatchImporter:
    """批量导入器"""
    
    def __init__(self, importer):
        """初始化批量导入器
        
        Args:
            importer: DataImporter 实例
        """
        self.importer = importer
        self.results = []
    
    def import_batch(self, file_paths, callback=None):
        """批量导入文件
        
        Args:
            file_paths: 文件路径列表
            callback: 进度回调函数 (current, total, file_name)
            
        Returns:
            dict: 导入结果 {'success': list, 'failed': list}
        """
        results = {'success': [], 'failed': []}
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths):
            try:
                # 调用进度回调
                if callback:
                    callback(i + 1, total, os.path.basename(file_path))
                
                # 导入文件
                df = self.importer.import_file(file_path)
                
                # 验证和清洗
                df = self.importer.clean_data(df)
                
                results['success'].append({
                    'file_path': file_path,
                    'data': df,
                    'rows': len(df)
                })
                
                logger.info(f"批量导入成功: {file_path}")
                
            except Exception as e:
                results['failed'].append({
                    'file_path': file_path,
                    'error': str(e)
                })
                logger.error(f"批量导入失败: {file_path} - {e}")
        
        self.results = results
        return results
    
    def get_summary(self):
        """获取导入摘要
        
        Returns:
            dict: 导入摘要
        """
        success_count = len(self.results.get('success', []))
        failed_count = len(self.results.get('failed', []))
        total_rows = sum(r['rows'] for r in self.results.get('success', []))
        
        return {
            'total_files': success_count + failed_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'total_rows': total_rows
        }


class BatchImportDialog:
    """批量导入对话框"""
    
    def __init__(self, parent, batch_importer, callback):
        """初始化批量导入对话框
        
        Args:
            parent: 父窗口
            batch_importer: BatchImporter 实例
            callback: 导入完成回调函数
        """
        self.parent = parent
        self.batch_importer = batch_importer
        self.callback = callback
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("批量导入")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建界面
        self._create_ui()
    
    def _create_ui(self):
        """创建界面"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="批量导入数据", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        # 文件列表框架
        list_frame = ttk.LabelFrame(main_frame, text="待导入文件", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 文件列表
        self.file_list = tk.Listbox(list_frame, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        self.file_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Button(btn_frame, text="添加文件", command=self._add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="添加文件夹", command=self._add_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空列表", command=self._clear_list).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="移除选中", command=self._remove_selected).pack(side=tk.LEFT)
        
        # 进度框架
        progress_frame = ttk.LabelFrame(main_frame, text="导入进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="就绪")
        self.progress_label.pack()
        
        # 操作按钮
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="开始导入", command=self._start_import).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # 文件路径列表
        self.file_paths = []
    
    def _add_files(self):
        """添加文件"""
        file_types = [
            ("所有支持的格式", "*.xlsx *.xls *.csv *.json *.txt"),
            ("Excel files", "*.xlsx *.xls"),
            ("CSV files", "*.csv"),
            ("JSON files", "*.json"),
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        file_paths = filedialog.askopenfilenames(
            title="选择数据文件",
            filetypes=file_types
        )
        
        for file_path in file_paths:
            if file_path not in self.file_paths:
                self.file_paths.append(file_path)
                self.file_list.insert(tk.END, os.path.basename(file_path))
    
    def _add_folder(self):
        """添加文件夹"""
        folder_path = filedialog.askdirectory(title="选择文件夹")
        if not folder_path:
            return
        
        # 支持的扩展名
        extensions = ['.xlsx', '.xls', '.csv', '.json', '.txt']
        
        for ext in extensions:
            for file_path in Path(folder_path).glob(f"*{ext}"):
                file_path = str(file_path)
                if file_path not in self.file_paths:
                    self.file_paths.append(file_path)
                    self.file_list.insert(tk.END, os.path.basename(file_path))
    
    def _clear_list(self):
        """清空列表"""
        self.file_paths.clear()
        self.file_list.delete(0, tk.END)
    
    def _remove_selected(self):
        """移除选中项"""
        selected = self.file_list.curselection()
        if not selected:
            return
        
        # 从后往前删除，避免索引变化
        for index in reversed(selected):
            self.file_paths.pop(index)
            self.file_list.delete(index)
    
    def _start_import(self):
        """开始导入"""
        if not self.file_paths:
            messagebox.showwarning("警告", "请先添加文件！")
            return
        
        def progress_callback(current, total, file_name):
            """进度回调"""
            self.progress_bar['value'] = (current / total) * 100
            self.progress_label.config(text=f"正在导入: {file_name} ({current}/{total})")
            self.dialog.update()
        
        try:
            # 执行批量导入
            results = self.batch_importer.import_batch(self.file_paths, callback=progress_callback)
            
            # 获取摘要
            summary = self.batch_importer.get_summary()
            
            # 显示结果
            message = f"批量导入完成！\n\n"
            message += f"总文件数: {summary['total_files']}\n"
            message += f"成功: {summary['success_count']}\n"
            message += f"失败: {summary['failed_count']}\n"
            message += f"总行数: {summary['total_rows']}"
            
            if results['failed']:
                message += "\n\n失败文件:\n"
                for failed in results['failed']:
                    message += f"  • {os.path.basename(failed['file_path'])}: {failed['error']}\n"
            
            messagebox.showinfo("导入完成", message)
            
            # 调用回调
            if self.callback:
                self.callback(results)
            
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"批量导入失败：{e}")


# 使用示例
if __name__ == "__main__":
    # 测试数据导入器
    importer = DataImporter()
    
    # 创建测试 CSV 文件
    test_csv = "test_data.csv"
    with open(test_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['姓名', '学号', '成绩'])
        writer.writerow(['张三', '001', 85])
        writer.writerow(['李四', '002', 92])
        writer.writerow(['王五', '003', 78])
    
    # 导入 CSV
    try:
        df = importer.import_file(test_csv)
        print(f"导入成功: {len(df)} 行")
        print(df)
        
        # 验证数据
        is_valid, errors, warnings = importer.validate_data(df, required_columns=['姓名', '学号'])
        print(f"验证结果: valid={is_valid}, errors={errors}, warnings={warnings}")
        
    except Exception as e:
        print(f"导入失败: {e}")
    
    # 清理测试文件
    import os
    os.remove(test_csv)
    
    print("测试完成！")
