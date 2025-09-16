import gradio as gr
import os
import threading
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import time

class BatchProcessorComponent:
    """批量处理组件"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.processing_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.is_processing = False
        self.current_batch = []
        self.batch_results = {}
        
    def create_batch_interface(self):
        """创建批量处理界面"""
        with gr.Column():
            gr.Markdown("### 🔄 批量处理")
            
            with gr.Row():
                with gr.Column(scale=2):
                    # 批量设置
                    batch_settings = gr.Column()
                    with batch_settings:
                        gr.Markdown("#### 批量设置")
                        
                        max_workers = gr.Slider(
                            minimum=1,
                            maximum=5,
                            value=3,
                            step=1,
                            label="并发数量",
                            info="同时处理的文件数量"
                        )
                        
                        retry_failed = gr.Checkbox(
                            label="自动重试失败的文件",
                            value=True
                        )
                        
                        max_retries = gr.Number(
                            label="最大重试次数",
                            value=2,
                            minimum=0,
                            maximum=5
                        )
                        
                with gr.Column(scale=3):
                    # 批量队列显示
                    queue_display = gr.Dataframe(
                        headers=["文件名", "状态", "进度", "开始时间", "预计完成"],
                        datatype=["str", "str", "str", "str", "str"],
                        interactive=False,
                        label="处理队列",
                        row_count=8
                    )
                    
            with gr.Row():
                start_batch_btn = gr.Button("▶️ 开始批量处理", variant="primary")
                pause_batch_btn = gr.Button("⏸️ 暂停处理", variant="secondary")
                stop_batch_btn = gr.Button("⏹️ 停止处理", variant="secondary")
                clear_queue_btn = gr.Button("🗑️ 清空队列", variant="secondary")
                
            # 批量处理状态
            batch_status = gr.Textbox(
                label="批量处理状态",
                interactive=False,
                lines=4
            )
            
            # 批量结果摘要
            batch_summary = gr.Textbox(
                label="处理摘要",
                interactive=False,
                lines=3
            )
            
        components = {
            'max_workers': max_workers,
            'retry_failed': retry_failed,
            'max_retries': max_retries,
            'queue_display': queue_display,
            'batch_status': batch_status,
            'batch_summary': batch_summary
        }
        
        buttons = {
            'start_batch_btn': start_batch_btn,
            'pause_batch_btn': pause_batch_btn,
            'stop_batch_btn': stop_batch_btn,
            'clear_queue_btn': clear_queue_btn
        }
        
        return components, buttons
    
    def add_files_to_queue(self, file_paths: List[str], config: Dict[str, Any]) -> str:
        """添加文件到处理队列"""
        added_count = 0
        
        for file_path in file_paths:
            if os.path.exists(file_path) and file_path.endswith('.pdf'):
                task = {
                    'id': f"task_{int(time.time() * 1000)}_{added_count}",
                    'file_path': file_path,
                    'filename': os.path.basename(file_path),
                    'config': config.copy(),
                    'status': '等待中',
                    'progress': 0,
                    'start_time': None,
                    'estimated_completion': None,
                    'retry_count': 0,
                    'error_message': None
                }
                
                self.processing_queue.put(task)
                self.current_batch.append(task)
                added_count += 1
                
        return f"已添加 {added_count} 个文件到处理队列"
    
    def start_batch_processing(self, 
                             translate_function: Callable,
                             max_workers: int = 3,
                             retry_failed: bool = True,
                             max_retries: int = 2) -> str:
        """开始批量处理"""
        if self.is_processing:
            return "批量处理正在进行中"
            
        if self.processing_queue.empty():
            return "处理队列为空，请先添加文件"
            
        self.is_processing = True
        self.max_workers = max_workers
        
        # 启动批量处理线程
        processing_thread = threading.Thread(
            target=self._batch_process_worker,
            args=(translate_function, retry_failed, max_retries)
        )
        processing_thread.daemon = True
        processing_thread.start()
        
        return f"开始批量处理，并发数: {max_workers}"
    
    def _batch_process_worker(self, 
                            translate_function: Callable,
                            retry_failed: bool,
                            max_retries: int):
        """批量处理工作线程"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            
            while not self.processing_queue.empty() or futures:
                # 提交新任务
                while len(futures) < self.max_workers and not self.processing_queue.empty():
                    try:
                        task = self.processing_queue.get_nowait()
                        task['status'] = '处理中'
                        task['start_time'] = time.time()
                        
                        future = executor.submit(self._process_single_file, task, translate_function)
                        futures[future] = task
                    except queue.Empty:
                        break
                
                # 检查完成的任务
                completed_futures = []
                for future in as_completed(futures, timeout=1):
                    completed_futures.append(future)
                    
                for future in completed_futures:
                    task = futures.pop(future)
                    
                    try:
                        result = future.result()
                        if result['success']:
                            task['status'] = '完成'
                            task['progress'] = 100
                        else:
                            task['status'] = '失败'
                            task['error_message'] = result.get('error', '未知错误')
                            
                            # 重试逻辑
                            if retry_failed and task['retry_count'] < max_retries:
                                task['retry_count'] += 1
                                task['status'] = '重试中'
                                self.processing_queue.put(task)
                                
                    except Exception as e:
                        task['status'] = '异常'
                        task['error_message'] = str(e)
                        
                    self.batch_results[task['id']] = task
                    
        self.is_processing = False
    
    def _process_single_file(self, task: Dict[str, Any], translate_function: Callable) -> Dict[str, Any]:
        """处理单个文件"""
        try:
            file_path = task['file_path']
            config = task['config']
            
            # 调用翻译函数
            result = translate_function(
                pdf_file_path=file_path,
                target_language=config.get('target_language', '中文'),
                file_format=config.get('file_format', 'markdown'),
                progress_callback=lambda p: self._update_task_progress(task['id'], p)
            )
            
            return {
                'success': True,
                'result': result,
                'output_file': result.get('output_file') if isinstance(result, dict) else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_task_progress(self, task_id: str, progress: float):
        """更新任务进度"""
        for task in self.current_batch:
            if task['id'] == task_id:
                task['progress'] = int(progress * 100)
                break
    
    def get_queue_display_data(self) -> List[List[str]]:
        """获取队列显示数据"""
        display_data = []
        
        for task in self.current_batch:
            row = [
                task['filename'],
                task['status'],
                f"{task['progress']}%",
                time.strftime('%H:%M:%S', time.localtime(task['start_time'])) if task['start_time'] else '-',
                self._estimate_completion_time(task)
            ]
            display_data.append(row)
            
        return display_data
    
    def _estimate_completion_time(self, task: Dict[str, Any]) -> str:
        """估算完成时间"""
        if not task['start_time'] or task['progress'] == 0:
            return '-'
            
        elapsed = time.time() - task['start_time']
        if task['progress'] >= 100:
            return '已完成'
            
        estimated_total = elapsed / (task['progress'] / 100)
        remaining = estimated_total - elapsed
        
        if remaining < 60:
            return f"{int(remaining)}秒"
        elif remaining < 3600:
            return f"{int(remaining/60)}分钟"
        else:
            return f"{int(remaining/3600)}小时"
    
    def get_batch_status(self) -> str:
        """获取批量处理状态"""
        if not self.current_batch:
            return "暂无批量任务"
            
        total = len(self.current_batch)
        completed = sum(1 for task in self.current_batch if task['status'] == '完成')
        failed = sum(1 for task in self.current_batch if task['status'] == '失败')
        processing = sum(1 for task in self.current_batch if task['status'] == '处理中')
        waiting = sum(1 for task in self.current_batch if task['status'] == '等待中')
        
        status_lines = [
            f"总任务数: {total}",
            f"已完成: {completed} | 处理中: {processing}",
            f"等待中: {waiting} | 失败: {failed}",
            f"处理状态: {'进行中' if self.is_processing else '已停止'}"
        ]
        
        return "\n".join(status_lines)
    
    def get_batch_summary(self) -> str:
        """获取批量处理摘要"""
        if not self.batch_results:
            return "暂无处理结果"
            
        successful = sum(1 for result in self.batch_results.values() if result['status'] == '完成')
        failed = sum(1 for result in self.batch_results.values() if result['status'] == '失败')
        
        total_time = 0
        for result in self.batch_results.values():
            if result['start_time'] and result['status'] == '完成':
                # 这里需要实际的结束时间，简化处理
                total_time += 60  # 假设每个文件平均1分钟
                
        summary_lines = [
            f"成功: {successful} | 失败: {failed}",
            f"总耗时: {int(total_time/60)}分钟",
            f"平均耗时: {int(total_time/max(successful, 1))}秒/文件"
        ]
        
        return "\n".join(summary_lines)
    
    def pause_processing(self) -> str:
        """暂停处理"""
        self.is_processing = False
        return "批量处理已暂停"
    
    def stop_processing(self) -> str:
        """停止处理"""
        self.is_processing = False
        # 清空队列中等待的任务
        while not self.processing_queue.empty():
            try:
                self.processing_queue.get_nowait()
            except queue.Empty:
                break
        return "批量处理已停止，队列已清空"
    
    def clear_queue(self) -> str:
        """清空队列"""
        self.current_batch = []
        self.batch_results = {}
        while not self.processing_queue.empty():
            try:
                self.processing_queue.get_nowait()
            except queue.Empty:
                break
        return "处理队列已清空"
