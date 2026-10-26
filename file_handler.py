import hashlib
import logging
import os
from utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader

"""
负责文件处理相关功能代码：
1.get_file_md5_hex -> 参数：文件路径 -> 判断文件是否存在或者是不是文件 -> 创建md5对象 ->以二进制打开文件，每次只读4KB,然后混入摘要 -> 全部内容读完返回md5十六进制字符串
得到文件的md5十六进制字符串

2.listdir_with_allowed_type -> 参数：文件路径，允许的文件后缀 -> 创建文件列表-> 判断是不是文件夹 -> 对列表内的文件进行循环，如果符合要求后缀，就加入file列表 -> 最后把file列表转换成元组，防止改变
这个函数是用来获取知识库目录里待加载的文档路径。
目录扫描结果本身就应该是 “只读快照”：扫描一次拿到哪些文件就是哪些，调用方不应该随便往里面乱加路径。所以最后要转换成元组

3.pdf_loader/txt_loader:把 PDF、txt 文件，读取转换成 LangChain 的 Document对象列表，给后面 RAG 流程用。

      def load(self) -> list[Document]:
        ...
        return list(self.lazy_load())
"""
def get_file_md5_hex(filepath: str):
    if not os.path.exists(filepath):
        logger.error(f"文件 {filepath}不存在")
        return None

    if not os.path.isfile(filepath):
        logger.error(f"路径{filepath}不是文件")
        return None

    md5_obj = hashlib.md5()

    chunk_size=4096

    try:
        with open(filepath, "rb") as f:
            chunk = f.read(chunk_size)
            while chunk:
                md5_obj.update(chunk)
                chunk = f.read(chunk_size)

            md5_hex = md5_obj.hexdigest()
        return md5_hex
    except Exception as e:
        logger.error(f"计算文件{filepath}md5失败,{str(e)}")
        return None

#返回文件夹内的文件列表（允许的文件后缀）
def listdir_with_allowed_type(path,allowed_types):
    files = []

    if not os.path.isdir(path):
        logger.error(f"[listdir_with_allowed_type]{path}不是文件夹")
        return None

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))

    #转为元组，不允许被修改
    return tuple(files)

def pdf_loader(filepath: str, passwd=None) -> list[Document]:
    return PyPDFLoader(filepath, passwd).load()


def txt_loader(filepath: str) -> list[Document]:
    return TextLoader(filepath, encoding="utf-8").load()

