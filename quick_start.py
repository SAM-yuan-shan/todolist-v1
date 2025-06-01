#!/usr/bin/env python3
"""
智能待办事项管理器 - 快速启动脚本
支持单窗口和双窗口模式
"""
import tkinter as tk
import subprocess
import sys
import os
import json

# 配置文件路径
CONFIG_FILE = "startup_config.json"

def load_config():
    """加载启动配置"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"mode": "single"}  # 默认配置

def save_config(config):
    """保存启动配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except:
        pass

def show_startup_dialog():
    """显示启动选项对话框"""
    root = tk.Tk()
    root.title("启动选项")
    root.geometry("450x450")  # 增加窗口高度
    root.resizable(False, False)
    
    # 居中窗口
    root.eval('tk::PlaceWindow . center')
    
    # 加载上次的配置
    config = load_config()
    
    # 创建主框架
    main_frame = tk.Frame(root, padx=30, pady=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    title_label = tk.Label(main_frame, text="智能待办事项管理器", 
                          font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # 说明
    info_label = tk.Label(main_frame, text="请选择启动模式：", 
                         font=("Arial", 12))
    info_label.pack(pady=(0, 15))
    
    # 选项变量，使用上次保存的设置
    mode = tk.StringVar(value=config.get("mode", "single"))
    
    # 单窗口选项
    single_radio = tk.Radiobutton(main_frame, text="单窗口模式（默认）", 
                                 variable=mode, value="single", 
                                 font=("Arial", 11))
    single_radio.pack(anchor=tk.W, pady=5)
    
    single_desc = tk.Label(main_frame, text="所有功能在一个窗口中，包含AI助手标签页", 
                          font=("Arial", 9), fg="gray")
    single_desc.pack(anchor=tk.W, padx=20, pady=(0, 10))
    
    # 双窗口选项
    dual_radio = tk.Radiobutton(main_frame, text="双窗口模式（推荐）", 
                               variable=mode, value="dual", 
                               font=("Arial", 11))
    dual_radio.pack(anchor=tk.W, pady=5)
    
    dual_desc = tk.Label(main_frame, text="主窗口 + 独立AI助手窗口，方便同时操作", 
                        font=("Arial", 9), fg="gray")
    dual_desc.pack(anchor=tk.W, padx=20, pady=(0, 20))
    
    # 记住选择复选框
    remember_choice = tk.BooleanVar(value=True)
    remember_check = tk.Checkbutton(main_frame, text="记住我的选择", 
                                   variable=remember_choice,
                                   font=("Arial", 10))
    remember_check.pack(anchor=tk.W, pady=(10, 30))
    
    # 按钮框架 - 直接添加到main_frame底部
    button_frame = tk.Frame(main_frame)
    button_frame.pack(pady=20)
    
    def start_app():
        """启动应用"""
        print("按钮被点击了！")  # 调试信息
        selected_mode = mode.get()
        print(f"选择的模式: {selected_mode}")  # 调试信息
        
        # 如果选择记住设置，则保存配置
        if remember_choice.get():
            save_config({"mode": selected_mode})
            print("配置已保存")  # 调试信息
        
        print("准备关闭对话框...")  # 调试信息
        root.destroy()
        
        print("准备启动应用...")  # 调试信息
        if selected_mode == "dual":
            # 启动双窗口模式
            print("启动双窗口模式")
            subprocess.run([sys.executable, "main.py", "--dual"])
        else:
            # 启动单窗口模式
            print("启动单窗口模式")
            subprocess.run([sys.executable, "main.py"])
    
    def exit_app():
        """退出"""
        root.destroy()
    
    # 取消按钮
    cancel_button = tk.Button(button_frame, text="取消", command=exit_app,
                             bg="#f44336", fg="white",
                             font=("Arial", 12, "bold"),
                             width=12, height=2)
    cancel_button.pack(side=tk.LEFT, padx=20)
    
    # 确定按钮（主要按钮）
    confirm_button = tk.Button(button_frame, text="确定启动", command=start_app,
                              bg="#4CAF50", fg="white",
                              font=("Arial", 12, "bold"),
                              width=12, height=2)
    confirm_button.pack(side=tk.LEFT, padx=20)
    
    # 设置默认按钮和回车键绑定
    root.bind('<Return>', lambda e: start_app())
    root.bind('<Escape>', lambda e: exit_app())
    confirm_button.focus_set()
    
    # 运行对话框
    root.mainloop()

if __name__ == "__main__":
    show_startup_dialog() 