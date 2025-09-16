import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import ArgumentParser, ConfigLoader, LOG
from model import GLMModel, OpenAIModel
from translator import PDFTranslator

def main_cli():
    """命令行模式主函数"""
    argument_parser = ArgumentParser()
    args = argument_parser.parse_arguments()
    config_loader = ConfigLoader(args.config)

    config = config_loader.load_config()

    # 根据模型类型选择模型
    if args.model_type == 'OpenAIModel':
        model_name = args.openai_model if args.openai_model else config['OpenAIModel']['model']
        api_key = args.openai_api_key if args.openai_api_key else config['OpenAIModel']['api_key']
        model = OpenAIModel(model=model_name, api_key=api_key)
    elif args.model_type == 'GLMModel':
        model_url = args.glm_model_url if args.glm_model_url else config['GLMModel']['model_url']
        timeout = args.timeout if args.timeout else config['GLMModel']['timeout']
        model = GLMModel(model_url=model_url, timeout=timeout)
    else:
        # 默认使用OpenAI模型
        model_name = args.openai_model if args.openai_model else config['OpenAIModel']['model']
        api_key = args.openai_api_key if args.openai_api_key else config['OpenAIModel']['api_key']
        model = OpenAIModel(model=model_name, api_key=api_key)

    pdf_file_path = args.book if args.book else config['common']['book']
    file_format = args.file_format if args.file_format else config['common']['file_format']

    # 实例化 PDFTranslator 类，并调用 translate_pdf() 方法
    translator = PDFTranslator(model)
    translator.translate_pdf(pdf_file_path, file_format)

def main_gui():
    """GUI模式主函数"""
    try:
        from gui_app import launch_gui
        LOG.info("启动GUI模式...")
        launch_gui()
    except ImportError as e:
        LOG.error(f"GUI模式启动失败，缺少依赖: {e}")
        LOG.info("请安装gradio: pip install gradio")
        sys.exit(1)
    except Exception as e:
        LOG.error(f"GUI模式启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 检查是否有GUI参数
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        main_gui()
    else:
        main_cli()
