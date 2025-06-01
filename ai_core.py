"""
AI核心功能模块
包含API调用、缓存管理等核心功能
"""
import requests
import json
import threading
from datetime import datetime


class KVCache:
    """KV缓存用于维护对话上下文"""
    def __init__(self):
        self.cache = []
        self.max_history = 20  # 最多保留20轮对话

    def update_cache(self, user_input, model_response):
        """更新KV缓存"""
        self.cache.append({"role": "user", "content": user_input})
        self.cache.append({"role": "assistant", "content": model_response})
        
        # 保持缓存大小
        if len(self.cache) > self.max_history * 2:
            self.cache = self.cache[-self.max_history * 2:]

    def get_context(self):
        """获取当前对话上下文"""
        return self.cache

    def clear_cache(self):
        """清空缓存"""
        self.cache = []


class AICore:
    """AI核心功能类"""
    
    def __init__(self, config_manager=None):
        """初始化AI核心"""
        # 从配置管理器获取API配置
        if config_manager:
            self.api_key = config_manager.get_api_key()
            self.api_url = config_manager.get('ai_assistant.api_url', 'https://api.deepseek.com/v1/chat/completions')
            self.model = config_manager.get('ai_assistant.model', 'deepseek-chat')
            self.temperature = config_manager.get('ai_assistant.temperature', 0.7)
            self.max_tokens = config_manager.get('ai_assistant.max_tokens', 1000)
        else:
            # 默认配置
            self.api_key = "your_api_key_here"
            self.api_url = "https://api.deepseek.com/v1/chat/completions"
            self.model = "deepseek-chat"
            self.temperature = 0.7
            self.max_tokens = 1000
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 初始化KV缓存
        self.kv_cache = KVCache()
    
    def update_api_key(self, api_key):
        """更新API密钥"""
        self.api_key = api_key
        self.headers["Authorization"] = f"Bearer {api_key}"
    
    def test_api_connection(self):
        """测试API连接"""
        try:
            test_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                return True, "API连接成功"
            else:
                return False, f"API连接失败: {response.status_code}"
                
        except Exception as e:
            return False, f"连接错误: {str(e)}"
    
    def call_deepseek_api(self, user_input, system_prompt="", temperature=None, max_tokens=None):
        """调用DeepSeek API"""
        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话
            messages.extend(self.kv_cache.get_context())
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            # 准备请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "stream": False
            }
            
            # 发送请求
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                
                # 更新缓存
                self.kv_cache.update_cache(user_input, ai_response)
                
                return True, ai_response
            else:
                error_msg = f"API调用失败: {response.status_code}"
                if response.text:
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_msg += f" - {error_data['error'].get('message', '')}"
                    except:
                        pass
                return False, error_msg
                
        except requests.exceptions.Timeout:
            return False, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "网络连接错误，请检查网络设置"
        except Exception as e:
            return False, f"API调用异常: {str(e)}"
    
    def call_deepseek_api_stream(self, user_input, system_prompt="", on_chunk=None, temperature=None, max_tokens=None):
        """流式调用DeepSeek API"""
        try:
            # 构建消息
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # 添加历史对话
            messages.extend(self.kv_cache.get_context())
            
            # 添加当前用户输入
            messages.append({"role": "user", "content": user_input})
            
            # 准备请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "stream": True
            }
            
            # 发送流式请求
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        full_response += content
                                        if on_chunk:
                                            on_chunk(content)
                            except json.JSONDecodeError:
                                continue
                
                # 更新缓存
                if full_response:
                    self.kv_cache.update_cache(user_input, full_response)
                
                return True, full_response
            else:
                error_msg = f"API调用失败: {response.status_code}"
                return False, error_msg
                
        except Exception as e:
            return False, f"流式API调用异常: {str(e)}"
    
    def clear_cache(self):
        """清空对话缓存"""
        self.kv_cache.clear_cache()
    
    def get_cache_context(self):
        """获取缓存上下文"""
        return self.kv_cache.get_context() 