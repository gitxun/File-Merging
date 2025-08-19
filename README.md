// ...existing code...
# FileMerge — 批量 Word 文档切分、索引、摘要与合并工具

简体中文

本仓库实现了一个基于 Flask 的 Web 服务，用于批量处理 Word 文档（切分、提取标题/摘要、格式化、索引、合并并生成最终 Word）。前端通过 Socket.IO 展示实时进度，管理员账户用于上传并启动处理流程。

## 快速概览
- 入口：`app.py`（Flask + Flask-SocketIO）
- 核心流程：`file_merge_pipeline.py` 中的 `process_word_documents`
- 主要模块目录：
  - `Module_merge/`：合并与索引
  - `SummaryExtract/`：摘要与 LLM 调用
  - `FilePreProcess/`：预处理与日志
  - `TxtoWord/`：TXT -> Word 及格式化
- 运行时目录：
  - 上传输入：`uploaded_input/`
  - 输出结果：`default_output/`
  - 日志目录：`log/`
- 配置文件示例：`module_config.json`、`api_config.json`、`users.json`

## 快速运行（Windows）
1. 建议创建虚拟环境并激活：
   - PowerShell:
     ```
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - CMD:
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
   访问：http://localhost:5000

## 快速运行（Linux / macOS）
1. 创建并激活虚拟环境：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动服务（如需后台运行可使用 nohup 或 systemd）：
   ```bash
   python3 app.py
   # 或后台运行示例：
   nohup python3 app.py > server.log 2>&1 &
   ```
   访问：http://localhost:5000

## 使用要点
- 权限：只有 role 为 `admin` 的用户可通过 `/start` 发起处理任务（参见 `app.py`）。
- 输入：通过界面或 API 上传 Word 文件与模块配置，文件保存到 `uploaded_input/`。
- 输出：处理结果保存在 `default_output/`，下载接口仅允许该目录下文件。
- 进度：通过 Socket.IO 事件 `progress_update`、`process_done`、`process_error` 推送到前端。

## 主要入口与函数
- `app.py`：Web 接口、后台任务调度、下载接口
  - 启动任务：`start_process`
  - 后台执行：`run_process`
  - 下载：`download_result_file`
- `file_merge_pipeline.py`：
  - `process_word_documents(input_dir, output_root, ...)`：处理全过程（切分、索引、摘要、合并、生成 Word）

## 日志与清理
- 日志在 `log/`，由 `FilePreProcess/utils.py` 中的 `setup_logger` 与 `clean_old_logs` 管理。
- `process_word_documents` 支持指定保留日志天数（参数 `days_to_keep`）。

## 开发与贡献
- 项目按模块划分，便于单元测试与扩展。提交 PR 前请确保相关模块在本地可运行。
- 建议补充 `requirements.txt` 与示例 `users.json`（含管理员）以便快速上手。

## 常见问题
- 无法发起任务：请确认以管理员身份登录。
- API 调用失败：检查 `api_config.json` 与网络/密钥设置。
- 未找到输出文件：检查后台日志与 `default_output/` 目录，确认处理流程已完成。

## 许可证
本 README 与项目说明采用 CC BY-NC 4.0（署名-非商业性使用）。  
如需将整个代码仓库采用该许可证，请在仓库根目录添加 LICENSE 文件（内容可参考 Creative Commons 官方 CC BY-NC 4.0 文本）。

---
