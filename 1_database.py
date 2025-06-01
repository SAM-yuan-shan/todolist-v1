"""
数据库管理模块
负责SQLite数据库的初始化、连接和基本操作
"""
import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name='todo.db'):
        """初始化数据库管理器"""
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.init_database()
    
    def init_database(self):
        """初始化SQLite数据库"""
        # 设置check_same_thread=False以支持多线程访问
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        self.cursor = self.conn.cursor()
        
        # 创建待办事项表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                project TEXT,           -- 项目字段
                responsibility TEXT,    -- 责任级别字段
                priority INTEGER,       -- 1: 重要紧急, 2: 重要不紧急, 3: 不重要紧急, 4: 不重要不紧急
                urgency INTEGER,        -- 1: 紧急, 0: 不紧急
                importance INTEGER,     -- 1: 重要, 0: 不重要
                gtd_tag TEXT,          -- next-action, waiting-for, someday-maybe, inbox
                due_date TEXT,
                reminder_time TEXT,
                status TEXT DEFAULT 'pending',  -- pending, completed, cancelled
                created_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # 创建AI对话历史表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                context_summary TEXT,      -- 对话上下文摘要
                action_taken TEXT,         -- 执行的操作类型
                related_todo_ids TEXT,     -- 相关的待办事项ID(JSON格式)
                session_id TEXT,           -- 会话ID，用于关联连续对话
                created_at TEXT,
                conversation_type TEXT DEFAULT 'general'  -- general, task_management, query, etc.
            )
        ''')
        
        # 创建用户偏好和学习记录表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_type TEXT NOT NULL,  -- work_pattern, priority_style, communication_style, etc.
                preference_key TEXT NOT NULL,
                preference_value TEXT NOT NULL,
                confidence_score REAL DEFAULT 0.5,  -- 置信度分数 0-1
                learned_from TEXT,              -- 从哪次交互中学到的
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 创建AI记忆关键词表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_memory_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                category TEXT,              -- project, person, concept, etc.
                frequency INTEGER DEFAULT 1,
                last_mentioned TEXT,        -- 最后提及时间
                context TEXT,               -- 相关上下文
                importance_score REAL DEFAULT 0.5,
                created_at TEXT
            )
        ''')
        
        # 创建任务模板表（基于用户习惯学习）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT NOT NULL,
                title_pattern TEXT,
                default_project TEXT,
                default_priority INTEGER,
                default_gtd_tag TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,  -- 模板使用成功率
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # 检查是否需要添加项目列
        self.cursor.execute("PRAGMA table_info(todos)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'project' not in columns:
            self.cursor.execute('ALTER TABLE todos ADD COLUMN project TEXT')
        
        # 检查是否需要添加责任级别列
        if 'responsibility' not in columns:
            self.cursor.execute('ALTER TABLE todos ADD COLUMN responsibility TEXT DEFAULT "owner"')
        
        self.conn.commit()
    
    def add_todo(self, title, description, project, responsibility, priority, urgency, importance, 
                 gtd_tag, due_date, reminder_time):
        """添加新的待办事项"""
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute('''
            INSERT INTO todos (title, description, project, responsibility, priority, urgency, importance, 
                             gtd_tag, due_date, reminder_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, project, responsibility, priority, urgency, importance, gtd_tag, 
              due_date, reminder_time, created_at))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_todos(self):
        """获取所有待办事项的详细信息"""
        self.cursor.execute('''
            SELECT id, title, description, project, responsibility, priority, urgency, importance, 
                   gtd_tag, due_date, reminder_time, status, created_at, completed_at
            FROM todos 
            ORDER BY 
                CASE status 
                    WHEN 'pending' THEN 1 
                    WHEN 'completed' THEN 2 
                    ELSE 3 
                END,
                priority ASC,
                due_date ASC,
                created_at DESC
        ''')
        
        # 转换为字典列表以便于处理
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()
        
        todos = []
        for row in rows:
            todo_dict = dict(zip(columns, row))
            todos.append(todo_dict)
        
        return todos
    
    def get_todo_by_id(self, todo_id):
        """根据ID获取待办事项"""
        self.cursor.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
        return self.cursor.fetchone()
    
    def get_todos_by_date(self, date_str):
        """获取指定日期的待办事项"""
        self.cursor.execute('''
            SELECT id, title, project, gtd_tag, priority, status FROM todos 
            WHERE due_date = ? 
            ORDER BY priority, created_at
        ''', (date_str,))
        return self.cursor.fetchall()
    
    def get_todos_by_priority_and_gtd(self, priority, gtd_tag):
        """根据优先级和GTD标签获取待办事项"""
        self.cursor.execute('''
            SELECT id, title, project, due_date, status 
            FROM todos 
            WHERE priority = ? AND gtd_tag = ?
            ORDER BY due_date ASC
        ''', (priority, gtd_tag))
        return self.cursor.fetchall()
    
    def mark_todo_completed(self, todo_id):
        """标记待办事项为完成"""
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('''
            UPDATE todos SET status = 'completed', completed_at = ? WHERE id = ?
        ''', (completed_at, todo_id))
        self.conn.commit()
    
    def delete_todo(self, todo_id):
        """删除待办事项"""
        try:
            self.cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0  # 返回是否删除成功
        except Exception as e:
            print(f"删除待办事项失败: {e}")
            return False
    
    def get_pending_reminders(self, current_time):
        """获取需要提醒的待办事项"""
        self.cursor.execute('''
            SELECT id, title, description FROM todos 
            WHERE status = 'pending' AND reminder_time LIKE ?
        ''', (f"{current_time}%",))
        return self.cursor.fetchall()
    
    def get_statistics(self):
        """获取统计信息"""
        stats = {}
        
        # 总计统计
        self.cursor.execute('SELECT COUNT(*) FROM todos')
        stats['total'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM todos WHERE status = "completed"')
        stats['completed'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(*) FROM todos WHERE status = "pending"')
        stats['pending'] = self.cursor.fetchone()[0]
        
        # 四象限统计
        for i in range(1, 5):
            self.cursor.execute('''
                SELECT COUNT(*) FROM todos 
                WHERE priority = ? AND status = 'pending'
            ''', (i,))
            stats[f'quadrant_{i}'] = self.cursor.fetchone()[0]
        
        # GTD统计
        gtd_tags = ["next-action", "waiting-for", "someday-maybe", "inbox"]
        for tag in gtd_tags:
            self.cursor.execute('''
                SELECT COUNT(*) FROM todos 
                WHERE gtd_tag = ? AND status = 'pending'
            ''', (tag,))
            stats[f'gtd_{tag}'] = self.cursor.fetchone()[0]
        
        return stats
    
    def get_project_statistics(self):
        """获取项目统计"""
        self.cursor.execute('''
            SELECT project, COUNT(*) as count FROM todos 
            WHERE status = 'pending' AND project IS NOT NULL AND project != ''
            GROUP BY project 
            ORDER BY count DESC
            LIMIT 10
        ''')
        return self.cursor.fetchall()
    
    def get_upcoming_tasks(self, start_date, end_date):
        """获取即将到期的任务"""
        self.cursor.execute('''
            SELECT id, title, project, due_date FROM todos 
            WHERE status = 'pending' AND due_date BETWEEN ? AND ?
            ORDER BY due_date, priority
        ''', (start_date, end_date))
        return self.cursor.fetchall()
    
    def update_todo_status(self, todo_id, status):
        """更新待办事项状态"""
        try:
            if status == 'completed':
                completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.cursor.execute('''
                    UPDATE todos SET status = ?, completed_at = ? WHERE id = ?
                ''', (status, completed_at, todo_id))
            else:
                self.cursor.execute('''
                    UPDATE todos SET status = ? WHERE id = ?
                ''', (status, todo_id))
            
            self.conn.commit()
            return self.cursor.rowcount > 0  # 返回是否更新成功
        except Exception as e:
            print(f"更新待办事项状态失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    # AI记忆功能相关方法
    def save_ai_conversation(self, user_input, ai_response, context_summary=None, 
                           action_taken=None, related_todo_ids=None, session_id=None, 
                           conversation_type='general'):
        """保存AI对话历史"""
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute('''
            INSERT INTO ai_conversations 
            (user_input, ai_response, context_summary, action_taken, related_todo_ids, 
             session_id, created_at, conversation_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_input, ai_response, context_summary, action_taken, related_todo_ids, 
              session_id, created_at, conversation_type))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_recent_conversations(self, limit=10, session_id=None):
        """获取最近的对话历史"""
        if session_id:
            self.cursor.execute('''
                SELECT user_input, ai_response, action_taken, created_at 
                FROM ai_conversations 
                WHERE session_id = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (session_id, limit))
        else:
            self.cursor.execute('''
                SELECT user_input, ai_response, action_taken, created_at 
                FROM ai_conversations 
                ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
        return self.cursor.fetchall()
    
    def save_user_preference(self, preference_type, preference_key, preference_value, 
                           confidence_score=0.5, learned_from=None):
        """保存或更新用户偏好"""
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 检查是否已存在相同的偏好
        self.cursor.execute('''
            SELECT id FROM user_preferences 
            WHERE preference_type = ? AND preference_key = ?
        ''', (preference_type, preference_key))
        
        existing = self.cursor.fetchone()
        
        if existing:
            # 更新现有偏好
            self.cursor.execute('''
                UPDATE user_preferences 
                SET preference_value = ?, confidence_score = ?, learned_from = ?, updated_at = ?
                WHERE preference_type = ? AND preference_key = ?
            ''', (preference_value, confidence_score, learned_from, created_at, preference_type, preference_key))
        else:
            # 创建新偏好
            self.cursor.execute('''
                INSERT INTO user_preferences 
                (preference_type, preference_key, preference_value, confidence_score, learned_from, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (preference_type, preference_key, preference_value, confidence_score, learned_from, created_at, created_at))
        
        self.conn.commit()
    
    def get_user_preferences(self, preference_type=None):
        """获取用户偏好"""
        if preference_type:
            self.cursor.execute('''
                SELECT preference_key, preference_value, confidence_score 
                FROM user_preferences 
                WHERE preference_type = ?
                ORDER BY confidence_score DESC
            ''', (preference_type,))
        else:
            self.cursor.execute('''
                SELECT preference_type, preference_key, preference_value, confidence_score 
                FROM user_preferences 
                ORDER BY preference_type, confidence_score DESC
            ''')
        return self.cursor.fetchall()
    
    def update_keyword_memory(self, keyword, category=None, context=None):
        """更新关键词记忆"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 检查关键词是否已存在
        self.cursor.execute('SELECT id, frequency FROM ai_memory_keywords WHERE keyword = ?', (keyword,))
        existing = self.cursor.fetchone()
        
        if existing:
            # 更新频率和最后提及时间
            new_frequency = existing[1] + 1
            self.cursor.execute('''
                UPDATE ai_memory_keywords 
                SET frequency = ?, last_mentioned = ?, context = ?
                WHERE keyword = ?
            ''', (new_frequency, current_time, context, keyword))
        else:
            # 创建新关键词记录
            self.cursor.execute('''
                INSERT INTO ai_memory_keywords 
                (keyword, category, frequency, last_mentioned, context, created_at)
                VALUES (?, ?, 1, ?, ?, ?)
            ''', (keyword, category, current_time, context, current_time))
        
        self.conn.commit()
    
    def get_important_keywords(self, limit=20):
        """获取重要关键词"""
        self.cursor.execute('''
            SELECT keyword, category, frequency, importance_score, context 
            FROM ai_memory_keywords 
            ORDER BY frequency DESC, importance_score DESC 
            LIMIT ?
        ''', (limit,))
        return self.cursor.fetchall()
    
    def save_task_template(self, template_name, title_pattern, default_project=None, 
                         default_priority=None, default_gtd_tag=None):
        """保存任务模板"""
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute('''
            INSERT INTO task_templates 
            (template_name, title_pattern, default_project, default_priority, default_gtd_tag, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (template_name, title_pattern, default_project, default_priority, default_gtd_tag, created_at, created_at))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_task_templates(self):
        """获取任务模板"""
        self.cursor.execute('''
            SELECT template_name, title_pattern, default_project, default_priority, default_gtd_tag, usage_count, success_rate 
            FROM task_templates 
            ORDER BY usage_count DESC, success_rate DESC
        ''')
        return self.cursor.fetchall()
    
    def update_template_usage(self, template_name, success=True):
        """更新模板使用统计"""
        # 获取当前统计
        self.cursor.execute('SELECT usage_count, success_rate FROM task_templates WHERE template_name = ?', (template_name,))
        result = self.cursor.fetchone()
        
        if result:
            current_usage, current_success_rate = result
            new_usage = current_usage + 1
            
            # 计算新的成功率
            if success:
                new_success_rate = (current_success_rate * current_usage + 1) / new_usage
            else:
                new_success_rate = (current_success_rate * current_usage) / new_usage
            
            self.cursor.execute('''
                UPDATE task_templates 
                SET usage_count = ?, success_rate = ?, updated_at = ?
                WHERE template_name = ?
            ''', (new_usage, new_success_rate, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), template_name))
            
            self.conn.commit()
    
    def get_ai_context_for_user(self):
        """获取用户的AI上下文信息（用于个性化响应）"""
        context = {}
        
        # 获取最近的偏好
        preferences = self.get_user_preferences()
        context['preferences'] = {f"{p[0]}_{p[1]}": p[2] for p in preferences}
        
        # 获取常用关键词
        keywords = self.get_important_keywords(10)
        context['important_keywords'] = [k[0] for k in keywords]
        
        # 获取最近对话
        recent_conversations = self.get_recent_conversations(5)
        context['recent_context'] = [{"input": c[0], "action": c[2]} for c in recent_conversations]
        
        return context 