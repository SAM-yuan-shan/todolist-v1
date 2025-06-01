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
                
                # 在主线程中更新UI - 使用更安全的方式
                def update_ui():
                    try:
                        if success:
                            self.add_message("系统", message, "success")
                            self.status_label.config(text="连接正常", foreground="#28a745")
                        else:
                            self.add_message("系统", message, "error")
                            self.status_label.config(text="连接失败", foreground="#dc3545")
                        self.test_button.config(state="normal")
                    except Exception as e:
                        print(f"更新UI时出错: {e}")
                
                # 使用更安全的方式调度UI更新
                try:
                    self.test_button.after(0, update_ui)
                except Exception as e:
                    print(f"调度UI更新时出错: {e}")
                
            except Exception as e:
                def update_error():
                    try:
                        self.add_message("系统", f"测试连接时出错: {str(e)}", "error")
                        self.status_label.config(text="测试失败", foreground="#dc3545")
                        self.test_button.config(state="normal")
                    except Exception as ui_e:
                        print(f"更新错误UI时出错: {ui_e}")
                
                try:
                    self.test_button.after(0, update_error)
                except Exception as e:
                    print(f"调度错误UI更新时出错: {e}")
        
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
                self.ai_assistant.process_user_input(user_text)
            finally:
                # 恢复发送按钮
                def restore_button():
                    try:
                        self.send_button.config(state="normal")
                        self.status_label.config(text="就绪", foreground="#28a745")
                    except Exception as e:
                        print(f"恢复按钮状态时出错: {e}")
                
                try:
                    self.send_button.after(0, restore_button)
                except Exception as e:
                    print(f"调度按钮恢复时出错: {e}")
        
        threading.Thread(target=process_response, daemon=True).start()
    
    def add_message(self, sender, message, style="secondary"):
        """添加消息到聊天显示区域"""
        def _add_message_main_thread():
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 滚动到底部
                self.chat_display.see(tk.END)
                
                # 插入消息
                self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: ", style)
                self.chat_display.insert(tk.END, f"{message}\n\n")
                
                # 自动滚动到底部
                self.chat_display.see(tk.END)
            except Exception as e:
                print(f"添加消息时出错: {e}")
        
        # 确保在主线程中执行UI更新
        try:
            self.chat_display.after(0, _add_message_main_thread)
        except Exception as e:
            print(f"调度UI更新时出错: {e}")
    
    def add_streaming_message(self, sender, style="secondary"):
        """开始流式消息，返回消息标识符"""
        def _add_streaming_message_main_thread():
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # 滚动到底部
                self.chat_display.see(tk.END)
                
                # 插入消息头
                self.chat_display.insert(tk.END, f"[{timestamp}] {sender}: ", style)
                
                # 记录消息开始位置
                start_pos = self.chat_display.index(tk.END + "-1c")
                
                return {
                    'sender': sender,
                    'timestamp': timestamp,
                    'start_pos': start_pos,
                    'current_content': ''
                }
            except Exception as e:
                print(f"开始流式消息时出错: {e}")
                return None
        
        # 在主线程中执行并返回结果
        try:
            return self.chat_display.tk.call('after', 'idle', _add_streaming_message_main_thread)
        except Exception as e:
            print(f"调度流式消息时出错: {e}")
            # 直接调用作为备选方案
            timestamp = datetime.now().strftime("%H:%M:%S")
            return {
                'sender': sender,
                'timestamp': timestamp,
                'start_pos': None,
                'current_content': ''
            }
    
    def update_streaming_message(self, message_info, new_content, style=None):
        """更新流式消息内容"""
        if not message_info:
            return
            
        def _update_streaming_message_main_thread():
            try:
                # 添加新内容到当前内容
                message_info['current_content'] += new_content
                
                # 获取当前位置
                current_pos = self.chat_display.index(tk.END + "-1c")
                
                # 插入新内容
                if style:
                    self.chat_display.insert(current_pos, new_content, style)
                else:
                    self.chat_display.insert(current_pos, new_content)
                
                # 自动滚动到底部
                self.chat_display.see(tk.END)
                
                # 强制更新显示
                self.chat_display.update_idletasks()
                
            except Exception as e:
                print(f"更新流式消息出错: {e}")
        
        # 在主线程中执行
        try:
            self.chat_display.after(0, _update_streaming_message_main_thread)
        except Exception as e:
            print(f"调度流式消息更新时出错: {e}")
    
    def finish_streaming_message(self, message_info):
        """完成流式消息"""
        if not message_info:
            return
            
        def _finish_streaming_message_main_thread():
            try:
                # 添加换行符结束消息
                current_pos = self.chat_display.index(tk.END + "-1c")
                self.chat_display.insert(current_pos, "\n\n")
                
                # 滚动到底部
                self.chat_display.see(tk.END)
                
            except Exception as e:
                print(f"完成流式消息出错: {e}")
        
        # 在主线程中执行
        try:
            self.chat_display.after(0, _finish_streaming_message_main_thread)
        except Exception as e:
            print(f"调度流式消息完成时出错: {e}")
    
    def show_gtd_quadrant_confirmation(self, task_info, user_input):
        """显示GTD和四象限确认对话框"""
        import tkinter as tk
        from tkinter import ttk
        
        # 创建确认窗口
        confirm_window = tk.Toplevel()
        confirm_window.title("AI分析结果确认")
        confirm_window.geometry("600x500")
        confirm_window.resizable(False, False)
        confirm_window.grab_set()  # 模态窗口
        
        # 居中显示
        confirm_window.transient(self.chat_display.winfo_toplevel())
        confirm_window.geometry("+%d+%d" % (
            confirm_window.winfo_toplevel().winfo_rootx() + 50,
            confirm_window.winfo_toplevel().winfo_rooty() + 50
        ))
        
        main_frame = ttk.Frame(confirm_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame, 
            text="🤖 AI智能分析结果确认", 
            font=("Microsoft YaHei", 14, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # 任务信息显示
        info_frame = ttk.LabelFrame(main_frame, text="📋 任务信息", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 任务标题
        ttk.Label(info_frame, text="任务标题:", font=("Microsoft YaHei", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        ttk.Label(info_frame, text=task_info['title'], font=("Microsoft YaHei", 10)).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # 项目
        ttk.Label(info_frame, text="项目:", font=("Microsoft YaHei", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        ttk.Label(info_frame, text=task_info['project'], font=("Microsoft YaHei", 10)).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=5)
        
        # GTD标签确认区域
        gtd_frame = ttk.LabelFrame(main_frame, text="🏷️ GTD标签确认", padding="15")
        gtd_frame.pack(fill=tk.X, pady=(0, 15))
        
        gtd_options = [
            ("next-action", "下一步行动", "立即可执行的具体行动"),
            ("waiting-for", "等待中", "等待他人回复或外部条件"),
            ("someday-maybe", "将来/也许", "未来可能要做的事情"),
            ("inbox", "收件箱", "需要进一步处理的事项")
        ]
        
        gtd_var = tk.StringVar(value=task_info['gtd_tag'])
        
        ttk.Label(gtd_frame, text=f"AI建议: {self._get_gtd_name(task_info['gtd_tag'])}", 
                 font=("Microsoft YaHei", 10, "bold"), foreground="#007bff").pack(anchor="w", pady=(0, 10))
        
        for value, name, desc in gtd_options:
            radio_frame = ttk.Frame(gtd_frame)
            radio_frame.pack(fill=tk.X, pady=2)
            
            radio = ttk.Radiobutton(radio_frame, text=name, variable=gtd_var, value=value)
            radio.pack(side=tk.LEFT)
            
            desc_label = ttk.Label(radio_frame, text=f"({desc})", 
                                  font=("Microsoft YaHei", 9), foreground="#666")
            desc_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 四象限确认区域
        quadrant_frame = ttk.LabelFrame(main_frame, text="⭐ 四象限确认", padding="15")
        quadrant_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 重要性和紧急性
        importance_var = tk.BooleanVar(value=bool(task_info.get('importance', 0)))
        urgency_var = tk.BooleanVar(value=bool(task_info.get('urgency', 0)))
        
        current_priority_name = self._get_priority_name(task_info['priority'])
        ttk.Label(quadrant_frame, text=f"AI建议: {current_priority_name}", 
                 font=("Microsoft YaHei", 10, "bold"), foreground="#007bff").pack(anchor="w", pady=(0, 10))
        
        check_frame = ttk.Frame(quadrant_frame)
        check_frame.pack(fill=tk.X)
        
        ttk.Checkbutton(check_frame, text="重要 (影响长远目标或核心价值)", 
                       variable=importance_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(check_frame, text="紧急 (有明确时间限制或立即后果)", 
                       variable=urgency_var).pack(anchor="w", pady=2)
        
        # 实时更新优先级显示
        priority_display = ttk.Label(quadrant_frame, text="", font=("Microsoft YaHei", 10, "bold"))
        priority_display.pack(anchor="w", pady=(10, 0))
        
        def update_priority_display():
            importance = importance_var.get()
            urgency = urgency_var.get()
            if importance and urgency:
                priority_text = "→ 第一象限: 重要且紧急 (立即执行)"
                priority_display.config(foreground="#dc3545")
            elif importance and not urgency:
                priority_text = "→ 第二象限: 重要但不紧急 (计划执行)"
                priority_display.config(foreground="#ffc107")
            elif not importance and urgency:
                priority_text = "→ 第三象限: 不重要但紧急 (委派执行)"
                priority_display.config(foreground="#17a2b8")
            else:
                priority_text = "→ 第四象限: 不重要且不紧急 (删除或推迟)"
                priority_display.config(foreground="#6c757d")
            
            priority_display.config(text=priority_text)
        
        # 绑定更新事件
        importance_var.trace('w', lambda *args: update_priority_display())
        urgency_var.trace('w', lambda *args: update_priority_display())
        update_priority_display()  # 初始显示
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        result = {'confirmed': False, 'task_info': None}
        
        def confirm_action():
            # 更新任务信息
            updated_task_info = task_info.copy()
            updated_task_info['gtd_tag'] = gtd_var.get()
            updated_task_info['importance'] = 1 if importance_var.get() else 0
            updated_task_info['urgency'] = 1 if urgency_var.get() else 0
            
            # 重新计算优先级
            importance = importance_var.get()
            urgency = urgency_var.get()
            if importance and urgency:
                updated_task_info['priority'] = 1
            elif importance and not urgency:
                updated_task_info['priority'] = 2
            elif not importance and urgency:
                updated_task_info['priority'] = 3
            else:
                updated_task_info['priority'] = 4
            
            result['confirmed'] = True
            result['task_info'] = updated_task_info
            confirm_window.destroy()
        
        def cancel_action():
            result['confirmed'] = False
            confirm_window.destroy()
        
        def reanalyze_action():
            result['confirmed'] = False
            result['reanalyze'] = True
            confirm_window.destroy()
        
        # 按钮
        ttk.Button(button_frame, text="✅ 确认并添加", 
                  command=confirm_action, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🔄 重新分析", 
                  command=reanalyze_action, width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="❌ 取消", 
                  command=cancel_action, width=15).pack(side=tk.LEFT)
        
        # 等待用户操作
        confirm_window.wait_window()
        
        # 处理结果
        if result['confirmed']:
            self.ai_assistant.confirm_add_task_with_updates(result['task_info'], user_input)
        elif result.get('reanalyze'):
            self.ai_assistant.reparse_task(user_input)
    
    def _get_priority_name(self, priority):
        """获取优先级名称"""
        priority_names = {
            1: "重要且紧急",
            2: "重要但不紧急", 
            3: "不重要但紧急",
            4: "不重要且不紧急"
        }
        return priority_names.get(priority, "未知")
    
    def show_task_confirmation(self, task_info, user_input):
        """显示任务确认界面 - 使用GTD和四象限确认对话框"""
        self.show_gtd_quadrant_confirmation(task_info, user_input)
    
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