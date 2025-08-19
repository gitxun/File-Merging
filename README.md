# FileMerge — 批量 Word 文档切分、索引、摘要与合并工具

简体中文 | 本仓库实现了一个基于 Flask 的 Web 服务，用于批量处理 Word 文档（切分为 txt、提取标题/摘要、格式化、合并并生成最终 Word）。前端通过 Socket.IO 展示实时进度，支持管理员用户上传文件并启动处理流程。

## 快速概览
- Web 服务入口：[`app.py`](app.py)（启动后监听 0.0.0.0:5000，使用 socketio 进行进度推送）
- 核心处理流程：[`file_merge_pipeline.py`](file_merge_pipeline.py) 中的 [`process_word_documents`](file_merge_pipeline.py)
- 与 LLM/摘要相关的调用：[`SummaryExtract/api_call.py`](SummaryExtract/api_call.py)（函数示例：[`chat`](SummaryExtract/api_call.py)、[`chat_without_context`](SummaryExtract/api_call.py)）
- 模块化合并逻辑集中在 `Module_merge` 目录（如 [`Module_merge/merge.py`](Module_merge/merge.py)、[`Module_merge/merge_prepare.py`](Module_merge/merge_prepare.py)、[`Module_merge/text_to_json.py`](Module_merge/text_to_json.py)、[`Module_merge/index_create.py`](Module_merge/index_create.py)，以及 [`Module_merge/txt_merge.py`](Module_merge/txt_merge.py)）
- Word 切分前处理：[`FilePreProcess/batch_runner.py`](FilePreProcess/batch_runner.py) 的 [`batch_process_word_files`](FilePreProcess/batch_runner.py)；日志工具：[`FilePreProcess/utils.py`](FilePreProcess/utils.py)（[`setup_logger`](FilePreProcess/utils.py)、[`get_log_file_path`](FilePreProcess/utils.py)、[`clean_old_logs`](FilePreProcess/utils.py)）

## 仓库结构（部分）
- app.py — Flask 应用与 API（登录、管理员、启动处理、下载结果）
- file_merge_pipeline.py — 处理流程编排与进度回调（[`process_word_documents`](file_merge_pipeline.py)）
- Module_merge/ — 合并与索引相关模块
- SummaryExtract/ — 与 LLM 交互 / 摘要生成
- FilePreProcess/ — 文档预处理与日志工具
- templates/、static/ — 前端页面与静态资源（示例：[`templates/admin_users.html`](templates/admin_users.html)、[`static/main.js`](static/main.js)）
- module_config.json、api_config.json、users.json — 运行所需的配置与用户数据文件
- uploaded_input/、default_output/、log/ — 上传输入、输出结果与日志目录

## 环境与依赖
建议在虚拟环境中安装依赖。主要依赖项（示例）：
- Flask
- Flask-SocketIO
- Flask-Login
- Flask-Bcrypt
- python-dotenv / openai SDK（如果使用云 API）

安装示例：
```sh
# filepath: README.md
# 安装（示例）
pip install -r requirements.txt
