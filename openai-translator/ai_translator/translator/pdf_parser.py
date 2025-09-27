import pdfplumber
import io
from PIL import Image as PILImage
from typing import Optional, List, Tuple
try:
    from ..book import Book, Page, Content, ContentType, TableContent, ImageContent
except ImportError:  # pragma: no cover - fallback for direct execution
    from book import Book, Page, Content, ContentType, TableContent, ImageContent
try:
    from .exceptions import PageOutOfRangeException
except ImportError:  # pragma: no cover - fallback for direct execution
    from exceptions import PageOutOfRangeException
try:
    from ..utils import LOG
except ImportError:  # pragma: no cover - fallback for direct execution
    from utils import LOG


class PDFParser:
    def __init__(self):
        pass
    
    def _extract_images_from_page(self, pdf_page) -> List[Tuple[PILImage.Image, Tuple[float, float, float, float]]]:
        """
        从PDF页面提取图片及其位置信息
        Returns: List of (PIL_Image, bbox) tuples
        """
        images_with_positions = []
        
        try:
            # 获取页面中的图片对象
            for obj in pdf_page.objects.get('image', []):
                try:
                    # 获取图片的位置信息
                    bbox = (obj['x0'], obj['y0'], obj['x1'], obj['y1'])
                    
                    # 尝试提取图片数据
                    if 'stream' in obj and obj['stream']:
                        # 从stream中提取图片
                        image_data = obj['stream'].get_data()
                        if image_data:
                            try:
                                image = PILImage.open(io.BytesIO(image_data))
                                images_with_positions.append((image, bbox))
                                LOG.debug(f"提取图片成功，位置: {bbox}")
                            except Exception as e:
                                LOG.warning(f"图片解析失败: {e}")
                
                except Exception as e:
                    LOG.warning(f"图片提取失败: {e}")
                    continue
                    
        except Exception as e:
            LOG.warning(f"页面图片提取失败: {e}")
        
        return images_with_positions
    
    def _sort_elements_by_position(self, elements: List[Tuple[any, Tuple[float, float, float, float]]]) -> List[any]:
        """
        根据位置信息对页面元素进行排序
        Args:
            elements: List of (content, bbox) tuples
        Returns:
            Sorted list of content objects
        """
        def get_sort_key(element):
            content, bbox = element
            # 按照从上到下，从左到右的顺序排序
            y_top = bbox[3] if len(bbox) >= 4 else 0  # y1 (top)
            x_left = bbox[0] if len(bbox) >= 1 else 0  # x0 (left)
            return (-y_top, x_left)  # 负号因为PDF坐标系y轴向上
        
        try:
            sorted_elements = sorted(elements, key=get_sort_key)
            return [content for content, bbox in sorted_elements]
        except Exception as e:
            LOG.warning(f"元素排序失败: {e}")
            return [content for content, bbox in elements]

    def parse_pdf(self, pdf_file_path: str, pages: Optional[int] = None) -> Book:
        book = Book(pdf_file_path)

        with pdfplumber.open(pdf_file_path) as pdf:
            if pages is not None and pages > len(pdf.pages):
                raise PageOutOfRangeException(len(pdf.pages), pages)

            if pages is None:
                pages_to_parse = pdf.pages
            else:
                pages_to_parse = pdf.pages[:pages]

            for page_num, pdf_page in enumerate(pages_to_parse):
                page = Page()
                
                LOG.info(f"正在解析第 {page_num + 1} 页...")
                
                # 收集所有页面元素及其位置信息
                all_elements = []
                
                # 1. 提取图片
                images_with_positions = self._extract_images_from_page(pdf_page)
                for image, bbox in images_with_positions:
                    image_content = ImageContent(
                        image_data=image,
                        bbox=bbox,
                        description=f"第{page_num + 1}页图片"
                    )
                    all_elements.append((image_content, bbox))
                    LOG.debug(f"[image] 位置: {bbox}")
                
                # 2. 提取表格及位置
                tables = pdf_page.extract_tables()
                table_bboxes = []
                
                # 获取表格区域的位置信息（简化处理）
                if tables:
                    # 简化：为每个表格分配一个大致的位置
                    page_height = pdf_page.height
                    for i, table_data in enumerate(tables):
                        # 估算表格位置（这里简化处理，实际项目中可以更精确）
                        estimated_bbox = (0, page_height - (i + 1) * 100, pdf_page.width, page_height - i * 100)
                        table_bboxes.append(estimated_bbox)
                        
                        table_content = TableContent(table_data)
                        all_elements.append((table_content, estimated_bbox))
                        LOG.debug(f"[table] 位置: {estimated_bbox}")
                
                # 3. 处理文本内容
                raw_text = pdf_page.extract_text()
                
                # 从原始文本中移除表格内容
                for table_data in tables:
                    for row in table_data:
                        for cell in row:
                            if cell:
                                raw_text = raw_text.replace(str(cell), "", 1)
                
                if raw_text:
                    # 清理文本
                    raw_text_lines = raw_text.splitlines()
                    cleaned_raw_text_lines = [line.strip() for line in raw_text_lines if line.strip()]
                    cleaned_raw_text = "\n".join(cleaned_raw_text_lines)
                    
                    if cleaned_raw_text:
                        # 文本位置（简化：假设文本占据页面主要区域）
                        text_bbox = (0, 0, pdf_page.width, pdf_page.height)
                        text_content = Content(content_type=ContentType.TEXT, original=cleaned_raw_text)
                        all_elements.append((text_content, text_bbox))
                        LOG.debug(f"[text] 内容长度: {len(cleaned_raw_text)}")

                # 4. 按位置排序所有元素
                if all_elements:
                    sorted_contents = self._sort_elements_by_position(all_elements)
                    for content in sorted_contents:
                        page.add_content(content)
                else:
                    LOG.warning(f"第 {page_num + 1} 页未发现任何内容")

                book.add_page(page)
                LOG.info(f"第 {page_num + 1} 页解析完成，包含 {len(page.contents)} 个元素")

        return book
