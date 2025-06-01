"""
AI助手模块 - 重构版
集成DeepSeek API，智能理解和操作待办事项
"""
import re
import importlib
from datetime import datetime

# 动态导入拆分的模块
try:
    from ai_core import AICore
    from task_parser import TaskParser
    from ai_ui import AIUserInterface
    from sql_handler import SQLHandler
except ImportError:
    # 如果直接导入失败，尝试动态导入
    import importlib.util
    
    def load_module(module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    # 动态加载模块
    ai_core_module = load_module("ai_core", "ai_core.py")
    AICore = ai_core_module.AICore
    
    task_parser_module = load_module("task_parser", "task_parser.py")
    TaskParser = task_parser_module.TaskParser
    
    ai_ui_module = load_module("ai_ui", "ai_ui.py")
    AIUserInterface = ai_ui_module.AIUserInterface
    
    sql_handler_module = load_module("sql_handler", "sql_handler.py")
    SQLHandler = sql_handler_module.SQLHandler


class AIAssistant:
    """AI助手主类 - 重构版"""
    
    def __init__(self, database_manager, ui_components, config_manager=None, role_manager=None):
        """初始化AI助手"""
        self.database_manager = database_manager
        self.ui_components = ui_components
        self.config_manager = config_manager
        self.role_manager = role_manager
        
        # 初始化各个模块
        self.ai_core = AICore(config_manager)
        self.task_parser = TaskParser(role_manager)  # 传递角色管理器
        self.ui = AIUserInterface(self)
        
        # 初始化SQL处理器（如果启用MCP）
        self.sql_handler = None
        if config_manager and config_manager.is_mcp_enabled():
            # 传递数据库路径而不是database_manager对象
            db_path = config_manager.get_database_path()
            self.sql_handler = SQLHandler(db_path)
        
        # AI记忆相关属性
        self.current_session_id = self._generate_session_id()
        self.conversation_count = 0
        
        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()

    def _generate_session_id(self):
        """生成会话ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def create_ai_panel(self, parent):
        """创建AI助手面板"""
        return self.ui.create_ai_panel(parent)
    
    def process_user_input(self, user_input):
        """处理用户输入的接口方法"""
        return self.process_ai_response(user_input)
    
    def process_ai_response(self, user_input):
        """处理AI响应的主要逻辑"""
        try:
            # 增加对话计数
            self.conversation_count += 1
            
            # 首先检查是否是SQL查询请求（如果启用MCP）
            if self.sql_handler:
                query_result = self.sql_handler.handle_query_request(user_input.lower())
                if query_result:
                    self.add_message("AI助手", query_result, "assistant")
                    # 保存对话历史
                    self._save_conversation(user_input, query_result, "sql_query")
                    return
        
            # 获取待办事项上下文
            todo_context = self.get_todo_context()
            
            # 获取AI记忆上下文
            memory_context = self._get_memory_context()
            
            # 构建完整的系统提示词
            full_system_prompt = f"{self.system_prompt}\n\n当前待办事项数据:\n{todo_context}\n\n用户个性化信息:\n{memory_context}"
            
            # 调用AI API
            success, ai_response = self.ai_core.call_deepseek_api(
                user_input, 
                full_system_prompt
            )
            
            if success:
                # 解析AI响应，确定操作类型
                action = self.parse_ai_response(ai_response, user_input)
                
                # 学习用户偏好和关键词
                self._learn_from_interaction(user_input, ai_response, action)
                
                if action == "add_task":
                    self.execute_add_operation(user_input)
                    # 保存对话历史
                    self._save_conversation(user_input, ai_response, "add_task")
                elif action in ["delete_task", "complete_task", "update_task"]:
                    self.show_operation_confirmation(action, ai_response, user_input)
                    # 保存对话历史
                    self._save_conversation(user_input, ai_response, action)
                else:
                    # 直接显示AI响应
                    self.add_message("AI助手", ai_response, "assistant")
                    # 保存对话历史
                    self._save_conversation(user_input, ai_response, "general")
            else:
                # API调用失败，使用离线响应
                offline_response = self.offline_response(user_input, ai_response)
                self.add_message("AI助手", offline_response, "assistant")
                # 保存对话历史
                self._save_conversation(user_input, offline_response, "offline")
                
        except Exception as e:
            error_msg = f"处理请求时出错: {str(e)}"
            self.add_message("系统", error_msg, "error")
            # 保存错误对话
            self._save_conversation(user_input, error_msg, "error")

    def get_todo_context(self):
        """获取待办事项上下文"""
        try:
            todos = self.database_manager.get_all_todos()
            if not todos:
                return "当前没有待办事项。"
            
            context = f"当前共有 {len(todos)} 个待办事项:\n\n"
            
            # 按状态分组
            pending_todos = [t for t in todos if t['status'] == 'pending']
            completed_todos = [t for t in todos if t['status'] == 'completed']
            
            context += f"待处理任务 ({len(pending_todos)} 个):\n"
            for todo in pending_todos[:10]:  # 限制显示数量
                priority_name = self.task_parser.get_priority_name(todo['priority'])
                context += f"- ID:{todo['id']} | {todo['title']} | {priority_name} | {todo['project']}\n"
                    
            if len(pending_todos) > 10:
                context += f"... 还有 {len(pending_todos) - 10} 个待处理任务\n"
            
            context += f"\n已完成任务 ({len(completed_todos)} 个)\n"
            
            return context
            
        except Exception as e:
            return f"获取待办事项数据时出错: {str(e)}"

    def parse_ai_response(self, ai_response, user_input):
        """解析AI响应，确定操作类型"""
        response_lower = ai_response.lower()
        input_lower = user_input.lower()
        
        # 检测添加任务的意图
        add_keywords = ['添加', '新增', '创建', '加入', '新建']
        if any(keyword in input_lower for keyword in add_keywords):
            return "add_task"
        
        # 检测删除任务的意图
        delete_keywords = ['删除', '移除', '去掉', '清除']
        if any(keyword in input_lower for keyword in delete_keywords):
            return "delete_task"
        
        # 检测完成任务的意图
        complete_keywords = ['完成', '标记完成', '做完', '结束']
        if any(keyword in input_lower for keyword in complete_keywords):
            return "complete_task"
        
        # 检测更新任务的意图
        update_keywords = ['修改', '更新', '编辑', '改变']
        if any(keyword in input_lower for keyword in update_keywords):
            return "update_task"
        
        return "chat"  # 默认为聊天
    
    def show_operation_confirmation(self, action, ai_response, user_input):
        """显示操作确认"""
        self.ui.show_operation_confirmation(action, ai_response, user_input)

    def execute_operation(self, action, user_input):
        """执行操作"""
        if action == "delete_task":
            self.execute_delete_operation(user_input)
        elif action == "complete_task":
            self.execute_complete_operation(user_input)
        elif action == "update_task":
            self.execute_update_operation(user_input)

    def execute_add_operation(self, user_input):
        """执行添加任务操作"""
        try:
            # 解析任务信息
            task_info = self.task_parser.parse_task_from_input(user_input)
            
            if task_info:
                # 显示任务确认界面
                self.show_task_confirmation(task_info, user_input)
            else:
                self.add_message("系统", "无法解析任务信息，请重新输入", "error")
                
        except Exception as e:
            self.add_message("系统", f"解析任务时出错: {str(e)}", "error")

    def show_task_confirmation(self, task_info, user_input):
        """显示任务确认界面"""
        self.ui.show_task_confirmation(task_info, user_input)

    def confirm_add_task(self, user_input):
        """确认添加任务"""
        try:
            if self.ui.task_info:
                task_info = self.ui.task_info
            
                # 添加任务到数据库 - 修复参数传递
                success = self.database_manager.add_todo(
                    title=task_info['title'],
                    description=task_info['description'],
                    project=task_info['project'],
                    priority=task_info['priority'],
                    urgency=task_info.get('urgency', 0),  # 添加urgency参数
                    importance=task_info.get('importance', 0),  # 添加importance参数
                    gtd_tag=task_info['gtd_tag'],
                    due_date=task_info['due_date'],
                    reminder_time=task_info['reminder_time']
                )
                
                if success:
                    self.add_message("系统", f"任务 '{task_info['title']}' 添加成功！", "success")
                    # 刷新UI
                    if hasattr(self.ui_components, 'refresh_todo_list'):
                        self.ui_components.refresh_todo_list()
                else:
                    self.add_message("系统", "添加任务失败", "error")
                
        except Exception as e:
            self.add_message("系统", f"添加任务时出错: {str(e)}", "error")

    def confirm_add_task_with_updates(self, updated_task_info, user_input):
        """确认添加任务（支持用户更新的GTD和四象限分类）"""
        try:
            # 添加任务到数据库 - 使用用户确认后的信息
            success = self.database_manager.add_todo(
                title=updated_task_info['title'],
                description=updated_task_info['description'],
                project=updated_task_info['project'],
                priority=updated_task_info['priority'],
                urgency=updated_task_info.get('urgency', 0),
                importance=updated_task_info.get('importance', 0),
                gtd_tag=updated_task_info['gtd_tag'],
                due_date=updated_task_info['due_date'],
                reminder_time=updated_task_info['reminder_time']
            )
            
            if success:
                # 显示确认信息，包含用户的选择
                priority_name = self.task_parser.get_priority_name(updated_task_info['priority'])
                gtd_name = self._get_gtd_name(updated_task_info['gtd_tag'])
                
                confirmation_msg = f"""✅ 任务添加成功！

📋 任务: {updated_task_info['title']}
📁 项目: {updated_task_info['project']}
⭐ 优先级: {priority_name}
🏷️ GTD标签: {gtd_name}
📅 截止日期: {updated_task_info['due_date'] or '无'}

任务已按您确认的分类添加到系统中。"""
                
                self.add_message("系统", confirmation_msg, "success")
                
                # 刷新UI
                if hasattr(self.ui_components, 'refresh_todo_list'):
                    self.ui_components.refresh_todo_list()
                if hasattr(self.ui_components.main_app, 'refresh_all_views'):
                    self.ui_components.main_app.refresh_all_views()
            else:
                self.add_message("系统", "添加任务失败", "error")
                
        except Exception as e:
            self.add_message("系统", f"添加任务时出错: {str(e)}", "error")
    
    def _get_gtd_name(self, gtd_tag):
        """获取GTD标签名称"""
        gtd_names = {
            'next-action': '下一步行动',
            'waiting-for': '等待中',
            'someday-maybe': '将来/也许',
            'inbox': '收件箱'
        }
        return gtd_names.get(gtd_tag, gtd_tag)

    def reparse_task(self, user_input):
        """重新解析任务"""
        self.add_message("系统", "任务解析已取消。请重新描述您的任务需求，我会重新为您解析。", "info")

    def execute_delete_operation(self, user_input):
        """执行删除操作"""
        try:
            # 提取任务ID
            task_ids = self.task_parser.extract_task_ids(user_input)
            
            if task_ids:
                for task_id in task_ids:
                    success = self.database_manager.delete_todo(task_id)
                    if success:
                        self.add_message("系统", f"任务 {task_id} 删除成功", "success")
                    else:
                        self.add_message("系统", f"删除任务 {task_id} 失败", "error")
                
                # 刷新UI
                if hasattr(self.ui_components, 'refresh_todo_list'):
                    self.ui_components.refresh_todo_list()
            else:
                self.add_message("系统", "未找到要删除的任务ID", "warning")
                
        except Exception as e:
            self.add_message("系统", f"删除任务时出错: {str(e)}", "error")

    def execute_complete_operation(self, user_input):
        """执行完成操作"""
        try:
            # 提取任务ID
            task_ids = self.task_parser.extract_task_ids(user_input)
            
            if task_ids:
                for task_id in task_ids:
                    success = self.database_manager.update_todo_status(task_id, 'completed')
                    if success:
                        self.add_message("系统", f"任务 {task_id} 标记为已完成", "success")
                    else:
                        self.add_message("系统", f"完成任务 {task_id} 失败", "error")
                
                # 刷新UI
                if hasattr(self.ui_components, 'refresh_todo_list'):
                    self.ui_components.refresh_todo_list()
            else:
                self.add_message("系统", "未找到要完成的任务ID", "warning")
                
        except Exception as e:
            self.add_message("系统", f"完成任务时出错: {str(e)}", "error")

    def execute_update_operation(self, user_input):
        """执行更新操作"""
        self.add_message("系统", "任务更新功能正在开发中", "info")
    
    def reunderstand_request(self, user_input):
        """重新理解请求"""
        self.add_message("系统", "操作已取消。请重新描述您的需求，我会重新为您分析。", "info")
    
    def offline_response(self, user_input, error_msg=None):
        """离线响应"""
        response = "抱歉，AI服务暂时不可用。"
        
        if error_msg:
            response += f"\n错误信息: {error_msg}"
        
        # 尝试基本的关键词匹配
        input_lower = user_input.lower()
        
        if any(keyword in input_lower for keyword in ['查看', '显示', '列表']):
            try:
                todos = self.database_manager.get_all_todos()
                if todos:
                    response += f"\n\n当前有 {len(todos)} 个待办事项。"
                else:
                    response += "\n\n当前没有待办事项。"
            except:
                pass
        
        response += "\n\n请检查网络连接或API配置后重试。"
        return response

    def add_message(self, sender, message, style="secondary"):
        """添加消息"""
        self.ui.add_message(sender, message, style)

    def refresh_context(self):
        """刷新上下文"""
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self):
        """构建系统提示词"""
        base_prompt = """你是一个专业的待办事项AI助手，具有记忆和学习能力。

核心能力：
1. 智能理解用户的待办事项需求
2. 记住用户的偏好和工作模式
3. 根据历史交互提供个性化建议
4. 执行任务的增删改查操作
5. 提供数据分析和洞察

任务操作规则：
- 添加任务：解析标题、描述、项目、优先级、GTD标签、截止日期等
- 删除任务：根据ID或描述准确识别目标任务
- 完成任务：标记任务状态为完成
- 查询任务：提供筛选和统计信息

优先级分类（重要性+紧急性四象限）：
1. 重要且紧急 - 立即处理
2. 重要不紧急 - 计划处理  
3. 不重要但紧急 - 委托处理
4. 不重要不紧急 - 有空处理

GTD标签含义：
- next-action: 下一步行动
- waiting-for: 等待中
- someday-maybe: 将来/也许
- inbox: 收件箱

个性化服务：
- 学习用户的表达习惯和偏好
- 记住常用项目和工作模式
- 基于历史互动提供更贴心的建议
- 适应用户的沟通风格

回复风格：
- 简洁明了，避免冗长
- 针对性强，基于用户历史偏好
- 主动询问不明确的信息
- 提供可行的操作建议

记忆运用：
- 参考用户偏好进行任务分类建议
- 利用常用关键词理解用户意图
- 基于历史互动模式调整回复风格
- 主动关联相关的历史任务或项目"""

        # 如果有角色管理器，添加角色相关的提示
        if self.role_manager:
            try:
                current_role = self.role_manager.get_current_role()
                if current_role:
                    role_prompt = f"""

当前用户角色设定：{current_role['name']}
角色描述：{current_role['description']}
工作重点：{current_role['work_focus']}
沟通风格：{current_role['communication_style']}
时间偏好：{current_role['time_preference']}

请根据用户的角色特点提供更适合的建议和服务。"""
                    base_prompt += role_prompt
            except:
                pass
        
        return base_prompt

    def _get_memory_context(self):
        """获取AI记忆上下文"""
        try:
            memory_info = self.database_manager.get_ai_context_for_user()
            
            context_parts = []
            
            # 用户偏好
            if memory_info.get('preferences'):
                context_parts.append("用户偏好:")
                for pref_key, pref_value in memory_info['preferences'].items():
                    context_parts.append(f"- {pref_key}: {pref_value}")
            
            # 重要关键词
            if memory_info.get('important_keywords'):
                context_parts.append("\n常用概念: " + ", ".join(memory_info['important_keywords']))
            
            # 最近对话上下文
            if memory_info.get('recent_context'):
                context_parts.append("\n最近交互:")
                for ctx in memory_info['recent_context'][-3:]:  # 只取最近3次
                    if ctx['action']:
                        context_parts.append(f"- 用户说: {ctx['input'][:50]}... → 执行了: {ctx['action']}")
            
            return "\n".join(context_parts) if context_parts else "暂无个性化信息"
            
        except Exception as e:
            return f"获取记忆上下文失败: {str(e)}"

    def _save_conversation(self, user_input, ai_response, action_taken=None, related_todo_ids=None):
        """保存对话历史"""
        try:
            # 生成上下文摘要（简化版）
            context_summary = f"第{self.conversation_count}次对话"
            
            # 保存对话
            self.database_manager.save_ai_conversation(
                user_input=user_input,
                ai_response=ai_response,
                context_summary=context_summary,
                action_taken=action_taken,
                related_todo_ids=related_todo_ids,
                session_id=self.current_session_id,
                conversation_type=self._classify_conversation_type(user_input, action_taken)
            )
            
        except Exception as e:
            print(f"保存对话历史失败: {e}")

    def _classify_conversation_type(self, user_input, action_taken):
        """分类对话类型"""
        if action_taken in ['add_task', 'delete_task', 'complete_task', 'update_task']:
            return 'task_management'
        elif action_taken == 'sql_query':
            return 'data_query'
        elif any(keyword in user_input.lower() for keyword in ['统计', '分析', '报告', '总结']):
            return 'analysis'
        else:
            return 'general'

    def _learn_from_interaction(self, user_input, ai_response, action_taken):
        """从交互中学习用户偏好"""
        try:
            # 学习工作模式偏好
            self._learn_work_patterns(user_input, action_taken)
            
            # 学习优先级偏好
            self._learn_priority_preferences(user_input)
            
            # 学习沟通风格
            self._learn_communication_style(user_input)
            
            # 更新关键词记忆
            self._update_keyword_memory(user_input)
            
        except Exception as e:
            print(f"学习过程中出错: {e}")

    def _learn_work_patterns(self, user_input, action_taken):
        """学习工作模式"""
        input_lower = user_input.lower()
        
        # 学习时间偏好
        time_indicators = {
            '早上': 'morning_person',
            '晚上': 'night_person', 
            '下午': 'afternoon_person',
            '今天': 'immediate_planner',
            '明天': 'advance_planner',
            '下周': 'long_term_planner'
        }
        
        for indicator, preference in time_indicators.items():
            if indicator in input_lower:
                self.database_manager.save_user_preference(
                    'work_pattern', preference, 'true', 
                    confidence_score=0.7, learned_from=user_input[:50]
                )

    def _learn_priority_preferences(self, user_input):
        """学习优先级偏好"""
        input_lower = user_input.lower()
        
        priority_indicators = {
            '紧急': 'prefers_urgency',
            '重要': 'prefers_importance',
            '马上': 'immediate_action',
            '慢慢': 'patient_approach'
        }
        
        for indicator, preference in priority_indicators.items():
            if indicator in input_lower:
                self.database_manager.save_user_preference(
                    'priority_style', preference, 'true',
                    confidence_score=0.6, learned_from=user_input[:50]
                )

    def _learn_communication_style(self, user_input):
        """学习沟通风格"""
        input_lower = user_input.lower()
        
        # 分析用户的表达方式
        if len(user_input) > 50:
            self.database_manager.save_user_preference(
                'communication_style', 'detailed', 'true',
                confidence_score=0.5, learned_from="详细表达"
            )
        elif len(user_input) < 20:
            self.database_manager.save_user_preference(
                'communication_style', 'concise', 'true',
                confidence_score=0.5, learned_from="简洁表达"
            )

    def _update_keyword_memory(self, user_input):
        """更新关键词记忆"""
        # 提取关键词（简化版）
        import re
        
        # 常见的项目关键词
        project_words = re.findall(r'项目|工程|产品|系统|平台|应用', user_input)
        for word in project_words:
            self.database_manager.update_keyword_memory(word, 'project', user_input[:100])
        
        # 技术关键词
        tech_words = re.findall(r'开发|设计|测试|部署|维护|优化', user_input)
        for word in tech_words:
            self.database_manager.update_keyword_memory(word, 'technology', user_input[:100])
        
        # 人员关键词
        person_words = re.findall(r'团队|同事|客户|老板|领导', user_input)
        for word in person_words:
            self.database_manager.update_keyword_memory(word, 'person', user_input[:100]) 