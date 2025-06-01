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
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        
        # 创建待办事项表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                project TEXT,           -- 项目字段
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
        
        # 检查是否需要添加项目列
        self.cursor.execute("PRAGMA table_info(todos)")
        columns = [column[1] for column in self.cursor.fetchall()]
        if 'project' not in columns:
            self.cursor.execute('ALTER TABLE todos ADD COLUMN project TEXT')
        
        self.conn.commit()
    
    def add_todo(self, title, description, project, priority, urgency, importance, 
                 gtd_tag, due_date, reminder_time):
        """添加新的待办事项"""
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute('''
            INSERT INTO todos (title, description, project, priority, urgency, importance, 
                             gtd_tag, due_date, reminder_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, description, project, priority, urgency, importance, gtd_tag, 
              due_date, reminder_time, created_at))
        
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_todos(self):
        """获取所有待办事项"""
        self.cursor.execute('''
            SELECT id, title, project, due_date, status, priority, gtd_tag 
            FROM todos 
            ORDER BY due_date ASC
        ''')
        return self.cursor.fetchall()
    
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
        self.cursor.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        self.conn.commit()
    
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
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close() 