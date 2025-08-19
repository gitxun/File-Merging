from file_merge_pipeline import process_word_documents

def main():
    input_dir = r"D:\python_workspace\LLM_apply\projects_word_files"
    output_root = "projects_txt_modules"
    log_root_dir = "log"
    days_to_keep = 0  # 设置为0表示不保留旧日志
    module_config_file = "module_config.json"

    process_word_documents(
        input_dir=input_dir,
        output_root=output_root,
        log_root_dir=log_root_dir,
        days_to_keep=days_to_keep,
        module_config_file=module_config_file
    )

if __name__ == "__main__":
    main()
