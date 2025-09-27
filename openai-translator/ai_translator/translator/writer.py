import os
import base64
from reportlab.lib import colors, pagesizes, units
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage
import io

try:
    from ..book import Book, ContentType
except ImportError:  # pragma: no cover - fallback for direct execution
    from book import Book, ContentType
try:
    from ..utils import LOG
except ImportError:  # pragma: no cover - fallback for direct execution
    from utils import LOG

class Writer:
    def __init__(self):
        pass

    def save_translated_book(self, book: Book, output_file_path: str = None, file_format: str = "PDF"):
        if file_format.lower() == "pdf":
            self._save_translated_book_pdf(book, output_file_path)
        elif file_format.lower() == "markdown":
            self._save_translated_book_markdown(book, output_file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def _save_translated_book_pdf(self, book: Book, output_file_path: str = None):
        if output_file_path is None:
            output_file_path = book.pdf_file_path.replace('.pdf', f'_translated.pdf')

        LOG.info(f"pdf_file_path: {book.pdf_file_path}")
        LOG.info(f"开始翻译: {output_file_path}")

        # Register Chinese font
        font_path = "../fonts/simsun.ttc"  # 请将此路径替换为您的字体文件路径
        pdfmetrics.registerFont(TTFont("SimSun", font_path))

        # Create a new ParagraphStyle with the SimSun font
        simsun_style = ParagraphStyle('SimSun', fontName='SimSun', fontSize=12, leading=14)

        # Create a PDF document
        doc = SimpleDocTemplate(output_file_path, pagesize=pagesizes.letter)
        styles = getSampleStyleSheet()
        story = []

        # Iterate over the pages and contents
        for page in book.pages:
            for content in page.contents:
                if content.status:
                    if content.content_type == ContentType.TEXT:
                        # Add translated text to the PDF
                        text = content.translation
                        para = Paragraph(text, simsun_style)
                        story.append(para)

                    elif content.content_type == ContentType.TABLE:
                        # Add table to the PDF
                        table = content.translation
                        table_style = TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'SimSun'),  # 更改表头字体为 "SimSun"
                            ('FONTSIZE', (0, 0), (-1, 0), 14),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('FONTNAME', (0, 1), (-1, -1), 'SimSun'),  # 更改表格中的字体为 "SimSun"
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ])
                        pdf_table = Table(table.values.tolist())
                        pdf_table.setStyle(table_style)
                        story.append(pdf_table)
                        
                    elif content.content_type == ContentType.IMAGE:
                        # Add image to the PDF
                        try:
                            # 获取图片数据
                            image_data = content.original
                            if isinstance(image_data, PILImage.Image):
                                # 将PIL图片转换为BytesIO
                                img_buffer = io.BytesIO()
                                # 确保图片格式兼容
                                if image_data.mode in ('RGBA', 'LA', 'P'):
                                    image_data = image_data.convert('RGB')
                                image_data.save(img_buffer, format='JPEG')
                                img_buffer.seek(0)
                                
                                # 创建ReportLab图片对象
                                reportlab_image = Image(ImageReader(img_buffer))
                                
                                # 设置图片大小（保持比例，限制最大宽度）
                                max_width = 400
                                img_width, img_height = image_data.size
                                if img_width > max_width:
                                    ratio = max_width / img_width
                                    reportlab_image.drawWidth = max_width
                                    reportlab_image.drawHeight = img_height * ratio
                                else:
                                    reportlab_image.drawWidth = img_width
                                    reportlab_image.drawHeight = img_height
                                
                                story.append(reportlab_image)
                                
                                # 添加图片描述（如果有翻译）
                                if content.translation:
                                    desc_para = Paragraph(f"<i>{content.translation}</i>", simsun_style)
                                    story.append(desc_para)
                                    
                                LOG.debug(f"添加图片到PDF: {reportlab_image.drawWidth}x{reportlab_image.drawHeight}")
                                
                        except Exception as e:
                            LOG.warning(f"图片添加到PDF失败: {e}")
                            # 添加占位文本
                            if hasattr(content, 'description'):
                                placeholder = Paragraph(f"[图片: {content.description}]", simsun_style)
                            else:
                                placeholder = Paragraph("[图片内容]", simsun_style)
                            story.append(placeholder)
            # Add a page break after each page except the last one
            if page != book.pages[-1]:
                story.append(PageBreak())

        # Save the translated book as a new PDF file
        doc.build(story)
        LOG.info(f"翻译完成: {output_file_path}")

    def _save_translated_book_markdown(self, book: Book, output_file_path: str = None):
        if output_file_path is None:
            output_file_path = book.pdf_file_path.replace('.pdf', f'_translated.md')

        LOG.info(f"pdf_file_path: {book.pdf_file_path}")
        LOG.info(f"开始翻译: {output_file_path}")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            # Iterate over the pages and contents
            for page in book.pages:
                for content in page.contents:
                    if content.status:
                        if content.content_type == ContentType.TEXT:
                            # Add translated text to the Markdown file
                            text = content.translation
                            output_file.write(text + '\n\n')

                        elif content.content_type == ContentType.TABLE:
                            # Add table to the Markdown file
                            table = content.translation
                            header = '| ' + ' | '.join(str(column) for column in table.columns) + ' |' + '\n'
                            separator = '| ' + ' | '.join(['---'] * len(table.columns)) + ' |' + '\n'
                            # body = '\n'.join(['| ' + ' | '.join(row) + ' |' for row in table.values.tolist()]) + '\n\n'
                            body = '\n'.join(['| ' + ' | '.join(str(cell) for cell in row) + ' |' for row in table.values.tolist()]) + '\n\n'
                            output_file.write(header + separator + body)
                            
                        elif content.content_type == ContentType.IMAGE:
                            # Add image to the Markdown file
                            try:
                                # 保存图片到文件
                                image_data = content.original
                                if isinstance(image_data, PILImage.Image):
                                    # 生成图片文件名
                                    base_name = os.path.splitext(os.path.basename(output_file_path))[0]
                                    image_dir = os.path.join(os.path.dirname(output_file_path), f"{base_name}_images")
                                    os.makedirs(image_dir, exist_ok=True)
                                    
                                    # 使用内容的位置信息生成唯一文件名
                                    if hasattr(content, 'bbox') and content.bbox:
                                        bbox_str = f"_{int(content.bbox[0])}_{int(content.bbox[1])}"
                                    else:
                                        bbox_str = f"_{len(os.listdir(image_dir)) + 1}"
                                    
                                    image_filename = f"image{bbox_str}.jpg"
                                    image_path = os.path.join(image_dir, image_filename)
                                    
                                    # 确保图片格式兼容
                                    if image_data.mode in ('RGBA', 'LA', 'P'):
                                        image_data = image_data.convert('RGB')
                                    
                                    image_data.save(image_path, 'JPEG')
                                    
                                    # 生成相对路径用于Markdown
                                    relative_image_path = os.path.join(f"{base_name}_images", image_filename)
                                    
                                    # 写入Markdown图片语法
                                    if content.translation:
                                        # 使用翻译后的描述
                                        output_file.write(f"![{content.translation}]({relative_image_path})\n\n")
                                        output_file.write(f"*{content.translation}*\n\n")
                                    else:
                                        # 使用默认描述
                                        description = getattr(content, 'description', '图片')
                                        output_file.write(f"![{description}]({relative_image_path})\n\n")
                                    
                                    LOG.debug(f"图片已保存: {image_path}")
                                    
                            except Exception as e:
                                LOG.warning(f"图片保存失败: {e}")
                                # 添加占位文本
                                description = getattr(content, 'description', '图片内容')
                                if content.translation:
                                    output_file.write(f"**[图片: {content.translation}]**\n\n")
                                else:
                                    output_file.write(f"**[图片: {description}]**\n\n")

                # Add a page break (horizontal rule) after each page except the last one
                if page != book.pages[-1]:
                    output_file.write('---\n\n')

        LOG.info(f"翻译完成: {output_file_path}")