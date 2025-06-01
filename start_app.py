#!/usr/bin/env python3
"""
智能待办事项管理器启动脚本
"""

if __name__ == "__main__":
    try:
        print("正在启动智能待办事项管理器...")
        print("正在加载模块...")
        
        from main import TodoApp
        
        print("模块加载完成，正在初始化应用程序...")
        app = TodoApp()
        
        print("应用程序初始化完成，正在启动GUI...")
        app.run()
        
    except KeyboardInterrupt:
        print("\n用户中断，正在退出...")
    except Exception as e:
        print(f"应用程序启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...") 