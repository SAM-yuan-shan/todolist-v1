"""
四象限视图模块
负责四象限+GTD管理视图的显示和交互
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *

class QuadrantView:
    def __init__(self, database_manager, ui_components):
        """初始化四象限视图"""
        self.db_manager = database_manager
        self.ui_components = ui_components
        self.integrated_trees = {}
        
    def create_integrated_view_panel(self, parent):
        """创建右侧四象限+GTD整合视图面板"""
        # 创建主框架
        view_frame = ttk_bs.LabelFrame(
            parent, 
            text="四象限 + GTD 管理视图", 
            padding=10,
            bootstyle="light"
        )
        view_frame.pack(fill=BOTH, expand=True)
        
        # 创建2x2网格
        grid_frame = ttk_bs.Frame(view_frame)
        grid_frame.pack(fill=BOTH, expand=True)
        
        # 四象限信息
        quadrants_info = [
            ("重要且紧急", "danger", 0, 0),
            ("重要不紧急", "warning", 0, 1),
            ("不重要但紧急", "info", 1, 0),
            ("不重要不紧急", "secondary", 1, 1)
        ]
        
        # GTD标签信息
        gtd_tabs = [
            ("下一步", "next-action", "success"),
            ("等待中", "waiting-for", "warning"),
            ("将来/也许", "someday-maybe", "info"),
            ("收件箱", "inbox", "secondary")
        ]
        
        self.integrated_trees = {}
        
        for title, style, row, col in quadrants_info:
            # 创建象限框架
            quadrant_frame = ttk_bs.LabelFrame(
                grid_frame, 
                text=title, 
                padding=10,
                bootstyle=style
            )
            quadrant_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            
            # 创建GTD标签页
            gtd_notebook = ttk_bs.Notebook(quadrant_frame)
            gtd_notebook.pack(fill=BOTH, expand=True)
            
            priority = row * 2 + col + 1
            
            for gtd_name, gtd_tag, gtd_style in gtd_tabs:
                # 创建GTD标签页
                gtd_frame = ttk_bs.Frame(gtd_notebook)
                gtd_notebook.add(gtd_frame, text=gtd_name)
                
                # 创建树形视图
                tree = ttk_bs.Treeview(
                    gtd_frame,
                    columns=("status", "title", "project", "due_date"),
                    show="headings",
                    height=8
                )
                
                tree.heading("status", text="状态")
                tree.heading("title", text="标题")
                tree.heading("project", text="项目")
                tree.heading("due_date", text="截止日期")
                
                tree.column("status", width=50)
                tree.column("title", width=150)
                tree.column("project", width=100)
                tree.column("due_date", width=100)
                
                # 添加滚动条
                scrollbar = ttk_bs.Scrollbar(gtd_frame, orient="vertical", command=tree.yview)
                tree.configure(yscrollcommand=scrollbar.set)
                
                tree.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")
                
                # 绑定双击事件
                tree.bind("<Double-1>", lambda e, t=tree: self.on_todo_double_click(e, t))
                
                # 存储树形视图引用
                self.integrated_trees[(priority, gtd_tag)] = tree
        
        # 配置网格权重
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)
        
        return view_frame
    
    def refresh_integrated_view(self):
        """刷新四象限+GTD整合视图"""
        # 清空所有树形视图
        for (priority, gtd_tag), tree in self.integrated_trees.items():
            for item in tree.get_children():
                tree.delete(item)
        
        # 获取所有待办事项
        todos = self.db_manager.get_all_todos()
        
        # 按四象限和GTD标签分类显示
        for todo in todos:
            todo_id, title, project, due_date, status, priority, gtd_tag = todo
            
            # 确定树形视图
            tree_key = (priority, gtd_tag)
            if tree_key in self.integrated_trees:
                tree = self.integrated_trees[tree_key]
                
                # 显示状态图标
                status_icon = "✓" if status == "completed" else "○"
                
                # 插入项目
                tree.insert("", "end", values=(status_icon, title, project, due_date), tags=(todo_id,))
                
                # 设置已完成任务的样式
                if status == "completed":
                    item = tree.get_children()[-1]
                    tree.set(item, "status", "✓")
    
    def on_todo_double_click(self, event, tree):
        """处理待办事项双击事件"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        todo_id = item['tags'][0] if item['tags'] else None
        
        if todo_id:
            self.ui_components.create_todo_detail_window(None, todo_id, self.refresh_integrated_view) 