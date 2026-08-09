"""
奖学金评审软件 - 自动保存模块

功能：
1. 定时自动保存评审进度
2. 可配置保存间隔
3. 保存前数据验证
4. 保存状态提示
5. 崩溃恢复支持
"""

import os
import json
import time
import threading
import logging
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger(__name__)


class AutoSaveManager:
    """自动保存管理器"""
    
    def __init__(self, save_dir="autosave", save_interval=300):
        """初始化自动保存管理器
        
        Args:
            save_dir: 自动保存文件目录
            save_interval: 自动保存间隔（秒），默认 5 分钟
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        
        self.save_interval = save_interval
        self.is_running = False
        self._timer = None
        self._save_callback = None
        self._last_save_time = None
        self._last_save_data = None
        self._save_count = 0
        
        # 状态回调
        self._status_callback = None
        
    def start(self, save_callback, status_callback=None):
        """启动自动保存
        
        Args:
            save_callback: 保存回调函数，返回要保存的数据
            status_callback: 状态回调函数，用于显示保存状态
        """
        if self.is_running:
            logger.warning("自动保存已在运行")
            return
        
        self._save_callback = save_callback
        self._status_callback = status_callback
        self.is_running = True
        
        # 启动定时器
        self._schedule_next_save()
        
        logger.info(f"自动保存已启动，间隔 {self.save_interval} 秒")
        self._update_status("自动保存已启动")
    
    def stop(self):
        """停止自动保存"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        logger.info("自动保存已停止")
        self._update_status("自动保存已停止")
    
    def save_now(self, description="手动保存"):
        """立即保存
        
        Args:
            description: 保存描述
        """
        if not self._save_callback:
            logger.warning("未设置保存回调函数")
            return
        
        try:
            # 获取数据
            data = self._save_callback()
            
            # 检查数据是否有变化
            if data == self._last_save_data:
                logger.debug("数据无变化，跳过保存")
                return
            
            # 保存数据
            save_file = self._create_save_file(data, description)
            
            # 更新状态
            self._last_save_time = datetime.now()
            self._last_save_data = data
            self._save_count += 1
            
            logger.info(f"自动保存完成: {save_file}")
            self._update_status(f"已保存 ({self._save_count} 次)")
            
            # 清理旧的自动保存文件
            self._cleanup_old_saves()
            
            return save_file
        except Exception as e:
            logger.error(f"自动保存失败: {e}")
            self._update_status(f"保存失败: {e}")
            return None
    
    def _schedule_next_save(self):
        """调度下一次保存"""
        if not self.is_running:
            return
        
        self._timer = threading.Timer(self.save_interval, self._on_timer)
        self._timer.daemon = True
        self._timer.start()
    
    def _on_timer(self):
        """定时器回调"""
        if not self.is_running:
            return
        
        # 执行保存
        self.save_now(description="定时自动保存")
        
        # 调度下一次保存
        self._schedule_next_save()
    
    def _create_save_file(self, data, description):
        """创建保存文件
        
        Args:
            data: 要保存的数据
            description: 保存描述
            
        Returns:
            str: 保存文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_file = self.save_dir / f"autosave_{timestamp}.json"
        
        save_data = {
            'metadata': {
                'timestamp': timestamp,
                'description': description,
                'version': '1.0',
                'save_count': self._save_count
            },
            'data': data
        }
        
        with open(save_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        return str(save_file)
    
    def _cleanup_old_saves(self, max_saves=5):
        """清理旧的自动保存文件
        
        Args:
            max_saves: 最大保存文件数
        """
        saves = sorted(self.save_dir.glob("autosave_*.json"), reverse=True)
        if len(saves) > max_saves:
            for save in saves[max_saves:]:
                try:
                    save.unlink()
                    logger.debug(f"删除旧的自动保存文件: {save}")
                except Exception as e:
                    logger.warning(f"删除旧保存文件失败: {e}")
    
    def _update_status(self, message):
        """更新状态"""
        if self._status_callback:
            try:
                self._status_callback(message)
            except Exception:
                pass
    
    def get_latest_save(self):
        """获取最新的自动保存文件
        
        Returns:
            dict: 保存数据，如果没有则返回 None
        """
        saves = sorted(self.save_dir.glob("autosave_*.json"), reverse=True)
        if not saves:
            return None
        
        try:
            with open(saves[0], 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            return save_data
        except Exception as e:
            logger.error(f"读取自动保存文件失败: {e}")
            return None
    
    def list_saves(self):
        """列出所有自动保存文件
        
        Returns:
            list: 保存文件信息列表
        """
        saves = []
        for save_file in sorted(self.save_dir.glob("autosave_*.json"), reverse=True):
            try:
                with open(save_file, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                
                metadata = save_data.get('metadata', {})
                saves.append({
                    'file_path': str(save_file),
                    'file_name': save_file.name,
                    'timestamp': metadata.get('timestamp', ''),
                    'description': metadata.get('description', ''),
                    'size': save_file.stat().st_size
                })
            except Exception as e:
                logger.warning(f"读取保存文件失败 {save_file}: {e}")
        
        return saves


class AutoSaveStatusBar:
    """自动保存状态栏组件"""
    
    def __init__(self, parent, auto_save_manager):
        """初始化状态栏
        
        Args:
            parent: 父窗口
            auto_save_manager: AutoSaveManager 实例
        """
        self.parent = parent
        self.auto_save_manager = auto_save_manager
        
        # 创建状态栏
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        # 状态标签
        self.status_label = ttk.Label(self.frame, text="自动保存: 未启动")
        self.status_label.pack(side=tk.LEFT)
        
        # 按钮
        ttk.Button(self.frame, text="立即保存", command=self._save_now).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(self.frame, text="设置", command=self._show_settings).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 更新状态
        self._update_status("就绪")
    
    def _save_now(self):
        """立即保存"""
        result = self.auto_save_manager.save_now(description="用户手动保存")
        if result:
            messagebox.showinfo("保存成功", f"数据已保存到：\n{result}")
    
    def _show_settings(self):
        """显示设置对话框"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("自动保存设置")
        dialog.geometry("300x200")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 保存间隔设置
        ttk.Label(dialog, text="自动保存间隔（分钟）：").pack(pady=(20, 5))
        
        interval_var = tk.StringVar(value=str(self.auto_save_manager.save_interval // 60))
        interval_entry = ttk.Entry(dialog, textvariable=interval_var, width=10)
        interval_entry.pack()
        
        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def apply_settings():
            try:
                minutes = int(interval_var.get())
                if minutes < 1:
                    raise ValueError("间隔不能小于 1 分钟")
                
                self.auto_save_manager.save_interval = minutes * 60
                messagebox.showinfo("成功", f"自动保存间隔已设置为 {minutes} 分钟")
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("错误", f"无效的间隔值：{e}")
        
        ttk.Button(btn_frame, text="应用", command=apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _update_status(self, message):
        """更新状态显示"""
        self.status_label.config(text=f"自动保存: {message}")
    
    def set_status(self, message):
        """外部设置状态"""
        self._update_status(message)


class CrashRecoveryDialog:
    """崩溃恢复对话框"""
    
    def __init__(self, parent, auto_save_manager, restore_callback):
        """初始化崩溃恢复对话框
        
        Args:
            parent: 父窗口
            auto_save_manager: AutoSaveManager 实例
            restore_callback: 恢复回调函数
        """
        self.parent = parent
        self.auto_save_manager = auto_save_manager
        self.restore_callback = restore_callback
        
        # 检查是否有自动保存文件
        latest_save = auto_save_manager.get_latest_save()
        if latest_save is None:
            return
        
        # 显示恢复对话框
        self._show_recovery_dialog(latest_save)
    
    def _show_recovery_dialog(self, save_data):
        """显示恢复对话框"""
        metadata = save_data.get('metadata', {})
        timestamp = metadata.get('timestamp', '')
        description = metadata.get('description', '')
        
        # 格式化时间
        if timestamp:
            try:
                dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        message = f"检测到自动保存的数据：\n\n"
        message += f"时间：{timestamp}\n"
        message += f"描述：{description}\n\n"
        message += "是否恢复此数据？"
        
        if messagebox.askyesno("数据恢复", message):
            try:
                data = save_data.get('data')
                if data and self.restore_callback:
                    self.restore_callback(data)
                    messagebox.showinfo("成功", "数据恢复成功！")
            except Exception as e:
                messagebox.showerror("错误", f"数据恢复失败：{e}")


# 集成示例
class AutoSaveMixin:
    """自动保存混入类"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 初始化自动保存管理器
        self.auto_save_manager = AutoSaveManager(save_interval=300)  # 5分钟
        
        # 启动自动保存
        self.auto_save_manager.start(
            save_callback=self._get_save_data,
            status_callback=self._on_auto_save_status
        )
        
        # 创建状态栏
        self.auto_save_status_bar = AutoSaveStatusBar(self.root, self.auto_save_manager)
        
        # 检查崩溃恢复
        CrashRecoveryDialog(self.root, self.auto_save_manager, self._restore_data)
    
    def _get_save_data(self):
        """获取要保存的数据（子类实现）"""
        raise NotImplementedError("子类需要实现 _get_save_data 方法")
    
    def _restore_data(self, data):
        """恢复数据（子类实现）"""
        raise NotImplementedError("子类需要实现 _restore_data 方法")
    
    def _on_auto_save_status(self, message):
        """自动保存状态回调"""
        if hasattr(self, 'auto_save_status_bar'):
            self.auto_save_status_bar.set_status(message)
    
    def save_progress(self):
        """手动保存进度"""
        return self.auto_save_manager.save_now(description="手动保存")


# 使用示例
if __name__ == "__main__":
    # 测试自动保存管理器
    auto_save = AutoSaveManager(save_dir="test_autosave", save_interval=5)
    
    # 模拟数据
    test_data = {"counter": 0}
    
    def get_data():
        test_data["counter"] += 1
        return test_data
    
    # 启动自动保存
    auto_save.start(save_callback=get_data)
    
    # 等待一段时间
    print("自动保存已启动，等待 10 秒...")
    time.sleep(10)
    
    # 立即保存
    auto_save.save_now(description="测试保存")
    
    # 列出保存文件
    saves = auto_save.list_saves()
    print(f"保存文件列表: {saves}")
    
    # 停止自动保存
    auto_save.stop()
    
    # 清理测试文件
    import shutil
    shutil.rmtree("test_autosave", ignore_errors=True)
    print("测试完成！")
