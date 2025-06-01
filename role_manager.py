"""
角色管理模块
负责管理用户角色、项目和身份信息
"""
import json
import os
import tkinter as tk
from tkinter import messagebox, ttk
import ttkbootstrap as ttk_bs
from ttkbootstrap.constants import *

class RoleManager:
    """角色管理器类"""
    
    def __init__(self, config_file="user_profile.json"):
        self.config_file = config_file
        self.profile = {}
        self.default_roles = [
            {"id": "ceo", "name": "CEO/总经理", "description": "负责公司整体战略和重大决策"},
            {"id": "manager", "name": "部门经理", "description": "负责部门管理和团队协调"},
            {"id": "team_lead", "name": "团队负责人", "description": "负责项目执行和团队管理"},
            {"id": "developer", "name": "开发工程师", "description": "负责技术开发和实现"},
            {"id": "designer", "name": "设计师", "description": "负责产品设计和用户体验"},
            {"id": "marketing", "name": "市场营销", "description": "负责市场推广和客户关系"},
            {"id": "sales", "name": "销售", "description": "负责销售业务和客户拓展"},
            {"id": "hr", "name": "人力资源", "description": "负责人事管理和招聘"},
            {"id": "finance", "name": "财务", "description": "负责财务管理和成本控制"},
            {"id": "student", "name": "学生", "description": "学习和个人发展"},
            {"id": "freelancer", "name": "自由职业者", "description": "独立工作和项目管理"},
            {"id": "other", "name": "其他", "description": "自定义角色"}
        ]
        
        self.default_projects = [
            {"id": "work", "name": "工作项目", "description": "日常工作相关任务"},
            {"id": "personal", "name": "个人事务", "description": "个人生活相关任务"},
            {"id": "study", "name": "学习提升", "description": "学习和技能提升"},
            {"id": "health", "name": "健康管理", "description": "健康和运动相关"},
            {"id": "family", "name": "家庭事务", "description": "家庭和亲情相关"},
            {"id": "finance", "name": "财务管理", "description": "理财和投资相关"},
            {"id": "hobby", "name": "兴趣爱好", "description": "娱乐和兴趣相关"},
            {"id": "social", "name": "社交活动", "description": "社交和人际关系"},
            {"id": "travel", "name": "旅行计划", "description": "旅行和度假相关"},
            {"id": "other", "name": "其他项目", "description": "其他类型项目"}
        ]
        
        self.responsibility_levels = [
            {"id": "owner", "name": "负责人", "description": "对结果负全责，需要主导推进"},
            {"id": "participant", "name": "参与者", "description": "参与执行，配合负责人工作"},
            {"id": "observer", "name": "关注者", "description": "需要了解进展，但不直接参与"},
            {"id": "supporter", "name": "支持者", "description": "提供资源或技术支持"}
        ]
        
        self.load_profile()
    
    def load_profile(self):
        """加载用户配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.profile = json.load(f)
            else:
                self.profile = {
                    "user_info": {
                        "name": "",
                        "role_id": "",
                        "custom_role": "",
                        "department": "",
                        "company": ""
                    },
                    "default_project": "",
                    "default_responsibility": "owner",
                    "custom_roles": [],
                    "custom_projects": [],
                    "ai_context": {
                        "personality": "professional",
                        "communication_style": "formal",
                        "priority_preference": "urgent_important"
                    }
                }
                self.save_profile()
        except Exception as e:
            print(f"加载用户配置失败: {e}")
            self.profile = {}
    
    def save_profile(self):
        """保存用户配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存用户配置失败: {e}")
    
    def is_profile_configured(self):
        """检查用户配置是否完成"""
        user_info = self.profile.get("user_info", {})
        return bool(user_info.get("name") and user_info.get("role_id"))
    
    def get_user_info(self):
        """获取用户信息"""
        return self.profile.get("user_info", {})
    
    def get_role_name(self):
        """获取角色名称"""
        user_info = self.get_user_info()
        role_id = user_info.get("role_id")
        
        if role_id == "other":
            return user_info.get("custom_role", "其他")
        
        for role in self.default_roles:
            if role["id"] == role_id:
                return role["name"]
        
        # 检查自定义角色
        for role in self.profile.get("custom_roles", []):
            if role["id"] == role_id:
                return role["name"]
        
        return "未设置"
    
    def get_current_role(self):
        """获取当前角色信息"""
        user_info = self.get_user_info()
        role_id = user_info.get("role_id", "")
        
        if not role_id:
            return {"id": "", "name": "未设置", "description": ""}
        
        if role_id == "other":
            return {
                "id": "other",
                "name": user_info.get("custom_role", "其他"),
                "description": "自定义角色"
            }
        
        # 在默认角色中查找
        for role in self.default_roles:
            if role["id"] == role_id:
                return role
        
        # 在自定义角色中查找
        for role in self.profile.get("custom_roles", []):
            if role["id"] == role_id:
                return role
        
        return {"id": role_id, "name": "未知角色", "description": ""}
    
    def get_available_roles(self):
        """获取所有可用角色"""
        all_roles = self.default_roles.copy()
        all_roles.extend(self.profile.get("custom_roles", []))
        return all_roles
    
    def get_available_projects(self):
        """获取所有可用项目"""
        all_projects = self.default_projects.copy()
        all_projects.extend(self.profile.get("custom_projects", []))
        return all_projects
    
    def get_responsibility_levels(self):
        """获取责任级别"""
        return self.responsibility_levels
    
    def add_custom_role(self, role_id, name, description):
        """添加自定义角色"""
        custom_roles = self.profile.get("custom_roles", [])
        custom_roles.append({
            "id": role_id,
            "name": name,
            "description": description
        })
        self.profile["custom_roles"] = custom_roles
        self.save_profile()
    
    def add_custom_project(self, project_id, name, description):
        """添加自定义项目"""
        custom_projects = self.profile.get("custom_projects", [])
        custom_projects.append({
            "id": project_id,
            "name": name,
            "description": description
        })
        self.profile["custom_projects"] = custom_projects
        self.save_profile()
    
    def update_user_info(self, **kwargs):
        """更新用户信息"""
        user_info = self.profile.get("user_info", {})
        user_info.update(kwargs)
        self.profile["user_info"] = user_info
        self.save_profile()
    
    def set_defaults(self, default_project=None, default_responsibility=None):
        """设置默认值"""
        if default_project:
            self.profile["default_project"] = default_project
        if default_responsibility:
            self.profile["default_responsibility"] = default_responsibility
        self.save_profile()
    
    def get_ai_context(self):
        """获取AI上下文信息"""
        user_info = self.get_user_info()
        role_name = self.get_role_name()
        
        context = f"""
用户身份信息：
- 姓名：{user_info.get('name', '未设置')}
- 角色：{role_name}
- 部门：{user_info.get('department', '未设置')}
- 公司：{user_info.get('company', '未设置')}
- 默认项目：{self.profile.get('default_project', '未设置')}
- 默认责任级别：{self.profile.get('default_responsibility', 'owner')}

请根据用户的角色和身份特点，调整回复的语调、建议的优先级判断和任务管理方式。
"""
        return context.strip()
    
    def show_role_setup_dialog(self, parent=None):
        """显示角色设置对话框"""
        dialog = RoleSetupDialog(parent, self)
        return dialog.show()


class RoleSetupDialog:
    """角色设置对话框"""
    
    def __init__(self, parent, role_manager):
        self.parent = parent
        self.role_manager = role_manager
        self.dialog = None
        self.result = False
        
        # 输入控件引用
        self.name_entry = None
        self.role_combo = None
        self.custom_role_entry = None
        self.department_entry = None
        self.company_entry = None
        self.project_combo = None
        self.responsibility_combo = None
        
        # 变量将在show方法中创建，确保与对话框窗口关联
    
    def show(self):
        """显示对话框"""
        self.dialog = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.dialog.title("用户角色和项目配置")
        self.dialog.geometry("650x700")
        self.dialog.resizable(False, False)
        
        # 居中显示
        if self.parent:
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
        
        self.create_widgets()
        
        # 加载现有配置到界面
        self.load_existing_config()
        
        if self.parent:
            self.dialog.wait_window()
        
        return self.result
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk_bs.Frame(self.dialog, padding=20)
        main_frame.pack(fill=BOTH, expand=True)
        
        # 标题
        title_label = ttk_bs.Label(
            main_frame,
            text="欢迎使用智能待办事项管理器",
            font=("Microsoft YaHei", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk_bs.Label(
            main_frame,
            text="请设置您的角色和项目信息，以获得个性化的AI建议",
            font=("Microsoft YaHei", 10),
            bootstyle="secondary"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # 创建notebook
        notebook = ttk_bs.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=(0, 20))
        
        # 个人信息标签页
        self.create_personal_info_tab(notebook)
        
        # 项目设置标签页
        self.create_project_settings_tab(notebook)
        
        # 按钮框架
        button_frame = ttk_bs.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        ttk_bs.Button(
            button_frame,
            text="取消",
            bootstyle="secondary",
            command=self.cancel
        ).pack(side=RIGHT, padx=(10, 0))
        
        ttk_bs.Button(
            button_frame,
            text="保存配置",
            bootstyle="primary",
            command=self.save_and_close
        ).pack(side=RIGHT)
        
        # 如果是首次配置，添加跳过按钮
        if not self.role_manager.is_profile_configured():
            ttk_bs.Button(
                button_frame,
                text="稍后配置",
                bootstyle="outline-secondary",
                command=self.skip_setup
            ).pack(side=LEFT)
    
    def create_personal_info_tab(self, notebook):
        """创建个人信息标签页"""
        personal_frame = ttk_bs.Frame(notebook, padding=20)
        notebook.add(personal_frame, text="个人信息")
        
        # 姓名
        ttk_bs.Label(personal_frame, text="姓名 *", font=("Microsoft YaHei", 10, "bold")).grid(
            row=0, column=0, sticky=W, pady=(0, 5)
        )
        self.name_entry = ttk_bs.Entry(
            personal_frame,
            width=40,
            font=("Microsoft YaHei", 10)
        )
        self.name_entry.grid(row=1, column=0, columnspan=2, sticky=W+E, pady=(0, 15))
        
        # 角色选择
        ttk_bs.Label(personal_frame, text="角色 *", font=("Microsoft YaHei", 10, "bold")).grid(
            row=2, column=0, sticky=W, pady=(0, 5)
        )
        
        role_frame = ttk_bs.Frame(personal_frame)
        role_frame.grid(row=3, column=0, columnspan=2, sticky=W+E, pady=(0, 15))
        
        self.role_combo = ttk_bs.Combobox(
            role_frame,
            width=37,
            font=("Microsoft YaHei", 10),
            state="readonly"
        )
        self.role_combo.grid(row=0, column=0, sticky=W+E)
        
        # 填充角色选项
        roles = self.role_manager.get_available_roles()
        role_values = [f"{role['id']}:{role['name']}" for role in roles]
        self.role_combo['values'] = role_values
        
        # 设置当前值
        if self.role_combo.get():
            for role in roles:
                if role['id'] == self.role_combo.get().split(':')[0]:
                    self.role_combo.set(f"{role['id']}:{role['name']}")
                    break
        
        self.role_combo.bind('<<ComboboxSelected>>', self.on_role_changed)
        
        # 自定义角色输入框
        ttk_bs.Label(personal_frame, text="自定义角色名称:", font=("Microsoft YaHei", 9)).grid(
            row=4, column=0, sticky=W, pady=(0, 5)
        )
        self.custom_role_entry = ttk_bs.Entry(
            personal_frame,
            width=40,
            font=("Microsoft YaHei", 10)
        )
        self.custom_role_entry.grid(row=5, column=0, columnspan=2, sticky=W+E, pady=(0, 15))
        
        # 部门
        ttk_bs.Label(personal_frame, text="部门", font=("Microsoft YaHei", 10)).grid(
            row=6, column=0, sticky=W, pady=(0, 5)
        )
        self.department_entry = ttk_bs.Entry(
            personal_frame,
            width=40,
            font=("Microsoft YaHei", 10)
        )
        self.department_entry.grid(row=7, column=0, columnspan=2, sticky=W+E, pady=(0, 15))
        
        # 公司
        ttk_bs.Label(personal_frame, text="公司/组织", font=("Microsoft YaHei", 10)).grid(
            row=8, column=0, sticky=W, pady=(0, 5)
        )
        self.company_entry = ttk_bs.Entry(
            personal_frame,
            width=40,
            font=("Microsoft YaHei", 10)
        )
        self.company_entry.grid(row=9, column=0, columnspan=2, sticky=W+E, pady=(0, 15))
        
        # 配置网格权重
        personal_frame.grid_columnconfigure(0, weight=1)
        role_frame.grid_columnconfigure(0, weight=1)
        
        # 初始显示/隐藏自定义角色框
        self.toggle_custom_role_frame()
    
    def create_project_settings_tab(self, notebook):
        """创建项目设置标签页"""
        project_frame = ttk_bs.Frame(notebook, padding=20)
        notebook.add(project_frame, text="项目设置")
        
        # 默认项目
        ttk_bs.Label(project_frame, text="默认项目 *", font=("Microsoft YaHei", 10, "bold")).grid(
            row=0, column=0, sticky=W, pady=(0, 5)
        )
        
        self.project_combo = ttk_bs.Combobox(
            project_frame,
            width=40,
            font=("Microsoft YaHei", 10),
            state="readonly"
        )
        self.project_combo.grid(row=1, column=0, columnspan=2, sticky=W+E, pady=(0, 15))
        
        # 填充项目选项
        projects = self.role_manager.get_available_projects()
        project_values = [f"{project['id']}:{project['name']}" for project in projects]
        self.project_combo['values'] = project_values
        
        # 设置当前值
        if self.project_combo.get():
            for project in projects:
                if project['id'] == self.project_combo.get().split(':')[0]:
                    self.project_combo.set(f"{project['id']}:{project['name']}")
                    break
        else:
            self.project_combo.set("work:工作项目")
        
        # 默认责任级别
        ttk_bs.Label(project_frame, text="默认责任级别 *", font=("Microsoft YaHei", 10, "bold")).grid(
            row=2, column=0, sticky=W, pady=(0, 5)
        )
        
        self.responsibility_combo = ttk_bs.Combobox(
            project_frame,
            width=40,
            font=("Microsoft YaHei", 10),
            state="readonly"
        )
        self.responsibility_combo.grid(row=3, column=0, columnspan=2, sticky=W+E, pady=(0, 15))
        
        # 填充责任级别选项
        responsibilities = self.role_manager.get_responsibility_levels()
        responsibility_values = [f"{resp['id']}:{resp['name']}" for resp in responsibilities]
        self.responsibility_combo['values'] = responsibility_values
        
        # 设置当前值
        if self.responsibility_combo.get():
            for resp in responsibilities:
                if resp['id'] == self.responsibility_combo.get().split(':')[0]:
                    self.responsibility_combo.set(f"{resp['id']}:{resp['name']}")
                    break
        else:
            self.responsibility_combo.set("owner:负责人")
        
        # 说明文本
        info_text = """
项目设置说明：
• 默认项目：创建新任务时的默认项目分类
• 责任级别：表明您在项目中的角色和责任
  - 负责人：对结果负全责，需要主导推进
  - 参与者：参与执行，配合负责人工作
  - 关注者：需要了解进展，但不直接参与
  - 支持者：提供资源或技术支持

AI助手会根据您的角色和责任级别，提供相应的任务优先级建议和时间管理策略。
"""
        
        info_label = ttk_bs.Label(
            project_frame,
            text=info_text,
            font=("Microsoft YaHei", 9),
            bootstyle="secondary",
            justify=LEFT
        )
        info_label.grid(row=4, column=0, columnspan=2, sticky=W+E, pady=(10, 0))
        
        # 配置网格权重
        project_frame.grid_columnconfigure(0, weight=1)
    
    def on_role_changed(self, event=None):
        """角色选择改变时的处理"""
        self.toggle_custom_role_frame()
    
    def toggle_custom_role_frame(self):
        """显示/隐藏自定义角色输入框"""
        selected = self.role_combo.get()
        if selected.startswith("other:"):
            # 显示自定义角色相关控件
            pass  # 始终显示，根据需要可以添加特殊处理
        else:
            # 隐藏时清空自定义角色内容
            self.custom_role_entry.delete(0, tk.END)
    
    def save_and_close(self):
        """保存配置并关闭"""
        # 验证必填字段
        name_value = self.name_entry.get()
        print(f"Debug: 姓名值 = '{name_value}', 长度 = {len(name_value)}, 去空格后 = '{name_value.strip()}'")
        
        if not name_value or not name_value.strip():
            messagebox.showerror("错误", "请输入姓名")
            return
        
        role_selected = self.role_combo.get()
        if not role_selected:
            messagebox.showerror("错误", "请选择角色")
            return
        
        project_selected = self.project_combo.get()
        if not project_selected:
            messagebox.showerror("错误", "请选择默认项目")
            return
        
        responsibility_selected = self.responsibility_combo.get()
        if not responsibility_selected:
            messagebox.showerror("错误", "请选择责任级别")
            return
        
        # 提取ID值
        role_id = role_selected.split(':')[0] if ':' in role_selected else role_selected
        project_id = project_selected.split(':')[0] if ':' in project_selected else project_selected
        responsibility_id = responsibility_selected.split(':')[0] if ':' in responsibility_selected else responsibility_selected
        
        # 如果选择了"其他"角色，验证自定义角色名称
        if role_id == "other" and not self.custom_role_entry.get().strip():
            messagebox.showerror("错误", "请输入自定义角色名称")
            return
        
        # 保存配置
        self.role_manager.update_user_info(
            name=name_value.strip(),
            role_id=role_id,
            custom_role=self.custom_role_entry.get().strip(),
            department=self.department_entry.get().strip(),
            company=self.company_entry.get().strip()
        )
        
        self.role_manager.set_defaults(
            default_project=project_id,
            default_responsibility=responsibility_id
        )
        
        print(f"Debug: 配置保存成功，姓名 = '{name_value.strip()}'")
        self.result = True
        self.dialog.destroy()
    
    def skip_setup(self):
        """跳过设置"""
        self.result = False
        self.dialog.destroy()
    
    def cancel(self):
        """取消"""
        self.result = False
        self.dialog.destroy()
    
    def load_existing_config(self):
        """加载现有配置到界面"""
        user_info = self.role_manager.get_user_info()
        
        # 设置姓名
        if user_info.get('name'):
            self.name_entry.insert(0, user_info['name'])
        
        # 设置角色
        if user_info.get('role_id'):
            roles = self.role_manager.get_available_roles()
            for role in roles:
                if role['id'] == user_info['role_id']:
                    self.role_combo.set(f"{role['id']}:{role['name']}")
                    break
        
        # 设置自定义角色
        if user_info.get('custom_role'):
            self.custom_role_entry.insert(0, user_info['custom_role'])
        
        # 设置部门
        if user_info.get('department'):
            self.department_entry.insert(0, user_info['department'])
        
        # 设置公司
        if user_info.get('company'):
            self.company_entry.insert(0, user_info['company'])
        
        # 设置默认项目
        default_project = self.role_manager.profile.get('default_project', 'work')
        projects = self.role_manager.get_available_projects()
        for project in projects:
            if project['id'] == default_project:
                self.project_combo.set(f"{project['id']}:{project['name']}")
                break
        
        # 设置默认责任级别
        default_responsibility = self.role_manager.profile.get('default_responsibility', 'owner')
        responsibilities = self.role_manager.get_responsibility_levels()
        for resp in responsibilities:
            if resp['id'] == default_responsibility:
                self.responsibility_combo.set(f"{resp['id']}:{resp['name']}")
                break 