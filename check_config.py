import os
config_path = os.path.expanduser("~/AppData/Local/TreeChat/TreeChat/settings.ini")
print(f"配置文件路径: {config_path}")
print(f"文件是否存在: {os.path.exists(config_path)}")

if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        print("配置文件内容:")
        print(f.read())