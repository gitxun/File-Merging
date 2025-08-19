# FileMerge — 批量 Word 文档切分、索引、摘要与合并工具 / FileMerge — Batch Word Split, Index, Summarize & Merge

中文 / Chinese & English

简短说明 | Summary
- 本仓库实现了一个基于 Flask 的 Web 服务，用于批量处理 Word 文档：切分为 txt、提取标题/摘要、格式化、索引并合并生成最终 Word。前端通过 Socket.IO 展示实时进度。  
- This repo provides a Flask-based web service to batch-process Word documents: split to txt, extract headings/summaries, format, index and merge into final Word files. Progress is pushed to the frontend via Socket.IO.

目录 | Contents
- app.py — Flask 应用（登录、管理员、启动处理、下载）  
- file_merge_pipeline.py — 处理流程编排（process_word_documents）  
- Module_merge/ — 合并与索引模块  
- SummaryExtract/ — 摘要与 LLM 调用示例  
- FilePreProcess/ — 文档预处理与日志工具  
- templates/, static/ — 前端模板与静态资源  
- 配置/运行目录：module_config.json、api_config.json、users.json、uploaded_input/、default_output/、log/

快速开始（Windows） | Quick start (Windows)
1. 创建并激活虚拟环境（可选）
   - PowerShell:
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - CMD:
     ```cmd
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
2. 安装依赖（若有 requirements.txt）
   ```cmd
   pip install -r requirements.txt
   ```
3. 启动服务
   ```cmd
   python app.py
   ```
   打开浏览器访问：http://localhost:5000  
   Open http://localhost:5000

快速开始（Linux / macOS） | Quick start (Linux / macOS)
1. 创建并激活虚拟环境
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
3. 启动服务（后台运行示例）
   ```bash
   python3 app.py
   # 或者
   nohup python3 app.py > server.log 2>&1 &
   ```
   访问：http://localhost:5000

主要功能与流程 | Main features & pipeline
1. 文档切分（Word -> txt）  
2. 多级标题提取与索引生成  
3. 摘要提取（可接入 LLM）  
4. JSON/文本格式化与合并预处理  
5. 最终合并并生成 Word 文档  
- 相关主函数：file_merge_pipeline.py 中的 process_word_documents(input_dir, output_root, ...)  
- Progress callbacks via Socket.IO events (e.g. progress_update / process_done / process_error).

权限与用户 | Users & permissions
- 使用 users.json 管理用户，role 字段控制权限（如 admin 可发起任务）。  
- Only users with role == "admin" can call /start to run processing tasks.

配置要点 | Configuration
- module_config.json：控制切分/合并策略  
- api_config.json：外部 LLM/API 配置（如需）  
- users.json：用户和密码哈希信息  
- 输出目录限制：下载接口仅允许访问 default_output/ 下的文件以避免任意路径暴露。

日志 | Logging
- 日志文件保存在 log/，由 FilePreProcess/utils.py 的 setup_logger 与 clean_old_logs 管理。  
- Configure days_to_keep when calling process_word_documents to control log retention.

常见命令 | Common commands
- 生成 requirements 示例（如没有 requirements.txt，请在虚拟环境中运行 pip freeze > requirements.txt）  
- 启动后台（Linux）：nohup python3 app.py > server.log 2>&1 &

示例文件建议 | Suggested example files
- requirements.txt（列出 Flask, Flask-SocketIO, Flask-Login, Flask-Bcrypt 等依赖）  
- users.json 示例（包含一个管理员账户）  
- LICENSE（见下文）

许可证 | License
本项目说明及 README 采用 CC BY-NC 4.0（署名-非商业性使用）。    
This README is under CC BY-NC 4.0. 
