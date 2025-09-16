import gradio as gr
import time
from typing import Dict, Any, Generator

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
            
            overall_progress = gr.Slider(
                minimum=0, maximum=100, value=0, interactive=False, label="总体进度 (%)"
            )
            page_progress = gr.Slider(
                minimum=0, maximum=100, value=0, interactive=False, label="页面进度 (%)"
            )
            status_info = gr.Textbox(
                label="状态信息", interactive=False, lines=4
            )
            time_info = gr.Textbox(
                label="时间信息", interactive=False, lines=2
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
        page_progress_val = (content_idx + 1) / total_contents if total_contents > 0 else 0
        overall_progress_val = (page_num + page_progress_val) / self.total_pages if self.total_pages > 0 else 0
        
        self.current_progress = overall_progress_val
        self.status_message = f"正在翻译第 {page_num + 1}/{self.total_pages} 页，内容块 {content_idx + 1}/{total_contents}"
        
        return self.get_progress_info()
    
    def update_completion_status(self, success: bool, message: str = ""):
        """更新完成状态"""
        self.current_progress = 1.0
        self.status_message = f"翻译完成！{message}" if success else f"翻译失败：{message}"
        return self.get_progress_info()
    
    def get_progress_info(self) -> Dict[str, Any]:
        """获取当前进度信息"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        remaining_time = (elapsed_time / self.current_progress - elapsed_time) if self.current_progress > 0 else 0
        
        return {
            'overall_progress': self.current_progress * 100,
            'page_progress': ((self.current_page + 1) / self.total_pages * 100) if self.total_pages > 0 else 0,
            'status_message': self.status_message,
            'time_info': self.format_time_info(elapsed_time, remaining_time)
        }
    
    def format_time_info(self, elapsed: float, remaining: float) -> str:
        """格式化时间信息"""
        def format_seconds(seconds):
            if seconds < 60: return f"{seconds:.0f}秒"
            if seconds < 3600: return f"{seconds//60:.0f}分{seconds%60:.0f}秒"
            return f"{seconds//3600:.0f}小时{(seconds%3600)//60:.0f}分"
        
        return f"已用时间: {format_seconds(elapsed)}\n预计剩余: {format_seconds(remaining) if remaining > 0 else '计算中...'}"

    def create_progress_callback(self, progress_components) -> Generator[tuple, None, None]:
        """创建进度回调生成器"""
        overall_progress, page_progress, status_info, time_info = progress_components
        
        def update_generator():
            while self.current_progress < 1.0:
                progress_data = self.get_progress_info()
                yield (
                    progress_data['overall_progress'],
                    progress_data['page_progress'], 
                    progress_data['status_message'],
                    progress_data['time_info']
                )
                time.sleep(0.5)
        return update_generator
