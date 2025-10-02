# 快捷键配置文件
# 用于配置TreeChat应用中的键盘快捷键

# 文本输入区域快捷键
INPUT_SHORTCUTS = {
    # 换行
    'line_break': '<Shift-Return>',
    # 发送消息
    'send_message': '<Control-Return>',
    # 选择文本
    'select_all': '<Control-a>',
    'select_word': '<Control-w>',
    'select_line': '<Control-l>',
    # 文本编辑
    'undo': '<Control-z>',
    'redo': '<Control-y>',
    'cut': '<Control-x>',
    'copy': '<Control-c>',
    'paste': '<Control-v>',
    # 导航
    'move_up': '<Up>',
    'move_down': '<Down>',
    'move_left': '<Left>',
    'move_right': '<Right>',
    'move_to_start': '<Home>',
    'move_to_end': '<End>',
    'move_to_text_start': '<Control-Home>',
    'move_to_text_end': '<Control-End>',
    # 删除
    'delete_previous_word': '<Control-BackSpace>',
    'delete_next_word': '<Control-Delete>',
}

# 主窗口快捷键
MAIN_SHORTCUTS = {
    # 文件操作
    'new_chat': '<Control-n>',
    'open_chat': '<Control-o>',
    'save_chat': '<Control-s>',
    'save_chat_as': '<Control-Shift-s>',
    # 应用操作
    'open_settings': '<Control-comma>',
    'quit_app': '<Control-q>',
}

# 聊天记录区域快捷键
CHAT_SHORTCUTS = {
    # 选择和导航
    'select_all_chat': '<Control-a>',
    'scroll_up': '<Prior>',  # Page Up
    'scroll_down': '<Next>',  # Page Down
    'scroll_to_top': '<Control-Prior>',  # Ctrl+Page Up
    'scroll_to_bottom': '<Control-Next>',  # Ctrl+Page Down
}

# iFlow对话快捷键
IFLOW_SHORTCUTS = {
    # 对话操作
    'send_to_iflow': '<Control-Shift-Return>',
    'clear_chat': '<Control-l>',
    'toggle_theme': '<Control-t>',
    # 编辑操作
    'duplicate_line': '<Control-d>',
    'move_line_up': '<Alt-Up>',
    'move_line_down': '<Alt-Down>',
    # 搜索和替换
    'find': '<Control-f>',
    'replace': '<Control-h>',
    'find_next': '<F3>',
    'find_previous': '<Shift-F3>',
}