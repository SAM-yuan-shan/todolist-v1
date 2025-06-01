"""
智能待办事项管理器 - 主应用程序
整合所有功能模块的主入口
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S, TOP
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import importlib

# 动态导入各个功能模块
database_module = importlib.import_module('1_database')
reminder_module = importlib.import_module('2_reminder_service')
ui_module = importlib.import_module('3_ui_components')
calendar_module = importlib.import_module('4_calendar_view')
quadrant_module = importlib.import_module('5_quadrant_view')
summary_module = importlib.import_module('6_summary_view')
project_module = importlib.import_module('7_project_view')

DatabaseManager = database_module.DatabaseManager
ReminderService = reminder_module.ReminderService
UIComponents = ui_module.UIComponents
CalendarView = calendar_module.CalendarView
QuadrantView = quadrant_module.QuadrantView
SummaryView = summary_module.SummaryView
ProjectView = project_module.ProjectView

class TodoApp:
    def __init__(self):
        """初始化主应用程序"""
        # 创建主窗口 - 紫色主题
        self.root = ttk_bs.Window(themename="vapor")
        self.root.title("智能待办事项管理器")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # 设置紫色渐变背景
        self.setup_gradient_background()
        
        # 初始化各个管理器
        self.db_manager = DatabaseManager()
        self.reminder_service = ReminderService(self.db_manager)
        self.ui_components = UIComponents(self.db_manager)
        self.calendar_view = CalendarView(self.db_manager, self.ui_components)
        self.quadrant_view = QuadrantView(self.db_manager, self.ui_components)
        self.summary_view = SummaryView(self.db_manager, self.ui_components)
        self.project_view = ProjectView(self.db_manager, self.ui_components)
        
        # 创建界面
        self.create_widgets()
        
        # 启动提醒服务
        self.reminder_service.start_reminder_thread()
        
        # 加载数据
        self.refresh_all_views()
    
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
        self.create_summary_tab()
    
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
    
    def create_summary_tab(self):
        """创建汇总标签页"""
        summary_tab = self.summary_view.create_summary_tab(self.notebook)
        self.notebook.add(summary_tab, text="统计汇总")
    
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
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        finally:
            # 停止提醒服务
            self.reminder_service.stop_reminder_thread()
            # 关闭数据库连接
            self.db_manager.close()

if __name__ == "__main__":
    app = TodoApp()
    app.run() 