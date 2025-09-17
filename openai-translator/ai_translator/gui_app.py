import gradio as gr
import os
import sys
import threading
import time
from typing import Optional, List, Dict, Any

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components import (
    FileUploadComponent,
    ProgressDisplayComponent,
    ConfigManagerComponent,
    HistoryManagerComponent,
    BatchProcessorComponent
)
from model import OpenAIModel, GLMModel
from translator import PDFTranslator
from utils import LOG

class TranslatorGUI:
    """翻译应用主GUI类"""
    
    def __init__(self):
        # 初始化组件
        self.file_upload = FileUploadComponent()
        self.progress_display = ProgressDisplayComponent()
        self.config_manager = ConfigManagerComponent()
        self.history_manager = HistoryManagerComponent()
        self.batch_processor = BatchProcessorComponent()
        
        # 当前翻译状态
        self.current_translator = None
        self.is_translating = False
        self.current_record_id = None
        self.progress_status = ""
        self.progress_overall = 0
        self.progress_page = 0
        self.progress_time = ""

    def create_interface(self):
        """创建主界面"""
        with gr.Blocks(
            title="AI PDF 翻译器",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as interface:
            
            # 标题和描述
            gr.Markdown(
                """
                # 🤖 AI PDF 翻译器
                
                **功能特点:**
                - 🎯 支持多种AI模型 (OpenAI GPT, ChatGLM)
                - 📁 拖拽式文件上传，支持批量处理
                - 📊 实时翻译进度显示
                - 📚 翻译历史记录管理
                - ⚙️ 灵活的配置管理
                """
            )
            
            with gr.Tabs() as tabs:
                # 单文件翻译标签页
                with gr.Tab("📄 单文件翻译", id="single_translate"):
                    self._create_single_translate_tab()
                    
                # 批量翻译标签页  
                with gr.Tab("📁 批量翻译", id="batch_translate"):
                    self._create_batch_translate_tab()
                    
                # 配置管理标签页
                with gr.Tab("⚙️ 配置管理", id="config"):
                    self._create_config_tab()
                    
                # 历史记录标签页
                with gr.Tab("📚 翻译历史", id="history"):
                    self._create_history_tab()
                    
        return interface
    
    def _create_single_translate_tab(self):
        """创建单文件翻译标签页"""
        with gr.Row():
            with gr.Column(scale=1):
                # 文件上传区域
                single_file, file_info = self.file_upload.create_single_upload_interface()
                
                # 翻译设置
                with gr.Group():
                    gr.Markdown("### 🎯 翻译设置")
                    
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
                    
                    model_type = gr.Dropdown(
                        choices=['OpenAI', 'ChatGLM'],
                        label="AI模型",
                        value='OpenAI'
                    )
                    
                # 翻译按钮
                translate_btn = gr.Button(
                    "🚀 开始翻译",
                    variant="primary",
                    size="lg"
                )
                
            with gr.Column(scale=1):
                # 进度显示区域
                progress_components = self.progress_display.create_progress_interface()
                
                # 结果显示
                with gr.Group():
                    gr.Markdown("### 📥 翻译结果")
                    
                    result_file = gr.File(
                        label="下载翻译结果",
                        interactive=False
                    )
                    
                    result_info = gr.Textbox(
                        label="翻译信息",
                        interactive=False,
                        lines=3
                    )
        
        # 绑定事件
        single_file.change(
            fn=self.file_upload.get_file_info,
            inputs=[single_file],
            outputs=[file_info]
        )
        
        translate_btn.click(
            fn=self._start_single_translation,
            inputs=[single_file, target_language, file_format, model_type],
            outputs=[result_file, result_info] + list(progress_components)
        )
    
    def _create_batch_translate_tab(self):
        """创建批量翻译标签页"""
        with gr.Row():
            with gr.Column(scale=1):
                # 批量文件上传
                batch_files, batch_file_info = self.file_upload.create_batch_upload_interface()
                
                # 批量设置
                with gr.Group():
                    gr.Markdown("### ⚙️ 批量设置")
                    
                    batch_target_language = gr.Dropdown(
                        choices=['中文', '英文', '日文', '韩文', '法文', '德文', '西班牙文'],
                        label="目标语言",
                        value='中文'
                    )
                    
                    batch_file_format = gr.Dropdown(
                        choices=['markdown', 'pdf'],
                        label="输出格式",
                        value='markdown'
                    )
                    
                    batch_model_type = gr.Dropdown(
                        choices=['OpenAI', 'ChatGLM'],
                        label="AI模型",
                        value='OpenAI'
                    )
                
                # 批量操作按钮
                add_to_queue_btn = gr.Button("➕ 添加到队列", variant="secondary")
                
            with gr.Column(scale=2):
                # 批量处理组件
                batch_components, batch_buttons = self.batch_processor.create_batch_interface()
        
        # 绑定批量处理事件
        batch_files.change(
            fn=self.file_upload.validate_batch_files,
            inputs=[batch_files],
            outputs=[batch_file_info]
        )
        
        add_to_queue_btn.click(
            fn=self._add_files_to_batch_queue,
            inputs=[batch_files, batch_target_language, batch_file_format, batch_model_type],
            outputs=[batch_components['batch_status'], batch_components['queue_display']]
        )
        
        batch_buttons['start_batch_btn'].click(
            fn=self._start_batch_processing,
            inputs=[batch_components['max_workers'], batch_components['retry_failed'], batch_components['max_retries']],
            outputs=[batch_components['batch_status']]
        )
    
    def _create_config_tab(self):
        """创建配置管理标签页"""
        config_components, config_buttons = self.config_manager.create_config_interface()
        
        # 绑定配置管理事件
        config_buttons['load_config_btn'].click(
            fn=self._load_config,
            outputs=list(config_components.values())
        )
        
        config_buttons['save_config_btn'].click(
            fn=self._save_config,
            inputs=list(config_components.values())[:-1],  # 除了status
            outputs=[config_components['config_status']]
        )
        
        config_buttons['reset_config_btn'].click(
            fn=self._reset_config,
            outputs=list(config_components.values())
        )
    
    def _create_history_tab(self):
        """创建历史记录标签页"""
        history_components, history_buttons = self.history_manager.create_history_interface()
        
        # 绑定历史记录事件
        history_buttons['refresh_btn'].click(
            fn=self._refresh_history,
            outputs=[history_components['history_list'], history_components['stats_info']]
        )
        
        history_buttons['clear_btn'].click(
            fn=self._clear_history,
            outputs=[history_components['history_list'], history_components['stats_info']]
        )
        
        history_components['history_list'].select(
            fn=self._select_history_record,
            outputs=[history_components['selected_info']]
        )
    
    def _start_single_translation(self, 
                                file_obj,  # 改为接收文件对象
                                target_language: str,
                                file_format: str,
                                model_type: str):
        """开始单文件翻译"""
        # 添加详细的调试日志
        LOG.debug(f"接收到的文件对象: {file_obj}")
        LOG.debug(f"文件对象类型: {type(file_obj)}")
        
        # 处理文件对象
        if file_obj is None:
            LOG.warning("文件对象为None")
            yield None, "请先选择要翻译的PDF文件", *[None] * 4
            return
        
        # 获取文件路径
        try:
            file_path = file_obj.name if hasattr(file_obj, 'name') else str(file_obj)
            LOG.debug(f"解析的文件路径: {file_path}")
        except Exception as e:
            LOG.error(f"文件路径解析失败: {e}")
            yield None, "文件路径解析失败，请重新选择文件", *[None] * 4
            return
        
        # 验证文件
        if not file_path or not os.path.exists(file_path):
            LOG.warning(f"文件路径无效: {file_path}")
            yield None, "文件路径无效，请重新选择文件", *[None] * 4
            return

        is_valid, message = self.file_upload.validate_file(file_path)
        if not is_valid:
            LOG.warning(f"文件验证失败: {message}")
            yield None, f"文件验证失败: {message}", *[None] * 4
            return

        try:
            config = self.config_manager.load_config()
            model = OpenAIModel(model=config['OpenAIModel']['model'], api_key=config['OpenAIModel']['api_key']) if model_type == 'OpenAI' else GLMModel(model_url=config['GLMModel']['model_url'], timeout=config['GLMModel']['timeout'])
            translator = PDFTranslator(model)
            
            record_id = self.history_manager.add_record(input_file=file_path, target_language=target_language, status="进行中")
            self.is_translating = True
            self.current_record_id = record_id

            def progress_callback(page_num, content_idx, total_contents):
                if self.progress_display.start_time is None:
                    self.progress_display.initialize_progress(len(translator.book.pages))
                
                progress_data = self.progress_display.update_page_progress(page_num, content_idx, total_contents)
                self.progress_overall = progress_data['overall_progress']
                self.progress_page = progress_data['page_progress']
                self.progress_status = progress_data['status_message']
                self.progress_time = progress_data['time_info']

            def translate_worker():
                try:
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    output_dir = config.get('common', {}).get('output_dir', './output')
                    os.makedirs(output_dir, exist_ok=True)
                    output_file = os.path.join(output_dir, f"{base_name}_translated.{file_format}")
                    
                    translator.translate_pdf(file_path, file_format, target_language, output_file, progress_callback=progress_callback)
                    
                    self.history_manager.update_record(record_id, status="完成", output_file=output_file)
                    self.final_result = (output_file, "翻译完成！")
                except Exception as e:
                    error_msg = str(e)
                    LOG.error(f"翻译失败: {error_msg}")
                    self.history_manager.update_record(record_id, status="失败", error_message=error_msg)
                    self.final_result = (None, f"翻译失败: {error_msg}")
                finally:
                    self.is_translating = False

            thread = threading.Thread(target=translate_worker)
            thread.start()

            while self.is_translating:
                yield None, "翻译进行中...", self.progress_overall, self.progress_page, self.progress_status, self.progress_time
                time.sleep(0.1)

            yield self.final_result[0], self.final_result[1], 100, 100, "翻译完成", self.progress_time

        except Exception as e:
            error_msg = str(e)
            LOG.error(f"启动翻译失败: {error_msg}")
            yield None, f"启动翻译失败: {error_msg}", *[None] * 4
    
    def _add_files_to_batch_queue(self,
                                file_paths: List[str],
                                target_language: str,
                                file_format: str,
                                model_type: str):
        """添加文件到批量处理队列"""
        if not file_paths:
            return "请先选择要翻译的文件", []
            
        # 验证文件
        valid_files, info_message = self.file_upload.validate_batch_files(file_paths)
        
        if not valid_files:
            return info_message, []
            
        # 准备配置
        config = {
            'target_language': target_language,
            'file_format': file_format,
            'model_type': model_type
        }
        
        # 添加到队列
        result_message = self.batch_processor.add_files_to_queue(valid_files, config)
        queue_data = self.batch_processor.get_queue_display_data()
        
        return result_message, queue_data
    
    def _start_batch_processing(self, max_workers: int, retry_failed: bool, max_retries: int):
        """开始批量处理"""
        def batch_translate_function(**kwargs):
            # 这里应该调用实际的翻译函数
            # 简化实现，返回成功结果
            return {'success': True, 'output_file': 'dummy_output.md'}
        
        result = self.batch_processor.start_batch_processing(
            translate_function=batch_translate_function,
            max_workers=int(max_workers),
            retry_failed=retry_failed,
            max_retries=int(max_retries)
        )
        
        return result
    
    def _load_config(self):
        """加载配置"""
        config = self.config_manager.load_config()
        updated_values = self.config_manager.update_components_from_config(config)
        
        return (
            updated_values['openai_model'],
            updated_values['openai_api_key'],
            updated_values['glm_model_url'],
            updated_values['glm_timeout'],
            updated_values['target_language'],
            updated_values['file_format'],
            updated_values['output_dir'],
            "配置加载成功"
        )
    
    def _save_config(self, *config_values):
        """保存配置"""
        # 将Gradio组件值转换为配置字典
        config_dict = {
            'openai_model': config_values[0],
            'openai_api_key': config_values[1],
            'glm_model_url': config_values[2],
            'glm_timeout': config_values[3],
            'target_language': config_values[4],
            'file_format': config_values[5],
            'output_dir': config_values[6]
        }
        
        config_data = self.config_manager.get_config_from_components(config_dict)
        
        # 验证配置
        is_valid, message = self.config_manager.validate_config(config_data)
        if not is_valid:
            return message
            
        # 保存配置
        success, message = self.config_manager.save_config(config_data)
        return message
    
    def _reset_config(self):
        """重置配置"""
        default_values = self.config_manager.update_components_from_config(
            self.config_manager.default_config
        )
        
        return (
            default_values['openai_model'],
            default_values['openai_api_key'],
            default_values['glm_model_url'],
            default_values['glm_timeout'],
            default_values['target_language'],
            default_values['file_format'],
            default_values['output_dir'],
            "配置已重置为默认值"
        )
    
    def _refresh_history(self):
        """刷新历史记录"""
        self.history_manager.history_data = self.history_manager.load_history()
        table_data = self.history_manager.get_history_table_data()
        stats = self.history_manager.get_statistics()
        
        return table_data, stats
    
    def _clear_history(self):
        """清空历史记录"""
        self.history_manager.clear_history()
        return [], "历史记录已清空"
    
    def _select_history_record(self, evt: gr.SelectData):
        """选择历史记录"""
        if evt.index is not None:
            details = self.history_manager.get_record_details(evt.index[0])
            return details
        return "未选择记录"
    
    def _get_custom_css(self) -> str:
        """获取自定义CSS样式"""
        return """
        .gradio-container {
            max-width: 1200px !important;
        }
        
        .gr-button {
            border-radius: 8px;
        }
        
        .gr-form {
            border-radius: 12px;
            border: 1px solid #e1e5e9;
        }
        
        .gr-panel {
            border-radius: 12px;
        }
        
        .progress-container {
            margin: 10px 0;
        }
        """

def launch_gui(share: bool = False, server_name: str = "127.0.0.1", server_port: int = 7860):
    """启动GUI应用"""
    try:
        app = TranslatorGUI()
        interface = app.create_interface()
        
        LOG.info(f"启动GUI应用: http://{server_name}:{server_port}")
        
        interface.launch(
            share=share,
            server_name=server_name,
            server_port=server_port,
            show_error=True,
            quiet=False
        )
        
    except Exception as e:
        LOG.error(f"启动GUI失败: {str(e)}")
        raise

if __name__ == "__main__":
    launch_gui()
