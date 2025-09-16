import gradio as gr
import os
from typing import List, Optional

class FileUploadComponent:
    """文件上传组件 - 支持拖拽和批量上传"""
    
    def __init__(self):
        self.supported_formats = [".pdf"]
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def create_upload_interface(self):
        """创建文件上传界面"""
        with gr.Column():
            gr.Markdown("### 📁 文件上传")
            
            # 单文件上传
            single_file = gr.File(
                label="选择PDF文件",
                file_types=[".pdf"],
                file_count="single"
            )
            
            # 批量文件上传
            batch_files = gr.File(
                label="批量上传PDF文件",
                file_types=[".pdf"],
                file_count="multiple"
            )
            
            # 文件信息显示
            file_info = gr.Textbox(
                label="文件信息",
                interactive=False,
                lines=3
            )
            
        return single_file, batch_files, file_info
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """验证上传的文件"""
        if not file_path:
            return False, "未选择文件"
            
        if not os.path.exists(file_path):
            return False, "文件不存在"
            
        # 检查文件扩展名
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.supported_formats:
            return False, f"不支持的文件格式: {ext}"
            
        # 检查文件大小
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            return False, f"文件过大: {file_size / (1024*1024):.1f}MB (最大50MB)"
            
        return True, f"文件验证通过: {os.path.basename(file_path)} ({file_size / (1024*1024):.1f}MB)"
    
    def validate_batch_files(self, file_paths: List[str]) -> tuple[List[str], str]:
        """验证批量上传的文件"""
        if not file_paths:
            return [], "未选择文件"
            
        valid_files = []
        info_messages = []
        
        for file_path in file_paths:
            is_valid, message = self.validate_file(file_path)
            if is_valid:
                valid_files.append(file_path)
                info_messages.append(f"✅ {message}")
            else:
                info_messages.append(f"❌ {os.path.basename(file_path)}: {message}")
        
        info_text = "\n".join(info_messages)
        if valid_files:
            info_text += f"\n\n共选择 {len(valid_files)} 个有效文件"
        
        return valid_files, info_text
    
    def get_file_info(self, file_path: Optional[str]) -> str:
        """获取文件信息"""
        if not file_path:
            return "未选择文件"
            
        is_valid, message = self.validate_file(file_path)
        return message