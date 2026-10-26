import os

"""给工程提供一个获得绝对路径的功能"""
"""
1.get_project_root -> 获得工程所在根目录，这里固定返回D:\project\PythonProject\RAG与智能体开发项目\
__file__固定指向path_util.py的位置，__file__ 是每个 .py 文件自己的内置属性，天生就锚定它自己所在的磁盘位置。谁 import 它、从哪个目录运行，都改变不了它。
在哪里写就是哪里的文件位置，而不是调用

2.get_abs_path -> 把根目录和所传相对路径做拼接，要求所传相对路径必须是相对根目录的，不然会导致路径不全
硬性要求是三级，小项目会这么做
"""
def get_project_root():
    """
    获取工程所在根目录
    my_project/
    ├── utils/
    │   └── path_util.py
    └── src/
        └── test.py
    前提是三级，所以跳两次
    :return:
    """
    #当前文件所在路径
    current_file = os.path.abspath(__file__)
    #再往上跳一级，拿到文件所在文件夹的路径
    current_dir = os.path.dirname(current_file)
    #获取项目跟目录
    project_root = os.path.dirname(current_dir)
    return project_root

def get_abs_path(relative_path):
    """
    传递相对路径，得到绝对路径
    相对路径是有要求的，是文件绝对路径剪切掉根目录，如果有三级 project -> dir -> .py
    相对路径是 dir/.py  只传.py是不允许的
    :param relative_path:
    :return:
    """
    #这里不管在哪个文件里调用，都能拿到项目根目录，__file__ 指向"写它的那个文件自己"，不是"调用它的文件"。
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)

if __name__ == '__main__':
    print(get_abs_path("path_tool.py"))#会少一级，这里并不是相对路径