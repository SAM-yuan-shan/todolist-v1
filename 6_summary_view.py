"""
统计汇总视图模块
负责统计信息的显示和管理
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from datetime import datetime, timedelta

class SummaryView:
    def __init__(self, database_manager, ui_components):
        """初始化统计汇总视图"""
        self.db_manager = database_manager
        self.ui_components = ui_components
        self.full_summary_labels = {}
        self.project_stats_frame = None
        self.upcoming_tree = None
        
    def create_summary_tab(self, parent):
        """创建汇总标签页"""
        summary_tab = ttk_bs.Frame(parent)
        
        # 创建汇总面板
        self.create_full_summary_panel(summary_tab)
        
        return summary_tab
    
    def create_full_summary_panel(self, parent):
        """创建完整的汇总面板"""
        # 创建滚动框架
        canvas = tk.Canvas(parent, bg='#2D1B69', highlightthickness=0)
        scrollbar = ttk_bs.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk_bs.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 总体统计
        total_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="总体统计", 
            padding=20,
            bootstyle="primary"
        )
        total_frame.pack(fill=X, padx=20, pady=20)
        
        # 总计信息
        total_info_frame = ttk_bs.Frame(total_frame)
        total_info_frame.pack(fill=X, pady=(0, 15))
        
        self.full_summary_labels["total"] = ttk_bs.Label(
            total_info_frame, 
            text="总计: 0", 
            font=("Microsoft YaHei", 18, "bold"),
            bootstyle="primary"
        )
        self.full_summary_labels["total"].pack(side=LEFT)
        
        self.full_summary_labels["completed"] = ttk_bs.Label(
            total_info_frame, 
            text="已完成: 0", 
            font=("Microsoft YaHei", 14),
            bootstyle="success"
        )
        self.full_summary_labels["completed"].pack(side=RIGHT)
        
        # 四象限统计
        quadrant_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="四象限统计", 
            padding=20,
            bootstyle="warning"
        )
        quadrant_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        quadrant_grid = ttk_bs.Frame(quadrant_frame)
        quadrant_grid.pack(fill=X)
        
        quadrant_names = ["重要紧急", "重要不紧急", "不重要紧急", "不重要不紧急"]
        colors = ["danger", "warning", "info", "secondary"]
        
        for i, (name, color) in enumerate(zip(quadrant_names, colors)):
            row = i // 2
            col = i % 2
            
            quad_frame = ttk_bs.Frame(quadrant_grid)
            quad_frame.grid(row=row, column=col, sticky="ew", padx=10, pady=10)
            
            label = ttk_bs.Label(
                quad_frame, 
                text=f"{name}: 0", 
                bootstyle=color,
                font=("Microsoft YaHei", 12, "bold")
            )
            label.pack()
            self.full_summary_labels[f"quadrant_{i+1}"] = label
        
        quadrant_grid.grid_columnconfigure(0, weight=1)
        quadrant_grid.grid_columnconfigure(1, weight=1)
        
        # GTD统计
        gtd_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="GTD统计", 
            padding=20,
            bootstyle="info"
        )
        gtd_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        gtd_grid = ttk_bs.Frame(gtd_frame)
        gtd_grid.pack(fill=X)
        
        gtd_names = ["下一步行动", "等待中", "将来/也许", "收件箱"]
        gtd_tags = ["next-action", "waiting-for", "someday-maybe", "inbox"]
        gtd_colors = ["success", "warning", "info", "secondary"]
        
        for i, (name, tag, color) in enumerate(zip(gtd_names, gtd_tags, gtd_colors)):
            row = i // 2
            col = i % 2
            
            gtd_item_frame = ttk_bs.Frame(gtd_grid)
            gtd_item_frame.grid(row=row, column=col, sticky="ew", padx=10, pady=10)
            
            label = ttk_bs.Label(
                gtd_item_frame, 
                text=f"{name}: 0", 
                bootstyle=color,
                font=("Microsoft YaHei", 12, "bold")
            )
            label.pack()
            self.full_summary_labels[f"gtd_{tag}"] = label
        
        gtd_grid.grid_columnconfigure(0, weight=1)
        gtd_grid.grid_columnconfigure(1, weight=1)
        
        # 项目统计
        project_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="项目统计", 
            padding=20,
            bootstyle="success"
        )
        project_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        # 项目列表将动态生成
        self.project_stats_frame = ttk_bs.Frame(project_frame)
        self.project_stats_frame.pack(fill=X)
        
        # 近期任务
        recent_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="近期任务", 
            padding=20,
            bootstyle="danger"
        )
        recent_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        # 即将到期的任务
        self.upcoming_tree = ttk_bs.Treeview(
            recent_frame,
            columns=("title", "project", "due_date", "days_left"),
            show="headings",
            height=8
        )
        
        self.upcoming_tree.heading("title", text="标题")
        self.upcoming_tree.heading("project", text="项目")
        self.upcoming_tree.heading("due_date", text="截止日期")
        self.upcoming_tree.heading("days_left", text="剩余天数")
        
        self.upcoming_tree.column("title", width=200)
        self.upcoming_tree.column("project", width=120)
        self.upcoming_tree.column("due_date", width=100)
        self.upcoming_tree.column("days_left", width=100)
        
        scrollbar_upcoming = ttk_bs.Scrollbar(recent_frame, orient="vertical", command=self.upcoming_tree.yview)
        self.upcoming_tree.configure(yscrollcommand=scrollbar_upcoming.set)
        
        self.upcoming_tree.pack(side="left", fill="both", expand=True)
        scrollbar_upcoming.pack(side="right", fill="y")
        
        # 绑定双击事件
        self.upcoming_tree.bind("<Double-1>", lambda e: self.on_todo_double_click(e, self.upcoming_tree))
        
        # 配置滚动
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def on_todo_double_click(self, event, tree):
        """处理待办事项双击事件"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        todo_id = item['tags'][0] if item['tags'] else None
        
        if todo_id:
            self.ui_components.create_todo_detail_window(None, todo_id, self.refresh_full_summary)
    
    def refresh_full_summary(self):
        """刷新完整汇总信息"""
        # 获取统计信息
        stats = self.db_manager.get_statistics()
        
        # 更新四象限统计
        quadrant_names = ["重要紧急", "重要不紧急", "不重要紧急", "不重要不紧急"]
        for i in range(1, 5):
            count = stats.get(f'quadrant_{i}', 0)
            self.full_summary_labels[f"quadrant_{i}"].config(text=f"{quadrant_names[i-1]}: {count}")
        
        # 更新GTD统计
        gtd_tags = ["next-action", "waiting-for", "someday-maybe", "inbox"]
        gtd_names = ["下一步行动", "等待中", "将来/也许", "收件箱"]
        
        for tag, name in zip(gtd_tags, gtd_names):
            count = stats.get(f'gtd_{tag}', 0)
            self.full_summary_labels[f"gtd_{tag}"].config(text=f"{name}: {count}")
        
        # 更新总计统计
        total = stats.get('pending', 0)
        self.full_summary_labels["total"].config(text=f"总计: {total}")
        
        # 更新已完成统计
        completed = stats.get('completed', 0)
        self.full_summary_labels["completed"].config(text=f"已完成: {completed}")
        
        # 刷新项目统计
        self.refresh_project_stats()
        
        # 刷新即将到期任务
        self.refresh_upcoming_tasks()
    
    def refresh_project_stats(self):
        """刷新项目统计"""
        if not self.project_stats_frame:
            return
            
        # 清空现有的项目统计
        for widget in self.project_stats_frame.winfo_children():
            widget.destroy()
        
        # 获取项目统计
        projects = self.db_manager.get_project_statistics()
        
        if not projects:
            ttk_bs.Label(
                self.project_stats_frame,
                text="暂无项目数据",
                font=("Microsoft YaHei", 10),
                bootstyle="secondary"
            ).pack()
            return
        
        # 显示项目统计
        for i, (project, count) in enumerate(projects):
            project_frame = ttk_bs.Frame(self.project_stats_frame)
            project_frame.pack(fill=X, pady=2)
            
            # 项目名称
            ttk_bs.Label(
                project_frame,
                text=f"{project}:",
                font=("Microsoft YaHei", 10, "bold")
            ).pack(side=LEFT)
            
            # 任务数量
            ttk_bs.Label(
                project_frame,
                text=f"{count} 个任务",
                font=("Microsoft YaHei", 10),
                bootstyle="info"
            ).pack(side=RIGHT)
    
    def refresh_upcoming_tasks(self):
        """刷新即将到期的任务"""
        if not self.upcoming_tree:
            return
            
        # 清空树形视图
        for item in self.upcoming_tree.get_children():
            self.upcoming_tree.delete(item)
        
        # 查询未来7天内到期的待办事项
        today = datetime.now().date()
        week_later = today + timedelta(days=7)
        
        todos = self.db_manager.get_upcoming_tasks(
            today.strftime('%Y-%m-%d'), 
            week_later.strftime('%Y-%m-%d')
        )
        
        for todo in todos:
            todo_id, title, project, due_date_str = todo
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                days_left = (due_date - today).days
                
                if days_left < 0:
                    days_text = f"已过期 {abs(days_left)} 天"
                    tag = "overdue"
                elif days_left == 0:
                    days_text = "今天到期"
                    tag = "today"
                elif days_left <= 3:
                    days_text = f"{days_left} 天"
                    tag = "urgent"
                else:
                    days_text = f"{days_left} 天"
                    tag = "normal"
                
                item = self.upcoming_tree.insert("", "end", values=(title, project or "无", due_date_str, days_text), tags=(todo_id,))
                
                # 根据紧急程度设置颜色
                if tag == "overdue":
                    self.upcoming_tree.set(item, "days_left", f"⚠️ {days_text}")
                elif tag == "today":
                    self.upcoming_tree.set(item, "days_left", f"🔥 {days_text}")
                elif tag == "urgent":
                    self.upcoming_tree.set(item, "days_left", f"⏰ {days_text}")
                    
            except:
                continue 