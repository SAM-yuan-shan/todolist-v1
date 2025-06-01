"""
SQL处理模块
包含数据库查询、MCP功能等
"""
import sqlite3
import re
from datetime import datetime


class SQLHandler:
    """SQL查询处理器"""
    
    def __init__(self, db_name):
        """初始化SQL处理器"""
        self.db_name = db_name # Store db_name
        self.sql_connection = None
        self.init_sql_connection()
    
    def init_sql_connection(self):
        """初始化SQLite连接"""
        try:
            self.sql_connection = sqlite3.connect(self.db_name, check_same_thread=False)
            self.sql_connection.row_factory = sqlite3.Row  # 使结果可以按列名访问
            print(f"SQL连接初始化成功: {self.db_name}")
            return True
        except Exception as e:
            print(f"初始化SQL连接失败: {e}")
            return False
    
    def execute_sql_query(self, query):
        """执行SQL查询（只读）"""
        try:
            if not self.sql_connection:
                return False, "数据库连接未初始化"
            
            # 安全检查：只允许SELECT和PRAGMA查询
            query_upper = query.upper().strip()
            if not (query_upper.startswith('SELECT') or query_upper.startswith('PRAGMA')):
                return False, "只允许执行SELECT和PRAGMA查询"
            
            cursor = self.sql_connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 转换为字典列表
            result_list = []
            for row in results:
                result_list.append(dict(row))
            
            return True, result_list
            
        except Exception as e:
            return False, f"查询执行失败: {str(e)}"
    
    def execute_write_query(self, query):
        """执行写入查询（INSERT, UPDATE, DELETE）"""
        try:
            if not self.sql_connection:
                return False, "数据库连接未初始化"
            
            # 安全检查：只允许特定的写入操作
            query_upper = query.upper().strip()
            allowed_operations = ['INSERT', 'UPDATE', 'DELETE']
            if not any(query_upper.startswith(op) for op in allowed_operations):
                return False, "只允许执行INSERT、UPDATE、DELETE操作"
            
            cursor = self.sql_connection.cursor()
            cursor.execute(query)
            self.sql_connection.commit()
            
            return True, f"操作成功，影响行数: {cursor.rowcount}"
            
        except Exception as e:
            return False, f"写入操作失败: {str(e)}"
    
    def get_table_schema(self, table_name):
        """获取表结构"""
        try:
            query = f"PRAGMA table_info({table_name})"
            success, results = self.execute_sql_query(query)
            if success:
                return True, results
            else:
                return False, results
        except Exception as e:
            return False, f"获取表结构失败: {str(e)}"
    
    def list_all_tables(self):
        """列出所有表"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            success, results = self.execute_sql_query(query)
            if success:
                table_names = [row['name'] for row in results]
                return True, table_names
            else:
                return False, results
        except Exception as e:
            return False, f"获取表列表失败: {str(e)}"
    
    def handle_query_request(self, user_input_lower):
        """处理查询请求"""
        try:
            # 检测查询意图
            query_keywords = [
                '查询', '查看', '显示', '统计', '分析', '搜索', '找',
                'select', 'count', 'sum', 'avg', 'max', 'min'
            ]
            
            if not any(keyword in user_input_lower for keyword in query_keywords):
                return None
            
            # 构建查询
            query = self._build_query_from_input(user_input_lower)
            if not query:
                return self._basic_query_fallback()
            
            # 执行查询
            success, results = self.execute_sql_query(query)
            if success:
                return self._format_query_results(results, user_input_lower)
            else:
                return f"查询执行失败: {results}"
                
        except Exception as e:
            return f"处理查询请求时出错: {str(e)}"
    
    def _build_query_from_input(self, user_input_lower):
        """根据用户输入构建SQL查询"""
        base_query = "SELECT * FROM todos"
        conditions = []
        
        # 状态筛选
        if '待处理' in user_input_lower or '未完成' in user_input_lower:
            conditions.append("status = 'pending'")
        elif '已完成' in user_input_lower or '完成' in user_input_lower:
            conditions.append("status = 'completed'")
        
        # 优先级筛选
        if '重要紧急' in user_input_lower or '优先级1' in user_input_lower:
            conditions.append("priority = 1")
        elif '重要不紧急' in user_input_lower or '优先级2' in user_input_lower:
            conditions.append("priority = 2")
        elif '不重要紧急' in user_input_lower or '优先级3' in user_input_lower:
            conditions.append("priority = 3")
        elif '不重要不紧急' in user_input_lower or '优先级4' in user_input_lower:
            conditions.append("priority = 4")
        
        # GTD标签筛选
        if '下一步' in user_input_lower or 'next-action' in user_input_lower:
            conditions.append("gtd_tag = 'next-action'")
        elif '等待' in user_input_lower or 'waiting' in user_input_lower:
            conditions.append("gtd_tag = 'waiting-for'")
        elif '将来' in user_input_lower or 'someday' in user_input_lower:
            conditions.append("gtd_tag = 'someday-maybe'")
        elif '收件箱' in user_input_lower or 'inbox' in user_input_lower:
            conditions.append("gtd_tag = 'inbox'")
        
        # 项目筛选
        projects = ['工作', '学习', '生活', '个人']
        for project in projects:
            if project in user_input_lower:
                conditions.append(f"project = '{project}'")
                break
        
        # 时间筛选
        if '今天' in user_input_lower:
            today = datetime.now().strftime('%Y-%m-%d')
            conditions.append(f"due_date = '{today}'")
        elif '本周' in user_input_lower:
            # 简化处理，查询最近7天
            conditions.append("due_date >= date('now', '-7 days')")
        elif '过期' in user_input_lower or '逾期' in user_input_lower:
            conditions.append("due_date < date('now') AND status = 'pending'")
        
        # 统计查询
        if '统计' in user_input_lower or '数量' in user_input_lower or 'count' in user_input_lower:
            if '项目' in user_input_lower:
                return "SELECT project, COUNT(*) as count FROM todos GROUP BY project"
            elif '优先级' in user_input_lower:
                return "SELECT priority, COUNT(*) as count FROM todos GROUP BY priority"
            elif '状态' in user_input_lower:
                return "SELECT status, COUNT(*) as count FROM todos GROUP BY status"
            else:
                return "SELECT COUNT(*) as total_count FROM todos"
        
        # 构建完整查询
        if conditions:
            query = base_query + " WHERE " + " AND ".join(conditions)
        else:
            query = base_query
        
        # 添加排序
        query += " ORDER BY priority ASC, created_at DESC"
        
        return query
    
    def _format_query_results(self, results, user_input_lower):
        """格式化查询结果"""
        if not results:
            return "没有找到符合条件的任务。"
        
        # 统计查询的格式化
        if '统计' in user_input_lower or 'count' in user_input_lower:
            if 'total_count' in results[0]:
                return f"总任务数: {results[0]['total_count']}"
            else:
                formatted = "统计结果:\n"
                for row in results:
                    if 'project' in row:
                        formatted += f"- {row['project']}: {row['count']}个任务\n"
                    elif 'priority' in row:
                        priority_names = {1: '重要紧急', 2: '重要不紧急', 3: '不重要紧急', 4: '不重要不紧急'}
                        priority_name = priority_names.get(row['priority'], f"优先级{row['priority']}")
                        formatted += f"- {priority_name}: {row['count']}个任务\n"
                    elif 'status' in row:
                        status_names = {'pending': '待处理', 'completed': '已完成'}
                        status_name = status_names.get(row['status'], row['status'])
                        formatted += f"- {status_name}: {row['count']}个任务\n"
                return formatted.strip()
        
        # 普通查询的格式化
        formatted = f"找到 {len(results)} 个任务:\n\n"
        
        for i, task in enumerate(results, 1):
            formatted += f"{i}. 【ID: {task['id']}】{task['title']}\n"
            
            # 优先级
            priority_names = {1: '重要紧急', 2: '重要不紧急', 3: '不重要紧急', 4: '不重要不紧急'}
            priority_name = priority_names.get(task['priority'], f"优先级{task['priority']}")
            formatted += f"   优先级: {priority_name}\n"
            
            # GTD标签
            gtd_names = {
                'next-action': '下一步行动',
                'waiting-for': '等待中',
                'someday-maybe': '将来/也许',
                'inbox': '收件箱'
            }
            gtd_name = gtd_names.get(task['gtd_tag'], task['gtd_tag'])
            formatted += f"   GTD标签: {gtd_name}\n"
            
            # 项目和状态
            formatted += f"   项目: {task['project']}\n"
            status_name = '已完成' if task['status'] == 'completed' else '待处理'
            formatted += f"   状态: {status_name}\n"
            
            # 时间信息
            if task['due_date']:
                formatted += f"   截止日期: {task['due_date']}\n"
            if task['reminder_time']:
                formatted += f"   提醒时间: {task['reminder_time']}\n"
            
            formatted += "\n"
        
        return formatted.strip()
    
    def _basic_query_fallback(self):
        """基本查询回退"""
        try:
            # 获取基本统计信息
            queries = [
                ("总任务数", "SELECT COUNT(*) as count FROM todos"),
                ("待处理任务", "SELECT COUNT(*) as count FROM todos WHERE status = 'pending'"),
                ("已完成任务", "SELECT COUNT(*) as count FROM todos WHERE status = 'completed'"),
                ("重要紧急任务", "SELECT COUNT(*) as count FROM todos WHERE priority = 1 AND status = 'pending'")
            ]
            
            result = "当前任务概览:\n"
            for name, query in queries:
                success, data = self.execute_sql_query(query)
                if success and data:
                    result += f"- {name}: {data[0]['count']}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"获取任务概览失败: {str(e)}"
    
    def get_mcp_schema_prompt(self):
        """生成用于AI的数据库模式和操作说明提示。"""
        prompt_parts = []
        prompt_parts.append("你可以与一个SQLite数据库交互来管理待办事项。数据库包含以下表和列：")

        success_tables, tables = self.list_all_tables()
        if not success_tables or not tables:
            # 如果没有表或者获取表失败，至少告知AI数据库是空的或者有问题
            prompt_parts.append("\n  注意: 当前数据库中没有表，或者无法获取表列表。")
            # return None # 或者可以继续生成操作说明，让AI知道如何创建表等（如果支持的话）
        else:
            for table_name in tables:
                prompt_parts.append(f"\n表名: {table_name}")
                success_schema, schema_info = self.get_table_schema(table_name)
                if success_schema and schema_info:
                    for column in schema_info:
                        col_name = column.get('name', 'N/A')
                        col_type = column.get('type', 'N/A')
                        col_pk = " (主键)" if column.get('pk') else ""
                        prompt_parts.append(f"    - 列: {col_name} (类型: {col_type}){col_pk}")
                else:
                    prompt_parts.append("    (无法获取此表的详细模式)")
        
        prompt_parts.append("\n你可以通过生成特定格式的指令来查询或修改数据库。")
        prompt_parts.append("\n重要: 当你需要我执行数据库查询时，请明确指出，例如：")
        prompt_parts.append("  '查询所有待办事项' 或 '帮我看看状态为pending的任务有哪些'。")
        prompt_parts.append("  我将尝试将你的自然语言请求转换为SQL语句并执行。")
        prompt_parts.append("\n如果你想让我执行一个你构造好的精确SQL语句，请将SQL语句包裹在特殊的标记中，格式如下：")
        prompt_parts.append("  `EXECUTE_SQL: SELECT * FROM todos WHERE status = 'completed'`")
        prompt_parts.append("  其中 `EXECUTE_SQL:` 是固定的前缀，后面紧跟你的SQL语句。")
        prompt_parts.append("  只支持 SELECT, INSERT, UPDATE, DELETE 语句。")
        
        return "\n".join(prompt_parts) 