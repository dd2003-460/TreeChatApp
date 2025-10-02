import tkinter as tk

root = tk.Tk()
root.title("测试窗口")
label = tk.Label(root, text="如果能看到这个窗口，说明 Tkinter 正常运行！")
label.pack(padx=20, pady=20)
root.mainloop() 