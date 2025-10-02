try:
    import customtkinter as ctk
    USE_CUSTOMTKINTER = True
except ImportError:
    import tkinter as tk
    ctk = tk
    USE_CUSTOMTKINTER = False

from ui.main_window import MainWindow

if __name__ == "__main__":
    if USE_CUSTOMTKINTER:
        # 设置CustomTkinter外观模式和颜色主题
        ctk.set_appearance_mode("dark")  # 可选: "light", "dark", "system"
        ctk.set_default_color_theme("blue")  # 可选: "blue", "green", "dark-blue"
        root = ctk.CTk()
    else:
        root = tk.Tk()
    
    main_window = MainWindow(root)
    # 移除这行代码：
    # main_window.load_ai_model_settings()
    root.mainloop()
