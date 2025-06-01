"""
智能待办事项管理器 - 主应用程序
整合所有功能模块的主入口
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S, TOP
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import importlib
import os

# 动态导入各个功能模块
database_module = importlib.import_module('1_database')
reminder_module = importlib.import_module('2_reminder_service')
ui_module = importlib.import_module('3_ui_components')
calendar_module = importlib.import_module('4_calendar_view')
quadrant_module = importlib.import_module('5_quadrant_view')
summary_module = importlib.import_module('6_summary_view')
project_module = importlib.import_module('7_project_view')

# 导入新的AI功能模块
ai_assistant_module = importlib.import_module('8_ai_assistant')
config_module = importlib.import_module('9_config_manager')

# 导入角色管理模块
role_module = importlib.import_module('role_manager')

DatabaseManager = database_module.DatabaseManager
ReminderService = reminder_module.ReminderService
UIComponents = ui_module.UIComponents
CalendarView = calendar_module.CalendarView
QuadrantView = quadrant_module.QuadrantView
SummaryView = summary_module.SummaryView
ProjectView = project_module.ProjectView
AIAssistant = ai_assistant_module.AIAssistant
ConfigManager = config_module.ConfigManager
RoleManager = role_module.RoleManager

class TodoApp:
    def __init__(self):
        """初始化主应用程序"""
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化角色管理器
        self.role_manager = RoleManager()
        
        # 显示首次运行对话框（如果是第一次运行）
        if self.config_manager.is_first_run():
            self.config_manager.show_first_run_dialog()
            self.config_manager.set_first_run_complete()
        
        # 创建主窗口 - 紫色主题
        self.root = ttk_bs.Window(themename="vapor")
        self.root.title("智能待办事项管理器")
        
        # 从配置获取窗口大小
        window_config = self.config_manager.get('ui.window_size', {'width': 1400, 'height': 900})
        self.root.geometry(f"{window_config['width']}x{window_config['height']}")
        self.root.minsize(1200, 700)
        
        # 设置紫色渐变背景
        self.setup_gradient_background()
        
        # 初始化各个管理器
        db_path = self.config_manager.get_database_path()
        self.db_manager = DatabaseManager(db_path)
        self.reminder_service = ReminderService(self.db_manager)
        self.ui_components = UIComponents(self.db_manager, self.role_manager)  # 传递角色管理器
        self.calendar_view = CalendarView(self.db_manager, self.ui_components)
        self.quadrant_view = QuadrantView(self.db_manager, self.ui_components)
        self.summary_view = SummaryView(self.db_manager, self.ui_components)
        self.project_view = ProjectView(self.db_manager, self.ui_components)
        
        # 初始化AI助手，传递角色管理器
        self.ai_assistant = AIAssistant(self.db_manager, self.ui_components, self.config_manager, self.role_manager)
        
        # 创建界面
        self.create_widgets()
        
        # 启动提醒服务
        self.reminder_service.start_reminder_thread()
        
        # 加载数据
        self.refresh_all_views()
        
        # 检查用户角色配置（在主窗口创建后）
        self.root.after(500, self.check_role_configuration)
    
    def setup_gradient_background(self):
        """设置紫色渐变背景"""
        style = ttk_bs.Style()
        # 设置紫色渐变主题
        style.configure('Gradient.TFrame', background='#2D1B69')
        style.configure('Card.TFrame', background='rgba(139, 69, 255, 0.1)')
    
    def create_widgets(self):
        """创建主界面"""
        # 创建主框架
        main_frame = ttk_bs.Frame(self.root, style='Gradient.TFrame')
        main_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # 创建标题
        title_label = ttk_bs.Label(
            main_frame, 
            text="智能待办事项管理器", 
            font=("Microsoft YaHei", 24, "bold"),
            bootstyle="light",
            background='#2D1B69',
            foreground='#E6E6FA'
        )
        title_label.pack(pady=(0, 25))
        
        # 创建标签页控件
        self.notebook = ttk_bs.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=True)
        
        # 创建各个标签页
        self.create_main_view_tab()
        self.create_calendar_tab()
        self.create_project_tab()
        self.create_ai_assistant_tab()  # 新增AI助手标签页
        self.create_summary_tab()
        self.create_settings_tab()  # 新增设置标签页
    
    def create_main_view_tab(self):
        """创建主视图标签页"""
        main_tab = ttk_bs.Frame(self.notebook)
        self.notebook.add(main_tab, text="主视图")
        
        # 创建主要内容区域
        content_frame = ttk_bs.Frame(main_tab, style='Gradient.TFrame')
        content_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # 使用grid布局确保完美对齐
        content_frame.grid_columnconfigure(1, weight=1)  # 右侧列可扩展
        content_frame.grid_rowconfigure(0, weight=1)     # 行可扩展
        
        # 左侧：添加待办事项 - 固定宽度
        left_frame = ttk_bs.Frame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.configure(width=380)
        left_frame.pack_propagate(False)
        
        # 创建添加待办事项面板
        self.ui_components.create_add_todo_panel(left_frame, self.refresh_all_views)
        
        # 右侧：主要内容区域
        right_frame = ttk_bs.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        # 右上角：水平布局 - 任务汇总 + 提醒中心（固定较小高度）
        top_horizontal_frame = ttk_bs.Frame(right_frame)
        top_horizontal_frame.pack(side=TOP, fill=X, pady=(0, 10))
        top_horizontal_frame.configure(height=120)  # 固定较小高度
        top_horizontal_frame.pack_propagate(False)
        
        # 左侧：任务汇总（较小）
        summary_container = ttk_bs.Frame(top_horizontal_frame)
        summary_container.pack(side=LEFT, fill=BOTH, padx=(0, 10))
        summary_container.configure(width=280)  # 进一步减小宽度
        summary_container.pack_propagate(False)
        
        summary_frame = ttk_bs.LabelFrame(
            summary_container, 
            text="任务汇总", 
            bootstyle="primary",
            padding=6  # 减小内边距
        )
        summary_frame.pack(fill=BOTH, expand=True)
        
        self.summary_labels = self.ui_components.create_summary_panel(summary_frame)
        
        # 右侧：提醒中心（较大）
        reminder_container = ttk_bs.Frame(top_horizontal_frame)
        reminder_container.pack(side=RIGHT, fill=BOTH, expand=True)
        
        self.create_reminder_panel(reminder_container)
        
        # 右下角：四象限视图区域（更多空间）
        quadrant_frame = ttk_bs.Frame(right_frame)
        quadrant_frame.pack(side=TOP, fill=BOTH, expand=True)
        
        self.quadrant_view.create_integrated_view_panel(quadrant_frame)
    
    def create_reminder_panel(self, parent):
        """创建提醒功能面板"""
        reminder_frame = ttk_bs.LabelFrame(
            parent, 
            text="提醒中心", 
            bootstyle="info",  # 改为蓝色主题，移除红色
            padding=6
        )
        reminder_frame.pack(fill=BOTH, expand=True)
        
        # 第一行：提醒状态和控制按钮
        control_frame = ttk_bs.Frame(reminder_frame)
        control_frame.pack(fill=X, pady=(0, 5))
        
        # 提醒状态显示
        self.reminder_status_label = ttk_bs.Label(
            control_frame,
            text="提醒服务: 运行中",
            bootstyle="success",
            font=("Microsoft YaHei", 9)
        )
        self.reminder_status_label.pack(side=LEFT)
        
        # 提醒控制按钮
        button_frame = ttk_bs.Frame(control_frame)
        button_frame.pack(side=RIGHT)
        
        self.pause_reminder_btn = ttk_bs.Button(
            button_frame,
            text="暂停提醒",
            bootstyle="warning-outline",
            command=self.toggle_reminder_service,
            width=8
        )
        self.pause_reminder_btn.pack(side=LEFT, padx=(0, 3))
        
        test_reminder_btn = ttk_bs.Button(
            button_frame,
            text="测试提醒",
            bootstyle="info-outline",
            command=self.test_reminder,
            width=8
        )
        test_reminder_btn.pack(side=LEFT)
        
        # 第二行：筛选器
        filter_frame = ttk_bs.Frame(reminder_frame)
        filter_frame.pack(fill=X, pady=(0, 5))
        
        ttk_bs.Label(
            filter_frame,
            text="筛选任务:",
            font=("Microsoft YaHei", 8, "bold")
        ).pack(side=LEFT)
        
        # 天数筛选下拉框
        self.filter_days_var = tk.StringVar(value="3")
        filter_combo = ttk_bs.Combobox(
            filter_frame,
            textvariable=self.filter_days_var,
            values=["1", "3", "7", "14", "30", "全部"],
            width=8,
            state="readonly"
        )
        filter_combo.pack(side=LEFT, padx=(5, 5))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_upcoming_reminders())
        
        ttk_bs.Label(
            filter_frame,
            text="天内到期",
            font=("Microsoft YaHei", 8)
        ).pack(side=LEFT)
        
        # 第三行：即将到期的任务
        upcoming_frame = ttk_bs.Frame(reminder_frame)
        upcoming_frame.pack(fill=BOTH, expand=True)
        
        upcoming_label = ttk_bs.Label(
            upcoming_frame,
            text="即将到期任务:",
            font=("Microsoft YaHei", 8, "bold")
        )
        upcoming_label.pack(anchor=W)
        
        # 创建滚动区域显示即将到期的任务
        self.upcoming_text = tk.Text(
            upcoming_frame,
            height=2,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 8),
            bg="#2D1B69",
            fg="#E6E6FA",
            relief="flat",
            borderwidth=0
        )
        self.upcoming_text.pack(fill=BOTH, expand=True, pady=(2, 0))
        
        # 初始化即将到期任务显示
        self.refresh_upcoming_reminders()
    
    def toggle_reminder_service(self):
        """切换提醒服务状态"""
        if self.reminder_service.running:
            self.reminder_service.stop_reminder_thread()
            self.reminder_status_label.config(
                text="提醒服务: 已暂停",
                bootstyle="danger"
            )
            self.pause_reminder_btn.config(text="启动提醒")
        else:
            self.reminder_service.start_reminder_thread()
            self.reminder_status_label.config(
                text="提醒服务: 运行中",
                bootstyle="success"
            )
            self.pause_reminder_btn.config(text="暂停提醒")
    
    def test_reminder(self):
        """测试提醒功能"""
        self.reminder_service.send_notification(
            "测试提醒",
            "这是一个测试提醒，用于验证提醒功能是否正常工作。"
        )
        messagebox.showinfo("提醒测试", "测试提醒已发送！请查看系统通知。")
    
    def refresh_upcoming_reminders(self):
        """刷新即将到期的提醒"""
        from datetime import datetime, timedelta
        
        # 获取筛选天数
        filter_days = self.filter_days_var.get() if hasattr(self, 'filter_days_var') else "3"
        
        today = datetime.now().date()
        
        if filter_days == "全部":
            # 显示所有未完成的任务
            end_date = today + timedelta(days=365)  # 一年内的任务
        else:
            # 根据选择的天数筛选
            days = int(filter_days)
            end_date = today + timedelta(days=days)
        
        upcoming_tasks = self.db_manager.get_upcoming_tasks(
            today.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        # 清空文本框
        self.upcoming_text.delete(1.0, tk.END)
        
        if not upcoming_tasks:
            if filter_days == "全部":
                self.upcoming_text.insert(tk.END, "暂无未完成的任务")
            else:
                self.upcoming_text.insert(tk.END, f"暂无{filter_days}天内到期的任务")
        else:
            # 计算剩余天数并显示
            for task in upcoming_tasks[:5]:  # 只显示前5个
                task_id, title, project, due_date = task
                
                # 计算剩余天数
                try:
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    days_left = (due_date_obj - today).days
                    
                    if days_left < 0:
                        days_text = f"已逾期{abs(days_left)}天"
                        status_color = "🔴"
                    elif days_left == 0:
                        days_text = "今天到期"
                        status_color = "🟡"
                    elif days_left <= 3:
                        days_text = f"还有{days_left}天"
                        status_color = "🟠"
                    else:
                        days_text = f"还有{days_left}天"
                        status_color = "🟢"
                    
                    project_text = f"[{project}] " if project else ""
                    self.upcoming_text.insert(
                        tk.END, 
                        f"{status_color} {project_text}{title} ({days_text})\n"
                    )
                except ValueError:
                    # 如果日期格式有问题，显示原始日期
                    project_text = f"[{project}] " if project else ""
                    self.upcoming_text.insert(
                        tk.END, 
                        f"• {project_text}{title} ({due_date})\n"
                    )
        
        self.upcoming_text.config(state=tk.DISABLED)
    
    def create_calendar_tab(self):
        """创建日历标签页"""
        calendar_tab = self.calendar_view.create_calendar_tab(self.notebook)
        self.notebook.add(calendar_tab, text="日历视图")
    
    def create_project_tab(self):
        """创建项目汇总标签页"""
        project_tab = self.project_view.create_project_tab(self.notebook)
        self.notebook.add(project_tab, text="项目汇总")
    
    def create_ai_assistant_tab(self):
        """创建AI助手标签页"""
        ai_tab = ttk_bs.Frame(self.notebook)
        self.notebook.add(ai_tab, text="AI助手")
        
        # 创建AI助手面板
        self.ai_assistant.create_ai_panel(ai_tab)
    
    def create_summary_tab(self):
        """创建汇总标签页"""
        summary_tab = self.summary_view.create_summary_tab(self.notebook)
        self.notebook.add(summary_tab, text="统计汇总")
    
    def create_settings_tab(self):
        """创建设置标签页"""
        settings_tab = ttk_bs.Frame(self.notebook)
        self.notebook.add(settings_tab, text="设置")
        
        # 创建设置内容
        self.create_settings_content(settings_tab)
    
    def create_settings_content(self, parent):
        """创建设置页面内容"""
        # 创建滚动框架
        canvas = tk.Canvas(parent, bg='#2d1b5e')
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # AI配置部分
        ai_frame = ttk.LabelFrame(scrollable_frame, text="AI助手配置", padding=20)
        ai_frame.pack(fill="x", padx=20, pady=10)

        # API设置
        ttk.Label(ai_frame, text="DeepSeek API Key:", font=('Arial', 12, 'bold')).pack(anchor="w")
        
        api_frame = ttk.Frame(ai_frame)
        api_frame.pack(fill="x", pady=(5, 10))
        
        self.api_key_var = tk.StringVar()
        if self.config_manager:
            self.api_key_var.set(self.config_manager.get_api_key())
        
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=50)
        api_entry.pack(side="left", padx=(0, 10))
        
        ttk.Button(api_frame, text="保存", command=self.save_api_settings).pack(side="left", padx=(0, 5))
        ttk.Button(api_frame, text="测试连接", command=self.test_api_connection).pack(side="left")

        # MCP功能开关
        self.mcp_enabled_var = tk.BooleanVar()
        if self.config_manager:
            self.mcp_enabled_var.set(self.config_manager.is_mcp_enabled())
        
        mcp_cb = ttk.Checkbutton(ai_frame, text="启用MCP功能 (高级SQL查询)", 
                                variable=self.mcp_enabled_var)
        mcp_cb.pack(anchor="w", pady=5)

        # AI记忆管理部分
        memory_frame = ttk.LabelFrame(scrollable_frame, text="AI记忆管理", padding=20)
        memory_frame.pack(fill="x", padx=20, pady=10)

        # 记忆统计信息
        stats_frame = ttk.Frame(memory_frame)
        stats_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(stats_frame, text="学习统计", font=('Arial', 12, 'bold')).pack(anchor="w")
        
        self.memory_stats_text = tk.Text(stats_frame, height=8, width=80, state='disabled',
                                        bg='#1e1e1e', fg='white', font=('Consolas', 10))
        self.memory_stats_text.pack(fill="x", pady=5)

        # 记忆管理按钮
        memory_buttons_frame = ttk.Frame(memory_frame)
        memory_buttons_frame.pack(fill="x", pady=5)

        ttk.Button(memory_buttons_frame, text="刷新记忆统计", 
                  command=self.refresh_memory_stats).pack(side="left", padx=(0, 10))
        ttk.Button(memory_buttons_frame, text="导出对话历史", 
                  command=self.export_conversation_history).pack(side="left", padx=(0, 10))
        ttk.Button(memory_buttons_frame, text="清除学习数据", 
                  command=self.clear_learning_data).pack(side="left")

        # 用户偏好展示
        pref_frame = ttk.LabelFrame(memory_frame, text="用户偏好", padding=10)
        pref_frame.pack(fill="x", pady=10)

        self.preferences_text = tk.Text(pref_frame, height=6, width=80, state='disabled',
                                       bg='#1e1e1e', fg='white', font=('Consolas', 10))
        self.preferences_text.pack(fill="x")

        # 数据库管理部分（现有代码保持不变）
        db_frame = ttk.LabelFrame(scrollable_frame, text="数据库管理", padding=20)
        db_frame.pack(fill="x", padx=20, pady=10)

        # 数据库信息
        ttk.Label(db_frame, text="数据库状态", font=('Arial', 12, 'bold')).pack(anchor="w")
        
        self.db_info_text = tk.Text(db_frame, height=6, width=80, state='disabled',
                                   bg='#1e1e1e', fg='white', font=('Consolas', 10))
        self.db_info_text.pack(fill="x", pady=5)
        
        # 数据库操作按钮
        db_buttons_frame = ttk.Frame(db_frame)
        db_buttons_frame.pack(fill="x", pady=5)

        ttk.Button(db_buttons_frame, text="刷新状态", command=self.show_database_info).pack(side="left", padx=(0, 10))
        ttk.Button(db_buttons_frame, text="创建备份", command=self.create_database_backup).pack(side="left", padx=(0, 10))

        # 角色配置部分（现有代码保持不变）
        role_frame = ttk.LabelFrame(scrollable_frame, text="用户角色配置", padding=20)
        role_frame.pack(fill="x", padx=20, pady=10)

        role_buttons_frame = ttk.Frame(role_frame)
        role_buttons_frame.pack(fill="x", pady=5)

        ttk.Button(role_buttons_frame, text="配置用户角色", command=self.configure_user_role).pack(side="left", padx=(0, 10))
        ttk.Button(role_buttons_frame, text="重置角色配置", command=self.reset_user_role).pack(side="left", padx=(0, 10))
        
        # 检查是否已经跳过角色配置
        skip_role_config = self.config_manager.get('ui.skip_role_config', False)
        if skip_role_config:
            ttk.Button(role_buttons_frame, text="重新启用配置提醒", command=self.enable_role_config_reminder).pack(side="left")

        # 显示当前角色信息
        if self.role_manager and self.role_manager.is_profile_configured():
            current_role = self.role_manager.get_current_role()
            role_info = f"当前角色: {current_role['name']}\n描述: {current_role['description']}"
        else:
            role_info = "尚未配置用户角色"
            
        # 显示配置提醒状态
        skip_status = "已禁用启动提醒" if skip_role_config else "启动时会提醒配置"
        role_info += f"\n配置提醒状态: {skip_status}"

        role_info_label = ttk.Label(role_frame, text=role_info, font=('Arial', 10))
        role_info_label.pack(anchor="w", pady=10)

        # 设置初始显示
        self.refresh_database_status()  # 只刷新状态，不弹出对话框
        self.refresh_memory_stats()

        # 配置滚动
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return scrollable_frame
    
    def create_database_backup(self):
        """创建数据库备份"""
        try:
            # 这里可以调用数据库管理器的备份方法
            success = self.db_manager.create_backup()
            if success:
                messagebox.showinfo("备份成功", "数据库备份创建成功！")
            else:
                messagebox.showerror("备份失败", "创建数据库备份失败！")
        except Exception as e:
            messagebox.showerror("错误", f"备份过程中出错：{str(e)}")
    
    def show_database_info(self):
        """显示数据库信息"""
        try:
            config_module = importlib.import_module('9_config_manager')
            config_module.show_database_info_dialog(self.config_manager, self.root)
        except Exception as e:
            messagebox.showerror("错误", f"显示数据库信息时出错：{str(e)}")
    
    def refresh_database_status(self):
        """刷新数据库状态显示（不弹出对话框）"""
        try:
            # 获取数据库信息
            db_path = self.config_manager.get_database_path()
            abs_path = os.path.abspath(db_path)
            
            # 获取文件大小
            def get_file_size(file_path):
                try:
                    if os.path.exists(file_path):
                        size = os.path.getsize(file_path)
                        if size < 1024:
                            return f"{size} B"
                        elif size < 1024 * 1024:
                            return f"{size / 1024:.1f} KB"
                        else:
                            return f"{size / (1024 * 1024):.1f} MB"
                    return "文件不存在"
                except:
                    return "未知"
            
            # 构建状态信息
            status_text = f"""数据库状态信息:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
文件路径: {db_path}
文件大小: {get_file_size(abs_path)}
MCP功能: {'启用' if self.config_manager.is_mcp_enabled() else '禁用'}
连接状态: {'正常' if hasattr(self, 'db_manager') and self.db_manager else '未连接'}

数据库功能:
• 存储所有待办事项数据
• 支持GTD工作流和四象限管理
• 提供AI助手数据查询接口"""
            
            # 更新显示
            if hasattr(self, 'db_info_text'):
                self.db_info_text.config(state='normal')
                self.db_info_text.delete(1.0, tk.END)
                self.db_info_text.insert(1.0, status_text)
                self.db_info_text.config(state='disabled')
                
        except Exception as e:
            error_msg = f"刷新数据库状态失败: {str(e)}"
            if hasattr(self, 'db_info_text'):
                self.db_info_text.config(state='normal')
                self.db_info_text.delete(1.0, tk.END)
                self.db_info_text.insert(1.0, error_msg)
                self.db_info_text.config(state='disabled')
    
    def save_api_settings(self):
        """保存API设置"""
        try:
            api_key = self.api_key_var.get().strip()
            if api_key and api_key != "your_api_key_here":
                self.config_manager.set_api_key(api_key)
                # 更新AI助手的API密钥
                self.ai_assistant.ai_core.update_api_key(api_key)
                messagebox.showinfo("保存成功", "API配置已保存！")
            else:
                messagebox.showwarning("无效输入", "请输入有效的API Key！")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错：{str(e)}")
    
    def test_api_connection(self):
        """测试API连接"""
        try:
            # 先保存当前API密钥
            api_key = self.api_key_var.get().strip()
            if api_key and api_key != "your_api_key_here":
                self.ai_assistant.ai_core.update_api_key(api_key)
            
            # 测试连接
            success, message = self.ai_assistant.ai_core.test_api_connection()
            if success:
                messagebox.showinfo("连接成功", message)
            else:
                messagebox.showerror("连接失败", message)
        except Exception as e:
            messagebox.showerror("错误", f"测试连接时出错：{str(e)}")
    
    def refresh_memory_stats(self):
        """刷新AI记忆统计"""
        try:
            # 获取对话统计
            conversations = self.db_manager.get_recent_conversations(50)
            total_conversations = len(conversations)
            
            # 获取用户偏好统计
            preferences = self.db_manager.get_user_preferences()
            total_preferences = len(preferences)
            
            # 获取关键词统计
            keywords = self.db_manager.get_important_keywords(20)
            total_keywords = len(keywords)
            
            # 获取任务模板统计
            templates = self.db_manager.get_task_templates()
            total_templates = len(templates)
            
            # 构建统计信息
            stats_text = f"""AI学习统计信息:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
对话记录: {total_conversations} 次
用户偏好: {total_preferences} 项  
关键概念: {total_keywords} 个
任务模板: {total_templates} 个

最近对话类型分布:
"""
            
            # 分析对话类型
            conversation_types = {}
            for conv in conversations:
                conv_type = conv[2] if conv[2] else 'general'  # action_taken字段
                conversation_types[conv_type] = conversation_types.get(conv_type, 0) + 1
            
            for conv_type, count in conversation_types.items():
                stats_text += f"- {conv_type}: {count} 次\n"
            
            stats_text += f"\n记忆活跃度: {'高' if total_conversations > 20 else '中' if total_conversations > 5 else '低'}"
            
            # 更新显示
            self.memory_stats_text.config(state='normal')
            self.memory_stats_text.delete(1.0, tk.END)
            self.memory_stats_text.insert(1.0, stats_text)
            self.memory_stats_text.config(state='disabled')
            
            # 刷新偏好显示
            self.refresh_preferences_display()
            
        except Exception as e:
            error_msg = f"刷新记忆统计失败: {str(e)}"
            if hasattr(self, 'memory_stats_text'):
                self.memory_stats_text.config(state='normal')
                self.memory_stats_text.delete(1.0, tk.END)
                self.memory_stats_text.insert(1.0, error_msg)
                self.memory_stats_text.config(state='disabled')
    
    def refresh_preferences_display(self):
        """刷新用户偏好显示"""
        try:
            preferences = self.db_manager.get_user_preferences()
            
            pref_text = "学习到的用户偏好:\n"
            pref_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            if preferences:
                # 按类型分组显示
                pref_groups = {}
                for pref in preferences:
                    pref_type = pref[0]
                    if pref_type not in pref_groups:
                        pref_groups[pref_type] = []
                    pref_groups[pref_type].append(pref)
                
                for pref_type, items in pref_groups.items():
                    pref_text += f"\n{pref_type.replace('_', ' ').title()}:\n"
                    for item in items:
                        confidence = f"{float(item[3])*100:.0f}%" if item[3] else "50%"
                        pref_text += f"  • {item[1]}: {item[2]} (置信度: {confidence})\n"
            else:
                pref_text += "暂无学习到的偏好，与AI多互动即可建立个性化设置。"
            
            # 更新显示
            self.preferences_text.config(state='normal')
            self.preferences_text.delete(1.0, tk.END)
            self.preferences_text.insert(1.0, pref_text)
            self.preferences_text.config(state='disabled')
            
        except Exception as e:
            error_msg = f"刷新偏好显示失败: {str(e)}"
            if hasattr(self, 'preferences_text'):
                self.preferences_text.config(state='normal')
                self.preferences_text.delete(1.0, tk.END)
                self.preferences_text.insert(1.0, error_msg)
                self.preferences_text.config(state='disabled')
    
    def export_conversation_history(self):
        """导出对话历史"""
        try:
            from tkinter import filedialog
            from datetime import datetime
            import json
            
            # 选择保存位置
            filename = filedialog.asksaveasfilename(
                title="导出对话历史",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if filename:
                # 获取对话历史
                conversations = self.db_manager.get_recent_conversations(1000)  # 获取最近1000条
                
                # 准备导出数据
                export_data = {
                    "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "total_conversations": len(conversations),
                    "conversations": []
                }
                
                for conv in conversations:
                    export_data["conversations"].append({
                        "user_input": conv[0],
                        "ai_response": conv[1],
                        "action_taken": conv[2],
                        "created_at": conv[3]
                    })
                
                # 写入文件
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, ensure_ascii=False, indent=2)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"对话历史导出 - {export_data['export_time']}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for i, conv in enumerate(export_data["conversations"], 1):
                            f.write(f"对话 {i} - {conv['created_at']}\n")
                            f.write(f"用户: {conv['user_input']}\n")
                            f.write(f"AI: {conv['ai_response']}\n")
                            if conv['action_taken']:
                                f.write(f"操作: {conv['action_taken']}\n")
                            f.write("-" * 40 + "\n\n")
                
                messagebox.showinfo("导出成功", f"对话历史已导出到: {filename}")
                
        except Exception as e:
            messagebox.showerror("导出失败", f"导出对话历史时出错: {str(e)}")
    
    def clear_learning_data(self):
        """清除学习数据"""
        try:
            # 确认对话框
            result = messagebox.askyesno(
                "确认清除", 
                "这将清除所有AI学习数据，包括:\n- 对话历史\n- 用户偏好\n- 关键词记忆\n- 任务模板\n\n确定要继续吗？",
                icon='warning'
            )
            
            if result:
                # 清除各种学习数据
                self.db_manager.cursor.execute("DELETE FROM ai_conversations")
                self.db_manager.cursor.execute("DELETE FROM user_preferences")
                self.db_manager.cursor.execute("DELETE FROM ai_memory_keywords")
                self.db_manager.cursor.execute("DELETE FROM task_templates")
                self.db_manager.conn.commit()
                
                # 重置AI助手的会话ID
                if hasattr(self, 'ai_assistant'):
                    self.ai_assistant.current_session_id = self.ai_assistant._generate_session_id()
                    self.ai_assistant.conversation_count = 0
                
                messagebox.showinfo("清除成功", "AI学习数据已清除，助手将重新开始学习您的偏好。")
                
                # 刷新显示
                self.refresh_memory_stats()
                
        except Exception as e:
            messagebox.showerror("清除失败", f"清除学习数据时出错: {str(e)}")
    
    def refresh_all_views(self):
        """刷新所有视图"""
        # 刷新四象限视图
        self.quadrant_view.refresh_integrated_view()
        
        # 刷新简单汇总
        self.refresh_summary()
        
        # 刷新即将到期的提醒
        if hasattr(self, 'upcoming_text'):
            self.refresh_upcoming_reminders()
        
        # 刷新日历视图
        if hasattr(self.calendar_view, 'calendar_cells') and self.calendar_view.calendar_cells:
            self.calendar_view.update_calendar()
        
        # 刷新项目视图
        if hasattr(self.project_view, 'project_tree') and self.project_view.project_tree:
            self.project_view.refresh_project_view()
        
        # 刷新完整汇总面板
        if hasattr(self.summary_view, 'full_summary_labels') and self.summary_view.full_summary_labels:
            self.summary_view.refresh_full_summary()
        
        # 刷新AI助手的上下文
        if hasattr(self.ai_assistant, 'refresh_context'):
            self.ai_assistant.refresh_context()
    
    def refresh_summary(self):
        """刷新简单汇总统计"""
        if not hasattr(self, 'summary_labels'):
            return
            
        # 获取统计信息
        stats = self.db_manager.get_statistics()
        
        # 更新标签
        total = stats.get('total', 0)
        completed = stats.get('completed', 0)
        
        self.summary_labels["total"].config(text=f"总计: {total}")
        self.summary_labels["completed"].config(text=f"已完成: {completed}")
    
    def configure_user_role(self):
        """配置用户角色"""
        try:
            configured = self.role_manager.show_role_setup_dialog(self.root)
            if configured:
                messagebox.showinfo("配置成功", "用户角色配置已更新！")
                # 刷新界面显示
                self.refresh_all_views()
                # 重建AI系统提示词
                self.ai_assistant.system_prompt = self.ai_assistant._build_system_prompt()
            
            # 重新创建设置标签页内容以显示更新的信息
            for tab_id in range(self.notebook.index("end")):
                if self.notebook.tab(tab_id, "text") == "设置":
                    # 清空并重新创建设置标签页
                    settings_tab = self.notebook.nametowidget(self.notebook.tabs()[tab_id])
                    for widget in settings_tab.winfo_children():
                        widget.destroy()
                    self.create_settings_content(settings_tab)
                    break
        except Exception as e:
            messagebox.showerror("错误", f"配置角色时出错：{str(e)}")
    
    def reset_user_role(self):
        """重置用户角色"""
        try:
            result = messagebox.askyesno(
                "确认重置", 
                "确定要重置用户角色配置吗？\n这将清除所有个人设置信息。"
            )
            if result:
                # 删除用户配置文件
                if os.path.exists(self.role_manager.config_file):
                    os.remove(self.role_manager.config_file)
                
                # 重新初始化角色管理器
                self.role_manager = RoleManager()
                
                # 更新UI组件的角色管理器引用
                self.ui_components.role_manager = self.role_manager
                
                # 更新AI助手的角色管理器引用
                self.ai_assistant.role_manager = self.role_manager
                self.ai_assistant.task_parser.role_manager = self.role_manager
                
                # 重建AI系统提示词
                self.ai_assistant.system_prompt = self.ai_assistant._build_system_prompt()
                
                messagebox.showinfo("重置成功", "用户角色配置已重置！")
                
                # 重新创建设置标签页内容
                for tab_id in range(self.notebook.index("end")):
                    if self.notebook.tab(tab_id, "text") == "设置":
                        settings_tab = self.notebook.nametowidget(self.notebook.tabs()[tab_id])
                        for widget in settings_tab.winfo_children():
                            widget.destroy()
                        self.create_settings_content(settings_tab)
                        break
        except Exception as e:
            messagebox.showerror("错误", f"重置角色时出错：{str(e)}")
    
    def check_role_configuration(self):
        """检查用户角色配置"""
        # 检查是否已经设置过跳过角色配置
        skip_role_config = self.config_manager.get('ui.skip_role_config', False)
        
        if skip_role_config:
            return  # 如果设置了跳过，就不再显示配置对话框
            
        if not self.role_manager.is_profile_configured():
            # 显示角色配置对话框
            result = messagebox.askyesno(
                "角色配置", 
                "检测到您还未配置用户角色信息。\n\n配置角色信息可以让AI助手更好地为您服务。\n\n是否现在配置？\n\n（选择'否'将不再提醒，您可以稍后在设置中配置）"
            )
            
            if result:
                configured = self.role_manager.show_role_setup_dialog()
                if not configured:
                    # 用户选择稍后配置，使用默认设置
                    messagebox.showinfo(
                        "提示", 
                        "您可以稍后在设置中配置角色信息。\n当前将使用默认设置。"
                    )
            else:
                # 用户选择不配置，设置跳过标志
                self.config_manager.set('ui.skip_role_config', True)
                messagebox.showinfo(
                    "提示", 
                    "已设置跳过角色配置。\n如需配置，请在设置中手动配置角色信息。"
                )
    
    def enable_role_config_reminder(self):
        """重新启用角色配置提醒"""
        try:
            result = messagebox.askyesno(
                "重新启用配置提醒", 
                "确定要重新启用角色配置提醒吗？\n这将不再跳过角色配置。"
            )
            if result:
                self.config_manager.set('ui.skip_role_config', False)
                messagebox.showinfo("提示", "角色配置提醒已重新启用。")
                
                # 重新创建设置标签页内容以更新显示
                for tab_id in range(self.notebook.index("end")):
                    if self.notebook.tab(tab_id, "text") == "设置":
                        settings_tab = self.notebook.nametowidget(self.notebook.tabs()[tab_id])
                        for widget in settings_tab.winfo_children():
                            widget.destroy()
                        self.create_settings_content(settings_tab)
                        break
        except Exception as e:
            messagebox.showerror("错误", f"启用角色配置提醒时出错：{str(e)}")
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        finally:
            # 确保数据库连接正确关闭
            if hasattr(self, 'db_manager'):
                self.db_manager.close()

class AIAssistantWindow:
    """独立的AI助手窗口"""
    
    def __init__(self, main_app):
        self.main_app = main_app
        self.db_manager = main_app.db_manager
        self.ai_assistant = main_app.ai_assistant
        self.config_manager = main_app.config_manager
        
        # 创建独立窗口
        self.window = ttk_bs.Window(themename="vapor")
        self.window.title("AI智能助手")
        self.window.geometry("800x900")  # 增加高度从600到900
        self.window.minsize(600, 700)  # 增加最小高度从400到700
        
        self.create_widgets()
        
    def create_widgets(self):
        """创建AI助手界面"""
        # 创建主框架
        main_frame = ttk_bs.Frame(self.window, style='Gradient.TFrame')
        main_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # 创建标题
        title_label = ttk_bs.Label(
            main_frame, 
            text="AI智能助手", 
            font=("Microsoft YaHei", 20, "bold"),
            bootstyle="light",
            background='#2D1B69',
            foreground='#E6E6FA'
        )
        title_label.pack(pady=(0, 20))
        
        # 创建AI助手内容
        ai_content_frame = ttk_bs.Frame(main_frame)
        ai_content_frame.pack(fill=BOTH, expand=True)
        
        # 使用现有的AI助手面板创建方法
        self.main_app.ai_assistant.create_ai_panel(ai_content_frame)

def launch_dual_windows():
    """启动双窗口模式"""
    # 创建主应用
    main_app = TodoApp()
    
    # 创建独立的AI窗口
    ai_window = AIAssistantWindow(main_app)
    
    # 设置窗口位置避免重叠
    main_app.root.geometry("1200x800+100+100")  # 主窗口位置
    ai_window.window.geometry("800x900+1350+50")  # AI窗口位置（右侧，调整Y位置适应更高的窗口）
    
    # 显示AI窗口（不使用新线程，直接显示）
    ai_window.window.deiconify()  # 确保窗口显示
    
    # 启动主窗口的事件循环
    main_app.run()

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--dual":
        # 双窗口模式
        launch_dual_windows()
    else:
        # 单窗口模式（默认）
        app = TodoApp()
        app.run() 