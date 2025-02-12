import tkinter as tk
from tkinter import scrolledtext, ttk, simpledialog, filedialog, messagebox
import configparser
import os, json, time
from core.tree import Tree, TreeNode
from core.ai_model import AIModel

class MainWindow:
    def __init__(self, root):
        """
        初始化主窗口及其组件，整体界面包含：
        - 顶部菜单栏：文件菜单（新建、打开历史聊天记录、保存、另存为、退出）；
          左上角还有一个"设置"按钮，用于打开设置对话框。
        - 左侧：树形节点（类似文件夹结构）；
        - 右侧：聊天区域（聊天记录显示、输入框、发送按钮、保存记录按钮）。
        
        参数:
            root - Tkinter 根窗口
        """
        self.root = root
        self.root.title("树形聊天应用")

        # ------------------------ 菜单栏 ------------------------
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建聊天", command=self.new_chat_record)
        file_menu.add_command(label="打开历史聊天记录", command=self.open_chat_records)
        file_menu.add_command(label="保存聊天记录", command=self.save_chat_records)
        file_menu.add_command(label="另存为", command=self.save_chat_records_as)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)

        # ------------------------ 顶部设置按钮 ------------------------
        self.settings_button = tk.Button(self.root, text="设置", command=self.open_settings_dialog)
        self.settings_button.pack(anchor="nw", padx=5, pady=5)

        # 加载配置文件，指定编码为 utf-8 避免 UnicodeDecodeError
        config = configparser.ConfigParser()
        config.read(os.path.join("config", "settings.ini"), encoding="utf-8")
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
            self.send_shortcut = "Control-Return"

        # 确保记录文件夹存在
        if not os.path.exists(self.records_folder):
            os.makedirs(self.records_folder)

        # 初始化节点树和 AI 模型
        self.tree = Tree()
        self.ai_model = AIModel()

        # 创建水平分隔的 PanedWindow
        self.paned_window = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # 左侧区域：节点树显示
        self.tree_frame = tk.Frame(self.paned_window, width=200)
        self.paned_window.add(self.tree_frame, minsize=150)

        # 右侧区域：聊天区域
        self.chat_frame = tk.Frame(self.paned_window)
        self.paned_window.add(self.chat_frame, minsize=300)

        # 构造左侧树形组件
        self.tree_display = ttk.Treeview(self.tree_frame)
        self.tree_display.pack(fill=tk.BOTH, expand=1)
        self.tree_display.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree_display.bind("<Button-3>", self.show_menu)

        # 右键菜单（针对树形节点）：添加子节点、删除节点、修改节点名称、查看主题
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="添加子节点", command=self.add_child_node)
        self.menu.add_command(label="删除节点", command=self.delete_node)
        self.menu.add_command(label="修改节点名称", command=self.modify_node_name)
        self.menu.add_command(label="查看主题", command=self.show_topic)

        # 构造右侧聊天记录组件
        self.output_text = scrolledtext.ScrolledText(self.chat_frame, height=15)
        self.output_text.pack(fill=tk.BOTH, expand=1)
        self.output_text.bind("<Button-3>", self.show_chat_menu)
        self.chat_menu = tk.Menu(self.root, tearoff=0)
        self.chat_menu.add_command(label="从选中内容创建子节点", command=self.create_node_from_selection)

        # 构造聊天输入区：标签、输入框、发送按钮、保存记录按钮
        self.input_frame = tk.Frame(self.chat_frame)
        self.input_frame.pack(fill=tk.X)
        self.input_label = tk.Label(self.input_frame, text="输入:")
        self.input_label.pack(side=tk.LEFT)
        self.input_text = tk.Entry(self.input_frame)
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=1)
        self.send_button = tk.Button(self.input_frame, text="发送", command=self.send_message)
        self.send_button.pack(side=tk.LEFT)
        self.save_button = tk.Button(self.input_frame, text="保存记录", command=self.save_chat_records)
        self.save_button.pack(side=tk.LEFT)

        # 绑定快捷键
        self.root.bind(f"<{self.send_shortcut}>", self.send_message)

        # 更新树形显示及加载当前节点聊天记录
        self.update_tree_display()
        self.load_current_node_chats()

    def open_settings_dialog(self):
        """
        弹出设置对话框，将自动跳转、自动保存、提示跳转、提示保存、
        跳转时清空之前提示的开关显示在对话框中。
        用户修改后点击保存，更新配置文件。
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")

        # 自动跳转设置
        auto_switch_var = tk.BooleanVar(value=self.auto_switch)
        cb_auto_switch = tk.Checkbutton(dialog, text="自动切换到新节点", variable=auto_switch_var)
        cb_auto_switch.pack(anchor='w', padx=10, pady=5)

        # 自动保存设置
        auto_save_var = tk.BooleanVar(value=self.auto_save)
        cb_auto_save = tk.Checkbutton(dialog, text="自动保存聊天记录", variable=auto_save_var)
        cb_auto_save.pack(anchor='w', padx=10, pady=5)

        # 提示跳转设置
        show_jump_var = tk.BooleanVar(value=self.show_jump_alert)
        cb_show_jump = tk.Checkbutton(dialog, text="提示跳转新节点", variable=show_jump_var)
        cb_show_jump.pack(anchor='w', padx=10, pady=5)

        # 提示保存设置
        show_save_var = tk.BooleanVar(value=self.show_save_alert)
        cb_show_save = tk.Checkbutton(dialog, text="提示保存记录", variable=show_save_var)
        cb_show_save.pack(anchor='w', padx=10, pady=5)

        # 清空提示设置
        clear_on_jump_var = tk.BooleanVar(value=self.clear_on_jump)
        cb_clear_on_jump = tk.Checkbutton(dialog, text="跳转时清空之前提示", variable=clear_on_jump_var)
        cb_clear_on_jump.pack(anchor='w', padx=10, pady=5)

        # 快捷键设置
        shortcut_label = tk.Label(dialog, text="发送消息快捷键:")
        shortcut_label.pack(anchor='w', padx=10, pady=5)
        shortcut_entry = tk.Entry(dialog)
        shortcut_entry.insert(0, self.send_shortcut)
        shortcut_entry.pack(anchor='w', padx=10, pady=5)

        # 保存设置按钮
        def save_settings():
            self.auto_switch = auto_switch_var.get()
            self.auto_save = auto_save_var.get()
            self.show_jump_alert = show_jump_var.get()
            self.show_save_alert = show_save_var.get()
            self.clear_on_jump = clear_on_jump_var.get()
            self.send_shortcut = shortcut_entry.get()

            config = configparser.ConfigParser()
            config.read(os.path.join("config", "settings.ini"), encoding="utf-8")
            config.set('设置', 'auto_switch_to_new_node', str(self.auto_switch))
            config.set('设置', 'auto_save_chat', str(self.auto_save))
            config.set('设置', 'show_jump_alert', str(self.show_jump_alert))
            config.set('设置', 'show_save_alert', str(self.show_save_alert))
            config.set('设置', 'clear_on_jump', str(self.clear_on_jump))
            config.set('设置', 'send_shortcut', self.send_shortcut)

            with open(os.path.join("config", "settings.ini"), "w", encoding="utf-8") as configfile:
                config.write(configfile)

            self.root.unbind(f"<{self.send_shortcut}>")
            self.root.bind(f"<{self.send_shortcut}>", self.send_message)

            dialog.destroy()

        save_button = tk.Button(dialog, text="保存设置", command=save_settings)
        save_button.pack(pady=10)

    def send_message(self):
        """
        处理发送消息事件：
         - 如果输入以 "新主题:" 开头，则自动在当前节点下创建新节点，并根据设置自动切换及保存；
         - 否则视为普通聊天消息，发送后调用 AI 模型回复并保存记录。
        """
        input_text = self.input_text.get().strip()
        self.input_text.delete(0, tk.END)
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
            ai_reply = self.ai_model.get_reply(input_text)
            reply_msg = f"AI: {ai_reply}\n"
            self.output_text.insert(tk.END, reply_msg)
            self.tree.get_current_node().chats.append(reply_msg)
            if self.auto_save:
                self.save_chat_records()

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

    def save_chat_records(self):
        """
        将整个树状聊天记录（包括节点结构及所有节点聊天内容）序列化为 JSON，
        固定保存在"chat_all_records.json"文件中，存放于默认记录文件夹内。
        若 show_save_alert 开启，则在聊天区域提示保存成功。
        """
        def serialize_node(node):
            return {
                'id': node.id,
                'topic': node.topic,
                'chats': node.chats,
                'children': [serialize_node(child) for child in node.children]
            }
        tree_dict = serialize_node(self.tree.root)
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
            def serialize_node(node):
                return {
                    'id': node.id,
                    'topic': node.topic,
                    'chats': node.chats,
                    'children': [serialize_node(child) for child in node.children]
                }
            try:
                tree_dict = serialize_node(self.tree.root)
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

if __name__ == "__main__":
    root = tk.Tk()
    main_window = MainWindow(root)
    root.mainloop()
