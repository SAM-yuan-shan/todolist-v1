"""
日历视图模块
负责日历界面的显示和交互
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from datetime import datetime, timedelta
import calendar

class CalendarView:
    def __init__(self, database_manager, ui_components):
        """初始化日历视图"""
        self.db_manager = database_manager
        self.ui_components = ui_components
        self.current_date = datetime.now()
        self.calendar_cells = {}
        
    def create_calendar_tab(self, parent):
        """创建日历标签页"""
        calendar_tab = ttk_bs.Frame(parent)
        
        # 创建日历主框架
        calendar_main = ttk_bs.Frame(calendar_tab, style='Gradient.TFrame')
        calendar_main.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # 日历控制面板
        control_frame = ttk_bs.Frame(calendar_main)
        control_frame.pack(fill=X, pady=(0, 15))
        
        # 月份导航
        nav_frame = ttk_bs.Frame(control_frame)
        nav_frame.pack(side=LEFT)
        
        ttk_bs.Button(
            nav_frame, 
            text="◀", 
            command=self.prev_month,
            bootstyle="secondary",
            width=3
        ).pack(side=LEFT, padx=(0, 5))
        
        self.month_label = ttk_bs.Label(
            nav_frame, 
            text=self.current_date.strftime("%Y年 %m月"),
            font=("Microsoft YaHei", 16, "bold"),
            bootstyle="light"
        )
        self.month_label.pack(side=LEFT, padx=10)
        
        ttk_bs.Button(
            nav_frame, 
            text="▶", 
            command=self.next_month,
            bootstyle="secondary",
            width=3
        ).pack(side=LEFT, padx=(5, 0))
        
        # 今天按钮
        ttk_bs.Button(
            control_frame, 
            text="今天", 
            command=self.goto_today,
            bootstyle="primary"
        ).pack(side=RIGHT)
        
        # 日历网格框架
        calendar_frame = ttk_bs.Frame(calendar_main)
        calendar_frame.pack(fill=BOTH, expand=True)
        
        # 创建日历网格
        self.create_calendar_grid(calendar_frame)
        
        return calendar_tab
    
    def create_calendar_grid(self, parent):
        """创建日历网格"""
        # 星期标题
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        for i, day in enumerate(weekdays):
            label = ttk_bs.Label(
                parent, 
                text=day, 
                font=("Microsoft YaHei", 12, "bold"),
                bootstyle="light",
                anchor="center"
            )
            label.grid(row=0, column=i, sticky="ew", padx=1, pady=1)
        
        # 日期网格
        self.calendar_cells = {}
        for week in range(6):  # 最多6周
            for day in range(7):  # 7天
                cell_frame = ttk_bs.Frame(parent, style='Card.TFrame', padding=5)
                cell_frame.grid(row=week+1, column=day, sticky="nsew", padx=1, pady=1)
                
                # 日期标签
                date_label = ttk_bs.Label(
                    cell_frame, 
                    text="", 
                    font=("Microsoft YaHei", 10, "bold"),
                    anchor="nw"
                )
                date_label.pack(anchor="nw")
                
                # 任务列表框架
                tasks_frame = ttk_bs.Frame(cell_frame)
                tasks_frame.pack(fill=BOTH, expand=True, pady=(5, 0))
                
                self.calendar_cells[(week, day)] = {
                    'frame': cell_frame,
                    'date_label': date_label,
                    'tasks_frame': tasks_frame,
                    'date': None
                }
        
        # 配置网格权重
        for i in range(7):
            parent.grid_columnconfigure(i, weight=1)
        for i in range(7):
            parent.grid_rowconfigure(i, weight=1)
        
        # 初始化日历
        self.update_calendar()
    
    def prev_month(self):
        """上一个月"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year-1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month-1)
        self.update_calendar()
    
    def next_month(self):
        """下一个月"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year+1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month+1)
        self.update_calendar()
    
    def goto_today(self):
        """回到今天"""
        self.current_date = datetime.now()
        self.update_calendar()
    
    def update_calendar(self):
        """更新日历显示"""
        # 更新月份标签
        self.month_label.config(text=self.current_date.strftime("%Y年 %m月"))
        
        # 获取当月第一天和最后一天
        first_day = self.current_date.replace(day=1)
        if first_day.month == 12:
            last_day = first_day.replace(year=first_day.year+1, month=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=first_day.month+1) - timedelta(days=1)
        
        # 获取第一天是星期几（0=周一，6=周日）
        first_weekday = first_day.weekday()
        
        # 清空所有单元格
        for cell_info in self.calendar_cells.values():
            cell_info['date_label'].config(text="")
            for widget in cell_info['tasks_frame'].winfo_children():
                widget.destroy()
            cell_info['date'] = None
            cell_info['frame'].config(bootstyle="secondary")
        
        # 填充日期
        current_date = first_day
        week = 0
        day = first_weekday
        
        while current_date <= last_day:
            if week < 6 and day < 7:
                cell_info = self.calendar_cells[(week, day)]
                cell_info['date'] = current_date
                cell_info['date_label'].config(text=str(current_date.day))
                
                # 检查是否是今天
                if current_date.date() == datetime.now().date():
                    cell_info['frame'].config(bootstyle="primary")
                else:
                    cell_info['frame'].config(bootstyle="light")
                
                # 加载当天的任务
                self.load_day_tasks(current_date, cell_info['tasks_frame'])
            
            # 移动到下一天
            current_date += timedelta(days=1)
            day += 1
            if day >= 7:
                day = 0
                week += 1
    
    def load_day_tasks(self, date, tasks_frame):
        """加载指定日期的任务"""
        date_str = date.strftime('%Y-%m-%d')
        
        # 查询当天的任务
        tasks = self.db_manager.get_todos_by_date(date_str)
        
        # 显示任务
        for i, (todo_id, title, project, gtd_tag, priority, status) in enumerate(tasks):
            if i >= 3:  # 最多显示3个任务
                more_label = ttk_bs.Label(
                    tasks_frame,
                    text=f"...还有{len(tasks)-3}个",
                    font=("Microsoft YaHei", 8),
                    bootstyle="secondary"
                )
                more_label.pack(anchor="w")
                break
            
            # 根据优先级设置颜色
            priority_colors = {1: "danger", 2: "warning", 3: "info", 4: "secondary"}
            color = priority_colors.get(priority, "secondary")
            
            # 根据状态设置样式
            if status == 'completed':
                color = "success"
                title = f"✓ {title}"
            
            # 创建任务标签
            task_label = ttk_bs.Label(
                tasks_frame,
                text=f"{title[:10]}..." if len(title) > 10 else title,
                font=("Microsoft YaHei", 8),
                bootstyle=color,
                cursor="hand2"
            )
            task_label.pack(anchor="w", pady=1)
            
            # 绑定点击事件
            task_label.bind("<Button-1>", lambda e, d=date_str: self.show_day_detail(d))
    
    def show_day_detail(self, date_str):
        """显示某天的详细任务"""
        # 创建详情窗口
        detail_window = ttk_bs.Toplevel()
        detail_window.title(f"{date_str} 的任务详情")
        detail_window.geometry("800x600")
        detail_window.transient()
        detail_window.grab_set()
        
        # 主框架
        main_frame = ttk_bs.Frame(detail_window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # 标题
        title_label = ttk_bs.Label(
            main_frame,
            text=f"{date_str} 的所有任务",
            font=("Microsoft YaHei", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=(0, 20))
        
        # 任务列表
        tree_frame = ttk_bs.Frame(main_frame)
        tree_frame.pack(fill=BOTH, expand=True)
        
        # 创建树形视图
        tree = ttk_bs.Treeview(
            tree_frame,
            columns=("title", "project", "priority", "gtd", "status"),
            show="headings",
            height=15
        )
        
        tree.heading("title", text="标题")
        tree.heading("project", text="项目")
        tree.heading("priority", text="优先级")
        tree.heading("gtd", text="GTD标签")
        tree.heading("status", text="状态")
        
        tree.column("title", width=200)
        tree.column("project", width=120)
        tree.column("priority", width=100)
        tree.column("gtd", width=120)
        tree.column("status", width=80)
        
        # 滚动条
        scrollbar = ttk_bs.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 查询并显示任务
        tasks = self.db_manager.get_todos_by_date(date_str)
        
        priority_names = {1: "重要紧急", 2: "重要不紧急", 3: "不重要紧急", 4: "不重要不紧急"}
        gtd_names = {
            "next-action": "下一步行动",
            "waiting-for": "等待中", 
            "someday-maybe": "将来/也许",
            "inbox": "收件箱"
        }
        
        for task in tasks:
            todo_id, title, project, gtd_tag, priority, status = task
            priority_name = priority_names.get(priority, "未知")
            gtd_name = gtd_names.get(gtd_tag, gtd_tag)
            
            tree.insert("", "end", values=(title, project or "无", priority_name, gtd_name, status), tags=(todo_id,))
        
        # 绑定双击事件
        def on_double_click(event):
            selection = tree.selection()
            if not selection:
                return
            
            item = tree.item(selection[0])
            todo_id = item['tags'][0] if item['tags'] else None
            
            if todo_id:
                detail_window.destroy()  # 关闭日期详情窗口
                self.ui_components.create_todo_detail_window(None, todo_id, None)  # 显示任务详情
        
        tree.bind("<Double-1>", on_double_click)
        
        # 关闭按钮
        ttk_bs.Button(
            main_frame,
            text="关闭",
            command=detail_window.destroy,
            bootstyle="secondary"
        ).pack(pady=20) 