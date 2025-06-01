"""
配置管理器模块
负责应用程序配置的读取、写入和管理
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = {}
        self.default_config = {
            "database": {
                "path": "./todo_database.db",
                "backup_path": "./backups/",
                "auto_backup": True,
                "backup_interval_hours": 24
            },
            "ai_assistant": {
                "api_key": "your_api_key_here",
                "api_url": "https://api.deepseek.com/v1/chat/completions",
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 1000,
                "offline_mode": True
            },
            "ui": {
                "theme": "default",
                "window_size": {
                    "width": 1200,
                    "height": 800
                },
                "auto_save": True
            },
            "mcp": {
                "enabled": True,
                "sqlite_server": {
                    "enabled": True,
                    "tools": [
                        "read_query",
                        "write_query", 
                        "create_table",
                        "list_tables",
                        "describe_table",
                        "append_insight"
                    ]
                }
            },
            "first_run": True,
            "version": "1.0.0"
        }
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # 合并默认配置，确保所有必要的键都存在
                self.config = self._merge_config(self.default_config, self.config)
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = self.default_config.copy()
    
    def _merge_config(self, default, user):
        """递归合并配置，确保所有默认键都存在"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key_path, default=None):
        """获取配置值，支持点分隔的路径"""
        keys = key_path.split('.')
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path, value):
        """设置配置值，支持点分隔的路径"""
        keys = key_path.split('.')
        config = self.config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self.save_config()
    
    def is_first_run(self):
        """检查是否是首次运行"""
        return self.get('first_run', True)
    
    def set_first_run_complete(self):
        """标记首次运行完成"""
        self.set('first_run', False)
    
    def get_database_path(self):
        """获取数据库路径"""
        return self.get('database.path', './todo_database.db')
    
    def set_database_path(self, path):
        """设置数据库路径"""
        self.set('database.path', path)
    
    def get_api_key(self):
        """获取API密钥"""
        return self.get('ai_assistant.api_key', 'your_api_key_here')
    
    def set_api_key(self, api_key):
        """设置API密钥"""
        self.set('ai_assistant.api_key', api_key)
    
    def is_mcp_enabled(self):
        """检查MCP是否启用"""
        return self.get('mcp.enabled', True)
    
    def get_mcp_tools(self):
        """获取MCP工具列表"""
        return self.get('mcp.sqlite_server.tools', [])
    
    def create_backup(self):
        """创建配置文件备份"""
        try:
            backup_dir = "config_backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{backup_dir}/config_backup_{timestamp}.json"
            shutil.copy2(self.config_file, backup_file)
            return backup_file
        except Exception as e:
            print(f"创建配置备份失败: {e}")
            return None
    
    def show_first_run_dialog(self, parent=None):
        """显示首次运行对话框"""
        if not self.is_first_run():
            return
        
        dialog = FirstRunDialog(parent, self)
        dialog.show()

class FirstRunDialog:
    """首次运行配置对话框"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.dialog = None
        self.db_path_var = None
        self.api_key_var = None
        
    def show(self):
        """显示对话框"""
        self.dialog = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.dialog.title("智能待办事项管理器 - 首次运行配置")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        
        # 使对话框居中
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        
        if self.parent:
            self.dialog.wait_window()
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(main_frame, text="欢迎使用智能待办事项管理器！", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 说明文本
        info_text = """这是您第一次运行此应用程序。请配置以下设置：

• 数据库位置：您的待办事项数据将存储在这里
• API密钥：用于AI助手功能（可选）
• MCP功能：启用SQLite MCP服务器以增强AI能力"""
        
        info_label = tk.Label(main_frame, text=info_text, justify=tk.LEFT, 
                             wraplength=550, font=("Arial", 10))
        info_label.pack(pady=(0, 20))
        
        # 数据库路径配置
        db_frame = tk.LabelFrame(main_frame, text="数据库配置", padx=10, pady=10)
        db_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(db_frame, text="数据库文件路径:").pack(anchor=tk.W)
        
        path_frame = tk.Frame(db_frame)
        path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.db_path_var = tk.StringVar(value=self.config_manager.get_database_path())
        path_entry = tk.Entry(path_frame, textvariable=self.db_path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = tk.Button(path_frame, text="浏览", command=self.browse_database_path)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 显示当前工作目录
        current_dir = os.getcwd()
        tk.Label(db_frame, text=f"当前工作目录: {current_dir}", 
                font=("Arial", 8), fg="gray").pack(anchor=tk.W, pady=(5, 0))
        
        # API密钥配置
        api_frame = tk.LabelFrame(main_frame, text="AI助手配置（可选）", padx=10, pady=10)
        api_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(api_frame, text="DeepSeek API密钥:").pack(anchor=tk.W)
        self.api_key_var = tk.StringVar(value=self.config_manager.get_api_key())
        api_entry = tk.Entry(api_frame, textvariable=self.api_key_var, width=60, show="*")
        api_entry.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(api_frame, text="留空将使用离线模式（基本功能）", 
                font=("Arial", 8), fg="gray").pack(anchor=tk.W, pady=(5, 0))
        
        # MCP配置
        mcp_frame = tk.LabelFrame(main_frame, text="MCP功能配置", padx=10, pady=10)
        mcp_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.mcp_enabled_var = tk.BooleanVar(value=self.config_manager.is_mcp_enabled())
        mcp_check = tk.Checkbutton(mcp_frame, text="启用SQLite MCP服务器", 
                                  variable=self.mcp_enabled_var)
        mcp_check.pack(anchor=tk.W)
        
        mcp_info = """MCP (Model Context Protocol) 功能说明：
• 允许AI直接查询和操作数据库
• 提供更准确的数据分析和洞察
• 支持复杂的SQL查询和业务智能功能"""
        
        tk.Label(mcp_frame, text=mcp_info, justify=tk.LEFT, 
                font=("Arial", 8), fg="gray").pack(anchor=tk.W, pady=(5, 0))
        
        # 按钮
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        cancel_btn = tk.Button(button_frame, text="取消", command=self.cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ok_btn = tk.Button(button_frame, text="确定", command=self.save_and_close, 
                          bg="#4CAF50", fg="white")
        ok_btn.pack(side=tk.RIGHT)
    
    def browse_database_path(self):
        """浏览数据库文件路径"""
        file_path = filedialog.asksaveasfilename(
            title="选择数据库文件位置",
            defaultextension=".db",
            filetypes=[("SQLite数据库", "*.db"), ("所有文件", "*.*")]
        )
        if file_path:
            self.db_path_var.set(file_path)
    
    def save_and_close(self):
        """保存配置并关闭对话框"""
        try:
            # 验证数据库路径
            db_path = self.db_path_var.get().strip()
            if not db_path:
                messagebox.showerror("错误", "请指定数据库文件路径")
                return
            
            # 确保数据库目录存在
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            # 保存配置
            self.config_manager.set_database_path(db_path)
            
            api_key = self.api_key_var.get().strip()
            if api_key and api_key != "your_api_key_here":
                self.config_manager.set_api_key(api_key)
            
            self.config_manager.set('mcp.enabled', self.mcp_enabled_var.get())
            self.config_manager.set_first_run_complete()
            
            # 显示配置完成信息
            info_msg = f"""配置已保存！

数据库位置: {db_path}
API密钥: {'已设置' if api_key and api_key != 'your_api_key_here' else '未设置（离线模式）'}
MCP功能: {'启用' if self.mcp_enabled_var.get() else '禁用'}

应用程序将使用这些设置启动。"""
            
            messagebox.showinfo("配置完成", info_msg)
            
            if self.dialog:
                self.dialog.destroy()
                
        except Exception as e:
            messagebox.showerror("错误", f"保存配置时出错: {str(e)}")
    
    def cancel(self):
        """取消配置"""
        if messagebox.askyesno("确认", "确定要取消配置吗？应用程序将使用默认设置。"):
            if self.dialog:
                self.dialog.destroy()

def show_database_info_dialog(config_manager, parent=None):
    """显示数据库信息对话框"""
    dialog = tk.Toplevel(parent) if parent else tk.Tk()
    dialog.title("数据库信息")
    dialog.geometry("500x300")
    dialog.resizable(False, False)
    
    if parent:
        dialog.transient(parent)
        dialog.grab_set()
    
    main_frame = tk.Frame(dialog, padx=20, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    title_label = tk.Label(main_frame, text="数据库信息", font=("Arial", 14, "bold"))
    title_label.pack(pady=(0, 15))
    
    # 数据库路径信息
    db_path = config_manager.get_database_path()
    abs_path = os.path.abspath(db_path)
    
    info_text = f"""当前数据库配置：

文件路径: {db_path}
绝对路径: {abs_path}
文件大小: {get_file_size(abs_path)}
最后修改: {get_last_modified(abs_path)}
MCP功能: {'启用' if config_manager.is_mcp_enabled() else '禁用'}

数据库功能：
• 存储所有待办事项数据
• 支持GTD工作流和四象限管理
• 提供AI助手数据查询接口
• 自动备份和数据恢复"""
    
    info_label = tk.Label(main_frame, text=info_text, justify=tk.LEFT, 
                         font=("Arial", 10))
    info_label.pack(anchor=tk.W)
    
    # 按钮
    button_frame = tk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(20, 0))
    
    def open_db_folder():
        """打开数据库文件夹"""
        import subprocess
        import platform
        
        folder_path = os.path.dirname(abs_path)
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", folder_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", folder_path])
            else:  # Linux
                subprocess.run(["xdg-open", folder_path])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
    
    open_folder_btn = tk.Button(button_frame, text="打开文件夹", command=open_db_folder)
    open_folder_btn.pack(side=tk.LEFT)
    
    close_btn = tk.Button(button_frame, text="关闭", command=dialog.destroy)
    close_btn.pack(side=tk.RIGHT)
    
    if parent:
        dialog.wait_window()

def get_file_size(file_path):
    """获取文件大小"""
    try:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        else:
            return "文件不存在"
    except Exception:
        return "未知"

def get_last_modified(file_path):
    """获取文件最后修改时间"""
    try:
        if os.path.exists(file_path):
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        else:
            return "文件不存在"
    except Exception:
        return "未知" 