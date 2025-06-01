"""
AI助手模块
集成DeepSeek API，智能理解和操作待办事项
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, BOTH, LEFT, RIGHT, X, Y, W, E, N, S, TOP, BOTTOM
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *
import requests
import json
import threading
from datetime import datetime, timedelta
import re

class KVCache:
    """KV缓存用于维护对话上下文"""
    def __init__(self):
        self.cache = []
        self.max_history = 20  # 最多保留20轮对话

    def update_cache(self, user_input, model_response):
        """更新KV缓存"""
        self.cache.append({"role": "user", "content": user_input})
        self.cache.append({"role": "assistant", "content": model_response})
        
        # 保持缓存大小
        if len(self.cache) > self.max_history * 2:
            self.cache = self.cache[-self.max_history * 2:]

    def get_context(self):
        """获取当前对话上下文"""
        return self.cache

    def clear_cache(self):
        """清空缓存"""
        self.cache = []

class AIAssistant:
    def __init__(self, database_manager, ui_components, config_manager=None):
        """初始化AI助手"""
        self.database_manager = database_manager
        self.ui_components = ui_components
        self.config_manager = config_manager
        
        # 从配置管理器获取API配置
        if config_manager:
            self.api_key = config_manager.get_api_key()
            self.api_url = config_manager.get('ai_assistant.api_url', 'https://api.deepseek.com/v1/chat/completions')
            self.model = config_manager.get('ai_assistant.model', 'deepseek-chat')
            self.temperature = config_manager.get('ai_assistant.temperature', 0.7)
            self.max_tokens = config_manager.get('ai_assistant.max_tokens', 1000)
            self.mcp_enabled = config_manager.is_mcp_enabled()
        else:
            # 默认配置
            self.api_key = "your_api_key_here"
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model = "deepseek-chat"
            self.temperature = 0.7
            self.max_tokens = 1000
            self.mcp_enabled = False
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 初始化SQLite连接（如果启用MCP）
        if self.mcp_enabled:
            self.init_sql_connection()
        
        # 更新系统提示词
        self.system_prompt = self._build_system_prompt()
        
        # 初始化KV缓存
        self.kv_cache = KVCache()
        
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
        
        # 系统提示词
        self.system_prompt = """你是一个智能待办事项管理助手，具备强大的任务智能解析能力。

【重要】在回答任何问题之前，你必须：
1. 仔细查看和分析当前提供的待办事项数据
2. 基于实际的数据库内容来回答问题
3. 如果用户询问任务情况，要准确引用具体的任务ID、标题和状态
4. 始终以当前数据库的实际内容为准，不要假设或猜测

【智能解析能力】当用户输入任务时，系统会自动：
1. 🎯 四象限分类：根据关键词自动判断重要性和紧急性
   - 重要且紧急：包含"重要"+"紧急"关键词，如会议、汇报、bug修复
   - 重要不紧急：包含"重要"但无紧急词汇，如学习、计划、目标
   - 不重要但紧急：包含"紧急"但无重要词汇，如临时事务
   - 不重要不紧急：其他日常任务

2. 🏷️ GTD标签自动分类：
   - 下一步行动：包含"立即"、"马上"、"现在"、"今天"等
   - 等待中：包含"等待"、"等"、"依赖"等
   - 将来/也许：包含"将来"、"以后"、"有空"、"学习"等
   - 收件箱：其他未明确分类的任务

3. 📁 项目智能推断：
   - 工作项目：包含"工作"、"公司"、"会议"、"汇报"等
   - 学习项目：包含"学习"、"课程"、"阅读"、"研究"等
   - 生活项目：包含"买"、"购"、"家"、"健康"、"运动"等
   - 个人项目：包含"个人"、"爱好"、"兴趣"等

4. ⏰ 时间信息提取：
   - 自动识别"今天"、"明天"、"下周"、"3天后"等时间表达
   - 支持具体日期格式：2024-01-15、1月15日等
   - 支持时间点：上午9点、下午2:30等

你的能力包括：
1. 查看所有待办事项 - 基于实际数据库内容提供准确信息
2. 智能添加待办事项 - 自动解析并分类用户输入的任务
3. 修改现有待办事项 - 基于现有任务ID进行修改
4. 删除待办事项 - 根据任务ID或标题精确删除
5. 标记任务完成 - 将指定任务状态改为已完成
6. 按项目、优先级、GTD标签筛选任务 - 基于实际数据进行筛选
7. 分析任务分布和统计信息 - 提供基于真实数据的分析

待办事项包含以下字段：
- id: 任务ID（唯一标识符）
- title: 标题（任务名称）
- description: 描述（详细说明，包含智能解析结果）
- project: 项目名称（任务所属项目）
- priority: 优先级(1:重要紧急, 2:重要不紧急, 3:不重要紧急, 4:不重要不紧急)
- gtd_tag: GTD标签(next-action:下一步行动, waiting-for:等待中, someday-maybe:将来/也许, inbox:收件箱)
- due_date: 截止日期(YYYY-MM-DD格式)
- reminder_time: 提醒时间(YYYY-MM-DD HH:MM格式)
- status: 状态(pending:待处理, completed:已完成)

回答规范：
1. 每次回答前，先简要总结当前数据库状态（如：总任务数、待处理数、已完成数）
2. 如果用户询问具体任务，要引用准确的任务ID和标题
3. 提供操作建议时，要基于实际存在的任务
4. 当用户要求添加任务时，说明系统会自动进行智能分类
5. 对于复杂操作，提供确认界面让用户选择执行或重新理解

示例对话：
用户："添加一个重要任务：明天上午开会讨论项目进展"
助手："我将为您添加这个任务。系统会自动分析：
- 四象限：重要且紧急（包含'重要'和'明天'）
- GTD标签：下一步行动（包含'明天'）
- 项目：工作项目（包含'开会'和'项目'）
- 时间：明天的日期
请确认是否添加？"

记住：始终基于实际数据库内容回答，充分利用智能解析功能，为用户提供准确、高效的任务管理服务。"""

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
        config_frame = ttk_bs.LabelFrame(ai_frame, text="API配置", padding=10)
        config_frame.pack(fill=X, pady=(0, 10))
        
        # API Key输入
        key_frame = ttk_bs.Frame(config_frame)
        key_frame.pack(fill=X, pady=(0, 5))
        
        ttk_bs.Label(key_frame, text="DeepSeek API Key:", font=("Microsoft YaHei", 10)).pack(anchor=W)
        self.api_key_entry = ttk_bs.Entry(key_frame, show="*", font=("Microsoft YaHei", 9))
        self.api_key_entry.pack(fill=X, pady=(2, 0))
        self.api_key_entry.insert(0, self.api_key)
        
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
        
        test_api_btn = ttk_bs.Button(
            config_btn_frame,
            text="测试连接",
            command=self.test_api_connection,
            bootstyle="info-outline",
            width=10
        )
        test_api_btn.pack(side=LEFT)
        
        clear_history_btn = ttk_bs.Button(
            config_btn_frame,
            text="清空历史",
            command=self.clear_chat_history,
            bootstyle="warning-outline",
            width=10
        )
        clear_history_btn.pack(side=RIGHT)
        
        # 对话区域
        chat_frame = ttk_bs.LabelFrame(ai_frame, text="对话区域", padding=10)
        chat_frame.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # 聊天历史显示
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            height=15,
            font=("Microsoft YaHei", 10),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.chat_display.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # 输入区域
        input_frame = ttk_bs.Frame(chat_frame)
        input_frame.pack(fill=X)
        
        # 用户输入
        self.user_input = ttk_bs.Entry(
            input_frame,
            font=("Microsoft YaHei", 10)
        )
        self.user_input.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        self.user_input.bind('<Return>', lambda e: self.send_message())
        
        # 添加占位符效果
        placeholder_text = "请输入您的指令，例如：查看所有待办事项、添加一个新任务等..."
        self.user_input.insert(0, placeholder_text)
        self.user_input.config(foreground='gray')
        
        def on_focus_in(event):
            if self.user_input.get() == placeholder_text:
                self.user_input.delete(0, tk.END)
                self.user_input.config(foreground='black')
        
        def on_focus_out(event):
            if not self.user_input.get():
                self.user_input.insert(0, placeholder_text)
                self.user_input.config(foreground='gray')
        
        self.user_input.bind('<FocusIn>', on_focus_in)
        self.user_input.bind('<FocusOut>', on_focus_out)
        
        # 发送按钮
        send_btn = ttk_bs.Button(
            input_frame,
            text="发送",
            command=self.send_message,
            bootstyle="success",
            width=8
        )
        send_btn.pack(side=RIGHT)
        
        # 操作确认区域
        self.confirm_frame = ttk_bs.LabelFrame(ai_frame, text="操作确认", padding=10)
        # 初始隐藏
        
        # 状态栏
        status_frame = ttk_bs.Frame(ai_frame)
        status_frame.pack(fill=X, pady=(5, 0))
        
        self.status_label = ttk_bs.Label(
            status_frame,
            text="就绪",
            font=("Microsoft YaHei", 9),
            bootstyle="secondary"
        )
        self.status_label.pack(side=LEFT)
        
        # 添加欢迎消息
        self.add_message("AI助手", "您好！我是您的智能待办事项助手。我可以帮您：\n\n• 查看和分析待办事项\n• 添加新任务\n• 修改现有任务\n• 删除或完成任务\n• 按条件筛选任务\n\n请告诉我您需要什么帮助！", "info")

    def save_api_config(self):
        """保存API配置"""
        self.api_key = self.api_key_entry.get().strip()
        if self.api_key and self.api_key != "your_api_key_here":
            self.headers["Authorization"] = f"Bearer {self.api_key}"
            self.status_label.config(text="API配置已保存")
            messagebox.showinfo("配置保存", "API配置已保存成功！")
        else:
            messagebox.showwarning("配置错误", "请输入有效的API Key！")

    def test_api_connection(self):
        """测试API连接"""
        if not self.api_key or self.api_key == "your_api_key_here":
            messagebox.showwarning("配置错误", "请先配置API Key！")
            return
        
        def test_connection():
            try:
                self.status_label.config(text="测试连接中...")
                response = self.call_deepseek_api("你好，请回复'连接成功'")
                if response and "连接成功" in response:
                    self.status_label.config(text="API连接正常")
                    messagebox.showinfo("连接测试", "API连接测试成功！")
                else:
                    self.status_label.config(text="API连接异常")
                    messagebox.showerror("连接测试", f"API连接测试失败：{response}")
            except Exception as e:
                self.status_label.config(text="API连接失败")
                messagebox.showerror("连接测试", f"API连接测试失败：{str(e)}")
        
        threading.Thread(target=test_connection, daemon=True).start()

    def clear_chat_history(self):
        """清空聊天历史"""
        self.kv_cache.clear_cache()
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.add_message("AI助手", "聊天历史已清空。有什么可以帮您的吗？", "info")

    def send_message(self):
        """发送用户消息"""
        user_text = self.user_input.get().strip()
        placeholder_text = "请输入您的指令，例如：查看所有待办事项、添加一个新任务等..."
        
        # 检查是否为占位符文本或空文本
        if not user_text or user_text == placeholder_text:
            return
        
        if not self.api_key or self.api_key == "your_api_key_here":
            messagebox.showwarning("配置错误", "请先配置API Key！")
            return
        
        # 清空输入框并恢复占位符
        self.user_input.delete(0, tk.END)
        self.user_input.insert(0, placeholder_text)
        self.user_input.config(foreground='gray')
        
        # 显示用户消息
        self.add_message("用户", user_text, "primary")
        
        # 异步处理AI响应
        threading.Thread(target=self.process_ai_response, args=(user_text,), daemon=True).start()

    def process_ai_response(self, user_input):
        """处理AI响应"""
        message_id = None
        try:
            self.status_label.config(text="AI思考中...")
            
            # 获取当前待办事项数据
            todo_context = self.get_todo_context()
            
            # 构建完整的用户输入
            full_input = f"当前待办事项数据：\n{todo_context}\n\n用户指令：{user_input}"
            
            # 使用非流式输出以避免性能问题
            ai_response = self.call_deepseek_api(full_input)
            
            if ai_response and not ai_response.startswith("API请求失败") and not ai_response.startswith("处理响应失败"):
                self.status_label.config(text="就绪")
                
                # 添加AI回复到聊天显示
                self.add_message("AI助手", ai_response, "success")
                
                # 解析AI响应，检查是否包含操作指令
                self.parse_ai_response(ai_response, user_input)
            else:
                self.status_label.config(text="AI响应失败")
                self.add_message("AI助手", ai_response or "抱歉，我现在无法处理您的请求。请检查网络连接或API配置。", "danger")
                
        except Exception as e:
            self.status_label.config(text="处理失败")
            error_msg = f"处理请求时出现错误：{str(e)}"
            self.add_message("AI助手", error_msg, "danger")

    def call_deepseek_api_stream(self, user_input, message_id, temperature=0.7, max_tokens=1000):
        """调用DeepSeek API（流式输出）- 暂时禁用以解决性能问题"""
        # 暂时使用非流式输出
        return self.call_deepseek_api(user_input, temperature, max_tokens)

    def add_streaming_message(self, sender, message, style="secondary"):
        """添加流式消息到聊天显示区域 - 简化版本"""
        return self.add_message(sender, message, style)

    def update_streaming_message(self, message_id, new_content, style=None):
        """更新流式消息内容 - 简化版本"""
        # 暂时不使用流式更新，直接返回
        pass

    def call_deepseek_api(self, user_input, temperature=0.7, max_tokens=1000):
        """调用DeepSeek API（非流式，保留用于测试连接）"""
        # 检查API Key是否有效
        if self.api_key == "your_api_key_here" or not self.api_key.strip():
            return self.offline_response(user_input)
        
        try:
            # 构建请求数据
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.kv_cache.get_context())
            messages.append({"role": "user", "content": user_input})
            
            data = {
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # 更新缓存
            self.kv_cache.update_cache(user_input, ai_response)
            
            return ai_response
            
        except requests.exceptions.RequestException as e:
            return self.offline_response(user_input, f"API请求失败：{str(e)}")
        except Exception as e:
            return self.offline_response(user_input, f"处理响应失败：{str(e)}")

    def offline_response(self, user_input, error_msg=None):
        """离线模式响应"""
        # 获取当前数据库状态
        context = self.get_todo_context()
        
        # 基本的关键词检测
        user_input_lower = user_input.lower()
        
        if error_msg:
            response = f"⚠️ {error_msg}\n\n🔄 切换到离线模式为您服务：\n\n"
        else:
            response = "🤖 AI助手（离线模式）为您服务：\n\n"
        
        # 添加当前数据库状态
        response += f"📊 当前状态：\n{context}\n\n"
        
        # 根据用户输入提供相应的建议
        if any(word in user_input_lower for word in ["查看", "显示", "列出", "所有", "任务"]):
            response += "💡 建议操作：\n"
            response += "• 在主视图中查看四象限任务分布\n"
            response += "• 在日历视图中查看按日期排列的任务\n"
            response += "• 在项目视图中查看按项目分组的任务\n"
            
        elif any(word in user_input_lower for word in ["添加", "新增", "创建", "加"]):
            response += "📝 添加任务建议：\n"
            response += "• 请在左侧'添加待办事项'面板中填写任务信息\n"
            response += "• 系统会自动进行智能分类（四象限+GTD标签）\n"
            response += "• 支持设置截止日期和提醒时间\n"
            
        elif any(word in user_input_lower for word in ["删除", "移除", "完成"]):
            response += "🗑️ 任务操作建议：\n"
            response += "• 在主视图的四象限区域中找到对应任务\n"
            response += "• 点击任务右侧的操作按钮进行删除或标记完成\n"
            response += "• 也可以在其他视图中进行相同操作\n"
            
        elif any(word in user_input_lower for word in ["统计", "分析", "汇总"]):
            response += "📈 查看统计信息：\n"
            response += "• 主视图右上角有任务汇总面板\n"
            response += "• 汇总视图提供详细的统计分析\n"
            response += "• 可以查看项目分布、GTD标签分布等\n"
            
        else:
            response += "💡 可用功能：\n"
            response += "• 查看任务：'查看所有待办事项'\n"
            response += "• 添加任务：'添加新任务'\n"
            response += "• 任务操作：'删除任务'、'完成任务'\n"
            response += "• 查看统计：'显示任务统计'\n"
        
        response += "\n🔧 要启用完整AI功能，请：\n"
        response += "1. 在上方'API配置'中输入有效的DeepSeek API Key\n"
        response += "2. 点击'保存配置'和'测试连接'\n"
        response += "3. 重新发送您的指令"
        
        return response

    def get_todo_context(self):
        """获取当前待办事项上下文"""
        try:
            # 获取所有待办事项
            todos = self.database_manager.get_all_todos()
            
            # 获取统计信息
            stats = self.database_manager.get_statistics()
            
            # 构建简洁的上下文字符串
            context = f"=== 📊 数据库状态 ===\n"
            context += f"总任务:{stats['total']} | 待处理:{stats['pending']} | 已完成:{stats['completed']}\n"
            context += f"四象限分布: 重要紧急:{stats['quadrant_1']} | 重要不紧急:{stats['quadrant_2']} | 不重要紧急:{stats['quadrant_3']} | 不重要不紧急:{stats['quadrant_4']}\n\n"
            
            if todos:
                # 只显示待处理任务的简要信息
                pending_todos = [t for t in todos if t[4] == 'pending']
                
                if pending_todos:
                    context += f"=== ⏳ 待处理任务 ({len(pending_todos)}个) ===\n"
                    for todo in pending_todos[:10]:  # 最多显示10个
                        id, title, project, due_date, status, priority, gtd_tag = todo
                        priority_name = {1: "重要紧急", 2: "重要不紧急", 3: "不重要紧急", 4: "不重要不紧急"}.get(priority, "未知")
                        gtd_name = {"next-action": "下一步", "waiting-for": "等待", "someday-maybe": "将来", "inbox": "收件箱"}.get(gtd_tag, "未知")
                        
                        context += f"ID:{id} | {title} | {project or '无项目'} | {priority_name} | {gtd_name}"
                        if due_date:
                            context += f" | 截止:{due_date}"
                        context += "\n"
                    
                    if len(pending_todos) > 10:
                        context += f"... 还有 {len(pending_todos) - 10} 个任务\n"
                else:
                    context += "🎉 没有待处理任务\n"
            else:
                context += "📝 数据库为空，可以开始添加任务\n"
            
            return context
            
        except Exception as e:
            return f"❌ 获取数据失败：{str(e)}"

    def parse_ai_response(self, ai_response, user_input):
        """解析AI响应，检查是否包含操作指令"""
        # 检查是否包含操作关键词
        action_keywords = {
            "添加": "add",
            "新增": "add", 
            "创建": "add",
            "删除": "delete",
            "移除": "delete",
            "完成": "complete",
            "标记完成": "complete",
            "修改": "update",
            "更新": "update",
            "编辑": "update"
        }
        
        detected_action = None
        for keyword, action in action_keywords.items():
            if keyword in ai_response or keyword in user_input:
                detected_action = action
                break
        
        if detected_action:
            self.show_operation_confirmation(detected_action, ai_response, user_input)

    def show_operation_confirmation(self, action, ai_response, user_input):
        """显示操作确认界面"""
        # 显示确认框架
        self.confirm_frame.pack(fill=X, pady=(10, 0))
        
        # 清空之前的内容
        for widget in self.confirm_frame.winfo_children():
            widget.destroy()
        
        # 操作描述
        desc_label = ttk_bs.Label(
            self.confirm_frame,
            text=f"检测到操作请求：{action}",
            font=("Microsoft YaHei", 10, "bold"),
            bootstyle="warning"
        )
        desc_label.pack(anchor=W, pady=(0, 5))
        
        # AI建议
        suggestion_text = scrolledtext.ScrolledText(
            self.confirm_frame,
            height=4,
            font=("Microsoft YaHei", 9),
            wrap=tk.WORD
        )
        suggestion_text.pack(fill=X, pady=(0, 10))
        suggestion_text.insert(tk.END, f"AI建议：\n{ai_response}")
        suggestion_text.config(state=tk.DISABLED)
        
        # 按钮区域
        btn_frame = ttk_bs.Frame(self.confirm_frame)
        btn_frame.pack(fill=X)
        
        # 确认按钮
        confirm_btn = ttk_bs.Button(
            btn_frame,
            text="确认执行",
            command=lambda: self.execute_operation(action, user_input),
            bootstyle="success",
            width=12
        )
        confirm_btn.pack(side=LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_btn = ttk_bs.Button(
            btn_frame,
            text="取消操作",
            command=self.hide_operation_confirmation,
            bootstyle="danger-outline",
            width=12
        )
        cancel_btn.pack(side=LEFT, padx=(0, 10))
        
        # 重新理解按钮
        reunderstand_btn = ttk_bs.Button(
            btn_frame,
            text="重新理解",
            command=lambda: self.reunderstand_request(user_input),
            bootstyle="warning-outline",
            width=12
        )
        reunderstand_btn.pack(side=LEFT)

    def hide_operation_confirmation(self):
        """隐藏操作确认界面"""
        self.confirm_frame.pack_forget()
        self.add_message("系统", "操作已取消", "secondary")

    def execute_operation(self, action, user_input):
        """执行操作"""
        try:
            self.hide_operation_confirmation()
            
            if action == "add":
                self.execute_add_operation(user_input)
            elif action == "delete":
                self.execute_delete_operation(user_input)
            elif action == "complete":
                self.execute_complete_operation(user_input)
            elif action == "update":
                self.execute_update_operation(user_input)
            else:
                self.add_message("系统", f"暂不支持的操作类型：{action}", "warning")
                
        except Exception as e:
            self.add_message("系统", f"执行操作失败：{str(e)}", "danger")

    def execute_add_operation(self, user_input):
        """执行添加操作"""
        # 使用智能解析功能
        task_info = self.parse_task_from_input(user_input)
        
        if task_info:
            # 显示解析结果确认界面
            self.show_task_confirmation(task_info, user_input)
        else:
            self.add_message("系统", "⚠️ 无法从输入中解析出完整的任务信息，请在左侧添加任务面板中手动填写", "warning")

    def show_task_confirmation(self, task_info, user_input):
        """显示任务确认界面"""
        # 隐藏之前的确认界面
        if hasattr(self, 'task_confirm_frame'):
            self.task_confirm_frame.destroy()
        
        # 创建确认界面
        self.task_confirm_frame = ttk_bs.Frame(self.chat_frame, bootstyle="info")
        self.task_confirm_frame.pack(fill=X, padx=10, pady=5)
        
        # 标题
        title_label = ttk_bs.Label(
            self.task_confirm_frame,
            text="🤖 AI智能解析结果 - 请确认或修改",
            font=("Microsoft YaHei", 12, "bold"),
            bootstyle="info"
        )
        title_label.pack(pady=(10, 5))
        
        # 解析结果显示
        result_frame = ttk_bs.Frame(self.task_confirm_frame)
        result_frame.pack(fill=X, padx=10, pady=5)
        
        # 获取显示名称
        priority_name = self.get_priority_name(task_info['priority'])
        gtd_name = {
            "next-action": "下一步行动", 
            "waiting-for": "等待中", 
            "someday-maybe": "将来/也许", 
            "inbox": "收件箱"
        }.get(task_info['gtd_tag'], "未知")
        
        # 显示解析结果
        result_text = f"""📝 任务标题: {task_info['title']}
📁 项目: {task_info['project']}
🎯 优先级: {priority_name}
🏷️ GTD标签: {gtd_name}"""
        
        if task_info['due_date']:
            result_text += f"\n📅 截止日期: {task_info['due_date']}"
        if task_info['reminder_time']:
            result_text += f"\n⏰ 提醒时间: {task_info['reminder_time']}"
        
        result_label = ttk_bs.Label(
            result_frame,
            text=result_text,
            font=("Microsoft YaHei", 10),
            justify=LEFT
        )
        result_label.pack(anchor=W, pady=5)
        
        # 创建修改选项区域
        options_frame = ttk_bs.LabelFrame(
            self.task_confirm_frame,
            text="🔧 需要修改？请选择要调整的选项",
            bootstyle="warning"
        )
        options_frame.pack(fill=X, padx=10, pady=5)
        
        # 存储用户选择的变量
        self.task_modifications = {
            'title': tk.StringVar(value=task_info['title']),
            'project': tk.StringVar(value=task_info['project']),
            'priority': tk.IntVar(value=task_info['priority']),
            'gtd_tag': tk.StringVar(value=task_info['gtd_tag']),
            'due_date': tk.StringVar(value=task_info['due_date']),
            'reminder_time': tk.StringVar(value=task_info['reminder_time'])
        }
        
        # 标题修改
        title_frame = ttk_bs.Frame(options_frame)
        title_frame.pack(fill=X, padx=5, pady=2)
        ttk_bs.Label(title_frame, text="📝 任务标题:", width=12).pack(side=LEFT)
        title_entry = ttk_bs.Entry(title_frame, textvariable=self.task_modifications['title'])
        title_entry.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        # 项目修改
        project_frame = ttk_bs.Frame(options_frame)
        project_frame.pack(fill=X, padx=5, pady=2)
        ttk_bs.Label(project_frame, text="📁 项目:", width=12).pack(side=LEFT)
        project_combo = ttk_bs.Combobox(
            project_frame, 
            textvariable=self.task_modifications['project'],
            values=["默认项目", "工作", "学习", "生活", "个人"]
        )
        project_combo.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        # 优先级修改
        priority_frame = ttk_bs.Frame(options_frame)
        priority_frame.pack(fill=X, padx=5, pady=2)
        ttk_bs.Label(priority_frame, text="🎯 优先级:", width=12).pack(side=LEFT)
        priority_combo = ttk_bs.Combobox(
            priority_frame,
            textvariable=self.task_modifications['priority'],
            values=[1, 2, 3, 4],
            state="readonly"
        )
        priority_combo.pack(side=LEFT, padx=(5, 0))
        
        # 优先级说明
        priority_labels = {1: "重要且紧急", 2: "重要不紧急", 3: "不重要但紧急", 4: "不重要不紧急"}
        priority_desc = ttk_bs.Label(
            priority_frame, 
            text=f"({priority_labels.get(task_info['priority'], '未知')})",
            font=("Microsoft YaHei", 9)
        )
        priority_desc.pack(side=LEFT, padx=(5, 0))
        
        # GTD标签修改
        gtd_frame = ttk_bs.Frame(options_frame)
        gtd_frame.pack(fill=X, padx=5, pady=2)
        ttk_bs.Label(gtd_frame, text="🏷️ GTD标签:", width=12).pack(side=LEFT)
        gtd_combo = ttk_bs.Combobox(
            gtd_frame,
            textvariable=self.task_modifications['gtd_tag'],
            values=["inbox", "next-action", "waiting-for", "someday-maybe"],
            state="readonly"
        )
        gtd_combo.pack(side=LEFT, padx=(5, 0))
        
        # GTD标签说明
        gtd_labels = {
            "inbox": "收件箱", 
            "next-action": "下一步行动", 
            "waiting-for": "等待中", 
            "someday-maybe": "将来/也许"
        }
        gtd_desc = ttk_bs.Label(
            gtd_frame, 
            text=f"({gtd_labels.get(task_info['gtd_tag'], '未知')})",
            font=("Microsoft YaHei", 9)
        )
        gtd_desc.pack(side=LEFT, padx=(5, 0))
        
        # 截止日期修改
        date_frame = ttk_bs.Frame(options_frame)
        date_frame.pack(fill=X, padx=5, pady=2)
        ttk_bs.Label(date_frame, text="📅 截止日期:", width=12).pack(side=LEFT)
        date_entry = ttk_bs.Entry(
            date_frame, 
            textvariable=self.task_modifications['due_date']
        )
        date_entry.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        # 提醒时间修改
        reminder_frame = ttk_bs.Frame(options_frame)
        reminder_frame.pack(fill=X, padx=5, pady=2)
        ttk_bs.Label(reminder_frame, text="⏰ 提醒时间:", width=12).pack(side=LEFT)
        reminder_entry = ttk_bs.Entry(
            reminder_frame, 
            textvariable=self.task_modifications['reminder_time']
        )
        reminder_entry.pack(side=LEFT, fill=X, expand=True, padx=(5, 0))
        
        # 按钮区域
        btn_frame = ttk_bs.Frame(self.task_confirm_frame)
        btn_frame.pack(fill=X, padx=10, pady=10)
        
        # 确认添加按钮
        confirm_btn = ttk_bs.Button(
            btn_frame,
            text="✅ 确认添加",
            command=lambda: self.confirm_add_task(user_input),
            bootstyle="success",
            width=15
        )
        confirm_btn.pack(side=LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_btn = ttk_bs.Button(
            btn_frame,
            text="❌ 取消",
            command=self.hide_task_confirmation,
            bootstyle="danger-outline",
            width=15
        )
        cancel_btn.pack(side=LEFT, padx=(0, 10))
        
        # 重新解析按钮
        reparse_btn = ttk_bs.Button(
            btn_frame,
            text="🔄 重新解析",
            command=lambda: self.reparse_task(user_input),
            bootstyle="warning-outline",
            width=15
        )
        reparse_btn.pack(side=LEFT)
        
        # 滚动到底部
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def confirm_add_task(self, user_input):
        """确认添加任务"""
        try:
            # 获取用户修改后的信息
            final_task_info = {
                'title': self.task_modifications['title'].get().strip(),
                'project': self.task_modifications['project'].get().strip(),
                'priority': self.task_modifications['priority'].get(),
                'gtd_tag': self.task_modifications['gtd_tag'].get(),
                'due_date': self.task_modifications['due_date'].get().strip(),
                'reminder_time': self.task_modifications['reminder_time'].get().strip(),
                'description': f"原始输入: {user_input} | 用户确认后添加"
            }
            
            # 验证必填字段
            if not final_task_info['title']:
                self.add_message("系统", "❌ 任务标题不能为空", "danger")
                return
            
            # 添加任务到数据库
            task_id = self.database_manager.add_todo(
                task=final_task_info['title'],
                priority=final_task_info['priority'],
                project=final_task_info['project'],
                gtd_tag=final_task_info['gtd_tag'],
                due_date=final_task_info['due_date'] if final_task_info['due_date'] else None,
                reminder_time=final_task_info['reminder_time'] if final_task_info['reminder_time'] else None,
                description=final_task_info['description']
            )
            
            # 隐藏确认界面
            self.hide_task_confirmation()
            
            # 显示成功消息
            priority_name = self.get_priority_name(final_task_info['priority'])
            gtd_name = {
                "next-action": "下一步行动", 
                "waiting-for": "等待中", 
                "someday-maybe": "将来/也许", 
                "inbox": "收件箱"
            }.get(final_task_info['gtd_tag'], "未知")
            
            success_msg = f"✅ 任务添加成功！\n"
            success_msg += f"📋 任务ID: {task_id}\n"
            success_msg += f"📝 标题: {final_task_info['title']}\n"
            success_msg += f"📁 项目: {final_task_info['project']}\n"
            success_msg += f"🎯 优先级: {priority_name}\n"
            success_msg += f"🏷️ GTD标签: {gtd_name}"
            
            if final_task_info['due_date']:
                success_msg += f"\n📅 截止日期: {final_task_info['due_date']}"
            if final_task_info['reminder_time']:
                success_msg += f"\n⏰ 提醒时间: {final_task_info['reminder_time']}"
            
            self.add_message("系统", success_msg, "success")
            
            # 刷新界面
            self.refresh_context()
                
        except Exception as e:
            self.add_message("系统", f"❌ 添加任务失败：{str(e)}", "danger")

    def hide_task_confirmation(self):
        """隐藏任务确认界面"""
        if hasattr(self, 'task_confirm_frame'):
            self.task_confirm_frame.destroy()
        self.add_message("系统", "操作已取消", "secondary")

    def reparse_task(self, user_input):
        """重新解析任务"""
        self.hide_task_confirmation()
        self.add_message("系统", "🔄 正在重新解析任务...", "info")
        # 重新调用添加操作
        self.execute_add_operation(user_input)

    def execute_delete_operation(self, user_input):
        """执行删除操作"""
        # 解析要删除的任务ID或标题
        task_ids = self.extract_task_ids(user_input)
        task_titles = self.extract_task_titles(user_input)
        
        deleted_count = 0
        
        # 按ID删除
        for task_id in task_ids:
            try:
                task = self.database_manager.get_todo_by_id(task_id)
                if task:
                    self.database_manager.delete_todo(task_id)
                    deleted_count += 1
                    self.add_message("系统", f"✅ 已删除任务 ID:{task_id} - {task[1]}", "success")
                else:
                    self.add_message("系统", f"❌ 未找到ID为{task_id}的任务", "warning")
            except Exception as e:
                self.add_message("系统", f"❌ 删除任务ID:{task_id}失败：{str(e)}", "danger")
        
        # 按标题删除
        if task_titles and not task_ids:
            todos = self.database_manager.get_all_todos()
            for title in task_titles:
                for todo in todos:
                    if title.lower() in todo[1].lower():  # todo[1]是标题
                        try:
                            self.database_manager.delete_todo(todo[0])  # todo[0]是ID
                            deleted_count += 1
                            self.add_message("系统", f"✅ 已删除任务：{todo[1]}", "success")
                            break
                        except Exception as e:
                            self.add_message("系统", f"❌ 删除任务失败：{str(e)}", "danger")
        
        if deleted_count == 0:
            self.add_message("系统", "⚠️ 未找到要删除的任务，请指定具体的任务ID或标题", "warning")

    def execute_complete_operation(self, user_input):
        """执行完成操作"""
        # 解析要完成的任务
        task_ids = self.extract_task_ids(user_input)
        task_titles = self.extract_task_titles(user_input)
        
        completed_count = 0
        
        # 按ID完成
        for task_id in task_ids:
            try:
                task = self.database_manager.get_todo_by_id(task_id)
                if task:
                    self.database_manager.mark_todo_completed(task_id)
                    completed_count += 1
                    self.add_message("系统", f"✅ 已完成任务 ID:{task_id} - {task[1]}", "success")
                else:
                    self.add_message("系统", f"❌ 未找到ID为{task_id}的任务", "warning")
            except Exception as e:
                self.add_message("系统", f"❌ 完成任务ID:{task_id}失败：{str(e)}", "danger")
        
        # 按标题完成
        if task_titles and not task_ids:
            todos = self.database_manager.get_all_todos()
            for title in task_titles:
                for todo in todos:
                    if title.lower() in todo[1].lower() and todo[4] == 'pending':  # todo[4]是状态
                        try:
                            self.database_manager.mark_todo_completed(todo[0])
                            completed_count += 1
                            self.add_message("系统", f"✅ 已完成任务：{todo[1]}", "success")
                            break
                        except Exception as e:
                            self.add_message("系统", f"❌ 完成任务失败：{str(e)}", "danger")
        
        if completed_count == 0:
            self.add_message("系统", "⚠️ 未找到要完成的任务，请指定具体的任务ID或标题", "warning")

    def execute_update_operation(self, user_input):
        """执行更新操作"""
        # 解析要更新的任务和更新内容
        self.add_message("系统", "⚠️ 更新操作功能正在开发中，请使用其他方式修改任务", "warning")

    def parse_task_from_input(self, user_input):
        """从用户输入中智能解析任务信息，包括GTD标签和四象限分类"""
        try:
            # 基本任务信息
            task_info = {
                'title': '',
                'description': '',
                'project': '默认项目',
                'priority': 4,  # 默认不重要不紧急
                'urgency': 0,
                'importance': 0,
                'gtd_tag': 'inbox',  # 默认收件箱
                'due_date': '',
                'reminder_time': ''
            }
            
            # 1. 提取任务标题
            title = self._extract_task_title(user_input)
            if not title:
                return None
            task_info['title'] = title
            
            # 2. 智能分析任务类型和GTD标签
            task_info['gtd_tag'] = self._analyze_gtd_tag(user_input, title)
            
            # 3. 智能分析重要性和紧急性（四象限）
            importance, urgency = self._analyze_importance_urgency(user_input, title)
            task_info['importance'] = importance
            task_info['urgency'] = urgency
            task_info['priority'] = self._calculate_priority(importance, urgency)
            
            # 4. 提取项目信息
            task_info['project'] = self._extract_project(user_input)
            
            # 5. 提取时间信息
            due_date, reminder_time = self._extract_time_info(user_input)
            task_info['due_date'] = due_date
            task_info['reminder_time'] = reminder_time
            
            # 6. 生成任务描述
            task_info['description'] = self._generate_description(user_input, task_info)
            
            return task_info
            
        except Exception as e:
            self.add_message("系统", f"解析任务信息时出错：{str(e)}", "danger")
            return None

    def _extract_task_title(self, user_input):
        """提取任务标题"""
        # 移除常见的操作关键词和标点
        title_patterns = [
            r'(?:添加|新增|创建|我要|请|帮我)(?:任务|事项)?[：:]\s*(.+)',
            r'(?:添加|新增|创建|我要|请|帮我)\s*(.+)',
            r'任务[：:]\s*(.+)',
            r'(.+)'  # 兜底模式
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, user_input.strip(), re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                # 清理标题
                title = re.sub(r'[，。！？,!?]+$', '', title)  # 移除末尾标点
                title = re.sub(r'(很|非常|特别|比较)?(重要|紧急|急)', '', title)  # 移除优先级词汇
                title = re.sub(r'(今天|明天|后天|下周|下个月)', '', title)  # 移除时间词汇
                title = title.strip()
                if len(title) > 2:  # 确保标题有意义
                    return title
        return None

    def _analyze_gtd_tag(self, user_input, title):
        """智能分析GTD标签"""
        input_text = (user_input + " " + title).lower()
        
        # GTD标签关键词映射
        gtd_keywords = {
            'next-action': [
                '立即', '马上', '现在', '今天', '开始', '执行', '做', '处理',
                '完成', '解决', '实施', '行动', '进行', '着手'
            ],
            'waiting-for': [
                '等待', '等', '等人', '等回复', '等确认', '等审批', '等通知',
                '依赖', '需要', '等别人', '等他人', '等领导', '等客户'
            ],
            'someday-maybe': [
                '将来', '以后', '有空', '有时间', '考虑', '想', '可能',
                '也许', '或许', '打算', '计划', '希望', '想要', '学习'
            ],
            'inbox': [
                '记录', '记下', '提醒', '备忘', '想起', '不要忘记'
            ]
        }
        
        # 计算每个GTD标签的匹配分数
        scores = {}
        for gtd_tag, keywords in gtd_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in input_text:
                    score += 1
            scores[gtd_tag] = score
        
        # 特殊规则判断
        if any(word in input_text for word in ['立即', '马上', '现在', '今天', '紧急']):
            return 'next-action'
        elif any(word in input_text for word in ['等待', '等', '依赖']):
            return 'waiting-for'
        elif any(word in input_text for word in ['将来', '以后', '有空', '学习', '想']):
            return 'someday-maybe'
        
        # 返回得分最高的标签，如果都是0则返回inbox
        best_tag = max(scores.items(), key=lambda x: x[1])
        return best_tag[0] if best_tag[1] > 0 else 'inbox'

    def _analyze_importance_urgency(self, user_input, title):
        """智能分析重要性和紧急性"""
        input_text = (user_input + " " + title).lower()
        
        # 重要性关键词
        importance_keywords = {
            'high': ['重要', '关键', '核心', '主要', '优先', '必须', '关键性', '战略', '目标'],
            'medium': ['需要', '应该', '建议', '最好', '推荐'],
            'low': ['可以', '随便', '无所谓', '不重要', '次要']
        }
        
        # 紧急性关键词
        urgency_keywords = {
            'high': ['紧急', '急', '立即', '马上', '现在', '今天', '截止', 'deadline', '赶紧'],
            'medium': ['尽快', '及时', '近期', '这周', '本周', '明天'],
            'low': ['不急', '慢慢', '有空', '以后', '将来', '有时间']
        }
        
        # 计算重要性分数
        importance_score = 0
        for level, keywords in importance_keywords.items():
            for keyword in keywords:
                if keyword in input_text:
                    if level == 'high':
                        importance_score += 2
                    elif level == 'medium':
                        importance_score += 1
                    else:  # low
                        importance_score -= 1
        
        # 计算紧急性分数
        urgency_score = 0
        for level, keywords in urgency_keywords.items():
            for keyword in keywords:
                if keyword in input_text:
                    if level == 'high':
                        urgency_score += 2
                    elif level == 'medium':
                        urgency_score += 1
                    else:  # low
                        urgency_score -= 1
        
        # 特殊任务类型判断
        task_type_importance = {
            '会议': 1, '汇报': 1, '报告': 1, '总结': 1,
            '学习': 0, '阅读': 0, '研究': 0,
            '修复': 1, 'bug': 1, '问题': 1, '故障': 1,
            '项目': 1, '计划': 1, '方案': 1
        }
        
        task_type_urgency = {
            '会议': 1, '汇报': 1, '截止': 2,
            '修复': 2, 'bug': 2, '故障': 2, '问题': 1,
            '学习': -1, '阅读': -1, '研究': -1
        }
        
        for task_type, score in task_type_importance.items():
            if task_type in input_text:
                importance_score += score
        
        for task_type, score in task_type_urgency.items():
            if task_type in input_text:
                urgency_score += score
        
        # 转换为0/1值
        importance = 1 if importance_score > 0 else 0
        urgency = 1 if urgency_score > 0 else 0
        
        return importance, urgency

    def _calculate_priority(self, importance, urgency):
        """根据重要性和紧急性计算优先级"""
        if importance == 1 and urgency == 1:
            return 1  # 重要且紧急
        elif importance == 1 and urgency == 0:
            return 2  # 重要不紧急
        elif importance == 0 and urgency == 1:
            return 3  # 不重要但紧急
        else:
            return 4  # 不重要不紧急

    def _extract_project(self, user_input):
        """提取项目信息"""
            project_patterns = [
            r'项目[：:]\s*([^\s,，。！？]+)',
            r'属于\s*([^\s,，。！？]+)\s*项目',
            r'([^\s,，。！？]+)\s*项目',
            r'在\s*([^\s,，。！？]+)\s*中',
            r'关于\s*([^\s,，。！？]+)'
            ]
            
            for pattern in project_patterns:
                match = re.search(pattern, user_input, re.IGNORECASE)
                if match:
                project = match.group(1).strip()
                if len(project) > 1 and project not in ['这个', '那个', '一个']:
                    return project
        
        # 智能推断项目
        project_keywords = {
            '工作': ['工作', '公司', '办公', '业务', '客户', '会议', '汇报', '项目'],
            '学习': ['学习', '课程', '教程', '书', '阅读', '研究', '考试'],
            '生活': ['买', '购', '家', '生活', '健康', '运动', '娱乐'],
            '个人': ['个人', '自己', '私人', '爱好', '兴趣']
        }
        
        input_lower = user_input.lower()
        for project, keywords in project_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return project
        
        return '默认项目'

    def _extract_time_info(self, user_input):
        """提取时间信息"""
        from datetime import datetime, timedelta
        
        due_date = ''
        reminder_time = ''
        
        # 日期模式
            date_patterns = [
            (r'(\d{4}-\d{1,2}-\d{1,2})', lambda m: m.group(1)),
            (r'(\d{1,2})月(\d{1,2})日', lambda m: f"2024-{int(m.group(1)):02d}-{int(m.group(2)):02d}"),
            (r'今天', lambda m: datetime.now().strftime('%Y-%m-%d')),
            (r'明天', lambda m: (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')),
            (r'后天', lambda m: (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')),
            (r'下周', lambda m: (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')),
            (r'(\d+)天后', lambda m: (datetime.now() + timedelta(days=int(m.group(1)))).strftime('%Y-%m-%d'))
        ]
        
        for pattern, converter in date_patterns:
                match = re.search(pattern, user_input)
                if match:
                try:
                    due_date = converter(match)
                    break
                except:
                    continue
        
        # 时间模式
        time_patterns = [
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})点',
            r'上午(\d{1,2})点?',
            r'下午(\d{1,2})点?',
            r'晚上(\d{1,2})点?'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, user_input)
            if match:
                if due_date:
                    if '上午' in pattern:
                        hour = int(match.group(1))
                    elif '下午' in pattern or '晚上' in pattern:
                        hour = int(match.group(1)) + 12 if int(match.group(1)) < 12 else int(match.group(1))
                    else:
                        hour = int(match.group(1))
                    
                    minute = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) else 0
                    reminder_time = f"{due_date} {hour:02d}:{minute:02d}"
                break
        
        return due_date, reminder_time

    def _generate_description(self, user_input, task_info):
        """生成任务描述"""
        description_parts = []
        
        # 添加原始输入
        description_parts.append(f"原始输入: {user_input}")
        
        # 添加分析结果
        priority_name = self.get_priority_name(task_info['priority'])
        gtd_name = {
            "next-action": "下一步行动", 
            "waiting-for": "等待中", 
            "someday-maybe": "将来/也许", 
            "inbox": "收件箱"
        }.get(task_info['gtd_tag'], "未知")
        
        description_parts.append(f"智能分析: {priority_name} | {gtd_name}")
        
        return " | ".join(description_parts)

    def extract_task_ids(self, text):
        """从文本中提取任务ID"""
        # 匹配ID:数字 或 任务ID:数字 等模式
        id_patterns = [
            r'ID[：:]?\s*(\d+)',
            r'任务ID[：:]?\s*(\d+)',
            r'编号[：:]?\s*(\d+)',
            r'第\s*(\d+)\s*个',
            r'(\d+)\s*号任务'
        ]
        
        task_ids = []
        for pattern in id_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            task_ids.extend([int(match) for match in matches])
        
        return list(set(task_ids))  # 去重

    def extract_task_titles(self, text):
        """从文本中提取任务标题"""
        # 匹配引号中的内容或特定模式
        title_patterns = [
            r'[""]([^""]+)[""]',
            r"['']([^'']+)['']",
            r'任务[：:]?\s*([^\s,，。]+)',
            r'删除\s*([^\s,，。]+)',
            r'完成\s*([^\s,，。]+)'
        ]
        
        titles = []
        for pattern in title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            titles.extend(matches)
        
        return [title.strip() for title in titles if title.strip()]

    def get_priority_name(self, priority):
        """获取优先级名称"""
        priority_names = {
            1: "重要且紧急",
            2: "重要不紧急", 
            3: "不重要但紧急",
            4: "不重要不紧急"
        }
        return priority_names.get(priority, "未知")

    def reunderstand_request(self, user_input):
        """重新理解用户请求"""
        self.hide_operation_confirmation()
        self.add_message("系统", "正在重新分析您的请求...", "info")
        
        # 重新发送请求，要求AI更仔细地理解
        reunderstand_prompt = f"请重新仔细分析用户的请求，如果不确定具体操作，请询问更多细节：{user_input}"
        threading.Thread(target=self.process_ai_response, args=(reunderstand_prompt,), daemon=True).start()

    def add_message(self, sender, message, style="secondary"):
        """添加消息到聊天显示区域"""
        self.chat_display.config(state=tk.NORMAL)
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 添加发送者和时间
        self.chat_display.insert(tk.END, f"\n[{timestamp}] {sender}:\n", f"sender_{style}")
        
        # 添加消息内容
        self.chat_display.insert(tk.END, f"{message}\n", f"message_{style}")
        
        # 配置文本样式
        self.chat_display.tag_config(f"sender_{style}", font=("Microsoft YaHei", 10, "bold"))
        self.chat_display.tag_config(f"message_{style}", font=("Microsoft YaHei", 10))
        
        # 滚动到底部
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    def refresh_context(self):
        """刷新上下文数据"""
        # 当待办事项数据更新时调用此方法
        pass 

    def _build_system_prompt(self):
        """构建系统提示词"""
        base_prompt = """你是一个智能待办事项管理助手，专门帮助用户管理任务和提高工作效率。

## 核心功能
1. **任务管理**: 添加、删除、完成、更新待办事项
2. **智能解析**: 自动解析用户输入，提取任务信息
3. **GTD工作流**: 支持下一步行动、等待中、将来/也许、收件箱分类
4. **四象限管理**: 重要紧急、重要不紧急、不重要紧急、不重要不紧急
5. **数据分析**: 提供任务统计和工作效率洞察

## 智能解析能力
当用户输入任务时，你能够智能解析：
- **任务标题**: 提取核心任务内容
- **GTD标签**: 分析任务类型（下一步行动/等待中/将来也许/收件箱）
- **重要性和紧急性**: 判断任务的重要程度和紧急程度
- **优先级**: 基于四象限理论计算优先级（1-4）
- **项目分类**: 推断任务所属项目类型
- **时间信息**: 提取截止日期、提醒时间等

## 响应原则
1. **数据驱动**: 每次回答前都要查看当前数据库内容
2. **准确性**: 基于实际数据提供准确信息
3. **友好性**: 使用友好、专业的语调
4. **实用性**: 提供具体、可操作的建议
5. **简洁性**: 避免冗长的回复，突出重点"""

        if self.mcp_enabled:
            mcp_prompt = """

## MCP (Model Context Protocol) 功能
你现在具备了强大的SQLite MCP功能，可以直接查询和操作数据库：

### 可用的SQL工具
- **read_query**: 执行SELECT查询读取数据
- **write_query**: 执行INSERT/UPDATE/DELETE修改数据
- **create_table**: 创建新表
- **list_tables**: 列出所有表
- **describe_table**: 查看表结构
- **append_insight**: 添加业务洞察

### 数据库表结构
- **todos**: 主要任务表
  - id: 任务ID
  - task: 任务标题
  - priority: 优先级(1-4)
  - gtd_tag: GTD标签
  - status: 状态(pending/completed)
  - project: 项目分类
  - due_date: 截止日期
  - created_at: 创建时间
  - completed_at: 完成时间

### MCP使用指南
1. **查询数据**: 使用read_query获取准确的实时数据
2. **数据分析**: 利用SQL进行复杂的数据分析和统计
3. **洞察生成**: 使用append_insight记录重要的业务洞察
4. **安全操作**: 写操作前要谨慎，确保数据安全

### 示例SQL查询
```sql
-- 查看所有待办任务
SELECT * FROM todos WHERE status = 'pending' ORDER BY priority;

-- 统计各优先级任务数量
SELECT priority, COUNT(*) as count FROM todos GROUP BY priority;

-- 查看本周完成的任务
SELECT * FROM todos WHERE status = 'completed' 
AND completed_at >= date('now', '-7 days');
```

**重要**: 每次回答用户问题时，都应该先使用read_query查询最新的数据库内容，然后基于实际数据提供准确的回答。"""
            
            return base_prompt + mcp_prompt
        else:
            offline_prompt = """

## 离线模式
当前运行在离线模式下，具备以下功能：
- 基本任务管理操作
- 智能任务解析
- 简单的数据查询
- 工作流程建议

注意：离线模式下的数据查询能力有限，建议配置API密钥以获得完整功能。"""
            
            return base_prompt + offline_prompt 

    def init_sql_connection(self):
        """初始化SQLite连接（用于MCP功能）"""
        try:
            if hasattr(self, 'database_manager') and self.database_manager:
                # 使用数据库管理器的连接
                self.sql_connection = self.database_manager.conn
                print("✅ SQLite MCP连接初始化成功")
            else:
                print("⚠️ 数据库管理器未找到，MCP功能可能受限")
        except Exception as e:
            print(f"❌ SQLite MCP连接初始化失败: {e}")
            self.mcp_enabled = False
    
    def execute_sql_query(self, query):
        """执行SQL查询（MCP功能）"""
        if not self.mcp_enabled:
            raise Exception("MCP功能未启用")
        
        try:
            # 安全检查：只允许SELECT查询用于读取
            query_upper = query.strip().upper()
            if query_upper.startswith('SELECT') or query_upper.startswith('WITH'):
                cursor = self.sql_connection.cursor()
                cursor.execute(query)
                results = cursor.fetchall()
                
                # 获取列名
                column_names = [description[0] for description in cursor.description] if cursor.description else []
                
                # 格式化结果
                if results:
                    formatted_results = []
                    for row in results:
                        row_dict = dict(zip(column_names, row))
                        formatted_results.append(row_dict)
                    return formatted_results
                else:
                    return []
            else:
                # 对于非SELECT查询，需要特殊权限
                return self.execute_write_query(query)
                
        except Exception as e:
            raise Exception(f"SQL查询执行失败: {str(e)}")
    
    def execute_write_query(self, query):
        """执行写入查询（INSERT/UPDATE/DELETE）"""
        if not self.mcp_enabled:
            raise Exception("MCP功能未启用")
        
        try:
            query_upper = query.strip().upper()
            if any(query_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']):
                cursor = self.sql_connection.cursor()
                cursor.execute(query)
                self.sql_connection.commit()
                return {"affected_rows": cursor.rowcount, "message": "查询执行成功"}
            else:
                raise Exception("不支持的查询类型")
        except Exception as e:
            self.sql_connection.rollback()
            raise Exception(f"写入查询执行失败: {str(e)}")
    
    def get_table_schema(self, table_name):
        """获取表结构信息"""
        if not self.mcp_enabled:
            return "MCP功能未启用"
        
        try:
            query = f"PRAGMA table_info({table_name})"
            return self.execute_sql_query(query)
        except Exception as e:
            return f"获取表结构失败: {str(e)}"
    
    def list_all_tables(self):
        """列出所有表"""
        if not self.mcp_enabled:
            return "MCP功能未启用"
        
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            return self.execute_sql_query(query)
        except Exception as e:
            return f"获取表列表失败: {str(e)}" 

    def handle_query_request(self, user_input_lower):
        """处理查询请求"""
        response = ""
        
        if self.mcp_enabled:
            # 使用MCP功能进行智能查询
            try:
                if "所有" in user_input_lower or "全部" in user_input_lower:
                    # 查询所有任务
                    results = self.execute_sql_query("SELECT * FROM todos ORDER BY priority, created_at DESC")
                    if results:
                        response += f"📋 **当前所有任务** (共{len(results)}个):\\n\\n"
                        for task in results:
                            status_icon = "✅" if task['status'] == 'completed' else "⏳"
                            priority_name = self.get_priority_name(task['priority'])
                            response += f"{status_icon} **{task['task']}**\\n"
                            response += f"   📊 优先级: {priority_name} | 🏷️ GTD: {task['gtd_tag']} | 📁 项目: {task['project']}\\n"
                            if task['due_date']:
                                response += f"   ⏰ 截止: {task['due_date']}\\n"
                            response += "\\n"
                    else:
                        response += "📝 当前没有任务。"
                
                elif "统计" in user_input_lower or "分析" in user_input_lower:
                    # 统计分析
                    stats_queries = [
                        ("总任务数", "SELECT COUNT(*) as count FROM todos"),
                        ("待办任务", "SELECT COUNT(*) as count FROM todos WHERE status = 'pending'"),
                        ("已完成任务", "SELECT COUNT(*) as count FROM todos WHERE status = 'completed'"),
                        ("优先级分布", "SELECT priority, COUNT(*) as count FROM todos GROUP BY priority ORDER BY priority"),
                        ("GTD分布", "SELECT gtd_tag, COUNT(*) as count FROM todos GROUP BY gtd_tag"),
                        ("项目分布", "SELECT project, COUNT(*) as count FROM todos GROUP BY project")
                    ]
                    
                    response += "📊 **任务统计分析**:\\n\\n"
                    for name, query in stats_queries:
                        try:
                            result = self.execute_sql_query(query)
                            if name in ["总任务数", "待办任务", "已完成任务"]:
                                count = result[0]['count'] if result else 0
                                response += f"• {name}: {count}\\n"
                            else:
                                response += f"\\n**{name}**:\\n"
                                for item in result:
                                    if 'priority' in item:
                                        priority_name = self.get_priority_name(item['priority'])
                                        response += f"  - {priority_name}: {item['count']}个\\n"
                                    else:
                                        key = 'gtd_tag' if 'gtd_tag' in item else 'project'
                                        response += f"  - {item[key]}: {item['count']}个\\n"
                        except Exception as e:
                            response += f"• {name}: 查询失败 ({str(e)})\\n"
                
                elif "待办" in user_input_lower or "未完成" in user_input_lower:
                    # 查询待办任务
                    results = self.execute_sql_query("SELECT * FROM todos WHERE status = 'pending' ORDER BY priority, created_at DESC")
                    if results:
                        response += f"⏳ **待办任务** (共{len(results)}个):\\n\\n"
                        for task in results:
                            priority_name = self.get_priority_name(task['priority'])
                            response += f"• **{task['task']}**\\n"
                            response += f"  📊 {priority_name} | 🏷️ {task['gtd_tag']} | 📁 {task['project']}\\n"
                            if task['due_date']:
                                response += f"  ⏰ 截止: {task['due_date']}\\n"
                            response += "\\n"
                    else:
                        response += "🎉 太棒了！当前没有待办任务。"
                
                elif "已完成" in user_input_lower or "完成" in user_input_lower:
                    # 查询已完成任务
                    results = self.execute_sql_query("SELECT * FROM todos WHERE status = 'completed' ORDER BY completed_at DESC LIMIT 10")
                    if results:
                        response += f"✅ **最近完成的任务** (最近10个):\\n\\n"
                        for task in results:
                            response += f"✅ **{task['task']}**\\n"
                            response += f"  📁 {task['project']} | 完成时间: {task['completed_at']}\\n\\n"
                    else:
                        response += "📝 还没有完成的任务。"
                
                else:
                    # 默认显示概览
                    overview_query = """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                    FROM todos
                    """
                    result = self.execute_sql_query(overview_query)
                    if result:
                        stats = result[0]
                        response += f"📊 **任务概览**:\\n"
                        response += f"• 总任务: {stats['total']}个\\n"
                        response += f"• 待办: {stats['pending']}个\\n"
                        response += f"• 已完成: {stats['completed']}个\\n\\n"
                        
                        # 显示最近的待办任务
                        recent_tasks = self.execute_sql_query("SELECT * FROM todos WHERE status = 'pending' ORDER BY priority, created_at DESC LIMIT 5")
                        if recent_tasks:
                            response += "⏳ **最近的待办任务**:\\n"
                            for task in recent_tasks:
                                priority_name = self.get_priority_name(task['priority'])
                                response += f"• {task['task']} ({priority_name})\\n"
                
            except Exception as e:
                response += f"❌ 查询失败: {str(e)}\\n\\n"
                # 降级到基本查询
                response += self._basic_query_fallback()
        else:
            # 非MCP模式的基本查询
            response += self._basic_query_fallback()
        
        return response
    
    def _basic_query_fallback(self):
        """基本查询降级方案"""
        try:
            todos = self.database_manager.get_all_todos()
            stats = self.database_manager.get_statistics()
            
            response = f"📊 **任务概览** (基本模式):\\n"
            response += f"• 总任务: {stats.get('total_tasks', 0)}个\\n"
            response += f"• 待办: {stats.get('pending_tasks', 0)}个\\n"
            response += f"• 已完成: {stats.get('completed_tasks', 0)}个\\n\\n"
            
            pending_todos = [todo for todo in todos if todo[4] == 'pending']
            if pending_todos:
                response += "⏳ **待办任务**:\\n"
                for todo in pending_todos[:5]:  # 只显示前5个
                    priority_name = self.get_priority_name(todo[2])
                    response += f"• {todo[1]} ({priority_name})\\n"
            
            return response
        except Exception as e:
            return f"❌ 查询失败: {str(e)}"