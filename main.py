import os
import sys
import traceback
import logging
import tempfile
import json

# 如果是打包后的应用
application_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
log_path = os.path.join(tempfile.gettempdir(), 'BCutASRLabeling', 'error_log.txt')

# 确保日志文件的目录存在
os.makedirs(os.path.dirname(log_path), exist_ok=True)

# 设置日志
logging.basicConfig(filename=log_path, level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

if getattr(sys, 'frozen', False):
    # 如果是打包后的 exe 运行
    bundle_dir = sys._MEIPASS
    os.environ['GRADIO_ANALYTICS_ENABLED'] = 'False'
    os.environ['GRADIO_OFFLINE'] = 'True'
else:
    # 如果是脚本运行
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(bundle_dir)
sys.path.append(os.path.join(bundle_dir, 'gradio'))

# 其余的导入和代码...

import gradio as gr
from bcut_asr import BcutASR
from bcut_asr.orm import ResultStateEnum
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import webbrowser
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

all_annotations = []
allowed_paths = ["."]  # 初始允许的路径

def process_single_file(file_path, model_name):
    try:
        asr = BcutASR(file_path)
        asr.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Origin': 'https://www.bilibili.com'
        })
        
        asr.upload()
        asr.create_task()
        
        while True:
            result = asr.result()
            if result.state == ResultStateEnum.COMPLETE:
                break
            elif result.state == ResultStateEnum.ERROR:
                logging.error(f"处理文件失败: {file_path}, 错误: 任务状态为ERROR")
                return None
            time.sleep(1)
        
        if result.state == ResultStateEnum.COMPLETE:
            subtitle = result.parse()
            if subtitle.has_data():
                text = subtitle.to_txt().strip()
                text = re.sub(r'\s+', '，', text)
                text = text.strip('，')
                if not text.endswith('。'):
                    text += '。'
                
                filename = os.path.basename(file_path)
                relative_path = f"./Data/{model_name}/audios/wavs/{filename}"
                return f"{relative_path}|{model_name}|ZH|{text}"
            else:
                logging.warning(f"文件没有识别出文本: {file_path}")
                return None
    except Exception as e:
        logging.error(f"处理文件时发生异常: {file_path}, 错误: {str(e)}")
        return None

def annotate_audio(folder_path, model_name, num_threads=4, progress=gr.Progress()):
    files = [f for f in os.listdir(folder_path) if f.endswith(('.wav', '.mp3', '.flac', '.aac', '.m4a'))]
    results = []
    failed_files = []
    
    progress(0, desc="开始处理音频文件")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_file = {executor.submit(process_single_file, os.path.join(folder_path, f), model_name): f for f in files}
        for i, future in enumerate(as_completed(future_to_file)):
            file = future_to_file[future]
            result = future.result()
            if result:
                results.append(result)
            else:
                failed_files.append(file)
            progress((i + 1) / len(files), desc=f"已处理 {i + 1}/{len(files)} 个文件")
    
    output_file = os.path.join(folder_path, f'{model_name}.list')
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in results:
            f.write(line + '\n')
    
    save_last_process(folder_path, model_name)
    
    if failed_files:
        logging.warning(f"以下文件处理失败: {', '.join(failed_files)}")
    
    return f"标注完成，共处理 {len(results)}/{len(files)} 个文件。结果已保存到 {output_file}\n处理失败的文件: {', '.join(failed_files)}"

def load_annotations(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]

def save_annotations(file_path, annotations):
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in annotations:
            f.write(line + '\n')

def load_all_annotations(folder_path, model_name):
    list_file = os.path.join(folder_path, f'{model_name}.list')
    return load_annotations(list_file) if os.path.exists(list_file) else []

def natural_sort_key(s):
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]

def edit_annotations(folder_path, model_name, page=1, all_annotations=None):
    logging.info(f"加载标注: 文件夹={folder_path}, 模型名称={model_name}, 页面={page}")
    
    if all_annotations is None:
        all_annotations = load_all_annotations(folder_path, model_name)
    
    if not all_annotations:
        logging.warning(f"没有找到标注")
        return [gr.update(visible=False)] * 60 + [gr.update(visible=False), gr.update(visible=False), "没有找到标注"]

    # 对整个标注行进行排序，基于文件名
    sorted_annotations = sorted(all_annotations, key=lambda x: natural_sort_key(os.path.basename(x.split('|')[0])))

    total_pages = (len(sorted_annotations) + 19) // 20
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * 20
    end_idx = start_idx + 20

    current_annotations = sorted_annotations[start_idx:end_idx]
    outputs = []
    for line in current_annotations:
        parts = line.split('|')
        audio_path = parts[0]  # 这是相对路径
        audio_filename = os.path.basename(audio_path)
        full_audio_path = os.path.join(folder_path, audio_filename)
        outputs.extend([
            gr.update(value=full_audio_path, visible=True),
            gr.update(value=f"标注 {audio_filename}", visible=True),
            gr.update(value=parts[3], visible=True, interactive=True),
        ])

    outputs.extend([gr.update(visible=False)] * (60 - len(outputs)))

    page_info = f"第 {page} 页，共 {total_pages} 页"
    logging.info(f"成功加载标注: 找到 {len(current_annotations)} 条记录")
    return outputs + [
        gr.update(value=page_info),  
        gr.update(value=page),       
        gr.update(value=page_info),  
        gr.update(value=page),       
        f"成功加载 {len(current_annotations)} 条记录"  
    ]

def load_last_process():
    json_path = os.path.join(get_app_path(), 'last_process.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            logging.info(f"成功加载上次处理信息: {data}")
            return data.get('folder_path', ''), data.get('model_name', '')
        except Exception as e:
            logging.error(f"读取 last_process.json 时出错: {e}")
    else:
        logging.info("未找到 last_process.json 文件")
    return '', ''

def save_last_process(folder_path, model_name):
    json_path = os.path.join(get_app_path(), 'last_process.json')
    try:
        with open(json_path, 'w') as f:
            json.dump({'folder_path': folder_path, 'model_name': model_name}, f)
        logging.info(f"成功保存处理信息: folder_path={folder_path}, model_name={model_name}")
    except Exception as e:
        logging.error(f"保存 last_process.json 时出错: {e}")

def jump_to_page(folder_path, model_name, page):
    global all_annotations
    page = int(page)
    total_pages = (len(all_annotations) + 19) // 20
    page = max(1, min(page, total_pages))
    return edit_annotations(folder_path, model_name, page, all_annotations)

def load_and_preprocess(folder_path, model_name):
    global all_annotations, allowed_paths
    if folder_path not in allowed_paths:
        allowed_paths.append(folder_path)
    all_annotations = load_all_annotations(folder_path, model_name)
    return edit_annotations(folder_path, model_name, 1, all_annotations)

def save_annotation(folder_path, model_name, page, index, new_text):
    global all_annotations
    sorted_annotations = sorted(all_annotations, key=lambda x: natural_sort_key(os.path.basename(x.split('|')[0])))
    annotation_index = (page - 1) * 20 + index
    if 0 <= annotation_index < len(sorted_annotations):
        parts = sorted_annotations[annotation_index].split('|')
        parts[3] = new_text
        sorted_annotations[annotation_index] = '|'.join(parts)
        all_annotations = sorted_annotations  # 更新全局变量
        save_annotations(os.path.join(folder_path, f'{model_name}.list'), all_annotations)
        return f"已保存修改：第 {page} 页，第 {index + 1} 条"
    return "保失败：索引超出范围"

def create_ui():
    last_folder, last_model = load_last_process()

    with gr.Blocks(css="""
        .page-controls { display: flex; justify-content: space-between; align-items: center; margin: 10px 0; }
        .page-input { width: 60px; }
        .annotation-box { border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; }
        .annotation-content { border: 1px solid #eee; padding: 5px; margin-top: 5px; }
    """) as app:
        gr.Markdown("# BCut ASR Audio Labeling")
        
        with gr.Tab("自动标注"):
            folder_path = gr.Textbox(label="音频文件夹路径", value=last_folder)
            model_name = gr.Textbox(label="模型名称", value=last_model)
            num_threads = gr.Slider(minimum=1, maximum=16, step=1, value=4, label="线程数量")
            submit_btn = gr.Button("开始标注")
            output = gr.Textbox(label="标注结果")
            
            submit_btn.click(annotate_audio, inputs=[folder_path, model_name, num_threads], outputs=output)

        with gr.Tab("精标"):
            edit_folder_path = gr.Textbox(label="标注文件夹路径", value=last_folder)
            edit_model_name = gr.Textbox(label="模型名称", value=last_model)
            load_btn = gr.Button("加载标注")
            
            def create_page_controls():
                with gr.Row(elem_classes="page-controls"):
                    prev_btn = gr.Button("上一页")
                    page_info = gr.Markdown("第 1 页，共 1 页")
                    next_btn = gr.Button("下一页")
                    page_input = gr.Number(value=1, label="跳转到", elem_classes="page-input")
                    go_btn = gr.Button("跳转")
                return prev_btn, page_info, next_btn, page_input, go_btn

            top_controls = create_page_controls()
            
            annotation_list = []
            for _ in range(20):
                with gr.Group(elem_classes="annotation-box"):
                    with gr.Row():
                        audio = gr.Audio(label="音频", visible=False)
                        with gr.Column():
                            label = gr.Markdown(visible=False)
                            with gr.Group(elem_classes="annotation-content"):
                                text = gr.Textbox(label="", visible=False, lines=3, interactive=True)
                    annotation_list.extend([audio, label, text])

            bot_controls = create_page_controls()
            
            edit_output = gr.Textbox(label="操作结果")

            load_btn.click(
                load_and_preprocess,
                inputs=[edit_folder_path, edit_model_name],
                outputs=annotation_list + [top_controls[1], top_controls[3], bot_controls[1], bot_controls[3]] + [edit_output]
            )

            for controls in [top_controls, bot_controls]:
                prev_btn, page_info, next_btn, page_input, go_btn = controls
                prev_btn.click(
                    lambda folder, model, page: jump_to_page(folder, model, int(page) - 1),
                    inputs=[edit_folder_path, edit_model_name, page_input],
                    outputs=annotation_list + [top_controls[1], top_controls[3], bot_controls[1], bot_controls[3]] + [edit_output]
                )
                next_btn.click(
                    lambda folder, model, page: jump_to_page(folder, model, int(page) + 1),
                    inputs=[edit_folder_path, edit_model_name, page_input],
                    outputs=annotation_list + [top_controls[1], top_controls[3], bot_controls[1], bot_controls[3]] + [edit_output]
                )
                go_btn.click(
                    jump_to_page,
                    inputs=[edit_folder_path, edit_model_name, page_input],
                    outputs=annotation_list + [top_controls[1], top_controls[3], bot_controls[1], bot_controls[3]] + [edit_output]
                )

            for i, text in enumerate([item for item in annotation_list if isinstance(item, gr.Textbox)]):
                text.change(
                    save_annotation,
                    inputs=[edit_folder_path, edit_model_name, top_controls[3], gr.Number(value=i, visible=False), text],
                    outputs=[edit_output]
                )

    return app

def open_browser():
    time.sleep(2)
    webbrowser.open('http://127.0.0.1:7860')

def add_gradio_to_path():
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
    else:
        bundle_dir = os.path.dirname(os.path.abspath(__file__))

    gradio_dir = os.path.join(bundle_dir, 'gradio')
    if os.path.exists(gradio_dir):
        sys.path.insert(0, gradio_dir)

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

add_gradio_to_path()

if __name__ == '__main__':
    try:
        logging.info(f"应用路径: {get_app_path()}")
        allowed_paths = [path for path in allowed_paths if os.path.isdir(path)]
        app = create_ui()
        threading.Thread(target=open_browser).start()
        app.launch(allowed_paths=allowed_paths)
    except Exception as e:
        error_msg = f"发生错误: {str(e)}\n{traceback.format_exc()}"
        logging.error(error_msg)
        
        # 将错误信息写入文件
        error_file = os.path.join(get_app_path(), 'error.txt')
        with open(error_file, 'w') as f:
            f.write(error_msg)
        
        # 显示错误信息消息框（仅在 Windows 上）
        if sys.platform.startswith('win'):
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, error_msg, "错误", 0)

        sys.exit(1)
