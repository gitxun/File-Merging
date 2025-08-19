# FileMerge — 批量 Word 文档切分、索引、摘要与合并工具

简体中文

本仓库实现了一个基于 Flask 的 Web 服务，用于批量处理 Word 文档（切分、提取标题/摘要、格式化、索引、合并并生成最终 Word）。前端通过 Socket.IO 展示实时进度，管理员账号用于上传并启动处理流程。

## 项目概览
- Web 服务入口：`app.py`（使用 Flask + Flask-SocketIO）
- 核心处理流程：`file_merge_pipeline.py` 中的 `process_word_documents`
- 模块示例目录：
  - `Module_merge/`：合并与索引相关模块
  - `SummaryExtract/`：与 LLM/摘要交互
  - `FilePreProcess/`：文档预处理与日志工具
- 前端模版与静态资源：`templates/`、`static/`
- 运行时目录：
  - 上传输入：`uploaded_input/`
  - 输出结果：`default_output/`
  - 日志目录：`log/`
- 配置/数据文件示例：
  - `module_config.json`、`api_config.json`
  - `users.json`（用户/权限存储）

## 快速运行（Windows）
1. 创建并激活虚拟环境（可选）：
   powershell:
   ```
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   cmd:
   ```
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

2. 安装依赖（若有 requirements.txt）：
   ```
   pip install -r requirements.txt
   ```

3. 启动服务：
   ```
   python app.py
   ```
   打开浏览器访问：http://localhost:5000

## 配置要点
- 管理权限：只有 role 为 `admin` 的用户可通过 `/start` 接口发起处理任务。请在 `users.json` 中配置管理员账号或通过管理员界面添加用户。
- API/模型：若使用外部 LLM 或 API，请在 `api_config.json` 中配置密钥与端点，`SummaryExtract/api_call.py` 为示例接入代码。
- 模块行为：通过 `module_config.json` 调整切分/合并策略。
- 输出与下载：处理输出在 `default_output/`，下载接口限制只能访问该目录下文件以避免任意路径暴露。

## 主要入口与函数
- `app.py`
  - 启动任务：`/start` -> `start_process`
  - 后台处理：`run_process`
  - 下载：`/download` -> `download_result_file`
- `file_merge_pipeline.py`
  - `process_word_documents(input_dir, output_root, ...)`：处理流程编排与进度回调
- 其他模块：见 `Module_merge/`、`SummaryExtract/`、`FilePreProcess/`

## 日志与清理
- 日志存放在 `log/`，由 `FilePreProcess/utils.py` 中的 `setup_logger`、`clean_old_logs` 管理。
- 可在调用 `process_word_documents` 时通过参数控制保留日志的天数。

## 开发与贡献
- 仓库按功能模块拆分，便于独立开发与测试。提交 PR 时请附说明与必要的配置修改。
- 可补充 `requirements.txt`、示例 `users.json`（含管理员）及 demo 模块配置以便快速上手。

## 常见问题
- 无法发起任务：请确认已以管理员身份登录。
- API 调用失败：检查 `api_config.json` 与网络/密钥设置。
- 未找到输出文件：检查后台日志与 `default_output/` 目录，确认处理流程结束并返回结果路径。

## 许可证
请在仓库根目录添加 LICENSE 文件并在此处说明采用的许可证类型。

---
