# BCut ASR Audio Labeling

这是一个基于bcut-asr（必剪）的音频自动标注工具，主要用于制作Bert-VITS2的数据集标注。本工具提供了简单易用的Gradio界面，支持多线程处理，让您轻松白嫖B站的语音识别能力。

## 功能特点

- 简洁的Gradio用户界面
- 选择本地音频文件夹进行批量处理
- 自动对文件夹内的音频文件进行标注
- 多线程处理，显著提高效率
- 自动添加基本标点符号，优化输出文本
- 将标注结果输出为Bert-VITS2兼容的list文件格式
- 精标功能，支持手动编辑和修正自动生成的标注

## 系统要求

- Python >= 3.10
- poetry

## 安装步骤

1. 克隆本项目:
   ```
   git clone https://github.com/gushuaialan1/BCut-ASR-Audio-Labeling.git
   cd BCut-ASR-Audio-Labeling
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

2. 应用将自动在你的默认浏览器中打开。如果没有自动打开，请手动访问 http://localhost:8501

3. 在Gradio界面中，您可以选择以下两个功能：

   a. 自动标注：
   - 输入音频文件夹路径
   - 输入模型名称
   - 选择线程数量（默认为4）
   - 点击"开始标注"按钮

   b. 精标：
   - 输入标注文件夹路径
   - 输入模型名称
   - 点击"加载标注"按钮
   - 使用界面提供的控件进行标注编辑和修正

4. 对于自动标注，处理完成后，在输入的文件夹中会生成`{model_name}.list`文件，包含所有的标注结果。

5. 对于精标功能，您可以直接在界面上编辑标注文本，系统会自动保存您的修改。

## 输出格式

每行的格式为：
`./Data/{model_name}/audios/wavs/{filename}|{model_name}|ZH|{text}`

## 注意事项

- 支持的音频格式: .wav, .mp3, .flac, .aac, .m4a
- 默认假设所有音频都是中文(ZH)，说话人标识使用用户输入的模型名称
- 处理大量或长音频文件可能需要较长时间
- 请遵守B站的使用条款，合理使用本工具
- 精标功能支持分页浏览和编辑，方便处理大量标注

## 依赖

详见`requirements.txt`文件。

## 许可证

本项目采用 MIT 许可证。详情请见 [LICENSE](LICENSE) 文件。

## 致谢

特别感谢 [bcut-asr](https://github.com/SocialSisterYi/bcut-asr) 项目，本工具基于其功能开发。

## 贡献

欢迎提交问题和拉取请求。对于重大更改，请先开issue讨论您想要改变的内容。

## 免责声明

本工具仅供学习和研究使用。使用者应当遵守相关法律法规和B站的服务条款。作者不对使用本工具造成的任何问题负责。
