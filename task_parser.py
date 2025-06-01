"""
任务解析模块
包含智能任务解析、GTD分类、优先级分析等功能
"""
import re
from datetime import datetime, timedelta


class TaskParser:
    """任务解析器"""
    
    def __init__(self, role_manager=None):
        """初始化任务解析器"""
        self.role_manager = role_manager
    
    def parse_task_from_input(self, user_input):
        """从用户输入中解析任务信息"""
        try:
            task_info = {}
            
            # 1. 提取任务标题
            task_info['title'] = self._extract_task_title(user_input)
            if not task_info['title']:
                return None
            
            # 2. 分析GTD标签
            task_info['gtd_tag'] = self._analyze_gtd_tag(user_input, task_info['title'])
            
            # 3. 分析重要性和紧急性，计算优先级
            importance, urgency = self._analyze_importance_urgency(user_input, task_info['title'])
            task_info['importance'] = 1 if importance else 0  # 添加importance字段
            task_info['urgency'] = 1 if urgency else 0        # 添加urgency字段
            task_info['priority'] = self._calculate_priority(importance, urgency)
            
            # 4. 提取项目信息（考虑用户默认项目）
            task_info['project'] = self._extract_project(user_input)
            
            # 5. 设置默认责任级别
            task_info['responsibility'] = self._get_default_responsibility()
            
            # 6. 提取时间信息
            due_date, reminder_time = self._extract_time_info(user_input)
            task_info['due_date'] = due_date
            task_info['reminder_time'] = reminder_time
            
            # 7. 生成任务描述
            task_info['description'] = self._generate_description(user_input, task_info)
            
            return task_info
            
        except Exception as e:
            raise Exception(f"解析任务信息时出错：{str(e)}")
    
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
        text = (user_input + " " + title).lower()
        
        # 下一步行动关键词
        next_action_keywords = [
            '立即', '马上', '现在', '今天', '今日', '当前', '急需', '赶紧',
            '立刻', '即刻', '尽快', '优先', '首先', '先做', '开始'
        ]
        
        # 等待中关键词
        waiting_keywords = [
            '等待', '等', '依赖', '需要', '等别人', '等回复', '等确认',
            '等通知', '等审批', '等结果', '等消息', '等反馈'
        ]
        
        # 将来/也许关键词
        someday_keywords = [
            '将来', '以后', '有空', '有时间', '考虑', '想要', '希望',
            '计划', '打算', '学习', '研究', '了解', '可能', '也许'
        ]
        
        # 检查关键词
        if any(keyword in text for keyword in next_action_keywords):
            return 'next-action'
        elif any(keyword in text for keyword in waiting_keywords):
            return 'waiting-for'
        elif any(keyword in text for keyword in someday_keywords):
            return 'someday-maybe'
        else:
            return 'inbox'  # 默认为收件箱
    
    def _analyze_importance_urgency(self, user_input, title):
        """分析重要性和紧急性"""
        text = (user_input + " " + title).lower()
        
        # 重要性关键词
        important_keywords = [
            '重要', '关键', '核心', '主要', '必须', '必要', '关键性',
            '重点', '优先', '首要', '战略', '目标', '计划', '项目',
            '会议', '汇报', '报告', '演示', '展示', '学习', '成长'
        ]
        
        # 紧急性关键词
        urgent_keywords = [
            '紧急', '急', '立即', '马上', '现在', '今天', '今日',
            '截止', 'deadline', '最后', '赶紧', '立刻', '即刻',
            '尽快', '火急', '十万火急', 'bug', '故障', '问题',
            '修复', '解决', '处理'
        ]
        
        # 时间紧急性
        time_urgent_patterns = [
            r'今天|今日|当天',
            r'明天|明日',
            r'本周|这周',
            r'\d+小时内',
            r'\d+分钟内',
            r'马上|立即|立刻'
        ]
        
        # 判断重要性
        importance = any(keyword in text for keyword in important_keywords)
        
        # 判断紧急性
        urgency = (any(keyword in text for keyword in urgent_keywords) or
                  any(re.search(pattern, text) for pattern in time_urgent_patterns))
        
        return importance, urgency
    
    def _calculate_priority(self, importance, urgency):
        """根据重要性和紧急性计算优先级"""
        if importance and urgency:
            return 1  # 重要且紧急
        elif importance and not urgency:
            return 2  # 重要但不紧急
        elif not importance and urgency:
            return 3  # 不重要但紧急
        else:
            return 4  # 不重要且不紧急
    
    def _extract_project(self, user_input):
        """提取项目信息"""
        text = user_input.lower()
        
        # 如果有角色管理器，优先使用其项目分类
        if self.role_manager:
            projects = self.role_manager.get_available_projects()
            
            # 检查用户输入是否直接提到某个项目
            for project in projects:
                project_keywords = [project['name'].lower(), project['id'].lower()]
                if project['description']:
                    project_keywords.extend(project['description'].lower().split())
                
                if any(keyword in text for keyword in project_keywords if len(keyword) > 1):
                    return project['id']
            
            # 基于内容智能匹配项目
            project_keywords = {
                'work': ['工作', '公司', '办公', '会议', '汇报', '报告', '项目', '业务', '客户', '同事', '开发', '编程'],
                'personal': ['个人', '私人', '自己', '生活'],
                'study': ['学习', '课程', '阅读', '研究', '书', '教程', '培训', '考试', '复习', '技能'],
                'health': ['健康', '运动', '锻炼', '医院', '体检', '养生', '跑步', '健身'],
                'family': ['家庭', '家人', '父母', '孩子', '家事', '家务'],
                'finance': ['理财', '投资', '财务', '钱', '账单', '支付', '银行'],
                'hobby': ['爱好', '兴趣', '娱乐', '游戏', '电影', '音乐', '绘画'],
                'social': ['社交', '朋友', '聚会', '约会', '活动'],
                'travel': ['旅行', '旅游', '出差', '度假', '机票', '酒店'],
            }
            
            # 检查项目关键词
            for project_id, keywords in project_keywords.items():
                if any(keyword in text for keyword in keywords):
                    return project_id
            
            # 返回用户默认项目
            return self.role_manager.profile.get('default_project', 'work')
        else:
            # 没有角色管理器时的原始逻辑
            project_keywords = {
                'work': ['工作', '公司', '办公', '会议', '汇报', '报告', '项目', '业务', '客户', '同事'],
                'study': ['学习', '课程', '阅读', '研究', '书', '教程', '培训', '考试', '复习'],
                'personal': ['买', '购', '购买', '购物', '家', '家庭', '健康', '运动', '锻炼', '医院', '体检'],
                'hobby': ['个人', '爱好', '兴趣', '娱乐', '游戏', '电影', '音乐', '旅行', '旅游']
            }
            
            # 检查项目关键词
            for project, keywords in project_keywords.items():
                if any(keyword in text for keyword in keywords):
                    return project
            
            return 'work'  # 默认项目
    
    def _get_default_responsibility(self):
        """获取默认责任级别"""
        if self.role_manager:
            return self.role_manager.profile.get('default_responsibility', 'owner')
        else:
            return 'owner'
    
    def _extract_time_info(self, user_input):
        """提取时间信息"""
        due_date = None
        reminder_time = None
        
        try:
            text = user_input.lower()
            now = datetime.now()
            
            # 相对时间模式
            if '今天' in text or '今日' in text:
                due_date = now.strftime('%Y-%m-%d')
            elif '明天' in text or '明日' in text:
                due_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
            elif '后天' in text:
                due_date = (now + timedelta(days=2)).strftime('%Y-%m-%d')
            elif '下周' in text:
                due_date = (now + timedelta(days=7)).strftime('%Y-%m-%d')
            elif '下个月' in text:
                due_date = (now + timedelta(days=30)).strftime('%Y-%m-%d')
            
            # 数字天数模式
            day_pattern = r'(\d+)天后'
            match = re.search(day_pattern, text)
            if match:
                days = int(match.group(1))
                due_date = (now + timedelta(days=days)).strftime('%Y-%m-%d')
            
            # 具体日期模式
            date_patterns = [
                r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
                r'(\d{1,2})月(\d{1,2})日',        # 1月15日
                r'(\d{1,2})/(\d{1,2})'           # 1/15
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    if pattern == date_patterns[0]:  # YYYY-MM-DD
                        year, month, day = match.groups()
                        due_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif pattern == date_patterns[1]:  # M月D日
                        month, day = match.groups()
                        year = now.year
                        due_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    elif pattern == date_patterns[2]:  # M/D
                        month, day = match.groups()
                        year = now.year
                        due_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    break
            
            # 时间点模式（用于提醒）
            time_patterns = [
                r'(\d{1,2}):(\d{2})',           # 14:30
                r'(\d{1,2})点(\d{1,2})分?',      # 2点30分
                r'上午(\d{1,2})点',              # 上午9点
                r'下午(\d{1,2})点',              # 下午2点
                r'晚上(\d{1,2})点'               # 晚上8点
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    if pattern == time_patterns[0]:  # HH:MM
                        hour, minute = match.groups()
                        if due_date:
                            reminder_time = f"{due_date} {hour.zfill(2)}:{minute}"
                    elif pattern == time_patterns[1]:  # X点Y分
                        hour, minute = match.groups()
                        if due_date:
                            reminder_time = f"{due_date} {hour.zfill(2)}:{minute.zfill(2)}"
                    elif pattern == time_patterns[2]:  # 上午X点
                        hour = int(match.group(1))
                        if due_date:
                            reminder_time = f"{due_date} {hour:02d}:00"
                    elif pattern == time_patterns[3]:  # 下午X点
                        hour = int(match.group(1)) + 12
                        if due_date:
                            reminder_time = f"{due_date} {hour:02d}:00"
                    elif pattern == time_patterns[4]:  # 晚上X点
                        hour = int(match.group(1)) + 18
                        if hour > 23:
                            hour = 23
                        if due_date:
                            reminder_time = f"{due_date} {hour:02d}:00"
                    break
            
        except Exception:
            pass  # 忽略时间解析错误
        
        return due_date, reminder_time
    
    def _generate_description(self, user_input, task_info):
        """生成任务描述"""
        description_parts = []
        
        # 添加原始输入
        description_parts.append(f"原始输入: {user_input}")
        
        # 添加智能解析结果
        description_parts.append("\n智能解析结果:")
        
        # GTD标签说明
        gtd_names = {
            'next-action': '下一步行动',
            'waiting-for': '等待中',
            'someday-maybe': '将来/也许',
            'inbox': '收件箱'
        }
        description_parts.append(f"- GTD标签: {gtd_names.get(task_info['gtd_tag'], '未知')}")
        
        # 优先级说明
        priority_names = {
            1: '重要且紧急',
            2: '重要但不紧急',
            3: '不重要但紧急',
            4: '不重要且不紧急'
        }
        description_parts.append(f"- 优先级: {priority_names.get(task_info['priority'], '未知')}")
        
        # 项目信息
        description_parts.append(f"- 项目: {task_info['project']}")
        
        # 时间信息
        if task_info['due_date']:
            description_parts.append(f"- 截止日期: {task_info['due_date']}")
        if task_info['reminder_time']:
            description_parts.append(f"- 提醒时间: {task_info['reminder_time']}")
        
        return "\n".join(description_parts)
    
    def extract_task_ids(self, text):
        """从文本中提取任务ID"""
        # 匹配数字ID
        id_patterns = [
            r'(?:任务|ID|id|编号)\s*[：:]\s*(\d+)',
            r'(?:删除|完成|修改)\s*(\d+)',
            r'#(\d+)',
            r'\b(\d+)\b'
        ]
        
        ids = []
        for pattern in id_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            ids.extend([int(match) for match in matches])
        
        return list(set(ids))  # 去重
    
    def extract_task_titles(self, text):
        """从文本中提取任务标题"""
        # 匹配引号中的内容
        title_patterns = [
            r'"([^"]+)"',
            r"'([^']+)'",
            r'《([^》]+)》',
            r'【([^】]+)】'
        ]
        
        titles = []
        for pattern in title_patterns:
            matches = re.findall(pattern, text)
            titles.extend(matches)
        
        return titles
    
    def get_priority_name(self, priority):
        """获取优先级名称"""
        priority_names = {
            1: '重要且紧急',
            2: '重要但不紧急', 
            3: '不重要但紧急',
            4: '不重要且不紧急'
        }
        return priority_names.get(priority, '未知优先级') 