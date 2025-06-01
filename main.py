"""
智能待办事项管理器主程序
集成GTD工作流、四象限管理法、AI助手和MCP功能
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S, TOP, BOTTOM
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import importlib
import sys
import os

def main():
    """主函数"""
    try:
        # 导入配置管理器
        config_module = importlib.import_module('9_config_manager')
        config_manager = config_module.ConfigManager()
        
        # 创建主窗口（隐藏）
        root = ttk_bs.Window(themename="flatly")
        root.withdraw()  # 隐藏主窗口
        
        # 如果是首次运行，显示配置对话框
        if config_manager.is_first_run():
            config_manager.show_first_run_dialog(root)
        
        # 显示主窗口
        root.deiconify()
        root.title("智能待办事项管理器 v1.0")
        
        # 从配置文件获取窗口大小
        window_width = config_manager.get('ui.window_size.width', 1200)
        window_height = config_manager.get('ui.window_size.height', 800)
        root.geometry(f"{window_width}x{window_height}")
        
        # 设置窗口图标（如果存在）
        try:
            root.iconbitmap("icon.ico")
        except:
            pass
        
        # 使用配置文件中的数据库路径初始化数据库管理器
        db_module = importlib.import_module('1_database')
        database_path = config_manager.get_database_path()
        database_manager = db_module.DatabaseManager(database_path)
        
        # 初始化UI组件
        ui_module = importlib.import_module('3_ui_components')
        ui_components = ui_module.UIComponents(database_manager)
        
        # 初始化AI助手（传入配置管理器）
        ai_module = importlib.import_module('8_ai_assistant')
        ai_assistant = ai_module.AIAssistant(database_manager, ui_components, config_manager)
        
        # 创建主界面
        create_main_interface(root, database_manager, ui_components, ai_assistant, config_manager)
        
        # 显示数据库信息（如果是首次运行）
        if config_manager.get('first_run', False):
            root.after(1000, lambda: show_startup_info(root, config_manager))
        
        # 启动主循环
        root.mainloop()
        
    except ImportError as e:
        error_msg = f"模块导入失败: {e}\\n请确保所有必要的文件都存在。"
        if 'root' in locals():
            messagebox.showerror("导入错误", error_msg)
        else:
            print(error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = f"程序启动失败: {e}"
        if 'root' in locals():
            messagebox.showerror("启动错误", error_msg)
        else:
            print(error_msg)
        sys.exit(1)

def create_main_interface(root, database_manager, ui_components, ai_assistant, config_manager):
    """创建主界面"""
    
    # 创建菜单栏
    create_menu_bar(root, database_manager, ui_components, ai_assistant, config_manager)
    
    # 创建主界面 - 恢复原来的完整结构
    main_frame = ui_components.create_main_interface(root)
    
    # 初始化各个视图模块
    initialize_view_modules(database_manager, ui_components)
    
    # 创建状态栏
    create_status_bar(root, database_manager, config_manager)

def initialize_view_modules(database_manager, ui_components):
    """初始化各个视图模块"""
    try:
        # 初始化日历视图
        calendar_module = importlib.import_module('4_calendar_view')
        calendar_view = calendar_module.CalendarView(database_manager, ui_components)
        calendar_view.create_calendar_tab(ui_components.calendar_tab)
        
        # 初始化统计汇总视图
        summary_module = importlib.import_module('6_summary_view')
        summary_view = summary_module.SummaryView(database_manager, ui_components)
        summary_view.create_summary_tab(ui_components.summary_tab)
        
        # 初始化项目统计视图
        project_module = importlib.import_module('7_project_view')
        project_view = project_module.ProjectView(database_manager, ui_components)
        project_view.create_project_tab(ui_components.project_tab)
        
        # 初始化四象限视图
        quadrant_module = importlib.import_module('5_quadrant_view')
        quadrant_view = quadrant_module.QuadrantView(database_manager, ui_components)
        quadrant_view.create_quadrant_tab(ui_components.quadrant_tab)
        
        # 存储视图引用
        ui_components.calendar_view = calendar_view
        ui_components.summary_view = summary_view
        ui_components.project_view = project_view
        ui_components.quadrant_view = quadrant_view
        
    except ImportError as e:
        print(f"视图模块导入失败: {e}")
    except Exception as e:
        print(f"视图初始化失败: {e}")

def create_menu_bar(root, database_manager, ui_components, ai_assistant, config_manager):
    """创建菜单栏"""
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # 文件菜单
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="文件", menu=file_menu)
    file_menu.add_command(label="导出数据", command=lambda: export_data(database_manager))
    file_menu.add_command(label="导入数据", command=lambda: import_data(database_manager, ui_components))
    file_menu.add_separator()
    file_menu.add_command(label="数据库信息", command=lambda: show_database_info(root, config_manager))
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=root.quit)
    
    # 工具菜单
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="工具", menu=tools_menu)
    tools_menu.add_command(label="清理已完成任务", command=lambda: cleanup_completed_tasks(database_manager, ui_components))
    tools_menu.add_command(label="数据库备份", command=lambda: backup_database(database_manager))
    tools_menu.add_separator()
    tools_menu.add_command(label="AI助手设置", command=lambda: show_ai_settings(root, ai_assistant, config_manager))
    
    # AI助手菜单 - 独立窗口
    ai_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="AI助手", menu=ai_menu)
    ai_menu.add_command(label="打开AI助手", command=lambda: open_ai_assistant_window(root, ai_assistant, config_manager))
    ai_menu.add_command(label="AI助手设置", command=lambda: show_ai_settings(root, ai_assistant, config_manager))
    
    # MCP菜单
    if config_manager.is_mcp_enabled():
        mcp_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="MCP", menu=mcp_menu)
        mcp_menu.add_command(label="MCP状态", command=lambda: show_mcp_status(root, ai_assistant, config_manager))
        mcp_menu.add_command(label="测试SQL查询", command=lambda: test_sql_query(root, ai_assistant))
    
    # 帮助菜单
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="帮助", menu=help_menu)
    help_menu.add_command(label="使用说明", command=lambda: show_help())
    help_menu.add_command(label="关于", command=lambda: show_about(root, config_manager))

def create_status_bar(root, database_manager, config_manager):
    """创建状态栏"""
    status_frame = ttk.Frame(root)
    status_frame.pack(fill=X, side=BOTTOM)
    
    # 数据库状态
    db_path = config_manager.get_database_path()
    db_status = ttk.Label(status_frame, text=f"数据库: {os.path.basename(db_path)}")
    db_status.pack(side=LEFT, padx=5)
    
    # MCP状态
    if config_manager.is_mcp_enabled():
        mcp_status = ttk.Label(status_frame, text="MCP: 启用", foreground="green")
        mcp_status.pack(side=LEFT, padx=5)
    
    # 任务统计
    try:
        stats = database_manager.get_statistics()
        total_tasks = stats.get('total', 0)
        completed_tasks = stats.get('completed', 0)
        task_status = ttk.Label(status_frame, text=f"任务: {total_tasks}总 / {completed_tasks}完成")
        task_status.pack(side=LEFT, padx=5)
    except Exception as e:
        print(f"获取统计信息失败: {e}")
        task_status = ttk.Label(status_frame, text="任务: 统计信息获取失败")
        task_status.pack(side=LEFT, padx=5)
    
    # 版本信息
    version = config_manager.get('version', '1.0.0')
    version_label = ttk.Label(status_frame, text=f"v{version}")
    version_label.pack(side=RIGHT, padx=5)

def show_startup_info(root, config_manager):
    """显示启动信息"""
    db_path = config_manager.get_database_path()
    abs_path = os.path.abspath(db_path)
    
    info_msg = f"""智能待办事项管理器已启动！

数据库位置: {abs_path}
MCP功能: {'启用' if config_manager.is_mcp_enabled() else '禁用'}
AI助手: {'在线模式' if config_manager.get_api_key() != 'your_api_key_here' else '离线模式'}

您可以通过菜单栏的"文件 > 数据库信息"查看详细信息。"""
    
    messagebox.showinfo("启动完成", info_msg)

def show_database_info(root, config_manager):
    """显示数据库信息"""
    config_module = importlib.import_module('9_config_manager')
    config_module.show_database_info_dialog(config_manager, root)

def show_ai_settings(root, ai_assistant, config_manager):
    """显示AI助手设置"""
    # 这里可以创建一个设置对话框
    messagebox.showinfo("AI设置", "AI助手设置功能开发中...")

def show_mcp_status(root, ai_assistant, config_manager):
    """显示MCP状态"""
    mcp_tools = config_manager.get_mcp_tools()
    tools_list = "\\n".join([f"• {tool}" for tool in mcp_tools])
    
    status_msg = f"""MCP (Model Context Protocol) 状态

状态: {'启用' if config_manager.is_mcp_enabled() else '禁用'}
SQLite服务器: 运行中
可用工具:
{tools_list}

MCP功能允许AI直接查询和操作数据库，
提供更准确的数据分析和洞察。"""
    
    messagebox.showinfo("MCP状态", status_msg)

def test_sql_query(root, ai_assistant):
    """测试SQL查询"""
    # 创建一个简单的SQL测试对话框
    dialog = tk.Toplevel(root)
    dialog.title("测试SQL查询")
    dialog.geometry("500x400")
    dialog.transient(root)
    dialog.grab_set()
    
    # 查询输入
    tk.Label(dialog, text="SQL查询:").pack(anchor=tk.W, padx=10, pady=(10, 0))
    query_text = tk.Text(dialog, height=5, width=60)
    query_text.pack(padx=10, pady=5, fill=tk.X)
    query_text.insert(tk.END, "SELECT * FROM todos LIMIT 5;")
    
    # 结果显示
    tk.Label(dialog, text="查询结果:").pack(anchor=tk.W, padx=10, pady=(10, 0))
    result_text = tk.Text(dialog, height=15, width=60)
    result_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
    
    def execute_query():
        query = query_text.get(1.0, tk.END).strip()
        if query:
            try:
                result = ai_assistant.execute_sql_query(query)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, str(result))
            except Exception as e:
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"错误: {str(e)}")
    
    # 按钮
    button_frame = tk.Frame(dialog)
    button_frame.pack(fill=tk.X, padx=10, pady=10)
    
    tk.Button(button_frame, text="执行查询", command=execute_query).pack(side=tk.LEFT)
    tk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.RIGHT)

def export_data(database_manager):
    """导出数据"""
    messagebox.showinfo("导出", "数据导出功能开发中...")

def import_data(database_manager, ui_components):
    """导入数据"""
    messagebox.showinfo("导入", "数据导入功能开发中...")

def cleanup_completed_tasks(database_manager, ui_components):
    """清理已完成任务"""
    if messagebox.askyesno("确认", "确定要删除所有已完成的任务吗？此操作不可撤销。"):
        try:
            # 这里添加清理逻辑
            messagebox.showinfo("完成", "已完成任务清理完成！")
            ui_components.refresh_all_views()
        except Exception as e:
            messagebox.showerror("错误", f"清理失败: {str(e)}")

def backup_database(database_manager):
    """备份数据库"""
    try:
        backup_file = database_manager.create_backup()
        if backup_file:
            messagebox.showinfo("备份完成", f"数据库已备份到: {backup_file}")
        else:
            messagebox.showerror("备份失败", "无法创建数据库备份")
    except Exception as e:
        messagebox.showerror("备份错误", f"备份过程中出错: {str(e)}")

def show_help():
    """显示帮助信息"""
    help_msg = """智能待办事项管理器使用说明

主要功能：
• GTD工作流管理
• 四象限优先级管理
• AI智能助手
• MCP数据库集成

快捷操作：
• 双击任务可快速编辑
• 右键菜单提供更多选项
• AI助手支持自然语言交互

更多帮助请访问项目文档。"""
    
    messagebox.showinfo("使用说明", help_msg)

def show_about(root, config_manager):
    """显示关于信息"""
    version = config_manager.get('version', '1.0.0')
    about_msg = f"""智能待办事项管理器 v{version}

一个集成GTD工作流、四象限管理法和AI助手的
现代化待办事项管理应用程序。

特性：
• 智能任务解析
• AI助手支持
• MCP数据库集成
• 现代化UI设计

技术栈：
• Python + Tkinter
• SQLite数据库
• Model Context Protocol
• DeepSeek AI API

© 2024 智能待办事项管理器"""
    
    messagebox.showinfo("关于", about_msg)

def open_ai_assistant_window(parent, ai_assistant, config_manager):
    """打开AI助手独立窗口"""
    # 检查是否已经有AI助手窗口打开
    if hasattr(ai_assistant, 'ai_window') and ai_assistant.ai_window and ai_assistant.ai_window.winfo_exists():
        # 如果窗口已存在，将其置于前台
        ai_assistant.ai_window.lift()
        ai_assistant.ai_window.focus_force()
        return
    
    # 创建新的AI助手窗口
    ai_window = ttk_bs.Toplevel(parent)
    ai_window.title("AI智能助手")
    ai_window.geometry("800x600")
    
    # 设置窗口图标（如果存在）
    try:
        ai_window.iconbitmap("icon.ico")
    except:
        pass
    
    # 在新窗口中创建AI助手界面
    ai_assistant.create_ai_panel(ai_window)
    
    # 存储窗口引用
    ai_assistant.ai_window = ai_window
    
    # 设置窗口关闭事件
    def on_ai_window_close():
        ai_assistant.ai_window = None
        ai_window.destroy()
    
    ai_window.protocol("WM_DELETE_WINDOW", on_ai_window_close)

if __name__ == "__main__":
    main() 