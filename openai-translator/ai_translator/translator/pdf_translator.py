from typing import Optional, Callable
try:
    from ..model import Model
except ImportError:  # pragma: no cover - fallback for direct execution
    from model import Model
try:
    from ..book import ContentType, Content
except ImportError:  # pragma: no cover - fallback for direct execution
    from book import ContentType, Content
try:
    from .pdf_parser import PDFParser
except ImportError:  # pragma: no cover - fallback for direct execution
    from pdf_parser import PDFParser
try:
    from .writer import Writer
except ImportError:  # pragma: no cover - fallback for direct execution
    from writer import Writer
try:
    from ..utils import LOG
except ImportError:  # pragma: no cover - fallback for direct execution
    from utils import LOG

class PDFTranslator:
    def __init__(self, model: Model):
        self.model = model
        self.pdf_parser = PDFParser()
        self.writer = Writer()

    def translate_pdf(self, pdf_file_path: str, file_format: str = 'PDF', target_language: str = '中文', output_file_path: str = None, pages: Optional[int] = None, progress_callback: Optional[Callable] = None):
        self.book = self.pdf_parser.parse_pdf(pdf_file_path, pages)

        for page_idx, page in enumerate(self.book.pages):
            for content_idx, content in enumerate(page.contents):
                if progress_callback:
                    progress_callback(page_idx, content_idx, len(page.contents))
                
                if content.content_type == ContentType.IMAGE:
                    # 处理图片内容：翻译图片描述
                    if hasattr(content, 'description') and content.description:
                        # 为图片描述创建翻译提示
                        description_content = Content(content_type=ContentType.TEXT, original=content.description)
                        prompt = self.model.translate_prompt(description_content, target_language)
                        LOG.debug(f"图片描述翻译提示: {prompt}")
                        translation, status = self.model.make_request(prompt)
                        LOG.info(f"图片描述翻译结果: {translation}")
                        
                        # 设置图片描述的翻译
                        self.book.pages[page_idx].contents[content_idx].set_translation(translation, status)
                    else:
                        # 如果没有描述，生成一个通用的翻译描述
                        if target_language.lower() in ['中文', 'chinese', '中']:
                            default_translation = f"第{page_idx + 1}页的图片内容"
                        else:
                            default_translation = f"Image content on page {page_idx + 1}"
                        
                        self.book.pages[page_idx].contents[content_idx].set_translation(default_translation, True)
                        LOG.info(f"图片使用默认描述: {default_translation}")
                else:
                    # 处理文本和表格内容
                    prompt = self.model.translate_prompt(content, target_language)
                    LOG.debug(prompt)
                    translation, status = self.model.make_request(prompt)
                    LOG.info(translation)
                    
                    # Update the content in self.book.pages directly
                    self.book.pages[page_idx].contents[content_idx].set_translation(translation, status)

        self.writer.save_translated_book(self.book, output_file_path, file_format)
