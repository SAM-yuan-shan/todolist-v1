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
    
    def __init__(self, database_manager, ui_components, config_manager=None):
        """初始化AI助手"""
        self.database_manager = database_manager
        self.ui_components = ui_components
        self.config_manager = config_manager
        
        # 初始化各个模块
        self.ai_core = AICore(config_manager)
        self.task_parser = TaskParser()
        self.ui = AIUserInterface(self)
        
        # 初始化SQL处理器（如果启用MCP）
        self.sql_handler = None
        if config_manager and config_manager.is_mcp_enabled():
            # 传递数据库路径而不是database_manager对象
            db_path = config_manager.get_database_path()
            self.sql_handler = SQLHandler(db_path)
        
        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()

    def create_ai_panel(self, parent):
        """创建AI助手面板"""
        return self.ui.create_ai_panel(parent)
    
    def process_user_input(self, user_input):
        """处理用户输入的接口方法"""
        return self.process_ai_response(user_input)
    
    def process_ai_response(self, user_input):
        """处理AI响应的主要逻辑"""
        try:
            # 首先检查是否是SQL查询请求（如果启用MCP）
            if self.sql_handler:
                query_result = self.sql_handler.handle_query_request(user_input.lower())
                if query_result:
                    self.add_message("AI助手", query_result, "assistant")
                    return
        
            # 获取待办事项上下文
            todo_context = self.get_todo_context()
            
            # 构建完整的系统提示词
            full_system_prompt = f"{self.system_prompt}\n\n当前待办事项数据:\n{todo_context}"
            
            # 调用AI API
            success, ai_response = self.ai_core.call_deepseek_api(
                user_input, 
                full_system_prompt
            )
            
            if success:
                # 解析AI响应，确定操作类型
                action = self.parse_ai_response(ai_response, user_input)
                
                if action == "add_task":
                    self.execute_add_operation(user_input)
                elif action in ["delete_task", "complete_task", "update_task"]:
                    self.show_operation_confirmation(action, ai_response, user_input)
                else:
                    # 直接显示AI响应
                    self.add_message("AI助手", ai_response, "assistant")
            else:
                # API调用失败，使用离线响应
                offline_response = self.offline_response(user_input, ai_response)
                self.add_message("AI助手", offline_response, "assistant")
                
        except Exception as e:
            error_msg = f"处理请求时出错: {str(e)}"
            self.add_message("系统", error_msg, "error")

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
        return """你是一个智能待办事项管理助手，具备强大的任务智能解析能力。

【重要】在回答任何问题之前，你必须：
1. 仔细查看和分析当前提供的待办事项数据
2. 基于实际的数据库内容来回答问题
3. 如果用户询问任务情况，要准确引用具体的任务ID、标题和状态
4. 始终以当前数据库的实际内容为准，不要假设或猜测

【智能解析能力】当用户输入任务时，系统会自动：
1. 🎯 四象限分类：根据关键词自动判断重要性和紧急性
2. 🏷️ GTD标签自动分类
3. 📁 项目智能推断
4. ⏰ 时间信息提取

你的能力包括：
1. 查看所有待办事项 - 基于实际数据库内容提供准确信息
2. 智能添加待办事项 - 自动解析并分类用户输入的任务
3. 修改现有待办事项 - 基于现有任务ID进行修改
4. 删除待办事项 - 根据任务ID或标题精确删除
5. 标记任务完成 - 将指定任务状态改为已完成
6. 按项目、优先级、GTD标签筛选任务 - 基于实际数据进行筛选
7. 分析任务分布和统计信息 - 提供基于真实数据的分析

回答规范：
1. 每次回答前，先简要总结当前数据库状态
2. 如果用户询问具体任务，要引用准确的任务ID和标题
3. 提供操作建议时，要基于实际存在的任务
4. 当用户要求添加任务时，说明系统会自动进行智能分类
5. 对于复杂操作，提供确认界面让用户选择执行或重新理解

记住：始终基于实际数据库内容回答，充分利用智能解析功能，为用户提供准确、高效的任务管理服务。""" 