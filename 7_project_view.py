"""
项目汇总视图模块
负责按项目维度展示和管理任务
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S, TOP, BOTTOM
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from datetime import datetime, timedelta

class ProjectView:
    def __init__(self, database_manager, ui_components):
        """初始化项目汇总视图"""
        self.db_manager = database_manager
        self.ui_components = ui_components
        self.project_tree = None
        self.selected_project = None
        self.project_stats_labels = {}
        self.filter_var = None
        self.progress_bars = {}
        self.notes_text = None
        self.schedule_text = None
        self.summary_text = None
        
    def create_project_tab(self, parent):
        """创建项目汇总标签页"""
        project_tab = ttk_bs.Frame(parent)
        
        # 创建项目汇总面板
        self.create_project_panel(project_tab)
        
        return project_tab
    
    def create_project_panel(self, parent):
        """创建项目汇总面板"""
        # 主容器
        main_frame = ttk_bs.Frame(parent)
        main_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        
        # 标题
        title_label = ttk_bs.Label(
            main_frame, 
            text="项目汇总", 
            font=("Microsoft YaHei", 20, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=(0, 20))
        
        # 创建水平分割的布局
        content_frame = ttk_bs.Frame(main_frame)
        content_frame.pack(fill=BOTH, expand=True)
        
        # 左侧：项目列表和筛选器
        left_frame = ttk_bs.LabelFrame(
            content_frame, 
            text="项目列表", 
            padding=15,
            bootstyle="info"
        )
        left_frame.pack(side=LEFT, fill=Y, padx=(0, 15))
        left_frame.configure(width=350)
        left_frame.pack_propagate(False)
        
        # 筛选器区域
        filter_frame = ttk_bs.Frame(left_frame)
        filter_frame.pack(fill=X, pady=(0, 15))
        
        ttk_bs.Label(
            filter_frame, 
            text="筛选项目:", 
            font=("Microsoft YaHei", 10, "bold")
        ).pack(anchor=W)
        
        filter_container = ttk_bs.Frame(filter_frame)
        filter_container.pack(fill=X, pady=(5, 0))
        
        self.filter_var = tk.StringVar(value="全部项目")
        filter_combo = ttk_bs.Combobox(
            filter_container,
            textvariable=self.filter_var,
            values=["全部项目", "活跃项目", "已完成项目", "待开始项目"],
            state="readonly",
            font=("Microsoft YaHei", 9),
            width=15
        )
        filter_combo.pack(side=LEFT, fill=X, expand=True, padx=(0, 5))
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_project_view())
        
        refresh_btn = ttk_bs.Button(
            filter_container,
            text="刷新",
            bootstyle="primary-outline",
            command=self.refresh_project_view,
            width=6
        )
        refresh_btn.pack(side=RIGHT)
        
        # 项目统计信息
        stats_frame = ttk_bs.Frame(left_frame)
        stats_frame.pack(fill=X, pady=(0, 15))
        
        self.project_stats_labels["total_projects"] = ttk_bs.Label(
            stats_frame, 
            text="总项目数: 0", 
            font=("Microsoft YaHei", 10, "bold"),
            bootstyle="primary"
        )
        self.project_stats_labels["total_projects"].pack(anchor=W)
        
        self.project_stats_labels["active_projects"] = ttk_bs.Label(
            stats_frame, 
            text="活跃项目: 0", 
            font=("Microsoft YaHei", 10),
            bootstyle="success"
        )
        self.project_stats_labels["active_projects"].pack(anchor=W)
        
        # 项目列表
        self.project_tree = ttk_bs.Treeview(
            left_frame,
            columns=("completion_rate",),
            show="tree headings",
            height=20
        )
        
        self.project_tree.heading("#0", text="项目名称")
        self.project_tree.heading("completion_rate", text="完成率")
        
        self.project_tree.column("#0", width=200)
        self.project_tree.column("completion_rate", width=80)
        
        # 项目列表滚动条
        project_scrollbar = ttk_bs.Scrollbar(left_frame, orient="vertical", command=self.project_tree.yview)
        self.project_tree.configure(yscrollcommand=project_scrollbar.set)
        
        self.project_tree.pack(side="left", fill="both", expand=True)
        project_scrollbar.pack(side="right", fill="y")
        
        # 绑定项目选择事件
        self.project_tree.bind("<<TreeviewSelect>>", self.on_project_select)
        
        # 右侧：项目详情展示
        right_frame = ttk_bs.Frame(content_frame)
        right_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        
        # 创建项目详情区域
        self.create_project_details(right_frame)
        
        # 初始化数据
        self.refresh_project_view()
    
    def create_project_details(self, parent):
        """创建项目详情展示区域"""
        # 项目详情标题
        self.selected_project_label = ttk_bs.Label(
            parent, 
            text="请选择一个项目", 
            font=("Microsoft YaHei", 16, "bold"),
            bootstyle="primary"
        )
        self.selected_project_label.pack(pady=(0, 20))
        
        # 创建滚动区域
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
        
        # 1. 项目进度区域 - 三条横向进度条
        progress_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="项目进度", 
            padding=20,
            bootstyle="success"
        )
        progress_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        # 总体完成度
        total_progress_frame = ttk_bs.Frame(progress_frame)
        total_progress_frame.pack(fill=X, pady=(0, 15))
        
        ttk_bs.Label(
            total_progress_frame, 
            text="总体完成度", 
            font=("Microsoft YaHei", 12, "bold")
        ).pack(anchor=W)
        
        self.progress_bars["total"] = ttk_bs.Progressbar(
            total_progress_frame,
            bootstyle="success-striped",
            length=400,
            mode="determinate"
        )
        self.progress_bars["total"].pack(fill=X, pady=(5, 0))
        
        self.progress_bars["total_label"] = ttk_bs.Label(
            total_progress_frame, 
            text="0% (0/0)", 
            font=("Microsoft YaHei", 10)
        )
        self.progress_bars["total_label"].pack(anchor=W, pady=(2, 0))
        
        # 重要任务完成度
        important_progress_frame = ttk_bs.Frame(progress_frame)
        important_progress_frame.pack(fill=X, pady=(0, 15))
        
        ttk_bs.Label(
            important_progress_frame, 
            text="重要任务完成度", 
            font=("Microsoft YaHei", 12, "bold")
        ).pack(anchor=W)
        
        self.progress_bars["important"] = ttk_bs.Progressbar(
            important_progress_frame,
            bootstyle="warning-striped",
            length=400,
            mode="determinate"
        )
        self.progress_bars["important"].pack(fill=X, pady=(5, 0))
        
        self.progress_bars["important_label"] = ttk_bs.Label(
            important_progress_frame, 
            text="0% (0/0)", 
            font=("Microsoft YaHei", 10)
        )
        self.progress_bars["important_label"].pack(anchor=W, pady=(2, 0))
        
        # 紧急任务完成度
        urgent_progress_frame = ttk_bs.Frame(progress_frame)
        urgent_progress_frame.pack(fill=X)
        
        ttk_bs.Label(
            urgent_progress_frame, 
            text="紧急任务完成度", 
            font=("Microsoft YaHei", 12, "bold")
        ).pack(anchor=W)
        
        self.progress_bars["urgent"] = ttk_bs.Progressbar(
            urgent_progress_frame,
            bootstyle="danger-striped",
            length=400,
            mode="determinate"
        )
        self.progress_bars["urgent"].pack(fill=X, pady=(5, 0))
        
        self.progress_bars["urgent_label"] = ttk_bs.Label(
            urgent_progress_frame, 
            text="0% (0/0)", 
            font=("Microsoft YaHei", 10)
        )
        self.progress_bars["urgent_label"].pack(anchor=W, pady=(2, 0))
        
        # 2. 注意事项区域
        notes_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="注意事项", 
            padding=20,
            bootstyle="warning"
        )
        notes_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        notes_header = ttk_bs.Frame(notes_frame)
        notes_header.pack(fill=X, pady=(0, 10))
        
        ttk_bs.Label(
            notes_header, 
            text="项目注意事项和重要提醒", 
            font=("Microsoft YaHei", 11, "bold")
        ).pack(side=LEFT)
        
        add_note_btn = ttk_bs.Button(
            notes_header,
            text="添加注意事项",
            bootstyle="warning-outline",
            command=self.add_note,
            width=12
        )
        add_note_btn.pack(side=RIGHT)
        
        self.notes_text = tk.Text(
            notes_frame,
            height=6,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg="#2D1B69",
            fg="#E6E6FA",
            relief="solid",
            borderwidth=1
        )
        self.notes_text.pack(fill=X)
        
        # 3. 时间安排区域
        schedule_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="时间安排", 
            padding=20,
            bootstyle="info"
        )
        schedule_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        schedule_header = ttk_bs.Frame(schedule_frame)
        schedule_header.pack(fill=X, pady=(0, 10))
        
        ttk_bs.Label(
            schedule_header, 
            text="项目时间规划和里程碑", 
            font=("Microsoft YaHei", 11, "bold")
        ).pack(side=LEFT)
        
        add_schedule_btn = ttk_bs.Button(
            schedule_header,
            text="添加时间安排",
            bootstyle="info-outline",
            command=self.add_schedule,
            width=12
        )
        add_schedule_btn.pack(side=RIGHT)
        
        self.schedule_text = tk.Text(
            schedule_frame,
            height=6,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg="#2D1B69",
            fg="#E6E6FA",
            relief="solid",
            borderwidth=1
        )
        self.schedule_text.pack(fill=X)
        
        # 4. 项目总结区域
        summary_frame = ttk_bs.LabelFrame(
            scrollable_frame, 
            text="项目总结", 
            padding=20,
            bootstyle="primary"
        )
        summary_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        summary_header = ttk_bs.Frame(summary_frame)
        summary_header.pack(fill=X, pady=(0, 10))
        
        ttk_bs.Label(
            summary_header, 
            text="项目感受和经验总结", 
            font=("Microsoft YaHei", 11, "bold")
        ).pack(side=LEFT)
        
        add_summary_btn = ttk_bs.Button(
            summary_header,
            text="添加总结",
            bootstyle="primary-outline",
            command=self.add_summary,
            width=10
        )
        add_summary_btn.pack(side=RIGHT)
        
        self.summary_text = tk.Text(
            summary_frame,
            height=6,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg="#2D1B69",
            fg="#E6E6FA",
            relief="solid",
            borderwidth=1
        )
        self.summary_text.pack(fill=X)
        
        # 配置滚动
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def get_project_statistics(self):
        """获取项目统计数据"""
        filter_condition = ""
        filter_value = self.filter_var.get() if self.filter_var else "全部项目"
        
        if filter_value == "活跃项目":
            filter_condition = "HAVING pending_tasks > 0"
        elif filter_value == "已完成项目":
            filter_condition = "HAVING pending_tasks = 0 AND total_tasks > 0"
        elif filter_value == "待开始项目":
            filter_condition = "HAVING total_tasks = 0"
        
        query = f'''
            SELECT 
                COALESCE(project, '未分类') as project_name,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_tasks
            FROM todos 
            GROUP BY COALESCE(project, '未分类')
            {filter_condition}
            ORDER BY total_tasks DESC
        '''
        
        self.db_manager.cursor.execute(query)
        return self.db_manager.cursor.fetchall()
    
    def get_project_progress_data(self, project_name):
        """获取项目进度数据"""
        if project_name == "未分类":
            base_query = "WHERE project IS NULL OR project = ''"
        else:
            base_query = f"WHERE project = '{project_name}'"
        
        # 总体进度
        self.db_manager.cursor.execute(f'''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM todos {base_query}
        ''')
        total_data = self.db_manager.cursor.fetchone()
        
        # 重要任务进度 (priority 1, 2)
        self.db_manager.cursor.execute(f'''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM todos {base_query} AND priority IN (1, 2)
        ''')
        important_data = self.db_manager.cursor.fetchone()
        
        # 紧急任务进度 (priority 1, 3)
        self.db_manager.cursor.execute(f'''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM todos {base_query} AND priority IN (1, 3)
        ''')
        urgent_data = self.db_manager.cursor.fetchone()
        
        return {
            'total': total_data,
            'important': important_data,
            'urgent': urgent_data
        }
    
    def refresh_project_view(self):
        """刷新项目视图"""
        # 清空项目树
        for item in self.project_tree.get_children():
            self.project_tree.delete(item)
        
        # 获取项目统计
        project_stats = self.get_project_statistics()
        
        total_projects = len(project_stats)
        active_projects = sum(1 for stats in project_stats if stats[3] > 0)
        
        # 更新统计标签
        self.project_stats_labels["total_projects"].config(text=f"总项目数: {total_projects}")
        self.project_stats_labels["active_projects"].config(text=f"活跃项目: {active_projects}")
        
        # 填充项目列表
        for project_name, total_tasks, completed_tasks, pending_tasks in project_stats:
            completion_rate = f"{(completed_tasks / total_tasks * 100):.1f}%" if total_tasks > 0 else "0%"
            
            # 根据完成率设置标签颜色
            if completed_tasks == total_tasks and total_tasks > 0:
                tags = ("completed",)
            elif pending_tasks > 0:
                tags = ("active",)
            else:
                tags = ("empty",)
            
            self.project_tree.insert(
                "", "end",
                text=project_name,
                values=(completion_rate,),
                tags=tags
            )
        
        # 配置标签颜色
        self.project_tree.tag_configure("completed", background="#d4edda", foreground="#155724")
        self.project_tree.tag_configure("active", background="#fff3cd", foreground="#856404")
        self.project_tree.tag_configure("empty", background="#f8d7da", foreground="#721c24")
        
        # 重置选中项目
        self.selected_project = None
        self.selected_project_label.config(text="请选择一个项目")
        self.clear_project_details()
    
    def on_project_select(self, event):
        """项目选择事件处理"""
        selection = self.project_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        project_name = self.project_tree.item(item, "text")
        self.selected_project = project_name
        
        # 更新项目详情标题
        self.selected_project_label.config(text=f"项目: {project_name}")
        
        # 加载项目详情
        self.load_project_details(project_name)
    
    def load_project_details(self, project_name):
        """加载项目详情"""
        # 更新进度条
        progress_data = self.get_project_progress_data(project_name)
        
        # 总体进度
        total, completed = progress_data['total']
        total_percent = (completed / total * 100) if total > 0 else 0
        self.progress_bars["total"]["value"] = total_percent
        self.progress_bars["total_label"].config(text=f"{total_percent:.1f}% ({completed}/{total})")
        
        # 重要任务进度
        important_total, important_completed = progress_data['important']
        important_percent = (important_completed / important_total * 100) if important_total > 0 else 0
        self.progress_bars["important"]["value"] = important_percent
        self.progress_bars["important_label"].config(text=f"{important_percent:.1f}% ({important_completed}/{important_total})")
        
        # 紧急任务进度
        urgent_total, urgent_completed = progress_data['urgent']
        urgent_percent = (urgent_completed / urgent_total * 100) if urgent_total > 0 else 0
        self.progress_bars["urgent"]["value"] = urgent_percent
        self.progress_bars["urgent_label"].config(text=f"{urgent_percent:.1f}% ({urgent_completed}/{urgent_total})")
        
        # 加载项目记录（注意事项、时间安排、总结）
        self.load_project_records(project_name)
    
    def load_project_records(self, project_name):
        """加载项目记录"""
        # 这里可以从数据库加载项目的注意事项、时间安排和总结
        # 暂时显示示例内容
        
        # 清空文本框
        self.notes_text.delete(1.0, tk.END)
        self.schedule_text.delete(1.0, tk.END)
        self.summary_text.delete(1.0, tk.END)
        
        # 示例内容
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        self.notes_text.insert(tk.END, f"[{current_time}] 项目 '{project_name}' 的注意事项:\n")
        self.notes_text.insert(tk.END, "• 关注重要任务的优先级\n")
        self.notes_text.insert(tk.END, "• 及时跟进紧急任务的进展\n")
        self.notes_text.insert(tk.END, "• 定期回顾项目整体进度\n\n")
        
        self.schedule_text.insert(tk.END, f"[{current_time}] 项目 '{project_name}' 的时间安排:\n")
        self.schedule_text.insert(tk.END, "• 项目启动阶段已完成\n")
        self.schedule_text.insert(tk.END, "• 当前处于执行阶段\n")
        self.schedule_text.insert(tk.END, "• 预计完成时间待确定\n\n")
        
        self.summary_text.insert(tk.END, f"[{current_time}] 项目 '{project_name}' 的总结感受:\n")
        self.summary_text.insert(tk.END, "• 项目进展顺利，团队配合良好\n")
        self.summary_text.insert(tk.END, "• 需要加强时间管理和优先级控制\n")
        self.summary_text.insert(tk.END, "• 持续关注项目质量和进度平衡\n\n")
    
    def clear_project_details(self):
        """清空项目详情"""
        # 重置进度条
        for key in ["total", "important", "urgent"]:
            if key in self.progress_bars:
                self.progress_bars[key]["value"] = 0
                self.progress_bars[f"{key}_label"].config(text="0% (0/0)")
        
        # 清空文本框
        if self.notes_text:
            self.notes_text.delete(1.0, tk.END)
        if self.schedule_text:
            self.schedule_text.delete(1.0, tk.END)
        if self.summary_text:
            self.summary_text.delete(1.0, tk.END)
    
    def add_note(self):
        """添加注意事项"""
        if not self.selected_project:
            messagebox.showwarning("警告", "请先选择一个项目")
            return
        
        # 创建输入对话框
        dialog = tk.Toplevel()
        dialog.title("添加注意事项")
        dialog.geometry("500x300")
        dialog.configure(bg='#2D1B69')
        dialog.resizable(False, False)
        
        # 设置对话框居中
        dialog.transient(dialog.master)
        dialog.grab_set()
        
        # 标题
        title_label = ttk_bs.Label(
            dialog,
            text=f"为项目 '{self.selected_project}' 添加注意事项",
            font=("Microsoft YaHei", 12, "bold"),
            bootstyle="warning"
        )
        title_label.pack(pady=15)
        
        # 输入框
        input_frame = ttk_bs.Frame(dialog)
        input_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))
        
        ttk_bs.Label(
            input_frame,
            text="请输入注意事项内容:",
            font=("Microsoft YaHei", 10)
        ).pack(anchor=W, pady=(0, 5))
        
        text_input = tk.Text(
            input_frame,
            height=8,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg="#2D1B69",
            fg="#E6E6FA",
            relief="solid",
            borderwidth=1
        )
        text_input.pack(fill=BOTH, expand=True)
        text_input.focus()
        
        # 按钮框架
        button_frame = ttk_bs.Frame(dialog)
        button_frame.pack(fill=X, padx=20, pady=(0, 15))
        
        def save_note():
            content = text_input.get(1.0, tk.END).strip()
            if content:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                note_text = f"[{current_time}] {content}\n"
                self.notes_text.insert(tk.END, note_text)
                dialog.destroy()
                messagebox.showinfo("成功", "注意事项已添加")
            else:
                messagebox.showwarning("警告", "请输入注意事项内容")
        
        def cancel():
            dialog.destroy()
        
        # 按钮
        ttk_bs.Button(
            button_frame,
            text="取消",
            bootstyle="secondary",
            command=cancel,
            width=10
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bs.Button(
            button_frame,
            text="保存",
            bootstyle="warning",
            command=save_note,
            width=10
        ).pack(side=RIGHT)
        
        # 绑定回车键保存
        dialog.bind('<Return>', lambda e: save_note())
        dialog.bind('<Escape>', lambda e: cancel())
    
    def add_schedule(self):
        """添加时间安排"""
        if not self.selected_project:
            messagebox.showwarning("警告", "请先选择一个项目")
            return
        
        # 创建输入对话框
        dialog = tk.Toplevel()
        dialog.title("添加时间安排")
        dialog.geometry("500x300")
        dialog.configure(bg='#2D1B69')
        dialog.resizable(False, False)
        
        # 设置对话框居中
        dialog.transient(dialog.master)
        dialog.grab_set()
        
        # 标题
        title_label = ttk_bs.Label(
            dialog,
            text=f"为项目 '{self.selected_project}' 添加时间安排",
            font=("Microsoft YaHei", 12, "bold"),
            bootstyle="info"
        )
        title_label.pack(pady=15)
        
        # 输入框
        input_frame = ttk_bs.Frame(dialog)
        input_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))
        
        ttk_bs.Label(
            input_frame,
            text="请输入时间安排内容:",
            font=("Microsoft YaHei", 10)
        ).pack(anchor=W, pady=(0, 5))
        
        text_input = tk.Text(
            input_frame,
            height=8,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg="#2D1B69",
            fg="#E6E6FA",
            relief="solid",
            borderwidth=1
        )
        text_input.pack(fill=BOTH, expand=True)
        text_input.focus()
        
        # 按钮框架
        button_frame = ttk_bs.Frame(dialog)
        button_frame.pack(fill=X, padx=20, pady=(0, 15))
        
        def save_schedule():
            content = text_input.get(1.0, tk.END).strip()
            if content:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                schedule_text = f"[{current_time}] {content}\n"
                self.schedule_text.insert(tk.END, schedule_text)
                dialog.destroy()
                messagebox.showinfo("成功", "时间安排已添加")
            else:
                messagebox.showwarning("警告", "请输入时间安排内容")
        
        def cancel():
            dialog.destroy()
        
        # 按钮
        ttk_bs.Button(
            button_frame,
            text="取消",
            bootstyle="secondary",
            command=cancel,
            width=10
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bs.Button(
            button_frame,
            text="保存",
            bootstyle="info",
            command=save_schedule,
            width=10
        ).pack(side=RIGHT)
        
        # 绑定回车键保存
        dialog.bind('<Return>', lambda e: save_schedule())
        dialog.bind('<Escape>', lambda e: cancel())
    
    def add_summary(self):
        """添加总结"""
        if not self.selected_project:
            messagebox.showwarning("警告", "请先选择一个项目")
            return
        
        # 创建输入对话框
        dialog = tk.Toplevel()
        dialog.title("添加项目总结")
        dialog.geometry("500x300")
        dialog.configure(bg='#2D1B69')
        dialog.resizable(False, False)
        
        # 设置对话框居中
        dialog.transient(dialog.master)
        dialog.grab_set()
        
        # 标题
        title_label = ttk_bs.Label(
            dialog,
            text=f"为项目 '{self.selected_project}' 添加总结",
            font=("Microsoft YaHei", 12, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=15)
        
        # 输入框
        input_frame = ttk_bs.Frame(dialog)
        input_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 15))
        
        ttk_bs.Label(
            input_frame,
            text="请输入项目总结内容:",
            font=("Microsoft YaHei", 10)
        ).pack(anchor=W, pady=(0, 5))
        
        text_input = tk.Text(
            input_frame,
            height=8,
            wrap=tk.WORD,
            font=("Microsoft YaHei", 10),
            bg="#2D1B69",
            fg="#E6E6FA",
            relief="solid",
            borderwidth=1
        )
        text_input.pack(fill=BOTH, expand=True)
        text_input.focus()
        
        # 按钮框架
        button_frame = ttk_bs.Frame(dialog)
        button_frame.pack(fill=X, padx=20, pady=(0, 15))
        
        def save_summary():
            content = text_input.get(1.0, tk.END).strip()
            if content:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                summary_text = f"[{current_time}] {content}\n"
                self.summary_text.insert(tk.END, summary_text)
                dialog.destroy()
                messagebox.showinfo("成功", "项目总结已添加")
            else:
                messagebox.showwarning("警告", "请输入项目总结内容")
        
        def cancel():
            dialog.destroy()
        
        # 按钮
        ttk_bs.Button(
            button_frame,
            text="取消",
            bootstyle="secondary",
            command=cancel,
            width=10
        ).pack(side=RIGHT, padx=(5, 0))
        
        ttk_bs.Button(
            button_frame,
            text="保存",
            bootstyle="primary",
            command=save_summary,
            width=10
        ).pack(side=RIGHT)
        
        # 绑定回车键保存
        dialog.bind('<Return>', lambda e: save_summary())
        dialog.bind('<Escape>', lambda e: cancel()) 