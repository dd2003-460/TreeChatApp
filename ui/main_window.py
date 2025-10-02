try:
    import customtkinter as ctk
    from customtkinter import CTkFrame, CTkButton, CTkLabel, CTkTextbox, CTkPanedWindow
    # 注意：CustomTkinter没有CTkMenu组件，使用标准tkinter的Menu
    from tkinter import Menu as CTkMenu
    USE_CUSTOMTKINTER = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, simpledialog, filedialog, messagebox, Menu
    ctk = tk
    CTkFrame = tk.Frame
    CTkButton = tk.Button
    CTkLabel = tk.Label
    CTkTextbox = tk.Text
    CTkMenu = Menu
    CTkPanedWindow = ttk.PanedWindow
    USE_CUSTOMTKINTER = False

import configparser
import os, json, time
import logging
try:
    from appdirs import user_data_dir
    USE_APPDIRS = True
except ImportError:
    USE_APPDIRS = False

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from core.tree import Tree, TreeNode
from core.ai_model import AIModel
from config.shortcuts import INPUT_SHORTCUTS, MAIN_SHORTCUTS, CHAT_SHORTCUTS

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("TreeChat")
        self.root.geometry("2400x2000")  # 设置窗口大小
        
        # 添加字体和样式设置
        self.font = ('Microsoft YaHei UI', 15)
        
        # 先加载配置文件和基础设置
        # ------------------------ 顶部菜单栏 ------------------------
        menubar = tk.Menu(self.root, font=('Microsoft YaHei UI', 15))
        file_menu = tk.Menu(menubar, tearoff=0, font=('Microsoft YaHei UI', 15))
        file_menu.add_command(label="新建聊天", command=self.new_chat_record)
        file_menu.add_command(label="打开历史聊天记录", command=self.open_chat_records)
        file_menu.add_command(label="保存聊天记录", command=self.save_chat_records)
        file_menu.add_command(label="另存为", command=self.save_chat_records_as)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)

        # 设置按钮字体大小，默认为20
        settings_button_font = (self.font[0], 20) if hasattr(self, 'font') else ('Microsoft YaHei UI', 20)
        
        if USE_CUSTOMTKINTER:
            self.settings_button = ctk.CTkButton(self.root, text="设置", command=self.open_settings_dialog, 
                                                corner_radius=10, fg_color="#3B8ED0", hover_color="#3671A2",
                                                font=settings_button_font)
        else:
            self.settings_button = tk.Button(self.root, text="设置", command=self.open_settings_dialog, font=settings_button_font)
        self.settings_button.pack(anchor="nw", padx=5, pady=5)

        # 获取配置文件路径
        if USE_APPDIRS:
            # 使用用户数据目录存储配置
            app_data_dir = user_data_dir("TreeChat", "TreeChat")
            config_path = os.path.join(app_data_dir, "settings.ini")
            # 确保目录存在
            os.makedirs(app_data_dir, exist_ok=True)
            # 如果用户数据目录中没有配置文件，从程序目录复制
            if not os.path.exists(config_path):
                try:
                    # 尝试从程序目录复制配置文件
                    default_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.ini")
                    if os.path.exists(default_config_path):
                        import shutil
                        shutil.copy2(default_config_path, config_path)
                except Exception as e:
                    logger.warning(f"无法复制默认配置文件: {e}")
        else:
            # 使用程序目录中的配置文件
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.ini")
        
        logger.info(f"配置文件路径: {config_path}")
        
        # 加载配置文件，指定编码为 utf-8 避免 UnicodeDecodeError
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")
        try:
            self.auto_switch = config.getboolean('设置', 'auto_switch_to_new_node')
        except Exception:
            self.auto_switch = True
        try:
            self.auto_save = config.getboolean('设置', 'auto_save_chat')
        except Exception:
            self.auto_save = False
        try:
            self.records_folder = config.get('设置', 'records_folder')
        except Exception:
            # 使用用户数据目录存储记录
            if USE_APPDIRS:
                self.records_folder = os.path.join(user_data_dir("TreeChat", "TreeChat"), "records")
            else:
                self.records_folder = "records"
        try:
            self.show_jump_alert = config.getboolean('设置', 'show_jump_alert')
        except Exception:
            self.show_jump_alert = True
        try:
            self.show_save_alert = config.getboolean('设置', 'show_save_alert')
        except Exception:
            self.show_save_alert = True
        try:
            self.clear_on_jump = config.getboolean('设置', 'clear_on_jump')
        except Exception:
            self.clear_on_jump = True
        try:
            self.send_shortcut = config.get('设置', 'send_shortcut')
        except Exception:
            self.send_shortcut = "Control-Enter"
        try:
            self.save_shortcut = config.get('设置', 'save_shortcut')
        except Exception:
            self.save_shortcut = "Control-s"
        try:
            self.new_chat_shortcut = config.get('设置', 'new_chat_shortcut')
        except Exception:
            self.new_chat_shortcut = "Control-n"
        try:
            self.open_shortcut = config.get('设置', 'open_shortcut')
        except Exception:
            self.open_shortcut = "Control-o"
        # 尝试从配置文件加载字体设置
        try:
            chat_font_str = config.get('设置', 'chat_font')
            font_parts = chat_font_str.split(',')
            self.chat_font = (font_parts[0], int(font_parts[1]))
        except Exception:
            self.chat_font = ('Microsoft YaHei UI', 10)
        try:
            input_font_str = config.get('设置', 'input_font')
            font_parts = input_font_str.split(',')
            self.input_font = (font_parts[0], int(font_parts[1]))
        except Exception:
            self.input_font = ('Microsoft YaHei UI', 10)
        try:
            self.button_font_size = config.getint('设置', 'button_font_size')
        except Exception:
            self.button_font_size = 10  # 默认按钮字体大小
        try:
            self.button_size = config.getint('设置', 'button_size')
        except Exception:
            self.button_size = 80  # 默认按钮大小
        try:
            self.global_font_size = config.getint('设置', 'global_font_size')
        except Exception:
            self.global_font_size = 10  # 默认全局字体大小

        # 确保记录文件夹存在
        try:
            if not os.path.exists(self.records_folder):
                os.makedirs(self.records_folder)
                logger.info(f"创建记录文件夹: {self.records_folder}")
        except Exception as e:
            logger.error(f"创建记录文件夹失败: {e}")
            # 如果无法创建用户数据目录，回退到程序目录
            self.records_folder = "records"
            if not os.path.exists(self.records_folder):
                os.makedirs(self.records_folder)

        # 初始化节点树和 AI 模型
        self.tree = Tree()
        self.ai_model = AIModel()
        
        # 现在可以安全地设置样式和加载AI模型设置了
        self.setup_styles()
        self.load_ai_model_settings()
        
        # 创建水平分隔的 PanedWindow
        if USE_CUSTOMTKINTER:
            self.paned_window = ctk.CTkPanedWindow(self.root, orientation="horizontal")
        else:
            self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True)

        # 左侧区域：节点树显示
        if USE_CUSTOMTKINTER:
            self.tree_frame = ctk.CTkFrame(self.paned_window, width=200, corner_radius=10)
        else:
            self.tree_frame = ttk.Frame(self.paned_window, width=200)
        self.paned_window.add(self.tree_frame, weight=1)

        # 右侧区域：聊天区域
        if USE_CUSTOMTKINTER:
            self.chat_frame = ctk.CTkFrame(self.paned_window, corner_radius=10)
        else:
            self.chat_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.chat_frame, weight=3)

        # 构造左侧树形组件
        self.tree_display = ttk.Treeview(self.tree_frame)
        self.tree_display.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_display.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree_display.bind("<Button-3>", self.show_menu)

        # 右键菜单（针对树形节点）：添加子节点、删除节点、修改节点名称、查看主题
        self.menu = tk.Menu(self.root, tearoff=0, font=('Microsoft YaHei UI', 10))
        self.menu.add_command(label="添加子节点", command=self.add_child_node)
        self.menu.add_command(label="删除节点", command=self.delete_node)
        self.menu.add_command(label="修改节点名称", command=self.modify_node_name)
        self.menu.add_command(label="查看主题", command=self.show_topic)

        # 构造右侧聊天记录组件
        if USE_CUSTOMTKINTER:
            self.output_text = ctk.CTkTextbox(self.chat_frame, height=15, font=self.chat_font, wrap="word")
        else:
            self.output_text = scrolledtext.ScrolledText(self.chat_frame, height=15, font=self.chat_font)
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.output_text.bind("<Button-3>", self.show_chat_menu)
        self.chat_menu = tk.Menu(self.root, tearoff=0)
        self.chat_menu.add_command(label="从选中内容创建子节点", command=self.create_node_from_selection)

        # 构造聊天输入区：标签、输入框、发送按钮、保存记录按钮
        if USE_CUSTOMTKINTER:
            self.input_frame = ctk.CTkFrame(self.chat_frame, corner_radius=10)
        else:
            self.input_frame = tk.Frame(self.chat_frame)
        self.input_frame.pack(fill="x", padx=10, pady=10)
        
        if USE_CUSTOMTKINTER:
            self.input_label = ctk.CTkLabel(self.input_frame, text="输入:", font=self.input_font)
        else:
            self.input_label = tk.Label(self.input_frame, text="输入:", font=self.input_font)
        self.input_label.pack(side="left", padx=(10, 5), pady=10)
        
        if USE_CUSTOMTKINTER:
            self.input_text = ctk.CTkTextbox(self.input_frame, font=self.input_font, height=100, wrap="word")
        else:
            self.input_text = tk.Text(self.input_frame, font=self.input_font, height=3, wrap=tk.WORD)
        self.input_text.pack(side="left", fill="x", expand=True, padx=5, pady=10)
        
        # 创建按钮框架（仅在CustomTkinter中使用）
        if USE_CUSTOMTKINTER:
            self.button_frame = ctk.CTkFrame(self.input_frame, width=100, corner_radius=10)
            self.button_frame.pack(side="right", padx=10, pady=10, fill="y")
            self.send_button = ctk.CTkButton(self.button_frame, text="发送", command=self.send_message, font=self.input_font, width=80,
                                           corner_radius=10, fg_color="#3B8ED0", hover_color="#3671A2")
            self.send_button.pack(side="top", pady=(0, 5))
            self.save_button = ctk.CTkButton(self.button_frame, text="保存记录", command=self.save_chat_records, font=self.input_font, width=80,
                                           corner_radius=10, fg_color="#3B8ED0", hover_color="#3671A2")
            self.save_button.pack(side="top")
        else:
            self.send_button = tk.Button(self.input_frame, text="发送", command=self.send_message, font=self.input_font)
            self.send_button.pack(side="left", padx=5, pady=10)
            self.save_button = tk.Button(self.input_frame, text="保存记录", command=self.save_chat_records, font=self.input_font)
            self.save_button.pack(side="left", padx=5, pady=10)

        # 绑定快捷键
        self.root.bind(INPUT_SHORTCUTS['send_message'], self.send_message)  # 发送消息
        self.root.bind(MAIN_SHORTCUTS['save_chat'], lambda e: self.save_chat_records())  # 保存聊天记录
        self.root.bind(MAIN_SHORTCUTS['new_chat'], lambda e: self.new_chat_record())  # 新建聊天
        self.root.bind(MAIN_SHORTCUTS['open_chat'], lambda e: self.open_chat_records())  # 打开聊天记录
        self.root.bind(MAIN_SHORTCUTS['open_settings'], lambda event: self.open_settings_dialog())  # 打开设置
        
        # 绑定输入框的快捷键
        self.input_text.bind(INPUT_SHORTCUTS['line_break'], self.insert_line_break)  # Shift+Enter换行
        self.input_text.bind(INPUT_SHORTCUTS['select_all'], self.select_all_input)  # Ctrl+A全选
        # 启用输入框的标准键盘快捷键
        self.input_text.bind("<Control-z>", lambda event: self.input_text.edit_undo())  # Ctrl+Z撤销
        self.input_text.bind("<Control-y>", lambda event: self.input_text.edit_redo())  # Ctrl+Y重做
        self.input_text.bind("<Control-x>", lambda event: self.input_text.event_generate("<<Cut>>"))  # Ctrl+X剪切
        self.input_text.bind("<Control-c>", lambda event: self.input_text.event_generate("<<Copy>>"))  # Ctrl+C复制
        self.input_text.bind("<Control-v>", lambda event: self.input_text.event_generate("<<Paste>>"))  # Ctrl+V粘贴
        # 修复Shift+方向键选择文本的问题
        self.input_text.bind("<Shift-Left>", self.handle_shift_left)
        self.input_text.bind("<Shift-Right>", self.handle_shift_right)
        self.input_text.bind("<Shift-Up>", self.handle_shift_up)
        self.input_text.bind("<Shift-Down>", self.handle_shift_down)
        
        # 移除下面这行代码，它导致了NameError错误
        # dialog.bind("<Control-s>", lambda event: save_settings())
        
        # 更新树形显示及加载当前节点聊天记录
        self.update_tree_display()
        self.load_current_node_chats()

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("600x500")
        dialog.minsize(500, 400)  # 设置最小尺寸
        dialog.resizable(True, True)  # 允许调整对话框大小
        
        # 设置对话框字体大小，默认为20
        dialog_font = (self.font[0], 20) if hasattr(self, 'font') else ('Microsoft YaHei UI', 20)
        
        # 添加Ctrl+S快捷键绑定（必须放在dialog定义之后）
        dialog.bind(MAIN_SHORTCUTS['save_chat'], lambda event: self.save_settings())
        
        # 创建标签页控件
        tab_control = ttk.Notebook(dialog)
        
        # 常规设置标签页
        general_tab = ttk.Frame(tab_control)
        tab_control.add(general_tab, text="常规设置")
        
        # AI模型设置标签页
        ai_tab = ttk.Frame(tab_control)
        tab_control.add(ai_tab, text="AI模型设置")
        
        tab_control.pack(expand=1, fill="both")

        # -------------------- 常规设置标签页 --------------------
        # 为常规设置标签页添加滚动条
        general_canvas = tk.Canvas(general_tab)
        general_scrollbar = ttk.Scrollbar(general_tab, orient="vertical", command=general_canvas.yview)
        general_scrollable_frame = ttk.Frame(general_canvas)
        
        general_scrollable_frame.bind(
            "<Configure>",
            lambda e: general_canvas.configure(
                scrollregion=general_canvas.bbox("all")
            )
        )
        
        general_canvas.create_window((0, 0), window=general_scrollable_frame, anchor="nw")
        general_canvas.configure(yscrollcommand=general_scrollbar.set)
        
        # 添加鼠标滚轮支持
        def _on_mousewheel(event):
            general_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        general_canvas.bind("<MouseWheel>", _on_mousewheel)
        general_scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        
        general_canvas.pack(side="left", fill="both", expand=True)
        general_scrollbar.pack(side="right", fill="y")
        
        # 添加字体设置区域
        font_frame = ttk.LabelFrame(general_scrollable_frame, text="字体设置")
        font_frame.pack(fill=tk.BOTH, expand=1, padx=10, pady=5)
        
        # 统一字体大小设置（最高优先级）
        ttk.Label(font_frame, text="统一字体大小 (最高优先级):").pack(anchor='w', padx=10, pady=5)
        global_font_size_var = tk.IntVar(value=self.global_font_size)
        global_font_size_spinbox = tk.Spinbox(font_frame, from_=8, to=72, textvariable=global_font_size_var, width=10)
        global_font_size_spinbox.pack(anchor='w', padx=10, pady=5)
        
        # 聊天区域字体设置
        ttk.Label(font_frame, text="聊天区域字体:").pack(anchor='w', padx=10, pady=5)
        chat_font_var = tk.StringVar(value=self.chat_font[0])
        ttk.Entry(font_frame, textvariable=chat_font_var).pack(anchor='w', padx=10, pady=5)
        
        # 聊天区域字体大小设置
        ttk.Label(font_frame, text="聊天区域字体大小:").pack(anchor='w', padx=10, pady=5)
        chat_font_size_var = tk.IntVar(value=self.chat_font[1])
        chat_font_size_spinbox = tk.Spinbox(font_frame, from_=8, to=72, textvariable=chat_font_size_var, width=10)
        chat_font_size_spinbox.pack(anchor='w', padx=10, pady=5)
        
        # 输入框字体设置
        ttk.Label(font_frame, text="输入框字体:").pack(anchor='w', padx=10, pady=5)
        input_font_var = tk.StringVar(value=self.input_font[0])
        ttk.Entry(font_frame, textvariable=input_font_var).pack(anchor='w', padx=10, pady=5)
        
        # 输入框字体大小设置
        ttk.Label(font_frame, text="输入框字体大小:").pack(anchor='w', padx=10, pady=5)
        input_font_size_var = tk.IntVar(value=self.input_font[1])
        input_font_size_spinbox = tk.Spinbox(font_frame, from_=8, to=72, textvariable=input_font_size_var, width=10)
        input_font_size_spinbox.pack(anchor='w', padx=10, pady=5)
        
        # 按钮字体大小设置
        ttk.Label(font_frame, text="按钮字体大小:").pack(anchor='w', padx=10, pady=5)
        button_font_size_var = tk.IntVar(value=self.button_font_size)
        button_font_size_spinbox = tk.Spinbox(font_frame, from_=8, to=72, textvariable=button_font_size_var, width=10)
        button_font_size_spinbox.pack(anchor='w', padx=10, pady=5)
        
        # 按钮大小设置
        ttk.Label(font_frame, text="按钮大小:").pack(anchor='w', padx=10, pady=5)
        button_size_var = tk.IntVar(value=self.button_size)  # 默认按钮宽度
        button_size_scale = ttk.Scale(font_frame, from_=50, to=200, variable=button_size_var, orient=tk.HORIZONTAL)
        button_size_scale.pack(anchor='w', padx=10, pady=5, fill=tk.X)
        button_size_label = ttk.Label(font_frame, textvariable=button_size_var)
        button_size_label.pack(anchor='w', padx=10, pady=5)
        
        # 界面缩放比例设置
        ttk.Label(font_frame, text="界面缩放比例:").pack(anchor='w', padx=10, pady=5)
        scale_var = tk.DoubleVar(value=1.0)
        scale_spinbox = tk.Spinbox(font_frame, from_=0.5, to=2.0, increment=0.1, textvariable=scale_var, width=10)
        scale_spinbox.pack(anchor='w', padx=10, pady=5)
        
        # 自动跳转设置
        auto_switch_var = tk.BooleanVar(value=self.auto_switch)
        cb_auto_switch = tk.Checkbutton(general_tab, text="自动切换到新节点", variable=auto_switch_var)
        cb_auto_switch.pack(anchor='w', padx=10, pady=5)

        # 自动保存设置
        auto_save_var = tk.BooleanVar(value=self.auto_save)
        cb_auto_save = tk.Checkbutton(general_tab, text="自动保存聊天记录", variable=auto_save_var)
        cb_auto_save.pack(anchor='w', padx=10, pady=5)

        # 提示跳转设置
        show_jump_var = tk.BooleanVar(value=self.show_jump_alert)
        cb_show_jump = tk.Checkbutton(general_tab, text="提示跳转新节点", variable=show_jump_var)
        cb_show_jump.pack(anchor='w', padx=10, pady=5)

        # 提示保存设置
        show_save_var = tk.BooleanVar(value=self.show_save_alert)
        cb_show_save = tk.Checkbutton(general_tab, text="提示保存记录", variable=show_save_var)
        cb_show_save.pack(anchor='w', padx=10, pady=5)

        # 清空提示设置
        clear_on_jump_var = tk.BooleanVar(value=self.clear_on_jump)
        cb_clear_on_jump = tk.Checkbutton(general_tab, text="跳转时清空之前提示", variable=clear_on_jump_var)
        cb_clear_on_jump.pack(anchor='w', padx=10, pady=5)

        # -------------------- AI模型设置标签页 --------------------
        # 为AI模型设置标签页添加滚动条
        ai_canvas = tk.Canvas(ai_tab)
        ai_scrollbar = ttk.Scrollbar(ai_tab, orient="vertical", command=ai_canvas.yview)
        ai_scrollable_frame = ttk.Frame(ai_canvas)
        
        ai_scrollable_frame.bind(
            "<Configure>",
            lambda e: ai_canvas.configure(
                scrollregion=ai_canvas.bbox("all")
            )
        )
        
        ai_canvas.create_window((0, 0), window=ai_scrollable_frame, anchor="nw")
        ai_canvas.configure(yscrollcommand=ai_scrollbar.set)
        
        # 添加鼠标滚轮支持
        def _on_mousewheel_ai(event):
            ai_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        ai_canvas.bind("<MouseWheel>", _on_mousewheel_ai)
        ai_scrollable_frame.bind("<MouseWheel>", _on_mousewheel_ai)
        
        ai_canvas.pack(side="left", fill="both", expand=True)
        ai_scrollbar.pack(side="right", fill="y")
        
        # 模型选择区域
        model_frame = ttk.LabelFrame(ai_scrollable_frame, text="模型选择")
        model_frame.pack(fill=tk.BOTH, expand=1, padx=10, pady=5)
        
        # Ollama服务地址设置
        url_frame = ttk.LabelFrame(ai_scrollable_frame, text="Ollama服务设置")
        url_frame.pack(fill=tk.BOTH, expand=1, padx=10, pady=5)
        
        # 服务地址输入框 - 确保使用正确的base_url属性
        ttk.Label(url_frame, text="Ollama服务地址:").pack(anchor='w', padx=10, pady=5)
        # 修复错误：使用正确的base_url属性而不是不存在的ollama_url
        url_var = tk.StringVar(value=self.ai_model.base_url)
        url_entry = ttk.Entry(url_frame, textvariable=url_var, width=50)
        url_entry.pack(anchor='w', padx=10, pady=5)
        
        def test_connection():
            """测试Ollama服务连接"""
            url = url_var.get()
            if self.ai_model.set_base_url(url):
                messagebox.showinfo("连接成功", f"成功连接到Ollama服务: {url}")
                # 刷新模型列表
                refresh_models()
            else:
                messagebox.showerror("连接失败", f"无法连接到Ollama服务: {url}\n请检查服务是否已启动或地址是否正确")
        
        # 测试连接按钮
        test_button = ttk.Button(url_frame, text="测试连接", command=test_connection)
        test_button.pack(anchor='w', padx=10, pady=5)
        
        # 可用模型列表
        ttk.Label(model_frame, text="可用模型:").pack(anchor='w', padx=10, pady=5)
        
        # 加载可用模型
        available_models = self.ai_model.get_available_models()
        if not available_models:
            ttk.Label(model_frame, text="未找到可用模型，请确保Ollama服务已启动").pack(anchor='w', padx=10, pady=5)
            # 创建一个空的模型列表
            available_models = []
        
        # 创建模型选择下拉框
        model_var = tk.StringVar(value=self.ai_model.model)
        model_combobox = ttk.Combobox(model_frame, textvariable=model_var, values=available_models, state="readonly", width=30)
        model_combobox.pack(anchor='w', padx=10, pady=5)
        
        # 修改刷新模型按钮的实现
        def refresh_models():
            success = self.ai_model.load_available_models()
            available_models = self.ai_model.get_available_models()
            if available_models:
                model_combobox['values'] = available_models
                # 如果当前选择的模型不在列表中，设置为第一个模型
                if model_var.get() not in available_models:
                    model_var.set(available_models[0])
                messagebox.showinfo("刷新成功", f"已成功刷新模型列表，找到 {len(available_models)} 个模型")
            else:
                messagebox.showwarning("刷新失败", "未找到可用模型，请确保Ollama服务已启动")
        
        # 添加手动添加模型的功能
        add_model_frame = ttk.Frame(model_frame)
        add_model_frame.pack(fill=tk.X, padx=10, pady=5)
        
        add_model_var = tk.StringVar()
        add_model_entry = ttk.Entry(add_model_frame, textvariable=add_model_var, width=25)
        add_model_entry.pack(side=tk.LEFT, padx=5, pady=5)
        
        def add_model_manually():
            model_name = add_model_var.get().strip()
            if model_name:
                if self.ai_model.add_model_manually(model_name):
                    messagebox.showinfo("添加成功", f"已成功添加模型: {model_name}")
                    # 刷新下拉列表
                    available_models = self.ai_model.get_available_models()
                    model_combobox['values'] = available_models
                    # 如果当前没有选择模型或选择的模型不在列表中，设置为新添加的模型
                    if not model_var.get() or model_var.get() not in available_models:
                        model_var.set(model_name)
                else:
                    messagebox.showerror("添加失败", f"无法添加模型: {model_name}\n请检查模型名称是否正确或Ollama服务是否正常运行")
            else:
                messagebox.showwarning("输入错误", "请输入模型名称")
        
        add_model_button = ttk.Button(add_model_frame, text="手动添加模型", command=add_model_manually)
        add_model_button.pack(side=tk.LEFT, padx=5, pady=5)

        refresh_button = ttk.Button(model_frame, text="刷新模型列表", command=refresh_models)
        refresh_button.pack(anchor='w', padx=10, pady=5)
        
        # 添加导入Ollama模型列表的功能说明
        import_info_label = ttk.Label(model_frame, text="提示：可以通过命令行运行 'ollama list' 查看可用模型，然后手动添加到列表中", wraplength=400)
        import_info_label.pack(anchor='w', padx=10, pady=5)

        # 保存设置按钮 - 完整的保存功能实现
        def save_settings():
            self.auto_switch = auto_switch_var.get()
            self.auto_save = auto_save_var.get()
            self.show_jump_alert = show_jump_var.get()
            self.show_save_alert = show_save_var.get()
            self.clear_on_jump = clear_on_jump_var.get()
            
            # 更新字体设置
            # 如果设置了统一字体大小，则使用统一设置
            global_font_size = global_font_size_var.get()
            if global_font_size > 0:  # 使用统一字体大小
                self.chat_font = (chat_font_var.get(), global_font_size)
                self.input_font = (input_font_var.get(), global_font_size)
                button_font_size = global_font_size
            else:  # 使用各自独立的字体大小
                self.chat_font = (chat_font_var.get(), chat_font_size_var.get())
                self.input_font = (input_font_var.get(), input_font_size_var.get())
                button_font_size = button_font_size_var.get()

            # 获取配置文件路径
            if USE_APPDIRS:
                app_data_dir = user_data_dir("TreeChat", "TreeChat")
                config_path = os.path.join(app_data_dir, "settings.ini")
                os.makedirs(app_data_dir, exist_ok=True)
            else:
                config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.ini")
            
            logger.info(f"保存配置到: {config_path}")

            config = configparser.ConfigParser()
            # 读取现有配置（如果存在）
            config.read(config_path, encoding="utf-8")
            if not config.has_section('设置'):
                config.add_section('设置')
            config.set('设置', 'auto_switch_to_new_node', str(self.auto_switch))
            config.set('设置', 'auto_save_chat', str(self.auto_save))
            config.set('设置', 'show_jump_alert', str(self.show_jump_alert))
            config.set('设置', 'show_save_alert', str(self.show_save_alert))
            config.set('设置', 'clear_on_jump', str(self.clear_on_jump))
            
            # 保存字体设置
            config.set('设置', 'chat_font', f"{self.chat_font[0]},{self.chat_font[1]}")
            config.set('设置', 'input_font', f"{self.input_font[0]},{self.input_font[1]}")
            
            # 保存字体大小设置
            config.set('设置', 'chat_font_size', str(self.chat_font[1]))
            config.set('设置', 'input_font_size', str(self.input_font[1]))
            config.set('设置', 'button_font_size', str(button_font_size))
            config.set('设置', 'button_size', str(button_size_var.get()))
            config.set('设置', 'global_font_size', str(global_font_size))
            
            # 保存界面缩放比例
            config.set('设置', 'scale_factor', str(scale_var.get()))

            # 保存AI模型设置
            try:
                selected_model = model_var.get()
                if selected_model:  # 确保模型名称不为空
                    config.set('设置', 'ai_model', selected_model)
                    if hasattr(self, 'ai_model'):
                        self.ai_model.set_model(selected_model)
                # 保存手动添加的模型列表
                manual_models = [model for model in self.ai_model.get_available_models() if model != selected_model]
                if manual_models:
                    config.set('设置', 'manual_models', ','.join(manual_models))
                else:
                    config.set('设置', 'manual_models', '')
            except Exception as e:
                logger.error(f"保存AI模型设置失败: {e}")
                print(f"保存AI模型设置失败: {e}")

            # 保存Ollama服务地址
            config.set('设置', 'ollama_base_url', url_var.get())

            try:
                with open(config_path, "w", encoding="utf-8") as configfile:
                    config.write(configfile)
                logger.info("配置已成功保存")
                messagebox.showinfo("设置已保存", "所有设置已成功保存")
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
                messagebox.showerror("保存失败", f"无法保存设置: {e}\n请检查程序是否有写入权限。")

            # 应用字体设置
            self.output_text.config(font=self.chat_font)
            self.input_label.config(font=self.input_font)
            self.input_text.config(font=self.input_font)
            # 应用按钮字体和大小设置
            button_font = (self.input_font[0], button_font_size)
            button_width = button_size_var.get()
            if USE_CUSTOMTKINTER:
                self.send_button.configure(font=button_font, width=button_width)
                self.save_button.configure(font=button_font, width=button_width)
                # 更新设置按钮字体
                self.settings_button.configure(font=(self.input_font[0], button_font_size))
            else:
                self.send_button.config(font=button_font, width=button_width//8)  # Tkinter按钮宽度单位不同
                self.save_button.config(font=button_font, width=button_width//8)
                # 更新设置按钮字体
                self.settings_button.config(font=(self.input_font[0], button_font_size))
            
            # 应用界面缩放
            scale_factor = scale_var.get()
            self.root.geometry(f"{int(1200*scale_factor)}x{int(800*scale_factor)}")

        # 将save_settings方法保存为实例方法，以便外部调用
        self.save_settings = save_settings

        # 创建按钮容器并将其放置在对话框底部
        button_frame = ttk.Frame(dialog)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        
        # 添加关闭按钮
        close_button = ttk.Button(button_frame, text="关闭", command=dialog.destroy)
        close_button.pack(side=tk.RIGHT, padx=5)
        
        # 创建保存设置按钮并放置在容器中
        save_button = ttk.Button(button_frame, text="保存设置", command=save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)

    def send_message(self, event=None):
        """
        处理发送消息事件：
         - 如果输入以 "新主题:" 开头，则自动在当前节点下创建新节点，并根据设置自动切换及保存；
         - 否则视为普通聊天消息，发送后调用 AI 模型回复并保存记录。
        """
        input_text = self.input_text.get("1.0", tk.END).strip()
        self.input_text.delete("1.0", tk.END)
        if input_text.startswith("新主题:"):
            topic = input_text[len("新主题:"):].strip()
            self.tree.add_topic(topic)
            sys_msg = f"系统: 已创建新主题 '{topic}'，并切换当前聊天上下文。\n"
            self.output_text.insert(tk.END, sys_msg)
            self.tree.get_current_node().chats.append(sys_msg)
            if self.auto_switch:
                self.load_current_node_chats()
            if self.auto_save:
                self.save_chat_records()
        else:
            user_msg = f"你: {input_text}\n"
            self.output_text.insert(tk.END, user_msg)
            self.tree.get_current_node().chats.append(user_msg)

            # 显示正在思考的提示
            thinking_msg = "AI: 正在思考...\n"
            self.output_text.insert(tk.END, thinking_msg)
            self.output_text.see(tk.END)
            self.root.update_idletasks()

            # 调用AI模型生成回复
            ai_reply = self.ai_model.generate_response(input_text)

            # 删除正在思考的提示并插入实际回复
            self.output_text.delete("end-2l", tk.END)
            reply_msg = f"AI: {ai_reply}\n"
            self.output_text.insert(tk.END, reply_msg)
            self.tree.get_current_node().chats.append(reply_msg)

            if self.auto_save:
                self.save_chat_records()

        return 'break'  # 防止事件继续传播

    def insert_line_break(self, event=None):
        """
        在输入框中插入换行符
        """
        # 获取当前光标位置
        cursor_pos = self.input_text.index(tk.INSERT)
        # 在光标位置插入换行符
        self.input_text.insert(cursor_pos, "\n")
        # 移动光标到新插入的换行符之后
        self.input_text.mark_set(tk.INSERT, f"{cursor_pos}+1c")
        return 'break'  # 防止事件继续传播

    def select_all_input(self, event=None):
        """
        全选输入框中的文本
        """
        self.input_text.tag_add(tk.SEL, "1.0", tk.END)
        return 'break'  # 防止事件继续传播

    def handle_shift_left(self, event=None):
        """
        处理Shift+Left键事件
        """
        self.input_text.event_generate("<Shift-Left>")
        return 'break'

    def handle_shift_right(self, event=None):
        """
        处理Shift+Right键事件
        """
        self.input_text.event_generate("<Shift-Right>")
        return 'break'

    def handle_shift_up(self, event=None):
        """
        处理Shift+Up键事件
        """
        self.input_text.event_generate("<Shift-Up>")
        return 'break'

    def handle_shift_down(self, event=None):
        """
        处理Shift+Down键事件
        """
        self.input_text.event_generate("<Shift-Down>")
        return 'break'

    def update_tree_display(self):
        """
        更新左侧树形节点显示，将所有节点重新插入到 Treeview 中
        """
        for item in self.tree_display.get_children():
            self.tree_display.delete(item)
        self.insert_node(self.tree.root)

    def insert_node(self, node, parent=""):
        """
        递归地将节点插入到 Treeview 中
        参数:
            node   - 当前的 TreeNode 对象
            parent - 父节点在 Treeview 中的 ID（采用节点的 id 作为唯一标识）
        """
        self.tree_display.insert(parent, "end", iid=node.id, text=node.topic, open=True)
        for child in node.children:
            self.insert_node(child, node.id)

    def show_menu(self, event):
        """
        右键点击树形节点显示操作菜单。
        """
        item = self.tree_display.identify_row(event.y)
        if item:
            self.tree_display.selection_set(item)
            self.menu.post(event.x_root, event.y_root)

    def add_child_node(self):
        """
        为选中节点添加一个默认主题为 "新主题" 的子节点，并更新显示。
        """
        selected_items = self.tree_display.selection()
        if selected_items:
            selected_item = selected_items[0]
            parent_node = self.get_node_by_item_id(selected_item, self.tree.root)
            if parent_node:
                new_node = TreeNode("新主题")
                parent_node.add_child(new_node)
                sys_msg = f"系统: 在 '{parent_node.topic}' 下添加了子节点 '新主题'。\n"
                parent_node.chats.append(sys_msg)
                self.update_tree_display()
                if self.auto_save:
                    self.save_chat_records()
        else:
            self.output_text.insert(tk.END, "系统: 请先选择一个节点！\n")

    def delete_node(self):
        """
        删除选中节点（根节点不可删除），并更新显示和保存操作。
        """
        selected_items = self.tree_display.selection()
        if selected_items:
            selected_item = selected_items[0]
            parent_item = self.tree_display.parent(selected_item)
            if parent_item:
                parent_node = self.get_node_by_item_id(parent_item, self.tree.root)
                node_to_delete = self.get_node_by_item_id(selected_item, self.tree.root)
                if parent_node and node_to_delete:
                    parent_node.delete_child(node_to_delete)
                    sys_msg = f"系统: 已删除节点 '{node_to_delete.topic}'。\n"
                    parent_node.chats.append(sys_msg)
                    self.update_tree_display()
                    if self.auto_save:
                        self.save_chat_records()
            else:
                self.output_text.insert(tk.END, "系统: 根节点不可删除！\n")
        else:
            self.output_text.insert(tk.END, "系统: 请先选择一个节点！\n")

    def modify_node_name(self):
        """
        修改选中节点的名称，并更新显示和保存动作。
        """
        selected_items = self.tree_display.selection()
        if selected_items:
            selected_item = selected_items[0]
            node = self.get_node_by_item_id(selected_item, self.tree.root)
            if node:
                new_name = simpledialog.askstring("修改节点名称", "请输入新的节点名称：", initialvalue=node.topic)
                if new_name and new_name.strip():
                    node.topic = new_name.strip()
                    sys_msg = f"系统: 节点名称已修改为 '{node.topic}'。\n"
                    node.chats.append(sys_msg)
                    self.update_tree_display()
                    if self.auto_save:
                        self.save_chat_records()
        else:
            self.output_text.insert(tk.END, "系统: 请先选择一个节点进行修改！\n")

    def show_topic(self):
        """
        在聊天记录区域显示所选节点的主题信息。
        """
        selected_items = self.tree_display.selection()
        if selected_items:
            selected_item = selected_items[0]
            node = self.get_node_by_item_id(selected_item, self.tree.root)
            if node:
                sys_msg = f"系统: 当前主题为 '{node.topic}'。\n"
                self.output_text.insert(tk.END, sys_msg)

    def get_node_by_item_id(self, item_id, current_node):
        """
        根据 Treeview 的 item_id 递归查找对应的 TreeNode 对象。
        
        参数:
            item_id     - 节点的唯一 ID。
            current_node - 当前遍历的 TreeNode 对象。
        
        返回:
            找到的 TreeNode 对象，否则返回 None。
        """
        if current_node.id == item_id:
            return current_node
        for child in current_node.children:
            found_node = self.get_node_by_item_id(item_id, child)
            if found_node:
                return found_node
        return None

    def show_chat_menu(self, event):
        """
        右键点击聊天记录区域显示菜单，支持从选中内容创建子节点。
        """
        self.chat_menu.post(event.x_root, event.y_root)

    def create_node_from_selection(self):
        """
        从聊天记录中选中部分创建新节点，并根据设置自动切换及保存。
        """
        try:
            selected_text = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
        except tk.TclError:
            self.output_text.insert(tk.END, "系统: 没有选中的文本！\n")
            return
        if not selected_text:
            self.output_text.insert(tk.END, "系统: 选中的文本为空！\n")
            return
        selected_tree_items = self.tree_display.selection()
        if selected_tree_items:
            parent_item = selected_tree_items[0]
            parent_node = self.get_node_by_item_id(parent_item, self.tree.root)
        else:
            parent_node = self.tree.root
        new_node = TreeNode(selected_text)
        parent_node.add_child(new_node)
        sys_msg = f"系统: 从聊天文本创建了新节点 '{selected_text}' 在 '{parent_node.topic}' 下。\n"
        parent_node.chats.append(sys_msg)
        self.update_tree_display()
        if self.auto_switch:
            self.tree.set_current_node(new_node)
            self.load_current_node_chats()
        if self.auto_save:
            self.save_chat_records()

    def load_current_node_chats(self):
        """
        加载当前节点的聊天记录。
        若设置 clear_on_jump 为 True，则先清空显示区域，并根据 show_jump_alert 在顶端提示当前节点名称。
        """
        if self.clear_on_jump:
            self.output_text.delete("1.0", tk.END)
            if self.show_jump_alert:
                self.output_text.insert(tk.END, f"系统: 当前节点为 '{self.tree.get_current_node().topic}'\n")
        current_chats = self.tree.get_current_node().chats
        if current_chats:
            self.output_text.insert(tk.END, "".join(current_chats))
        else:
            self.output_text.insert(tk.END, "系统: 当前节点暂无聊天记录。\n")

    def serialize_node(self, node):
        """
        序列化树节点为字典格式
        """
        return {
            'id': node.id,
            'topic': node.topic,
            'chats': node.chats,
            'children': [self.serialize_node(child) for child in node.children]
        }

    def save_chat_records(self):
        """
        将整个树状聊天记录（包括节点结构及所有节点聊天内容）序列化为 JSON，
        固定保存在"chat_all_records.json"文件中，存放于默认记录文件夹内。
        若 show_save_alert 开启，则在聊天区域提示保存成功。
        """
        tree_dict = self.serialize_node(self.tree.root)
        file_name = "chat_all_records.json"
        file_path = os.path.join(self.records_folder, file_name)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tree_dict, f, ensure_ascii=False, indent=4)
            if self.show_save_alert:
                self.output_text.insert(tk.END, f"系统: 聊天记录已保存至 {file_path}\n")
        except Exception as e:
            self.output_text.insert(tk.END, f"系统: 保存记录失败：{e}\n")

    def new_chat_record(self):
        """
        新建聊天记录，清空当前聊天内容并创建一个新的树状结构。
        """
        if messagebox.askyesno("新建聊天", "确定要开始新的聊天记录吗？这将清除当前所有记录！"):
            self.tree = Tree()
            self.update_tree_display()
            self.load_current_node_chats()
            self.output_text.insert(tk.END, "系统: 新建聊天记录成功。\n")

    def open_chat_records(self):
        """
        打开历史聊天记录文件，原模原样还原树状结构和各节点聊天内容。
        """
        file_path = filedialog.askopenfilename(title="打开历史聊天记录", filetypes=[("JSON文件", "*.json")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tree.root = self.build_tree_node_from_dict(data)
                self.tree.current_node = self.tree.root
                self.update_tree_display()
                self.load_current_node_chats()
                self.output_text.insert(tk.END, f"系统: 成功打开 {file_path}\n")
            except Exception as e:
                self.output_text.insert(tk.END, f"系统: 打开文件失败：{e}\n")

    def save_chat_records_as(self):
        """
        另存为：使用文件对话框选择保存位置和文件名，将整个树状聊天记录导出为 JSON 文件。
        """
        file_path = filedialog.asksaveasfilename(title="另存为", defaultextension=".json", filetypes=[("JSON 文件", "*.json")])
        if file_path:
            try:
                tree_dict = self.serialize_node(self.tree.root)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(tree_dict, f, ensure_ascii=False, indent=4)
                self.output_text.insert(tk.END, f"系统: 聊天记录已另存为 {file_path}\n")
            except Exception as e:
                self.output_text.insert(tk.END, f"系统: 另存为失败：{e}\n")

    def build_tree_node_from_dict(self, data):
        """
        递归从字典数据创建 TreeNode 对象，用于打开历史聊天记录时还原树状结构。
        """
        node = TreeNode(data['topic'])
        node.id = data.get('id', node.id)
        node.chats = data.get('chats', [])
        for child_data in data.get('children', []):
            child_node = self.build_tree_node_from_dict(child_data)
            node.children.append(child_node)
        return node

    def on_tree_select(self, event):
        """
        当用户点击树形节点时触发，切换当前节点并加载对应的聊天记录
        """
        selected_items = self.tree_display.selection()
        if selected_items:
            selected_item = selected_items[0]
            node = self.get_node_by_item_id(selected_item, self.tree.root)
            if node:
                self.tree.set_current_node(node)
                self.load_current_node_chats()

    def setup_styles(self):
        # 设置整体字体样式
        self.style = ttk.Style()
        self.style.configure('TButton', font=self.font)
        self.style.configure('Treeview', font=self.font)
        
        # 配置聊天区域样式
        # 在字体设置加载部分之后添加以下代码
        
        # 移除这行代码：
        # self.load_ai_model_settings()

    def load_ai_model_settings(self):
        """从配置文件加载AI模型设置"""
        # 获取配置文件路径
        if USE_APPDIRS:
            # 使用用户数据目录存储配置
            app_data_dir = user_data_dir("TreeChat", "TreeChat")
            config_path = os.path.join(app_data_dir, "settings.ini")
        else:
            # 使用程序目录中的配置文件
            config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "settings.ini")
        
        logger.info(f"加载AI模型设置，配置文件路径: {config_path}")
        
        config = configparser.ConfigParser()
        try:
            config.read(config_path, encoding="utf-8")
            
            # 首先加载服务地址
            if config.has_option('设置', 'ollama_base_url'):
                base_url = config.get('设置', 'ollama_base_url')
                logger.info(f"从配置文件加载Ollama服务地址: {base_url}")
                self.ai_model.set_base_url(base_url)
            
            # 添加启动时测试控制选项
            skip_startup_test = False
            if config.has_option('设置', 'skip_startup_model_test'):
                skip_startup_test = config.getboolean('设置', 'skip_startup_model_test')
            
            # 加载模型设置
            if config.has_option('设置', 'ai_model'):
                model_name = config.get('设置', 'ai_model')
                logger.info(f"从配置文件加载AI模型: {model_name}")
                
                # 先尝试刷新模型列表，但不强制执行测试
                self.ai_model.load_available_models()
                
                # 尝试设置模型
                success = self.ai_model.set_model(model_name)
                if not success:
                    logger.warning(f"无法设置模型 {model_name}，使用默认模型")
                    # 如果失败，直接设置模型名称，让AIModel内部处理
                    self.ai_model.model = model_name
                    # 尝试将模型添加到可用列表
                    if model_name not in self.ai_model.available_models:
                        self.ai_model.available_models.append(model_name)
                        
            # 加载手动添加的模型列表（如果存在）
            if config.has_option('设置', 'manual_models'):
                manual_models_str = config.get('设置', 'manual_models')
                if manual_models_str:
                    manual_models = manual_models_str.split(',')
                    for model in manual_models:
                        model = model.strip()
                        if model and model not in self.ai_model.available_models:
                            self.ai_model.available_models.append(model)
        except Exception as e:
            logger.error(f"加载AI模型设置失败: {str(e)}")
            # 使用默认设置
            self.ai_model.set_model("deepseek-r1:8b  gemma3n:e4b")  # 使用用户实际拥有的模型
            self.ai_model.set_base_url("http://localhost:11434")
            # 使用默认设置
            self.ai_model.set_model("gemma3n:e4b")  # 使用用户实际拥有的模型
            self.ai_model.set_base_url("http://localhost:11434")
