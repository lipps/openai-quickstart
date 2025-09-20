from typing import Optional, Callable
try:
    from ..model import Model
except ImportError:  # pragma: no cover - fallback for direct execution
    from model import Model
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
                
                prompt = self.model.translate_prompt(content, target_language)
                LOG.debug(prompt)
                translation, status = self.model.make_request(prompt)
                LOG.info(translation)
                
                # Update the content in self.book.pages directly
                self.book.pages[page_idx].contents[content_idx].set_translation(translation, status)

        self.writer.save_translated_book(self.book, output_file_path, file_format)
