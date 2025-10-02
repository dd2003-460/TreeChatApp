import ollama
import logging
import configparser
import os

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIModel:
    def __init__(self):
        # 初始化 AI 模型
        self.model = "gemma3n:e4b"  # 直接使用用户实际拥有的模型
        self.available_models = []
        self.chat_history = []  # 存储对话历史
        self.base_url = "http://localhost:11434"  # 默认服务地址
        try:
            self.client = ollama.Client(host=self.base_url)  # 创建客户端对象
            logger.info(f"已创建Ollama客户端，连接到: {self.base_url}")
            self.load_available_models()
        except Exception as e:
            logger.error(f"初始化Ollama客户端失败: {str(e)}")
            self.client = None

    def set_base_url(self, base_url):
        """设置Ollama服务地址"""
        try:
            self.base_url = base_url
            self.client = ollama.Client(host=base_url)
            logger.info(f"已更新Ollama服务地址: {base_url}")
            # 尝试获取模型列表验证连接
            self.load_available_models()
            return True
        except Exception as e:
            logger.error(f"设置服务地址失败: {str(e)}")
            return False

    def load_available_models(self):
        """加载可用的Ollama模型列表，处理不同的API响应类型"""
        logger.info("正在加载可用的Ollama模型...")
        self.available_models = []
        try:
            # 尝试获取模型列表
            models = self.client.list()
            
            # 处理不同格式的响应
            if hasattr(models, 'models'):
                # 新版Ollama API响应格式
                for model in models.models:
                    if hasattr(model, 'name'):
                        self.available_models.append(model.name)
            else:
                # 旧版Ollama API或列表直接作为响应
                for model in models:
                    if isinstance(model, dict) and 'name' in model:
                        self.available_models.append(model['name'])
                    elif hasattr(model, 'name'):
                        self.available_models.append(model.name)
            
            logger.info(f"成功加载 {len(self.available_models)} 个模型")
            return True
        except Exception as e:
            logger.error(f"加载模型列表失败: {str(e)}")
            # 不自动执行测试，而是让用户通过UI手动刷新或测试
            logger.warning("未执行自动模型测试，您可以通过设置界面手动刷新模型列表")
            # 保留一个默认模型以确保基本功能可用
            if not self.available_models:
                self.available_models.append(self.model)
            return False

    def _test_available_models(self):
        """测试多个已知模型的可用性（现在只有在手动调用时才执行）"""
        logger.info("开始测试已知模型的可用性...")
        # 保留现有的可用模型列表
        existing_models = self.available_models.copy()
        
        # 用户已知的本地模型列表
        known_models = ["gemma3:12b-it-qat", "gemma3:27b-it-qat", "gemma3n:e4b", "deepseek-r1:8b"]
        
        # 测试每个已知模型
        for model in known_models:
            try:
                if model not in existing_models:
                    logger.info(f"尝试直接测试模型: {model}")
                    # 使用简单的ping消息测试模型
                    test_response = self.client.chat(
                        model=model, 
                        messages=[{"role": "user", "content": "ping"}],
                        stream=False
                    )
                    
                    if test_response:
                        logger.info(f"直接测试模型 {model} 成功")
                        existing_models.append(model)
            except Exception as e:
                logger.error(f"测试模型 {model} 失败: {str(e)}")
        
        # 如果找到了新模型，更新可用模型列表
        if set(existing_models) != set(self.available_models):
            self.available_models = existing_models
            logger.info(f"通过备用测试找到 {len(self.available_models)} 个模型: {', '.join(self.available_models)}")
            
    def add_model_manually(self, model_name):
        """手动添加模型到可用列表"""
        if not self.client:
            logger.error("Ollama客户端未初始化，无法添加模型")
            return False
        
        try:
            # 测试模型是否可用
            test_response = self.client.chat(
                model=model_name, 
                messages=[{"role": "user", "content": "ping"}],
                stream=False
            )
            
            if test_response:
                # 检查模型是否已经在列表中
                if model_name not in self.available_models:
                    self.available_models.append(model_name)
                    logger.info(f"已手动添加模型: {model_name}")
                    return True
                else:
                    logger.info(f"模型 {model_name} 已在可用列表中")
                    return True
            else:
                logger.error(f"无法添加模型 {model_name}: 测试失败")
                return False
        except Exception as e:
            logger.error(f"添加模型 {model_name} 失败: {str(e)}")
            return False
    
    def set_model(self, model_name):
        """设置当前使用的模型"""
        # 如果模型名称为空，返回False
        if not model_name:
            logger.error("模型名称不能为空")
            return False
            
        # 检查模型是否在可用列表中或直接测试
        if model_name in self.available_models or self.add_model_manually(model_name):
            self.model = model_name
            self.chat_history = []  # 切换模型时清空对话历史
            logger.info(f"已切换到模型: {model_name}")
            return True
        else:
            logger.error(f"模型 {model_name} 不可用")
            return False

    def get_available_models(self):
        """获取可用模型列表"""
        return self.available_models

    def generate_response(self, input_text):
        """
        根据输入文本生成回复
        """
        try:
            # 添加用户消息到对话历史
            self.chat_history.append({'role': 'user', 'content': input_text})

            # 调用 Ollama API 生成回复
            response = self.client.chat(model=self.model, messages=self.chat_history)

            # 提取回复内容
            reply = response['message']['content']

            # 添加 AI 回复到对话历史
            self.chat_history.append({'role': 'assistant', 'content': reply})

            return reply
        except Exception as e:
            print(f"生成回复失败: {e}")
            return f"生成回复失败: {str(e)}"

    def get_reply(self, input_text):
        """供外部调用的获取回复方法"""
        return self.generate_response(input_text)

    def clear_chat_history(self):
        """清空对话历史"""
        self.chat_history = []
