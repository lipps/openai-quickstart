import gradio as gr
import yaml
import os
from typing import Dict, Any, Optional

class ConfigManagerComponent:
    """配置管理组件"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.default_config = {
            'OpenAIModel': {
                'model': 'gpt-4o-mini',
                'api_key': ''
            },
            'GLMModel': {
                'model_url': '',
                'timeout': 300
            },
            'common': {
                'book': '',
                'file_format': 'markdown'
            }
        }
        
    def create_config_interface(self):
        """创建配置管理界面"""
        with gr.Column():
            gr.Markdown("### ⚙️ 配置管理")
            
            with gr.Tab("OpenAI 配置"):
                openai_model = gr.Dropdown(
                    choices=['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
                    label="模型选择",
                    value='gpt-4o-mini'
                )
                
                openai_api_key = gr.Textbox(
                    label="API Key",
                    type="password",
                    placeholder="输入你的OpenAI API Key"
                )
                
            with gr.Tab("GLM 配置"):
                glm_model_url = gr.Textbox(
                    label="模型URL",
                    placeholder="输入ChatGLM模型URL"
                )
                
                glm_timeout = gr.Number(
                    label="超时时间(秒)",
                    value=300,
                    minimum=30,
                    maximum=600
                )
                
            with gr.Tab("通用配置"):
                target_language = gr.Dropdown(
                    choices=['中文', '英文', '日文', '韩文', '法文', '德文', '西班牙文'],
                    label="目标语言",
                    value='中文'
                )
                
                file_format = gr.Dropdown(
                    choices=['markdown', 'pdf'],
                    label="输出格式",
                    value='markdown'
                )
                
                output_dir = gr.Textbox(
                    label="输出目录",
                    value="./output",
                    placeholder="翻译文件保存目录"
                )
                
            with gr.Row():
                load_config_btn = gr.Button("📂 加载配置", variant="secondary")
                save_config_btn = gr.Button("💾 保存配置", variant="primary")
                reset_config_btn = gr.Button("🔄 重置配置", variant="secondary")
                
            config_status = gr.Textbox(
                label="配置状态",
                interactive=False,
                lines=2
            )
            
        components = {
            'openai_model': openai_model,
            'openai_api_key': openai_api_key,
            'glm_model_url': glm_model_url,
            'glm_timeout': glm_timeout,
            'target_language': target_language,
            'file_format': file_format,
            'output_dir': output_dir,
            'config_status': config_status
        }
        
        buttons = {
            'load_config_btn': load_config_btn,
            'save_config_btn': save_config_btn,
            'reset_config_btn': reset_config_btn
        }
        
        return components, buttons
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                return config
            else:
                return self.default_config.copy()
        except Exception as e:
            return self.default_config.copy()
    
    def save_config(self, config_data: Dict[str, Any]) -> tuple[bool, str]:
        """保存配置文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_path) if os.path.dirname(self.config_path) else '.', exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            return True, f"配置已保存到 {self.config_path}"
        except Exception as e:
            return False, f"保存配置失败: {str(e)}"
    
    def validate_config(self, config_data: Dict[str, Any]) -> tuple[bool, str]:
        """验证配置数据"""
        errors = []
        
        # 验证OpenAI配置
        if not config_data.get('OpenAIModel', {}).get('api_key'):
            errors.append("OpenAI API Key 不能为空")
            
        # 验证GLM配置（如果使用GLM）
        glm_url = config_data.get('GLMModel', {}).get('model_url')
        if glm_url and not glm_url.startswith(('http://', 'https://')):
            errors.append("GLM模型URL格式不正确")
            
        # 验证输出目录
        output_dir = config_data.get('common', {}).get('output_dir', './output')
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception:
            errors.append(f"无法创建输出目录: {output_dir}")
            
        if errors:
            return False, "配置验证失败:\n" + "\n".join(f"• {error}" for error in errors)
        else:
            return True, "配置验证通过"
    
    def get_config_from_components(self, components: Dict[str, Any]) -> Dict[str, Any]:
        """从Gradio组件获取配置数据"""
        return {
            'OpenAIModel': {
                'model': components['openai_model'],
                'api_key': components['openai_api_key']
            },
            'GLMModel': {
                'model_url': components['glm_model_url'],
                'timeout': int(components['glm_timeout'])
            },
            'common': {
                'target_language': components['target_language'],
                'file_format': components['file_format'],
                'output_dir': components['output_dir']
            }
        }
    
    def update_components_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """从配置数据更新Gradio组件"""
        return {
            'openai_model': config.get('OpenAIModel', {}).get('model', 'gpt-4o-mini'),
            'openai_api_key': config.get('OpenAIModel', {}).get('api_key', ''),
            'glm_model_url': config.get('GLMModel', {}).get('model_url', ''),
            'glm_timeout': config.get('GLMModel', {}).get('timeout', 300),
            'target_language': config.get('common', {}).get('target_language', '中文'),
            'file_format': config.get('common', {}).get('file_format', 'markdown'),
            'output_dir': config.get('common', {}).get('output_dir', './output')
        }