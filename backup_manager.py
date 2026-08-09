"""
奖学金评审软件 - 数据备份与恢复模块

功能：
1. 自动备份：每次导入数据或完成评审时自动备份
2. 手动备份：用户可随时手动创建备份
3. 恢复数据：从备份文件恢复评审数据
4. 备份管理：查看、删除、导出备份文件
"""

import os
import json
import shutil
import zipfile
import logging
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

logger = logging.getLogger(__name__)


class BackupManager:
    """数据备份管理器"""
    
    def __init__(self, backup_dir="backups", max_backups=10):
        """初始化备份管理器
        
        Args:
            backup_dir: 备份文件存储目录
            max_backups: 最大备份数量（自动清理旧备份）
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, data, backup_name=None, description=""):
        """创建备份文件
        
        Args:
            data: 要备份的数据（字典格式）
            backup_name: 备份名称（默认使用时间戳）
            description: 备份描述
            
        Returns:
            dict: 备份信息 {'file_path': str, 'timestamp': str, 'size': int}
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if backup_name is None:
            backup_name = f"backup_{timestamp}"
        
        backup_file = self.backup_dir / f"{backup_name}.json"
        
        # 添加元数据
        backup_data = {
            'metadata': {
                'timestamp': timestamp,
                'description': description,
                'version': '1.0'
            },
            'data': data
        }
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            file_size = backup_file.stat().st_size
            
            # 清理旧备份
            self._cleanup_old_backups()
            
            logger.info(f"备份创建成功: {backup_file}")
            return {
                'file_path': str(backup_file),
                'timestamp': timestamp,
                'size': file_size
            }
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            raise
    
    def restore_backup(self, backup_file):
        """从备份文件恢复数据
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            dict: 恢复的数据
        """
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            if 'metadata' not in backup_data or 'data' not in backup_data:
                raise ValueError("备份文件格式不正确")
            
            logger.info(f"从备份恢复数据: {backup_file}")
            return backup_data['data']
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
            raise
    
    def list_backups(self):
        """列出所有备份文件
        
        Returns:
            list: 备份文件信息列表
        """
        backups = []
        for backup_file in self.backup_dir.glob("*.json"):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                metadata = backup_data.get('metadata', {})
                backups.append({
                    'file_path': str(backup_file),
                    'file_name': backup_file.name,
                    'timestamp': metadata.get('timestamp', ''),
                    'description': metadata.get('description', ''),
                    'size': backup_file.stat().st_size
                })
            except Exception as e:
                logger.warning(f"读取备份文件失败 {backup_file}: {e}")
        
        # 按时间戳排序（最新的在前）
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def delete_backup(self, backup_file):
        """删除备份文件
        
        Args:
            backup_file: 备份文件路径
        """
        try:
            Path(backup_file).unlink()
            logger.info(f"删除备份文件: {backup_file}")
        except Exception as e:
            logger.error(f"删除备份文件失败: {e}")
            raise
    
    def export_backup(self, backup_file, export_path):
        """导出备份文件到指定路径
        
        Args:
            backup_file: 备份文件路径
            export_path: 导出路径
        """
        try:
            shutil.copy2(backup_file, export_path)
            logger.info(f"导出备份文件: {backup_file} -> {export_path}")
        except Exception as e:
            logger.error(f"导出备份文件失败: {e}")
            raise
    
    def _cleanup_old_backups(self):
        """清理旧备份文件，保留最新的 max_backups 个"""
        backups = self.list_backups()
        if len(backups) > self.max_backups:
            # 删除最旧的备份
            for backup in backups[self.max_backups:]:
                self.delete_backup(backup['file_path'])


class BackupDialog:
    """备份管理对话框"""
    
    def __init__(self, parent, backup_manager, current_data=None):
        """初始化备份管理对话框
        
        Args:
            parent: 父窗口
            backup_manager: BackupManager 实例
            current_data: 当前评审数据（用于创建备份）
        """
        self.parent = parent
        self.backup_manager = backup_manager
        self.current_data = current_data
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("数据备份与恢复")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 创建界面
        self._create_ui()
        
        # 加载备份列表
        self._refresh_backup_list()
    
    def _create_ui(self):
        """创建界面"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="数据备份与恢复", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="创建备份", command=self._create_backup).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="恢复选中备份", command=self._restore_backup).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除选中备份", command=self._delete_backup).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="导出选中备份", command=self._export_backup).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="刷新", command=self._refresh_backup_list).pack(side=tk.RIGHT)
        
        # 备份列表
        list_frame = ttk.LabelFrame(main_frame, text="备份列表", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建 Treeview
        columns = ("文件名", "时间", "描述", "大小")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
        
        self.tree.column("文件名", width=200)
        self.tree.column("时间", width=150)
        self.tree.column("描述", width=150)
        self.tree.column("大小", width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var).pack(fill=tk.X, pady=(10, 0))
    
    def _refresh_backup_list(self):
        """刷新备份列表"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 加载备份
        backups = self.backup_manager.list_backups()
        for backup in backups:
            # 格式化文件大小
            size = backup['size']
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            # 格式化时间戳
            timestamp = backup['timestamp']
            if timestamp:
                try:
                    dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    pass
            
            self.tree.insert("", "end", values=(
                backup['file_name'],
                timestamp,
                backup['description'],
                size_str
            ))
        
        self.status_var.set(f"共 {len(backups)} 个备份文件")
    
    def _create_backup(self):
        """创建备份"""
        if self.current_data is None:
            messagebox.showwarning("警告", "没有可备份的数据！")
            return
        
        # 输入备份描述
        description = tk.simpledialog.askstring("创建备份", "请输入备份描述（可选）：", parent=self.dialog)
        if description is None:
            return
        
        try:
            result = self.backup_manager.create_backup(
                self.current_data,
                description=description or ""
            )
            messagebox.showinfo("成功", f"备份创建成功！\n文件：{result['file_path']}")
            self._refresh_backup_list()
        except Exception as e:
            messagebox.showerror("错误", f"创建备份失败：{e}")
    
    def _restore_backup(self):
        """恢复备份"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要恢复的备份！")
            return
        
        # 获取选中的备份文件名
        file_name = self.tree.item(selected[0])['values'][0]
        backup_file = self.backup_manager.backup_dir / file_name
        
        # 确认恢复
        if not messagebox.askyesno("确认恢复", f"确定要恢复备份 '{file_name}' 吗？\n\n注意：恢复将覆盖当前数据！"):
            return
        
        try:
            data = self.backup_manager.restore_backup(backup_file)
            messagebox.showinfo("成功", "备份恢复成功！\n请重新加载数据。")
            self.dialog.destroy()
            return data
        except Exception as e:
            messagebox.showerror("错误", f"恢复备份失败：{e}")
            return None
    
    def _delete_backup(self):
        """删除备份"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的备份！")
            return
        
        file_name = self.tree.item(selected[0])['values'][0]
        
        if not messagebox.askyesno("确认删除", f"确定要删除备份 '{file_name}' 吗？\n\n此操作不可撤销！"):
            return
        
        try:
            backup_file = self.backup_manager.backup_dir / file_name
            self.backup_manager.delete_backup(backup_file)
            messagebox.showinfo("成功", "备份删除成功！")
            self._refresh_backup_list()
        except Exception as e:
            messagebox.showerror("错误", f"删除备份失败：{e}")
    
    def _export_backup(self):
        """导出备份"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要导出的备份！")
            return
        
        file_name = self.tree.item(selected[0])['values'][0]
        backup_file = self.backup_manager.backup_dir / file_name
        
        # 选择导出路径
        export_path = filedialog.asksaveasfilename(
            title="导出备份文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=file_name
        )
        
        if not export_path:
            return
        
        try:
            self.backup_manager.export_backup(backup_file, export_path)
            messagebox.showinfo("成功", f"备份导出成功！\n文件：{export_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出备份失败：{e}")


# 自动备份集成示例
class AutoBackupMixin:
    """自动备份混入类，可添加到主程序中"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backup_manager = BackupManager()
        self._last_backup_data = None
    
    def _auto_backup(self, description="自动备份"):
        """自动备份当前数据"""
        try:
            # 获取当前数据
            data = self._get_backup_data()
            
            # 检查数据是否有变化
            if data == self._last_backup_data:
                return
            
            # 创建备份
            self.backup_manager.create_backup(data, description=description)
            self._last_backup_data = data
            
            logger.info(f"自动备份完成: {description}")
        except Exception as e:
            logger.error(f"自动备份失败: {e}")
    
    def _get_backup_data(self):
        """获取需要备份的数据（子类实现）"""
        raise NotImplementedError("子类需要实现 _get_backup_data 方法")
    
    def open_backup_dialog(self):
        """打开备份管理对话框"""
        data = self._get_backup_data()
        BackupDialog(self.root, self.backup_manager, current_data=data)


# 使用示例
if __name__ == "__main__":
    # 测试备份管理器
    backup_mgr = BackupManager(backup_dir="test_backups")
    
    # 创建测试数据
    test_data = {
        "students": [
            {"name": "张三", "id": "001", "score": 85},
            {"name": "李四", "id": "002", "score": 92}
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    # 创建备份
    result = backup_mgr.create_backup(test_data, description="测试备份")
    print(f"备份创建成功: {result}")
    
    # 列出备份
    backups = backup_mgr.list_backups()
    print(f"备份列表: {backups}")
    
    # 恢复备份
    restored_data = backup_mgr.restore_backup(result['file_path'])
    print(f"恢复的数据: {restored_data}")
    
    # 清理测试备份
    import shutil
    shutil.rmtree("test_backups", ignore_errors=True)
    print("测试完成！")
