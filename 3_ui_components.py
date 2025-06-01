"""
UI组件模块
包含各种可复用的UI组件和界面元素
"""
import tkinter as tk
from tkinter import ttk, messagebox, BOTH, LEFT, RIGHT, X, Y, W, E, N, S
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
from datetime import datetime, timedelta

class UIComponents:
    def __init__(self, database_manager, role_manager=None):
        """初始化UI组件"""
        self.db_manager = database_manager
        self.role_manager = role_manager
        self.priority_names = {1: "重要且紧急", 2: "重要不紧急", 3: "不重要但紧急", 4: "不重要不紧急"}
        self.gtd_names = {
            "next-action": "下一步行动",
            "waiting-for": "等待中",
            "someday-maybe": "将来/也许",
            "inbox": "收件箱"
        }
    
    def create_add_todo_panel(self, parent, on_add_callback):
        """创建添加待办事项面板"""
        # 主框架
        add_frame = ttk_bs.LabelFrame(
            parent, 
            text="添加待办事项", 
            padding=10,
            bootstyle="primary",
            width=370
        )
        add_frame.pack(fill=BOTH, expand=True)
        add_frame.pack_propagate(False)
        
        # 添加按钮
        button_frame = ttk_bs.Frame(add_frame)
        button_frame.pack(fill=X, pady=(0, 15))
        
        style = ttk_bs.Style()
        style.configure("AddButton.TButton", font=("Microsoft YaHei", 14, "bold"))
        
        add_button = ttk_bs.Button(
            button_frame,
            text="✚ 添加待办事项",
            command=lambda: self.handle_add_todo(add_frame, on_add_callback),
            bootstyle="success",
            style="AddButton.TButton",
            width=25
        )
        add_button.pack(pady=10, ipady=10)
        
        # 分隔线
        separator = ttk_bs.Separator(add_frame, orient='horizontal')
        separator.pack(fill=X, pady=(0, 10))
        
        # 标题输入
        title_frame = ttk_bs.Frame(add_frame)
        title_frame.pack(fill=X, pady=(0, 8))
        
        title_label = ttk_bs.Label(title_frame, text="标题: *", font=("Microsoft YaHei", 10, "bold"))
        title_label.pack(anchor=W)
        
        title_entry = ttk_bs.Entry(title_frame, font=("Microsoft YaHei", 10))
        title_entry.pack(fill=X, pady=(2, 0))
        add_frame.title_entry = title_entry
        
        # 项目输入
        project_frame = ttk_bs.Frame(add_frame)
        project_frame.pack(fill=X, pady=(0, 8))
        
        project_label = ttk_bs.Label(project_frame, text="项目: *", font=("Microsoft YaHei", 10, "bold"))
        project_label.pack(anchor=W)
        
        # 项目选择下拉框
        project_combo = ttk_bs.Combobox(
            project_frame,
            font=("Microsoft YaHei", 10),
            state="readonly"
        )
        project_combo.pack(fill=X, pady=(2, 0))
        
        # 填充项目选项
        if self.role_manager:
            projects = self.role_manager.get_available_projects()
            project_values = [f"{project['name']}" for project in projects]
            project_combo['values'] = project_values
            
            # 设置默认项目
            default_project_id = self.role_manager.profile.get('default_project', 'work')
            for project in projects:
                if project['id'] == default_project_id:
                    project_combo.set(project['name'])
                    break
            
            # 保存项目ID映射
            project_combo.project_mapping = {project['name']: project['id'] for project in projects}
        else:
            project_combo['values'] = ["工作项目", "个人事务", "学习提升"]
            project_combo.set("工作项目")
            project_combo.project_mapping = {
                "工作项目": "work",
                "个人事务": "personal", 
                "学习提升": "study"
            }
        
        add_frame.project_combo = project_combo
        
        # 责任级别选择
        responsibility_frame = ttk_bs.Frame(add_frame)
        responsibility_frame.pack(fill=X, pady=(0, 8))
        
        responsibility_label = ttk_bs.Label(responsibility_frame, text="责任级别: *", font=("Microsoft YaHei", 10, "bold"))
        responsibility_label.pack(anchor=W)
        
        responsibility_combo = ttk_bs.Combobox(
            responsibility_frame,
            font=("Microsoft YaHei", 10),
            state="readonly"
        )
        responsibility_combo.pack(fill=X, pady=(2, 0))
        
        # 填充责任级别选项
        if self.role_manager:
            responsibilities = self.role_manager.get_responsibility_levels()
            responsibility_values = [f"{resp['name']}" for resp in responsibilities]
            responsibility_combo['values'] = responsibility_values
            
            # 设置默认责任级别
            default_responsibility = self.role_manager.profile.get('default_responsibility', 'owner')
            for resp in responsibilities:
                if resp['id'] == default_responsibility:
                    responsibility_combo.set(resp['name'])
                    break
            
            # 保存责任级别ID映射
            responsibility_combo.responsibility_mapping = {resp['name']: resp['id'] for resp in responsibilities}
        else:
            responsibility_combo['values'] = ["负责人", "参与者", "关注者", "支持者"]
            responsibility_combo.set("负责人")
            responsibility_combo.responsibility_mapping = {
                "负责人": "owner",
                "参与者": "participant",
                "关注者": "observer",
                "支持者": "supporter"
            }
        
        add_frame.responsibility_combo = responsibility_combo
        
        # 描述输入
        desc_frame = ttk_bs.Frame(add_frame)
        desc_frame.pack(fill=X, pady=(0, 8))
        
        desc_label = ttk_bs.Label(desc_frame, text="描述: (选填)", font=("Microsoft YaHei", 10))
        desc_label.pack(anchor=W)
        
        desc_text = tk.Text(desc_frame, height=2, font=("Microsoft YaHei", 9))
        desc_text.pack(fill=X, pady=(2, 0))
        add_frame.desc_text = desc_text
        
        # 四象限分类
        priority_frame = ttk_bs.LabelFrame(add_frame, text="四象限分类", padding=3)
        priority_frame.pack(fill=X, pady=(0, 8))
        
        priority_var = tk.IntVar(value=1)
        add_frame.priority_var = priority_var
        
        grid_frame = ttk_bs.Frame(priority_frame)
        grid_frame.pack()
        
        priorities = [
            (1, "重要紧急", 0, 0),
            (2, "重要不紧急", 0, 1),
            (3, "不重要紧急", 1, 0),
            (4, "不重要不紧急", 1, 1)
        ]
        
        for value, text, row, col in priorities:
            rb = ttk_bs.Radiobutton(
                grid_frame, 
                text=text, 
                variable=priority_var, 
                value=value,
                bootstyle="primary"
            )
            rb.grid(row=row, column=col, sticky=W, padx=3, pady=1)
        
        # GTD标签
        gtd_frame = ttk_bs.LabelFrame(add_frame, text="GTD标签", padding=3)
        gtd_frame.pack(fill=X, pady=(0, 8))
        
        gtd_var = tk.StringVar(value="inbox")
        add_frame.gtd_var = gtd_var
        
        gtd_grid_frame = ttk_bs.Frame(gtd_frame)
        gtd_grid_frame.pack()
        
        gtd_options = [
            ("next-action", "下一步行动", 0, 0),
            ("waiting-for", "等待中", 0, 1),
            ("someday-maybe", "将来/也许", 1, 0),
            ("inbox", "收件箱", 1, 1)
        ]
        
        for value, text, row, col in gtd_options:
            rb = ttk_bs.Radiobutton(
                gtd_grid_frame, 
                text=text, 
                variable=gtd_var, 
                value=value,
                bootstyle="info"
            )
            rb.grid(row=row, column=col, sticky=W, padx=3, pady=1)
        
        # 截止日期
        due_frame = ttk_bs.Frame(add_frame)
        due_frame.pack(fill=X, pady=(0, 8))
        
        due_label = ttk_bs.Label(due_frame, text="截止日期:", font=("Microsoft YaHei", 10))
        due_label.pack(anchor=W)
        
        due_date_entry = ttk_bs.DateEntry(due_frame, bootstyle="primary")
        due_date_entry.pack(fill=X, pady=(2, 0))
        add_frame.due_date_entry = due_date_entry
        
        # 提醒设置
        reminder_frame = ttk_bs.LabelFrame(add_frame, text="提醒设置", padding=3)
        reminder_frame.pack(fill=X, pady=(0, 8))
        
        # 提醒日期
        reminder_date_frame = ttk_bs.Frame(reminder_frame)
        reminder_date_frame.pack(fill=X, pady=(0, 3))
        
        ttk_bs.Label(reminder_date_frame, text="提醒时间:", font=("Microsoft YaHei", 9)).pack(anchor=W)
        reminder_date_entry = ttk_bs.DateEntry(reminder_date_frame, bootstyle="warning")
        reminder_date_entry.pack(fill=X, pady=(2, 0))
        add_frame.reminder_date_entry = reminder_date_entry
        
        # 提醒时间
        time_frame = ttk_bs.Frame(reminder_frame)
        time_frame.pack(fill=X)
        
        ttk_bs.Label(time_frame, text="时间:", font=("Microsoft YaHei", 9)).pack(side=LEFT)
        
        # 小时选择
        hour_var = tk.StringVar(value="09")
        add_frame.hour_var = hour_var
        hour_spinbox = ttk_bs.Spinbox(
            time_frame,
            from_=0, to=23,
            textvariable=hour_var,
            width=3,
            format="%02.0f"
        )
        hour_spinbox.pack(side=LEFT, padx=(5, 2))
        
        ttk_bs.Label(time_frame, text=":", font=("Microsoft YaHei", 9)).pack(side=LEFT)
        
        # 分钟选择
        minute_var = tk.StringVar(value="00")
        add_frame.minute_var = minute_var
        minute_spinbox = ttk_bs.Spinbox(
            time_frame,
            from_=0, to=59,
            textvariable=minute_var,
            width=3,
            format="%02.0f"
        )
        minute_spinbox.pack(side=LEFT, padx=(2, 0))
        
        # 提示标签
        tip_label = ttk_bs.Label(
            add_frame,
            text="💡 填写完信息后点击上方绿色按钮添加",
            font=("Microsoft YaHei", 9),
            bootstyle="info",
            anchor="center"
        )
        tip_label.pack(pady=(10, 0))
        
        return add_frame
    
    def handle_add_todo(self, add_frame, on_add_callback):
        """处理添加待办事项"""
        title = add_frame.title_entry.get().strip()
        project_name = add_frame.project_combo.get()
        responsibility_name = add_frame.responsibility_combo.get()
        
        # 验证必填项
        if not title:
            messagebox.showerror("错误", "请输入标题（必填项）")
            add_frame.title_entry.focus()
            return
        
        if not project_name:
            messagebox.showerror("错误", "请选择项目（必填项）")
            add_frame.project_combo.focus()
            return
        
        if not responsibility_name:
            messagebox.showerror("错误", "请选择责任级别（必填项）")
            add_frame.responsibility_combo.focus()
            return
        
        # 获取项目和责任级别的ID
        project_id = add_frame.project_combo.project_mapping.get(project_name, "work")
        responsibility_id = add_frame.responsibility_combo.responsibility_mapping.get(responsibility_name, "owner")
        
        description = add_frame.desc_text.get("1.0", tk.END).strip()
        priority = int(add_frame.priority_var.get())
        gtd_tag = add_frame.gtd_var.get()
        due_date = add_frame.due_date_entry.entry.get()
        
        # 构建提醒时间
        reminder_date = add_frame.reminder_date_entry.entry.get()
        reminder_hour = add_frame.hour_var.get()
        reminder_minute = add_frame.minute_var.get()
        reminder_time = f"{reminder_date} {reminder_hour}:{reminder_minute}:00"
        
        # 设置重要性和紧急性
        if priority == 1:  # 重要且紧急
            importance, urgency = 1, 1
        elif priority == 2:  # 重要不紧急
            importance, urgency = 1, 0
        elif priority == 3:  # 不重要但紧急
            importance, urgency = 0, 1
        else:  # 不重要不紧急
            importance, urgency = 0, 0
        
        try:
            # 添加到数据库
            todo_id = self.db_manager.add_todo(
                title, description, project_id, responsibility_id, priority, urgency, importance, 
                gtd_tag, due_date, reminder_time
            )
            
            # 显示成功消息
            messagebox.showinfo("成功", f"待办事项添加成功！\n标题: {title}\n项目: {project_name}\n责任级别: {responsibility_name}")
            
            # 清空输入框但保持默认选择
            add_frame.title_entry.delete(0, tk.END)
            add_frame.desc_text.delete("1.0", tk.END)
            
            # 重置为默认值
            if self.role_manager:
                # 重新设置默认项目
                default_project_id = self.role_manager.profile.get('default_project', 'work')
                projects = self.role_manager.get_available_projects()
                for project in projects:
                    if project['id'] == default_project_id:
                        add_frame.project_combo.set(project['name'])
                        break
                
                # 重新设置默认责任级别
                default_responsibility = self.role_manager.profile.get('default_responsibility', 'owner')
                responsibilities = self.role_manager.get_responsibility_levels()
                for resp in responsibilities:
                    if resp['id'] == default_responsibility:
                        add_frame.responsibility_combo.set(resp['name'])
                        break
            
            # 调用回调函数刷新界面
            if on_add_callback:
                on_add_callback()
                
        except Exception as e:
            messagebox.showerror("错误", f"添加待办事项失败: {str(e)}")
    
    def create_todo_detail_window(self, parent, todo_id, on_update_callback):
        """创建待办事项详情窗口"""
        todo = self.db_manager.get_todo_by_id(todo_id)
        if not todo:
            return
        
        # 创建详情窗口
        detail_window = ttk_bs.Toplevel(parent)
        detail_window.title("待办事项详情")
        detail_window.geometry("500x700")
        detail_window.resizable(False, False)
        detail_window.transient(parent)
        detail_window.grab_set()
        
        # 解包待办事项数据
        (id_, title, description, project, priority, urgency, importance, gtd_tag, 
         due_date, reminder_time, status, created_at, completed_at) = todo
        
        # 创建详情内容
        main_frame = ttk_bs.Frame(detail_window, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # 标题
        ttk_bs.Label(main_frame, text="标题:", font=("Microsoft YaHei", 12, "bold")).pack(anchor=W)
        ttk_bs.Label(main_frame, text=title, font=("Microsoft YaHei", 11)).pack(anchor=W, pady=(0, 10))
        
        # 项目
        ttk_bs.Label(main_frame, text="项目:", font=("Microsoft YaHei", 12, "bold")).pack(anchor=W)
        ttk_bs.Label(main_frame, text=project or "无", font=("Microsoft YaHei", 11)).pack(anchor=W, pady=(0, 10))
        
        # 描述
        ttk_bs.Label(main_frame, text="描述:", font=("Microsoft YaHei", 12, "bold")).pack(anchor=W)
        desc_text = tk.Text(main_frame, height=4, font=("Microsoft YaHei", 10))
        desc_text.insert("1.0", description or "无描述")
        desc_text.config(state="disabled")
        desc_text.pack(fill=X, pady=(0, 10))
        
        # 分类信息
        info_frame = ttk_bs.Frame(main_frame)
        info_frame.pack(fill=X, pady=10)
        
        ttk_bs.Label(info_frame, text=f"优先级: {self.priority_names.get(priority, '未知')}", 
                    font=("Microsoft YaHei", 11)).pack(anchor=W)
        ttk_bs.Label(info_frame, text=f"GTD标签: {self.gtd_names.get(gtd_tag, gtd_tag)}", 
                    font=("Microsoft YaHei", 11)).pack(anchor=W)
        ttk_bs.Label(info_frame, text=f"截止日期: {due_date}", 
                    font=("Microsoft YaHei", 11)).pack(anchor=W)
        ttk_bs.Label(info_frame, text=f"提醒时间: {reminder_time}", 
                    font=("Microsoft YaHei", 11)).pack(anchor=W)
        ttk_bs.Label(info_frame, text=f"状态: {status}", 
                    font=("Microsoft YaHei", 11)).pack(anchor=W)
        ttk_bs.Label(info_frame, text=f"创建时间: {created_at}", 
                    font=("Microsoft YaHei", 11)).pack(anchor=W)
        
        # 操作按钮
        button_frame = ttk_bs.Frame(main_frame)
        button_frame.pack(fill=X, pady=20)
        
        if status == 'pending':
            ttk_bs.Button(
                button_frame, 
                text="标记为完成", 
                command=lambda: self.mark_todo_completed(todo_id, detail_window, on_update_callback),
                bootstyle="success"
            ).pack(side=LEFT, padx=(0, 10))
        
        ttk_bs.Button(
            button_frame, 
            text="删除", 
            command=lambda: self.delete_todo(todo_id, detail_window, on_update_callback),
            bootstyle="danger"
        ).pack(side=LEFT, padx=(0, 10))
        
        ttk_bs.Button(
            button_frame, 
            text="关闭", 
            command=detail_window.destroy,
            bootstyle="secondary"
        ).pack(side=RIGHT)
    
    def mark_todo_completed(self, todo_id, window, on_update_callback):
        """标记待办事项为完成"""
        self.db_manager.mark_todo_completed(todo_id)
        window.destroy()
        messagebox.showinfo("成功", "待办事项已标记为完成！")
        if on_update_callback:
            on_update_callback()
    
    def delete_todo(self, todo_id, window, on_update_callback):
        """删除待办事项"""
        if messagebox.askyesno("确认删除", "确定要删除这个待办事项吗？"):
            self.db_manager.delete_todo(todo_id)
            window.destroy()
            messagebox.showinfo("成功", "待办事项已删除！")
            if on_update_callback:
                on_update_callback()
    
    def create_summary_panel(self, parent):
        """创建汇总面板"""
        # 创建水平布局的容器
        horizontal_frame = ttk_bs.Frame(parent)
        horizontal_frame.pack(fill=BOTH, expand=True)
        
        summary_labels = {}
        
        # 总计标签 - 左侧
        summary_labels["total"] = ttk_bs.Label(
            horizontal_frame, 
            text="总计: 0", 
            font=("Microsoft YaHei", 11, "bold"),
            bootstyle="primary"
        )
        summary_labels["total"].pack(side=LEFT, padx=(0, 15))
        
        # 已完成标签 - 右侧
        summary_labels["completed"] = ttk_bs.Label(
            horizontal_frame, 
            text="已完成: 0", 
            font=("Microsoft YaHei", 11),
            bootstyle="success"
        )
        summary_labels["completed"].pack(side=LEFT)
        
        return summary_labels 