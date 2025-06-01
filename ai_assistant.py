"""
AI助手模块 - 重构版
集成DeepSeek API，智能理解和操作待办事项，并与SQL数据库交互。
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
    # No need for DatabaseManager import as SQLHandler is now self-contained with db_name
except ImportError:
    # 如果直接导入失败，尝试动态导入
    import importlib.util
    
    def load_module(module_name, file_path):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            print(f"Error: Could not find spec for module {module_name} at {file_path}")
            return None
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except FileNotFoundError:
            print(f"Error: File not found for module {module_name} at {file_path}")
            return None
        except Exception as e:
            print(f"Error executing module {module_name}: {e}")
            return None
        return module
    
    # 动态加载模块
    ai_core_module = load_module("ai_core", "ai_core.py")
    AICore = ai_core_module.AICore if ai_core_module else None
    
    task_parser_module = load_module("task_parser", "task_parser.py")
    TaskParser = task_parser_module.TaskParser if task_parser_module else None
    
    ai_ui_module = load_module("ai_ui", "ai_ui.py")
    AIUserInterface = ai_ui_module.AIUserInterface if ai_ui_module else None
    
    sql_handler_module = load_module("sql_handler", "sql_handler.py")
    SQLHandler = sql_handler_module.SQLHandler if sql_handler_module else None

    if not all([AICore, TaskParser, AIUserInterface, SQLHandler]):
        print("FATAL: One or more core modules could not be loaded. Exiting.")
        # In a real app, you might exit or raise an exception here
        # For now, we'll let it proceed and potentially fail later if modules are None

class AIAssistant:
    """AI助手主类 - 集成SQL和UI"""
    
    def __init__(self, config_manager=None, db_name="todo.db"): # Added db_name
        """初始化AI助手"""
        self.config_manager = config_manager
        
        # 初始化核心AI、解析器、SQL处理器
        if AICore:
            self.ai_core = AICore(config_manager)
        else:
            print("Warning: AICore not loaded, AI functionality will be impaired.")
            self.ai_core = None 

        if TaskParser:
            self.task_parser = TaskParser()
        else:
            print("Warning: TaskParser not loaded.")
            self.task_parser = None
        
        if SQLHandler:
            self.sql_handler = SQLHandler(db_name=db_name) 
        else:
            print("Warning: SQLHandler not loaded, database interaction will fail.")
            self.sql_handler = None
            
        # 构建系统提示词 - 之后会修改以包含DB schema
        self.system_prompt = self._build_system_prompt() 

        # 初始化UI，将自身实例传递给UI
        if AIUserInterface:
            self.ui = AIUserInterface(self)
        else:
            print("Warning: AIUserInterface not loaded, UI will not be available.")
            self.ui = None
        
        self.ai_window = None # For tracking the AI assistant window instance, if UI uses it

    def process_user_input(self, user_input):
        """处理用户输入并获取AI响应 (待后续扩展SQL和UI交互)"""
        # This method will be significantly expanded later
        # For now, keep it simple to ensure basic AI call works
        if not self.ai_core:
            message = "AI Core not available."
            if self.ui: self.ui.add_message("System", message, "error")
            else: print(message)
            return message

        try:
            full_system_prompt = self.system_prompt 
            
            success, ai_response_content = self.ai_core.call_deepseek_api(
                user_input, 
                full_system_prompt
            )
            
            if success:
                # 检查AI的响应是否包含 EXECUTE_SQL: 指令
                sql_command_match = re.search(r"`EXECUTE_SQL:\s*(.+?)`", ai_response_content, re.IGNORECASE)
                
                if sql_command_match:
                    sql_to_execute = sql_command_match.group(1).strip()
                    if self.ui: self.ui.add_message("系统", f"AI建议执行SQL: {sql_to_execute}", "info")
                    else: print(f"AI建议执行SQL: {sql_to_execute}")
                    
                    # 根据SQL类型调用不同的执行方法
                    # (这是一个简化的判断，更复杂的场景可能需要更完善的SQL解析)
                    if sql_to_execute.upper().startswith(("SELECT", "PRAGMA")):
                        sql_success, result = self.sql_handler.execute_sql_query(sql_to_execute)
                    else:
                        sql_success, result = self.sql_handler.execute_write_query(sql_to_execute)
                    
                    if sql_success:
                        # 对结果进行格式化，使其更易读
                        formatted_result = self._format_sql_result(result, sql_to_execute)
                        if self.ui: self.ui.add_message("数据库", formatted_result, "success")
                        else: print(f"数据库操作成功: {formatted_result}")
                        return formatted_result # 或者返回一个表示成功的消息
                    else:
                        error_message = f"数据库操作失败: {result}"
                        if self.ui: self.ui.add_message("数据库", error_message, "error")
                        else: print(error_message)
                        return error_message
                else:
                    # 如果没有SQL指令，则直接显示AI的回复
                    if self.ui: self.ui.add_message("AI助手", ai_response_content, "assistant")
                    else: print(f"AI助手: {ai_response_content}")
                    return ai_response_content
            else:
                error_msg = f"处理AI响应时发生错误: {ai_response_content}"
                if self.ui: self.ui.add_message("System", error_msg, "error")
                else: print(f"系统错误: {error_msg}")
                return error_msg
                
        except Exception as e:
            error_msg = f"处理AI响应时发生严重错误: {str(e)}"
            if self.ui: self.ui.add_message("System", error_msg, "error")
            else: print(f"系统错误: {error_msg}")
            return error_msg

    def _build_system_prompt(self):
        """构建系统提示词 (后续会加入DB schema)"""
        prompt_parts = [
            "你是一个智能助手，可以帮助管理待办事项并与数据库交互。",
            "请直接与用户友好交互。",
            "如果用户只是聊天，请进行友好回应."
        ]
        
        if self.sql_handler:
            mcp_prompt = self.sql_handler.get_mcp_schema_prompt()
            if mcp_prompt:
                prompt_parts.append("\n--- 数据库交互指南 ---")
                prompt_parts.append(mcp_prompt)
                prompt_parts.append("--- 结束数据库交互指南 ---")
            else:
                prompt_parts.append("\n(注意: 数据库交互模块已加载，但无法生成详细的数据库指南。)")
        else:
            prompt_parts.append("\n(注意: 数据库交互模块未加载。)")
            
        return "\n".join(prompt_parts)

    # --- Methods related to UI interaction (to be called by AIUserInterface) ---
    def get_ai_core_instance(self): # AIUserInterface might need this
        return self.ai_core

    def get_config_manager_instance(self): # AIUserInterface might need this
        return self.config_manager

    def _format_sql_result(self, result, query):
        """格式化SQL查询结果以便更好地显示"""
        if isinstance(result, str): # 通常是错误消息或简单成功消息
            return result
        
        if isinstance(result, list):
            if not result: # 空列表，表示没有数据
                return "查询成功，但没有返回数据。"
            
            # 尝试更美观地打印列表中的字典
            formatted_lines = ["查询结果:"]
            if isinstance(result[0], dict):
                headers = result[0].keys()
                formatted_lines.append(" | ".join(headers))
                formatted_lines.append("-" * (sum(len(str(h)) for h in headers) + 3 * (len(headers) -1)) ) # Separator line
                for row_dict in result:
                    formatted_lines.append(" | ".join(str(row_dict.get(h, '')) for h in headers))
                return "\n".join(formatted_lines)
            else: # 如果不是字典列表，就简单地逐行打印
                for item in result:
                    formatted_lines.append(str(item))
                return "\n".join(formatted_lines)
        
        return str(result) # Fallback

    # Add other methods that AIUserInterface might call on AIAssistant,
    # for example, to trigger AI processing or to get/set configurations.
    # We'll add them as we identify the needs from ai_ui.py

# Commenting out the __main__ block for now, as it's not compatible
# with the newly integrated components and UI focus.
# We will need a proper application entry point (e.g., in a new main.py or app.py)
# to initialize Tkinter UI if that's the direction.

# if __name__ == '__main__':
#     # ... (old test code) ...
#     pass

# Example usage (optional, for testing this file directly)
if __name__ == '__main__':
    # 假设有一个 DummyConfigManager 和一个实现了 call_deepseek_api 的 DummyAICore
    class DummyConfigManager:
        pass

    class DummyAICore:
        def __init__(self, config_manager):
            pass
        def call_deepseek_api(self, user_input, system_prompt):
            print(f"--- System Prompt Sent to AI ---")
            print(system_prompt)
            print(f"--- User Input Sent to AI ---")
            print(user_input)
            print(f"---------------------------------")
            if "error" in user_input.lower():
                return False, "Simulated API error."
            return True, f"这是对'{user_input}'的模拟AI回复。"

    # This is a common pattern for testing without real API calls or complex dependencies
    try:
        original_ai_core = AICore # Keep a reference to the original
        AICore = DummyAICore      # Temporarily override AICore for this test
    except NameError: # This will happen if AICore couldn't be imported/loaded
        print("Warning: Real AICore not found, proceeding with DummyAICore for testing.")
        AICore = DummyAICore # Ensure AICore is set to DummyAICore
        original_ai_core = None # No original to restore

    print("AI助手测试模式 (使用模拟AI核心)")
    assistant = AIAssistant(config_manager=DummyConfigManager())
    
    print("\n请输入您的请求 (输入 '退出' 来结束):")
    while True:
        user_message = input("您: ")
        if user_message.lower() == '退出':
            break
        assistant.process_user_input(user_message)
    
    if original_ai_core: # Only restore if it was successfully captured
        AICore = original_ai_core # Restore original AICore if needed elsewhere
    print("AI助手测试结束。") 