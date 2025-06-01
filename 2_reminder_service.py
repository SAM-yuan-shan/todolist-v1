"""
提醒服务模块
负责处理待办事项的提醒功能
"""
import threading
import time
import sqlite3
from datetime import datetime
from plyer import notification

class ReminderService:
    def __init__(self, database_manager):
        """初始化提醒服务"""
        self.db_name = database_manager.db_name
        self.running = False
        self.reminder_thread = None
    
    def start_reminder_thread(self):
        """启动提醒线程"""
        if self.running:
            return
        
        self.running = True
        
        def reminder_worker():
            # 在提醒线程中创建独立的数据库连接
            thread_conn = sqlite3.connect(self.db_name)
            thread_cursor = thread_conn.cursor()
            
            while self.running:
                try:
                    self.check_reminders(thread_cursor)
                    time.sleep(60)  # 每分钟检查一次
                except Exception as e:
                    print(f"提醒服务错误: {e}")
                    break
            
            # 关闭线程的数据库连接
            thread_conn.close()
        
        self.reminder_thread = threading.Thread(target=reminder_worker, daemon=True)
        self.reminder_thread.start()
    
    def stop_reminder_thread(self):
        """停止提醒线程"""
        self.running = False
    
    def check_reminders(self, cursor):
        """检查并发送提醒"""
        now = datetime.now()
        current_time = now.strftime('%Y-%m-%d %H:%M')
        
        # 查询需要提醒的待办事项
        cursor.execute('''
            SELECT id, title, description FROM todos 
            WHERE status = 'pending' AND reminder_time LIKE ?
        ''', (f"{current_time}%",))
        todos = cursor.fetchall()
        
        for todo in todos:
            todo_id, title, description = todo
            try:
                self.send_notification(title, description)
            except Exception as e:
                print(f"发送通知失败: {e}")
    
    def send_notification(self, title, description):
        """发送系统通知"""
        try:
            message = f"{description[:50]}..." if description and len(description) > 50 else (description or "")
            notification.notify(
                title=f"待办事项提醒: {title}",
                message=message,
                timeout=10
            )
        except Exception as e:
            print(f"通知发送失败: {e}")
            # 如果系统通知失败，可以在这里添加其他提醒方式
            pass 