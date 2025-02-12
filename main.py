import tkinter as tk
from ui.main_window import MainWindow

if __name__ == "__main__":
    # 创建 Tkinter 根窗口
    root = tk.Tk()
    # 初始化主窗口
    main_window = MainWindow(root)
    # 进入消息循环
    root.mainloop()
