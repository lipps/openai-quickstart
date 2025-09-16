import gradio as gr
import time
from typing import Dict, Any, Optional

class ProgressDisplayComponent:
    """实时翻译进度显示组件"""
    
    def __init__(self):
        self.current_progress = 0
        self.total_pages = 0
        self.current_page = 0
        self.status_message = ""
        self.start_time = None
        
    def create_progress_interface(self):
        """创建进度显示界面"""
        with gr.Column():
            gr.Markdown("### 📊 翻译进度")
            
            # 总体进度
            gr.Markdown("**总体进度:**")
            overall_progress = gr.Slider(
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                label="总体进度 (%)"
            )
            
            # 页面进度
            gr.Markdown("**当前页面进度:**")
            page_progress = gr.Slider(
                minimum=0,
                maximum=100,
                value=0,
                interactive=False,
                label="页面进度 (%)"
            )
            
            # 状态信息
            status_info = gr.Textbox(
                label="状态信息",
                interactive=False,
                lines=4
            )
            
            # 时间信息
            time_info = gr.Textbox(
                label="时间信息",
                interactive=False,
                lines=2
            )
            
        return overall_progress, page_progress, status_info, time_info
    
    def initialize_progress(self, total_pages: int):
        """初始化进度信息"""
        self.total_pages = total_pages
        self.current_page = 0
        self.current_progress = 0
        self.start_time = time.time()
        self.status_message = f"开始翻译，共 {total_pages} 页"
        
    def update_page_progress(self, page_num: int, content_idx: int, total_contents: int):
        """更新页面进度"""
        self.current_page = page_num
        page_progress = (content_idx + 1) / total_contents if total_contents > 0 else 0
        overall_progress = (page_num + page_progress) / self.total_pages if self.total_pages > 0 else 0
        
        self.current_progress = overall_progress
        self.status_message = f"正在翻译第 {page_num + 1}/{self.total_pages} 页，内容块 {content_idx + 1}/{total_contents}"
        
        return self.get_progress_info()
    
    def update_completion_status(self, success: bool, message: str = ""):
        """更新完成状态"""
        if success:
            self.current_progress = 1.0
            self.status_message = f"翻译完成！{message}"
        else:
            self.status_message = f"翻译失败：{message}"
            
        return self.get_progress_info()
    
    def get_progress_info(self) -> Dict[str, Any]:
        """获取当前进度信息"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        # 计算预估剩余时间
        if self.current_progress > 0:
            estimated_total_time = elapsed_time / self.current_progress
            remaining_time = estimated_total_time - elapsed_time
        else:
            remaining_time = 0
            
        time_info = self.format_time_info(elapsed_time, remaining_time)
        
        return {
            'overall_progress': self.current_progress * 100,  # 转换为百分比
            'page_progress': ((self.current_page + 1) / self.total_pages * 100) if self.total_pages > 0 else 0,
            'status_message': self.status_message,
            'time_info': time_info
        }
    
    def format_time_info(self, elapsed: float, remaining: float) -> str:
        """格式化时间信息"""
        def format_seconds(seconds):
            if seconds < 60:
                return f"{seconds:.0f}秒"
            elif seconds < 3600:
                return f"{seconds//60:.0f}分{seconds%60:.0f}秒"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                return f"{hours:.0f}小时{minutes:.0f}分"
        
        elapsed_str = format_seconds(elapsed)
        remaining_str = format_seconds(remaining) if remaining > 0 else "计算中..."
        
        return f"已用时间: {elapsed_str}\n预计剩余: {remaining_str}"
    
    def create_progress_callback(self, progress_components):
        """创建进度回调函数"""
        overall_progress, page_progress, status_info, time_info = progress_components
        
        def update_callback(page_num: int, content_idx: int, total_contents: int):
            progress_data = self.update_page_progress(page_num, content_idx, total_contents)
            
            # 返回更新值而不是直接更新组件
            return (
                progress_data['overall_progress'],
                progress_data['page_progress'], 
                progress_data['status_message'],
                progress_data['time_info']
            )
            
        return update_callback