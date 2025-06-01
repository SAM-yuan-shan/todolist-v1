"""
AI用户界面模块
包含AI助手的所有UI组件和交互功能
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, BOTH, LEFT, RIGHT, X, Y, W, E, N, S, TOP, BOTTOM
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import threading
from datetime import datetime


class AIUserInterface:
    """AI用户界面管理器"""
    
    def __init__(self, ai_assistant):
        """初始化AI用户界面"""
        self.ai_assistant = ai_assistant
        
        # UI组件
        self.chat_display = None
        self.user_input = None
        self.send_button = None
        self.status_label = None
        self.api_key_entry = None
        self.test_button = None
        self.clear_button = None
        
        # 任务确认相关
        self.confirmation_frame = None
        self.task_info = None
        self.user_input_cache = None
        
        # 操作确认相关
        self.operation_frame = None
        self.operation_info = None
    
    def create_ai_panel(self, parent):
        """创建AI助手面板"""
        # 主框架
        ai_frame = ttk_bs.LabelFrame(
            parent,
            text="AI智能助手",
            padding=15,
            bootstyle="success"
        )
        ai_frame.pack(fill=BOTH, expand=True)
        
        # API配置区域
        self._create_api_config_section(ai_frame)
        
        # 聊天区域
        self._create_chat_section(ai_frame)
        
        # 输入区域
        self._create_input_section(ai_frame)
        
        # 状态栏
        self._create_status_section(ai_frame)
        
        return ai_frame
    
    def _create_api_config_section(self, parent):
        """创建API配置区域"""
        config_frame = ttk_bs.LabelFrame(parent, text="API配置", padding=10)
        config_frame.pack(fill=X, pady=(0, 10))
        
        # API Key输入
        key_frame = ttk_bs.Frame(config_frame)
        key_frame.pack(fill=X, pady=(0, 5))
        
        ttk_bs.Label(key_frame, text="DeepSeek API Key:", font=("Microsoft YaHei", 10)).pack(anchor=W)
        self.api_key_entry = ttk_bs.Entry(key_frame, show="*", font=("Microsoft YaHei", 9))
        self.api_key_entry.pack(fill=X, pady=(2, 0))
        self.api_key_entry.insert(0, self.ai_assistant.ai_core.api_key)
        
        # 配置按钮
        config_btn_frame = ttk_bs.Frame(config_frame)
        config_btn_frame.pack(fill=X)
        
        save_config_btn = ttk_bs.Button(
            config_btn_frame,
            text="保存配置",
            command=self.save_api_config,
            bootstyle="primary-outline",
            width=10
        )
        save_config_btn.pack(side=LEFT, padx=(0, 5))
        
        self.test_button = ttk_bs.Button(
            config_btn_frame,
            text="测试连接",
            command=self.test_api_connection,
            bootstyle="info-outline",
            width=10
        )
        self.test_button.pack(side=LEFT, padx=(0, 5))
        
        self.clear_button = ttk_bs.Button(
            config_btn_frame,
            text="清空历史",
            command=self.clear_chat_history,
            bootstyle="warning-outline",
            width=10
        )
        self.clear_button.pack(side=LEFT)
    
    def _create_chat_section(self, parent):
        """创建聊天区域"""
        chat_frame = ttk_bs.LabelFrame(parent, text="对话历史", padding=10)
        chat_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # 聊天显示区域
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            height=15,
            font=("Microsoft YaHei", 10),
            bg="#f8f9fa",
            fg="#212529",
            selectbackground="#007bff",
            selectforeground="white"
        )
        self.chat_display.pack(fill=BOTH, expand=True)
        
        # 配置文本标签样式
        self.chat_display.tag_configure("user", foreground="#007bff", font=("Microsoft YaHei", 10, "bold"))
        self.chat_display.tag_configure("assistant", foreground="#28a745", font=("Microsoft YaHei", 10))
        self.chat_display.tag_configure("system", foreground="#6c757d", font=("Microsoft YaHei", 9, "italic"))
        self.chat_display.tag_configure("error", foreground="#dc3545", font=("Microsoft YaHei", 10, "bold"))
        self.chat_display.tag_configure("success", foreground="#28a745", font=("Microsoft YaHei", 10, "bold"))
        self.chat_display.tag_configure("warning", foreground="#ffc107", font=("Microsoft YaHei", 10, "bold"))
        self.chat_display.tag_configure("info", foreground="#17a2b8", font=("Microsoft YaHei", 10, "bold"))
        
        # 初始欢迎消息
        self.add_message("系统", "AI智能助手已启动！我可以帮您智能管理待办事项。", "info")
        self.add_message("系统", "支持功能：添加任务、查看任务、修改任务、删除任务、标记完成等", "system")
    
    def _create_input_section(self, parent):
        """创建输入区域"""
        input_frame = ttk_bs.Frame(parent)
        input_frame.pack(fill=X, pady=(0, 10))
        
        # 输入提示
        ttk_bs.Label(input_frame, text="请输入您的需求:", font=("Microsoft YaHei", 10)).pack(anchor=W, pady=(0, 5))
        
        # 输入框和按钮
        input_container = ttk_bs.Frame(input_frame)
        input_container.pack(fill=X)
        
        self.user_input = ttk_bs.Entry(
            input_container,
            font=("Microsoft YaHei", 11),
            bootstyle="primary"
        )
        self.user_input.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        
        self.send_button = ttk_bs.Button(
            input_container,
            text="发送",
            command=self.send_message,
            bootstyle="primary",
            width=8
        )
        self.send_button.pack(side=RIGHT)
        
        # 绑定回车键
        self.user_input.bind('<Return>', lambda e: self.send_message())
        
        # 输入框焦点样式
        def on_focus_in(event):
            self.user_input.configure(bootstyle="success")
        
        def on_focus_out(event):
            self.user_input.configure(bootstyle="primary")
        
        self.user_input.bind('<FocusIn>', on_focus_in)
        self.user_input.bind('<FocusOut>', on_focus_out)
        
        # 示例提示
        examples_frame = ttk_bs.Frame(input_frame)
        examples_frame.pack(fill=X, pady=(5, 0))
        
        ttk_bs.Label(
            examples_frame,
            text="示例: '添加重要任务：明天上午开会' | '查看所有待处理任务' | '完成任务1'",
            font=("Microsoft YaHei", 8),
            foreground="#6c757d"
        ).pack(anchor=W)
    
    def _create_status_section(self, parent):
        """创建状态栏"""
        status_frame = ttk_bs.Frame(parent)
        status_frame.pack(fill=X)
        
        self.status_label = ttk_bs.Label(
            status_frame,
            text="就绪",
            font=("Microsoft YaHei", 9),
            foreground="#28a745"
        )
        self.status_label.pack(anchor=W)
    
    def save_api_config(self):
        """保存API配置"""
        api_key = self.api_key_entry.get().strip()
        if api_key:
            self.ai_assistant.ai_core.update_api_key(api_key)
            if self.ai_assistant.config_manager:
                self.ai_assistant.config_manager.set_api_key(api_key)
            self.add_message("系统", "API配置已保存", "success")
        else:
            messagebox.showwarning("警告", "请输入有效的API Key")
    
    def test_api_connection(self):
        """测试API连接"""
        self.status_label.config(text="正在测试连接...", foreground="#ffc107")
        self.test_button.config(state="disabled")
        
        def test_connection():
            try:
                success, message = self.ai_assistant.ai_core.test_api_connection()
                
                # 在主线程中更新UI
                def update_ui():
                    if success:
                        self.add_message("系统", message, "success")
                        self.status_label.config(text="连接正常", foreground="#28a745")
                    else:
                        self.add_message("系统", message, "error")
                        self.status_label.config(text="连接失败", foreground="#dc3545")
                    self.test_button.config(state="normal")
                
                self.test_button.after(0, update_ui)
                
            except Exception as e:
                def update_error():
                    self.add_message("系统", f"测试连接时出错: {str(e)}", "error")
                    self.status_label.config(text="测试失败", foreground="#dc3545")
                    self.test_button.config(state="normal")
                
                self.test_button.after(0, update_error)
        
        # 在后台线程中测试连接
        threading.Thread(target=test_connection, daemon=True).start()
    
    def clear_chat_history(self):
        """清空聊天历史"""
        if messagebox.askyesno("确认", "确定要清空聊天历史吗？"):
            self.chat_display.delete(1.0, tk.END)
            self.ai_assistant.ai_core.clear_cache()
            self.add_message("系统", "聊天历史已清空", "info")
    
    def send_message(self):
        """发送消息"""
        user_text = self.user_input.get().strip()
        if not user_text:
            return
        
        # 清空输入框
        self.user_input.delete(0, tk.END)
        
        # 显示用户消息
        self.add_message("用户", user_text, "user")
        
        # 更新状态
        self.status_label.config(text="AI正在思考...", foreground="#ffc107")
        self.send_button.config(state="disabled")
        
        # 在后台处理AI响应
        def process_response():
            try:
                self.ai_assistant.process_ai_response(user_text)
            finally:
                # 恢复发送按钮
                def restore_button():
                    self.send_button.config(state="normal")
                    self.status_label.config(text="就绪", foreground="#28a745")
                
                self.send_button.after(0, restore_button)
        
        threading.Thread(target=process_response, daemon=True).start()
    
    def add_message(self, sender, message, style="secondary"):
        """添加消息到聊天显示区域"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 滚动到底部
        self.chat_display.see(tk.END)
        
        # 插入消息
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: ", style)
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        # 自动滚动到底部
        self.chat_display.see(tk.END)
    
    def add_streaming_message(self, sender, message, style="secondary"):
        """添加流式消息（用于流式响应）"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 滚动到底部
        self.chat_display.see(tk.END)
        
        # 插入消息头
        self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: ", style)
        
        # 返回消息ID用于后续更新
        return f"{sender}_{timestamp}"
    
    def update_streaming_message(self, message_id, new_content, style=None):
        """更新流式消息内容"""
        # 简化实现：直接添加内容
        self.chat_display.insert(tk.END, new_content)
        self.chat_display.see(tk.END)
    
    def show_task_confirmation(self, task_info, user_input):
        """显示任务确认界面 - 使用弹出对话框"""
        self.task_info = task_info
        self.user_input_cache = user_input
        
        # 构建确认消息
        priority_name = self.ai_assistant.task_parser.get_priority_name(task_info['priority'])
        gtd_name = self._get_gtd_name(task_info['gtd_tag'])
        
        confirm_message = f"""AI已解析您的任务，请确认：

📋 任务标题: {task_info['title']}
📁 项目: {task_info['project']}
⭐ 优先级: {priority_name}
🏷️ GTD标签: {gtd_name}
📅 截止日期: {task_info['due_date'] or '无'}
⏰ 提醒时间: {task_info['reminder_time'] or '无'}

📝 描述: {task_info['description']}

是否确认添加此任务？"""
        
        # 使用tkinter的messagebox显示确认对话框
        import tkinter.messagebox as msgbox
        
        result = msgbox.askyesnocancel(
            "任务确认", 
            confirm_message,
            icon='question'
        )
        
        if result is True:  # 用户点击"是"
            self.ai_assistant.confirm_add_task(user_input)
        elif result is False:  # 用户点击"否" - 重新理解
            self.ai_assistant.reparse_task(user_input)
        # result is None 表示用户点击"取消"，不做任何操作
        
        # 清理缓存
        self.task_info = None
        self.user_input_cache = None
    
    def show_operation_confirmation(self, action, ai_response, user_input):
        """显示操作确认界面 - 使用弹出对话框"""
        self.operation_info = {
            'action': action,
            'ai_response': ai_response,
            'user_input': user_input
        }
        
        # 构建确认消息
        action_names = {
            'delete_task': '删除任务',
            'complete_task': '完成任务',
            'update_task': '更新任务'
        }
        
        action_name = action_names.get(action, action)
        
        confirm_message = f"""AI建议执行操作: {action_name}

🤖 AI分析:
{ai_response}

📝 您的输入: {user_input}

是否确认执行此操作？"""
        
        # 使用tkinter的messagebox显示确认对话框
        import tkinter.messagebox as msgbox
        
        result = msgbox.askyesnocancel(
            "操作确认", 
            confirm_message,
            icon='question'
        )
        
        if result is True:  # 用户点击"是"
            self.ai_assistant.execute_operation(action, user_input)
        elif result is False:  # 用户点击"否" - 重新理解
            self.ai_assistant.reunderstand_request(user_input)
        # result is None 表示用户点击"取消"，不做任何操作
        
        # 清理缓存
        self.operation_info = None
    
    def _get_gtd_name(self, gtd_tag):
        """获取GTD标签名称"""
        gtd_names = {
            'next-action': '下一步行动',
            'waiting-for': '等待中',
            'someday-maybe': '将来/也许',
            'inbox': '收件箱'
        }
        return gtd_names.get(gtd_tag, gtd_tag) 