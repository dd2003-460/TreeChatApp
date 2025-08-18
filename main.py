import tkinter as tk
from ui.main_window import MainWindow

if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)
    # 移除这行代码：
    # main_window.load_ai_model_settings()
    root.mainloop()
