import pandas as pd
from enum import Enum, auto
from PIL import Image as PILImage
from utils import LOG

class ContentType(Enum):
    TEXT = auto()
    TABLE = auto()
    IMAGE = auto()

class Content:
    def __init__(self, content_type, original, translation=None):
        self.content_type = content_type
        self.original = original
        self.translation = translation
        self.status = False

    def set_translation(self, translation, status):
        if not self.check_translation_type(translation):
            raise ValueError(f"Invalid translation type. Expected {self.content_type}, but got {type(translation)}")
        self.translation = translation
        self.status = status

    def check_translation_type(self, translation):
        if self.content_type == ContentType.TEXT and isinstance(translation, str):
            return True
        elif self.content_type == ContentType.TABLE and isinstance(translation, list):
            return True
        elif self.content_type == ContentType.IMAGE and isinstance(translation, PILImage.Image):
            return True
        return False


class TableContent(Content):
    def __init__(self, data, translation=None):
        df = pd.DataFrame(data)

        # Verify if the number of rows and columns in the data and DataFrame object match
        if len(data) != len(df) or len(data[0]) != len(df.columns):
            raise ValueError("The number of rows and columns in the extracted table data and DataFrame object do not match.")
        
        super().__init__(ContentType.TABLE, df)

    def set_translation(self, translation, status):
        try:
            if not isinstance(translation, str):
                raise ValueError(f"Invalid translation type. Expected str, but got {type(translation)}")
            
            # 使用更智能的解析方式
            lines = translation.strip().split('\n')
            table_data = []
            
            for line in lines:
                # 使用 | 作为分隔符，或者尝试其他分隔符
                if '|' in line:
                    row = [cell.strip() for cell in line.split('|')]
                elif '\t' in line:
                    row = [cell.strip() for cell in line.split('\t')]
                else:
                    # 回退到原始方法，但保留完整性
                    row = [line.strip()]
                
                if row and any(cell for cell in row):  # 过滤空行
                    table_data.append(row)
            
            # 确保所有行有相同的列数
            if table_data:
                max_cols = max(len(row) for row in table_data)
                for row in table_data:
                    while len(row) < max_cols:
                        row.append('')
            
            # 创建DataFrame
            if len(table_data) > 1:
                translated_df = pd.DataFrame(table_data[1:], columns=table_data[0])
            else:
                translated_df = pd.DataFrame(table_data)
                
            self.translation = translated_df
            self.status = status
        except Exception as e:
            LOG.error(f"Table translation failed: {e}")
            # 保留原始内容作为降级方案
            self.translation = self.original
            self.status = False
    def get_original_as_str(self):
        # 使用更清晰的表格格式
        return self.original.to_csv(sep='|', index=False)

    def __str__(self):
        return self.original.to_string(header=False, index=False)

    def iter_items(self, translated=False):
        target_df = self.translation if translated else self.original
        for row_idx, row in target_df.iterrows():
            for col_idx, item in enumerate(row):
                yield (row_idx, col_idx, item)

    def update_item(self, row_idx, col_idx, new_value, translated=False):
        target_df = self.translation if translated else self.original
        target_df.at[row_idx, col_idx] = new_value

    def get_original_as_str(self):
        return self.original.to_string(header=False, index=False)
