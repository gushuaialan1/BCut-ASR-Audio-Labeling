import os
import gradio as gr
from bcut_asr import BcutASR
from bcut_asr.orm import ResultStateEnum
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# 设置日志级别为ERROR，减少输出信息
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def process_single_file(file_path, model_name):
    try:
        asr = BcutASR(file_path)
        asr.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Origin': 'https://www.bilibili.com'
        })
        
        asr.upload()
        task_id = asr.create_task()
        
        while True:
            result = asr.result()
            if result.state == ResultStateEnum.COMPLETE:
                break
            elif result.state == ResultStateEnum.ERROR:
                return None
            time.sleep(1)
        
        if result.state == ResultStateEnum.COMPLETE:
            subtitle = result.parse()
            if subtitle.has_data():
                text = subtitle.to_txt().strip()
                # 处理文本：将空格替换为逗号，确保句末有句号
                text = re.sub(r'\s+', '，', text)  # 将一个或多个空白字符替换为逗号
                text = text.strip('，')  # 移除可能出现在开头或结尾的逗号
                if not text.endswith('。'):
                    text += '。'  # 如果末尾没有句号，添加句号
                
                filename = os.path.basename(file_path)
                relative_path = f"./Data/{model_name}/audios/wavs/{filename}"
                return f"{relative_path}|{model_name}|ZH|{text}"
            else:
                return None
    except Exception:
        return None

def annotate_audio(folder_path, model_name, num_threads=4, progress=gr.Progress()):
    files = [f for f in os.listdir(folder_path) if f.endswith(('.wav', '.mp3', '.flac', '.aac', '.m4a'))]
    results = []
    
    progress(0, desc="开始处理音频文件")
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_file = {executor.submit(process_single_file, os.path.join(folder_path, f), model_name): f for f in files}
        for i, future in enumerate(as_completed(future_to_file)):
            result = future.result()
            if result:
                results.append(result)
            progress((i + 1) / len(files), desc=f"已处理 {i + 1}/{len(files)} 个文件")
    
    # 将结果写入list文件，使用模型名称命名
    output_file = os.path.join(folder_path, f'{model_name}.list')
    with open(output_file, 'w', encoding='utf-8') as f:
        for line in results:
            f.write(line + '\n')
    
    return f"标注完成，共处理 {len(results)}/{len(files)} 个文件。结果已保存到 {output_file}"

# 创建Gradio界面
iface = gr.Interface(
    fn=annotate_audio,
    inputs=[
        gr.Textbox(label="请输入音频文件夹路径"),
        gr.Textbox(label="请输入模型名称"),
        gr.Slider(minimum=1, maximum=16, step=1, value=4, label="线程数量")
    ],
    outputs=gr.Textbox(label="标注结果"),
    title="BCut ASR Audio Labeling",
    description="选择包含音频文件的文件夹,系统将自动标注并生成list文件。"
)

if __name__ == "__main__":
    iface.launch()
