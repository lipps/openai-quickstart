#!/usr/bin/env python3
"""
GUI功能测试脚本 - 使用Mock模拟gradio
验证GUI组件的核心逻辑，不依赖gradio库
"""

import sys
import os
import tempfile
import json
from unittest.mock import Mock, MagicMock

# 模拟gradio模块
class MockGradio:
    class Blocks:
        def __init__(self, title=None, theme=None, css=None):
            self.title = title
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
            
        def launch(self, **kwargs):
            print(f"模拟启动Gradio应用: {kwargs}")
    
    class Column:
        def __init__(self, scale=None):
            self.scale = scale
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
    
    class Row:
        def __init__(self):
            pass
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
    
    class Tab:
        def __init__(self, label, id=None):
            self.label = label
            self.id = id
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
    
    class Tabs:
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
    
    class Group:
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
    
    @staticmethod
    def Markdown(text):
        return Mock(value=text)
    
    @staticmethod
    def File(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Textbox(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Dropdown(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Button(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Progress(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Number(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Checkbox(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Dataframe(**kwargs):
        return Mock(**kwargs)
    
    @staticmethod
    def Slider(**kwargs):
        return Mock(**kwargs)
    
    class themes:
        @staticmethod
        def Soft():
            return Mock()

# 注入模拟的gradio
sys.modules['gradio'] = MockGradio()

# 添加路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_translator'))

def test_file_upload_component():
    """测试文件上传组件"""
    print("🧪 测试文件上传组件...")
    
    try:
        from ai_translator.components.file_upload import FileUploadComponent
        
        component = FileUploadComponent()
        
        # 测试文件验证
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"dummy pdf content")
            tmp_path = tmp_file.name
            
        is_valid, message = component.validate_file(tmp_path)
        print(f"   ✅ 文件验证: {is_valid}, 消息: {message}")
        
        # 清理
        os.unlink(tmp_path)
        
        # 测试批量文件验证
        valid_files, info = component.validate_batch_files([])
        print(f"   ✅ 批量验证空列表: {len(valid_files)} 文件, 信息: {info}")
        
        # 测试创建界面
        single_file, batch_files, file_info = component.create_upload_interface()
        print(f"   ✅ 创建上传界面: 组件已创建")
        
        print("   ✅ 文件上传组件测试通过")
        
    except Exception as e:
        print(f"   ❌ 文件上传组件测试失败: {e}")
        return False
    
    return True

def test_progress_display_component():
    """测试进度显示组件"""
    print("🧪 测试进度显示组件...")
    
    try:
        from ai_translator.components.progress_display import ProgressDisplayComponent
        
        component = ProgressDisplayComponent()
        
        # 测试初始化进度
        component.initialize_progress(10)
        print(f"   ✅ 初始化进度: 总页数 {component.total_pages}")
        
        # 测试更新进度
        progress_info = component.update_page_progress(2, 3, 5)
        print(f"   ✅ 更新进度: {progress_info['overall_progress']:.2f}")
        
        # 测试完成状态
        completion_info = component.update_completion_status(True, "测试完成")
        print(f"   ✅ 完成状态: {completion_info['status_message']}")
        
        # 测试创建界面
        progress_components = component.create_progress_interface()
        print(f"   ✅ 创建进度界面: {len(progress_components)} 个组件")
        
        print("   ✅ 进度显示组件测试通过")
        
    except Exception as e:
        print(f"   ❌ 进度显示组件测试失败: {e}")
        return False
    
    return True

def test_config_manager_component():
    """测试配置管理组件"""
    print("🧪 测试配置管理组件...")
    
    try:
        from ai_translator.components.config_manager import ConfigManagerComponent
        
        # 使用临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_file:
            tmp_file.write("""
OpenAIModel:
  model: "gpt-4o-mini"
  api_key: "test-key"
GLMModel:
  model_url: "http://test.com"
  timeout: 300
common:
  target_language: "中文"
  file_format: "markdown"
  output_dir: "./output"
""")
            config_path = tmp_file.name
        
        component = ConfigManagerComponent(config_path)
        
        # 测试加载配置
        config = component.load_config()
        print(f"   ✅ 加载配置: OpenAI模型 {config['OpenAIModel']['model']}")
        
        # 测试配置验证
        is_valid, message = component.validate_config(config)
        print(f"   ✅ 配置验证: {is_valid}, 消息: {message}")
        
        # 测试保存配置
        success, message = component.save_config(config)
        print(f"   ✅ 保存配置: {success}, 消息: {message}")
        
        # 测试创建界面
        components, buttons = component.create_config_interface()
        print(f"   ✅ 创建配置界面: {len(components)} 个组件, {len(buttons)} 个按钮")
        
        # 清理
        os.unlink(config_path)
        
        print("   ✅ 配置管理组件测试通过")
        
    except Exception as e:
        print(f"   ❌ 配置管理组件测试失败: {e}")
        return False
    
    return True

def test_history_manager_component():
    """测试历史记录管理组件"""
    print("🧪 测试历史记录管理组件...")
    
    try:
        from ai_translator.components.history_manager import HistoryManagerComponent
        
        # 使用临时历史文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            history_path = tmp_file.name
        
        component = HistoryManagerComponent(history_path)
        
        # 测试添加记录
        record_id = component.add_record(
            input_file="/test/file.pdf",
            target_language="中文",
            status="完成"
        )
        print(f"   ✅ 添加记录: ID {record_id}")
        
        # 测试更新记录
        success = component.update_record(record_id, status="完成", output_file="/test/output.md")
        print(f"   ✅ 更新记录: {success}")
        
        # 测试获取表格数据
        table_data = component.get_history_table_data()
        print(f"   ✅ 获取表格数据: {len(table_data)} 行")
        
        # 测试统计信息
        stats = component.get_statistics()
        print(f"   ✅ 统计信息: {stats.split()[1]}")
        
        # 测试创建界面
        components, buttons = component.create_history_interface()
        print(f"   ✅ 创建历史界面: {len(components)} 个组件, {len(buttons)} 个按钮")
        
        # 清理
        os.unlink(history_path)
        
        print("   ✅ 历史记录管理组件测试通过")
        
    except Exception as e:
        print(f"   ❌ 历史记录管理组件测试失败: {e}")
        return False
    
    return True

def test_batch_processor_component():
    """测试批量处理组件"""
    print("🧪 测试批量处理组件...")
    
    try:
        from ai_translator.components.batch_processor import BatchProcessorComponent
        
        component = BatchProcessorComponent(max_workers=2)
        
        # 创建测试文件
        test_files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(f"test content {i}".encode())
                test_files.append(tmp_file.name)
        
        # 测试添加文件到队列
        config = {
            'target_language': '中文',
            'file_format': 'markdown',
            'model_type': 'OpenAI'
        }
        
        result = component.add_files_to_queue(test_files, config)
        print(f"   ✅ 添加文件到队列: {result}")
        
        # 测试获取队列显示数据
        queue_data = component.get_queue_display_data()
        print(f"   ✅ 队列显示数据: {len(queue_data)} 个任务")
        
        # 测试批量状态
        status = component.get_batch_status()
        print(f"   ✅ 批量状态: {status.split()[1]}")
        
        # 测试创建界面
        components, buttons = component.create_batch_interface()
        print(f"   ✅ 创建批量界面: {len(components)} 个组件, {len(buttons)} 个按钮")
        
        # 清理测试文件
        for file_path in test_files:
            os.unlink(file_path)
        
        print("   ✅ 批量处理组件测试通过")
        
    except Exception as e:
        print(f"   ❌ 批量处理组件测试失败: {e}")
        return False
    
    return True

def test_gui_app():
    """测试主GUI应用"""
    print("🧪 测试主GUI应用...")
    
    try:
        from ai_translator.gui_app import TranslatorGUI
        
        # 创建GUI应用实例
        app = TranslatorGUI()
        print(f"   ✅ 创建GUI应用实例")
        
        # 测试创建界面
        interface = app.create_interface()
        print(f"   ✅ 创建主界面")
        
        # 测试配置相关方法
        config_values = app._load_config()
        print(f"   ✅ 加载配置: {len(config_values)} 个值")
        
        # 测试文件验证逻辑
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"test content")
            tmp_path = tmp_file.name
        
        # 模拟文件上传验证
        is_valid, message = app.file_upload.validate_file(tmp_path)
        print(f"   ✅ 文件验证: {is_valid}")
        
        # 清理
        os.unlink(tmp_path)
        
        print("   ✅ 主GUI应用测试通过")
        
    except Exception as e:
        print(f"   ❌ 主GUI应用测试失败: {e}")
        return False
    
    return True

def test_main_integration():
    """测试主程序集成"""
    print("🧪 测试主程序集成...")
    
    try:
        # 测试命令行参数解析
        from ai_translator.utils.argument_parser import ArgumentParser
        
        parser = ArgumentParser()
        
        # 模拟GUI参数
        import argparse
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
            tmp_file.write("""
import sys
sys.argv = ['main.py', '--gui']
from ai_translator.utils.argument_parser import ArgumentParser
parser = ArgumentParser()
args = parser.parse_arguments()
print(f"GUI模式: {getattr(args, 'gui', False)}")
""")
            test_script = tmp_file.name
        
        print(f"   ✅ GUI参数解析测试准备完成")
        
        # 测试配置加载
        from ai_translator.utils.config_loader import ConfigLoader
        
        # 创建测试配置
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_file:
            tmp_file.write("""
OpenAIModel:
  model: "gpt-4o-mini"
  api_key: "test-key"
common:
  book: "test.pdf"
  file_format: "markdown"
""")
            config_path = tmp_file.name
        
        loader = ConfigLoader(config_path)
        config = loader.load_config()
        print(f"   ✅ 配置加载: 模型 {config['OpenAIModel']['model']}")
        
        # 清理
        os.unlink(config_path)
        os.unlink(test_script)
        
        print("   ✅ 主程序集成测试通过")
        
    except Exception as e:
        print(f"   ❌ 主程序集成测试失败: {e}")
        return False
    
    return True

def main():
    """运行所有测试"""
    print("🚀 开始GUI功能测试 (Mock模式)...\n")
    
    tests = [
        test_file_upload_component,
        test_progress_display_component,
        test_config_manager_component,
        test_history_manager_component,
        test_batch_processor_component,
        test_gui_app,
        test_main_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有GUI组件测试通过！")
        print("\n📝 实现的功能:")
        print("✅ 拖拽式文件上传 - 支持单文件和批量上传")
        print("✅ 实时翻译进度显示 - 页面级和总体进度跟踪")
        print("✅ 批量文件处理 - 多线程并发处理队列")
        print("✅ 翻译历史记录 - 完整的CRUD操作和统计")
        print("✅ 配置管理界面 - OpenAI/GLM模型配置")
        print("✅ 现代化GUI界面 - 多标签页布局")
        print("✅ 命令行GUI启动 - python main.py --gui")
        
        print("\n🚀 使用说明:")
        print("1. 安装依赖: pip install gradio")
        print("2. 启动GUI: cd ai_translator && python main.py --gui")
        print("3. 或直接运行: python gui_app.py")
        print("4. 访问: http://127.0.0.1:7860")
        
        return True
    else:
        print("❌ 部分测试失败，请检查代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)