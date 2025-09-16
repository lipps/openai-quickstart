import argparse

class ArgumentParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description='AI PDF Translator - 支持命令行和GUI模式')
        
        # GUI模式参数
        self.parser.add_argument('--gui', action='store_true', help='启动GUI模式')
        
        # 配置文件参数
        self.parser.add_argument('--config', type=str, default='config.yaml', help='Configuration file with model and API settings.')
        
        # 模型选择参数
        self.parser.add_argument('--model_type', type=str, choices=['GLMModel', 'OpenAIModel'], help='The type of translation model to use. Choose between "GLMModel" and "OpenAIModel".')        
        
        # GLM模型参数
        self.parser.add_argument('--glm_model_url', type=str, help='The URL of the ChatGLM model URL.')
        self.parser.add_argument('--timeout', type=int, help='Timeout for the API request in seconds.')
        
        # OpenAI模型参数
        self.parser.add_argument('--openai_model', type=str, help='The model name of OpenAI Model. Required if model_type is "OpenAIModel".')
        self.parser.add_argument('--openai_api_key', type=str, help='The API key for OpenAIModel. Required if model_type is "OpenAIModel".')
        
        # 翻译参数
        self.parser.add_argument('--book', type=str, help='PDF file to translate.')
        self.parser.add_argument('--file_format', type=str, help='The file format of translated book. Now supporting PDF and Markdown')
        self.parser.add_argument('--target_language', type=str, default='中文', help='Target language for translation.')
        self.parser.add_argument('--output_dir', type=str, default='./output', help='Output directory for translated files.')

    def parse_arguments(self):
        args = self.parser.parse_args()
        
        # 如果是GUI模式，不需要验证其他参数
        if hasattr(args, 'gui') and args.gui:
            return args
            
        # 命令行模式需要验证参数
        if args.model_type == 'OpenAIModel' and not args.openai_model and not args.openai_api_key:
            self.parser.error("--openai_model and --openai_api_key is required when using OpenAIModel")
            
        return args
