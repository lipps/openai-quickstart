import gradio as gr
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class HistoryManagerComponent:
    """翻译历史记录管理组件"""
    
    def __init__(self, history_file: str = "translation_history.json"):
        self.history_file = history_file
        self.history_data = self.load_history()
        
    def create_history_interface(self):
        """创建历史记录界面"""
        with gr.Column():
            gr.Markdown("### 📚 翻译历史")
            
            with gr.Row():
                refresh_btn = gr.Button("🔄 刷新", variant="secondary")
                clear_btn = gr.Button("🗑️ 清空历史", variant="secondary")
                export_btn = gr.Button("📤 导出历史", variant="secondary")
                
            # 历史记录列表
            history_list = gr.Dataframe(
                headers=["时间", "文件名", "源语言", "目标语言", "状态", "输出文件"],
                datatype=["str", "str", "str", "str", "str", "str"],
                interactive=False,
                wrap=True,
                row_count=10
            )
            
            # 详细信息显示
            with gr.Row():
                with gr.Column(scale=1):
                    selected_info = gr.Textbox(
                        label="选中记录详情",
                        interactive=False,
                        lines=8
                    )
                    
                with gr.Column(scale=1):
                    operation_buttons = gr.Column()
                    with operation_buttons:
                        rerun_btn = gr.Button("🔄 重新翻译", variant="primary")
                        download_btn = gr.Button("📥 下载结果", variant="secondary")
                        delete_btn = gr.Button("❌ 删除记录", variant="secondary")
                        
            # 统计信息
            stats_info = gr.Textbox(
                label="统计信息",
                interactive=False,
                lines=3
            )
            
        components = {
            'history_list': history_list,
            'selected_info': selected_info,
            'stats_info': stats_info
        }
        
        buttons = {
            'refresh_btn': refresh_btn,
            'clear_btn': clear_btn,
            'export_btn': export_btn,
            'rerun_btn': rerun_btn,
            'download_btn': download_btn,
            'delete_btn': delete_btn
        }
        
        return components, buttons
    
    def load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception:
            return []
    
    def save_history(self) -> bool:
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def add_record(self, 
                   input_file: str,
                   target_language: str = "中文",
                   source_language: str = "自动检测",
                   output_file: str = "",
                   status: str = "进行中",
                   **kwargs) -> str:
        """添加翻译记录"""
        
        record = {
            'id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'timestamp': datetime.now().isoformat(),
            'input_file': input_file,
            'filename': os.path.basename(input_file),
            'source_language': source_language,
            'target_language': target_language,
            'output_file': output_file,
            'status': status,
            'file_size': os.path.getsize(input_file) if os.path.exists(input_file) else 0,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration': None,
            'error_message': None,
            **kwargs
        }
        
        self.history_data.insert(0, record)  # 最新记录在前
        self.save_history()
        return record['id']
    
    def update_record(self, record_id: str, **updates) -> bool:
        """更新翻译记录"""
        for record in self.history_data:
            if record['id'] == record_id:
                record.update(updates)
                
                # 如果状态变为完成或失败，记录结束时间
                if updates.get('status') in ['完成', '失败']:
                    record['end_time'] = datetime.now().isoformat()
                    if record.get('start_time'):
                        start = datetime.fromisoformat(record['start_time'])
                        end = datetime.fromisoformat(record['end_time'])
                        record['duration'] = str(end - start)
                
                self.save_history()
                return True
        return False
    
    def get_history_table_data(self) -> List[List[str]]:
        """获取历史记录表格数据"""
        table_data = []
        for record in self.history_data:
            row = [
                record.get('timestamp', '')[:19].replace('T', ' '),  # 格式化时间
                record.get('filename', ''),
                record.get('source_language', ''),
                record.get('target_language', ''),
                record.get('status', ''),
                os.path.basename(record.get('output_file', '')) if record.get('output_file') else ''
            ]
            table_data.append(row)
        return table_data
    
    def get_record_details(self, row_index: int) -> str:
        """获取记录详细信息"""
        if 0 <= row_index < len(self.history_data):
            record = self.history_data[row_index]
            
            details = []
            details.append(f"记录ID: {record.get('id', 'N/A')}")
            details.append(f"输入文件: {record.get('input_file', 'N/A')}")
            details.append(f"输出文件: {record.get('output_file', 'N/A')}")
            details.append(f"文件大小: {self.format_file_size(record.get('file_size', 0))}")
            details.append(f"开始时间: {record.get('start_time', 'N/A')}")
            details.append(f"结束时间: {record.get('end_time', 'N/A')}")
            details.append(f"耗时: {record.get('duration', 'N/A')}")
            
            if record.get('error_message'):
                details.append(f"错误信息: {record.get('error_message')}")
                
            return "\n".join(details)
        return "未选择记录"
    
    def get_statistics(self) -> str:
        """获取统计信息"""
        total_records = len(self.history_data)
        if total_records == 0:
            return "暂无翻译记录"
            
        completed = sum(1 for r in self.history_data if r.get('status') == '完成')
        failed = sum(1 for r in self.history_data if r.get('status') == '失败')
        in_progress = sum(1 for r in self.history_data if r.get('status') == '进行中')
        
        total_size = sum(r.get('file_size', 0) for r in self.history_data)
        
        stats = []
        stats.append(f"总记录数: {total_records}")
        stats.append(f"完成: {completed} | 失败: {failed} | 进行中: {in_progress}")
        stats.append(f"总文件大小: {self.format_file_size(total_size)}")
        
        return "\n".join(stats)
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def clear_history(self) -> bool:
        """清空历史记录"""
        self.history_data = []
        return self.save_history()
    
    def delete_record(self, record_id: str) -> bool:
        """删除指定记录"""
        original_length = len(self.history_data)
        self.history_data = [r for r in self.history_data if r.get('id') != record_id]
        
        if len(self.history_data) < original_length:
            self.save_history()
            return True
        return False
    
    def export_history(self, export_path: str = None) -> tuple[bool, str]:
        """导出历史记录"""
        if not export_path:
            export_path = f"translation_history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
            return True, f"历史记录已导出到: {export_path}"
        except Exception as e:
            return False, f"导出失败: {str(e)}"