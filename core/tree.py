import uuid

class TreeNode:
    """
    树节点类，用于表示聊天记录的层次结构
    
    每个节点包含一个主题、唯一的ID、子节点列表和聊天记录
    """
    def __init__(self, topic):
        """
        初始化一个新的树节点

        参数:
            topic - 节点的话题（类似文件夹名称）
        """
        self.id = str(uuid.uuid4())  # 为每个节点生成唯一 ID
        self.topic = topic
        self.children = []
        self.chats = []  # 保存该节点下的聊天记录

    def add_child(self, child):
        """
        添加子节点

        参数:
            child - 新的子 TreeNode 对象
        """
        self.children.append(child)

    def delete_child(self, child):
        """
        删除子节点

        参数:
            child - 要删除的子 TreeNode 对象
        """
        self.children.remove(child)

    def __str__(self, level=0):
        """
        递归生成树的字符串表示，用于展示树的结构

        参数:
            level - 递归层级，起始为0

        返回:
            格式化后表示树结构的字符串
        """
        ret = ""
        if level == 0:
            ret += self.topic + "\n"
        else:
            ret += "  " * (level - 1) + "- " + self.topic + "\n"
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret

class Tree:
    """
    树结构类，用于管理聊天记录的层次结构
    
    包含一个根节点和当前活动节点的引用
    """
    def __init__(self):
        """
        初始化树，设置根节点为"会话根节点"
        """
        self.root = TreeNode("会话根节点")
        self.current_node = self.root

    def add_topic(self, topic):
        """
        添加一个新话题作为当前节点的子节点，并切换当前节点

        参数:
            topic - 新话题名称
        """
        new_node = TreeNode(topic)
        self.current_node.add_child(new_node)
        self.current_node = new_node

    def print_tree(self):
        """
        打印完整的树结构
        """
        print(self.root)

    def get_current_node(self):
        """
        获取当前节点

        返回:
            当前的 TreeNode 对象
        """
        return self.current_node

    def set_current_node(self, node):
        """
        设置当前节点

        参数:
            node - 要设置为当前节点的 TreeNode 对象
        """
        self.current_node = node
