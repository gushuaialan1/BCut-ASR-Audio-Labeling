# BCut ASR Audio Labeling

这是一个基于bcut-asr（必剪）的音频自动标注工具，主要用于制作Bert-VITS2的数据集标注。本工具提供了简单易用的Gradio界面，支持多线程处理，让您轻松白嫖B站的语音识别能力。

## 功能特点

- 简洁的Gradio用户界面
- 选择本地音频文件夹进行批量处理
- 自动对文件夹内的音频文件进行标注
- 多线程处理，显著提高效率
- 自动添加基本标点符号，优化输出文本
- 将标注结果输出为Bert-VITS2兼容的list文件格式

## 系统要求

- Python >= 3.10
- poetry

## 安装步骤

1. 克隆本项目:
   ```
   git clone [您的项目URL]
   cd [项目文件夹名]
   ```

2. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

3. 安装bcut-asr:
   ```
   git clone https://github.com/SocialSisterYi/bcut-asr
   cd bcut-asr
   poetry lock
   poetry build -f wheel
   pip install dist/bcut_asr-0.0.3-py3-none-any.whl  # 版本号可能会有所不同，请根据实际情况调整
   cd ..
   ```

## 使用方法

1. 运行程序:
   ```
   python main.py
   ```

2. 在Gradio界面中输入以下信息：
   - 音频文件夹路径
   - 模型名称
   - 线程数量（默认为4）

3. 点击提交，系统将自动处理文件夹中的音频文件并生成标注结果。

4. 处理完成后，在输入的文件夹中会生成`{model_name}.list`文件，包含所有的标注结果。

## 输出格式

每行的格式为：

## 注意事项

- 支持的音频格式: .wav, .mp3, .flac, .aac, .m4a
- 默认假设所有音频都是中文(ZH)，说话人标识使用用户输入的模型名称
- 处理大量或长音频文件可能需要较长时间
- 请遵守B站的使用条款，合理使用本工具

## 依赖

详见`requirements.txt`文件。

## 许可证

[在此添加您的许可证信息]
