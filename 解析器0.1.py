import json,os,sys
import re
from typing import Dict, Any, List, Optional
from copy import deepcopy


class 解析器:
    """
    支持继承和变量系统的我的世界UI JSON解析器
    特性：
    1. 支持组件继承（@语法）
    2. 变量作用域链 - 子节点可以访问父节点变量
    3. 深度属性合并
    4. 命名空间支持
    """
    组件库 = {}
    def __init__(自身):
        自身.全局变量表 = {}
        #解析器.组件库 = {}
        自身.命名空间映射 = {}
        自身.解析历史 = []
    
    def 解析JSON文件(自身, json数据: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析JSON数据，处理继承关系和变量系统
        """
        if not isinstance(json数据, dict):
            raise ValueError("输入数据必须是字典类型")
        
        自身.解析历史 = []
        # 第一步：提取命名空间
        命名空间 = 自身._提取命名空间(json数据)
        
        # 第二步：注册组件到库
        自身._注册组件到库(json数据, 命名空间)
        
        # 第三步：解析整个结构（从根节点开始，没有父变量表）
        return 自身._递归解析对象(json数据, 命名空间, None, "root")
    
    def 解析指定键(自身,key: str,命名空间) -> Dict[str, Any]:
        """
            解析指定组件键，处理可能的延迟继承
            @"命名空间.键"
            
        """
        自身.解析历史 = []

        # 先检查并处理延迟继承
        自身._处理延迟继承(key)
        
        json数据 = 解析器.组件库.get(key)
        if not json数据:
            print("组件库里没有指定数据:%s",key)
            return {}
       
        return 自身._递归解析对象(json数据, 命名空间, None, "root")

    def _处理延迟继承(自身, 组件全名: str) -> bool:
        """
        优化后的延迟继承处理 - 职责单一化
        只负责处理延迟继承标记，返回布尔值表示是否处理成功
        """
        if 组件全名 not in 解析器.组件库:
            return False
        
        组件值 = 解析器.组件库[组件全名]
        
        # 检查是否有延迟继承标记
        if not isinstance(组件值, dict) or '__继承信息__' not in 组件值:
            return False  # 没有延迟继承标记，直接返回
        
        try:
            继承信息 = 组件值['__继承信息__']
            原始数据 = 组件值.copy()
            del 原始数据['__继承信息__']
            
            基类引用 = 继承信息['基类引用']
            命名空间 = 自身.命名空间映射.get(组件全名, '')
            
            # 解析基类全名
            基类全名 = 自身._解析基类引用(基类引用, 命名空间)
            
            if 基类全名 not in 解析器.组件库:
                print(f"延迟继承失败: 基类 {基类全名} 仍未注册")
                return False
            
            # 递归处理基类的延迟继承（确保继承链完整）
            自身._处理延迟继承(基类全名)
            
            # 执行实际的继承合并
            成功 = 自身._执行延迟继承合并(组件全名, 原始数据, 基类全名, 命名空间)
            
            if 成功:
                print(f"✅ 延迟继承完成: {组件全名} -> {基类全名}")
            
            return 成功
            
        except Exception as e:
            print(f"❌ 延迟继承处理失败 {组件全名}: {e}")
            return False

    def _执行延迟继承合并(自身, 组件全名: str, 子类数据: Dict, 基类全名: str, 命名空间: str) -> bool:
        """
        执行实际的延迟继承合并操作
        """
        try:
            # 获取基类对象
            基类对象 = deepcopy(解析器.组件库[基类全名])
            
            # 创建基础的变量表
            # 基础变量表 = {}
            # 当前变量表 = 基础变量表.copy()
             
            # 提取子类变量
            # 自身._提取局部变量(子类数据, 当前变量表, f"延迟继承.{组件全名}")

            # 深度合并基类和子类
            初步合并对象 = deepcopy(基类对象)
            
            for 子键, 子值 in 子类数据.items():
                #if not 子键.startswith('$'):  # 跳过变量定义
                    初步解析值 = 自身._解析基础变量值(子值, f"延迟继承.{组件全名}.{子键}")
                    自身._深度合并属性(初步合并对象, 子键, 初步解析值)
            
            # 更新组件库
            解析器.组件库[组件全名] = 初步合并对象
            return True
            
        except Exception as e:
            print(f"延迟继承合并失败 {组件全名}: {e}")
            return False

    def _提取命名空间(自身, 数据: Dict[str, Any],文件路径) -> str:
        """提取文件的命名空间"""
        名称 = 数据.get("namespace", None)
        if not 名称:
            print("没有命名空间: %s",文件路径)
            exit()
        return 名称
    
    def _注册组件到库(自身, 数据: Dict[str, Any], 命名空间: str):
        """注册所有可继承组件到全局组件库，支持解析继承语法和初步继承处理"""
        for 键, 值 in 数据.items():
            if 键 != "namespace" and isinstance(值, dict):
                组件名 = 键
                基类引用 = None
                继承信息 = None
                
                # 检查键名是否包含继承语法（@符号）
                if '@' in 键:
                    部分 = 键.split('@')
                    if len(部分) == 2:
                        组件名, 基类引用 = 部分[0], 部分[1]
                        # 存储继承信息，用于后续解析
                        继承信息 = {
                            '基类引用': 基类引用,
                            '原始键': 键
                        }
                    else:
                        # 无效的继承语法，回退到原始逻辑
                        组件名 = 键
                
                全名 = f"{命名空间}.{组件名}"
                
                # 如果存在继承关系，尝试初步解析
                if 基类引用 and 继承信息:
                    try:
                        # 解析基类全名
                        基类全名 = 自身._解析基类引用(基类引用, 命名空间)
                        
                        # 检查基类是否已注册
                        if 基类全名 in 解析器.组件库:
                            # 获取基类定义并深拷贝
                            基类对象 = deepcopy(解析器.组件库[基类全名])
                            
                            # 创建基础的变量表用于初步解析
                            # 基础变量表 = {}
                            
                            # 提取当前组件的变量定义
                            # 当前变量表 = 基础变量表.copy()
                            # 自身._提取局部变量(值, 当前变量表, f"注册阶段.{全名}")
                            
                            # 初步合并：先基类，后子类重写
                            初步合并对象 = deepcopy(基类对象)
                            
                            # 应用子类的属性重写（深度合并）

                            for 子键, 子值 in 值.items():
                                # 这里进行基础解析，不处理深层继承（留待正式解析时处理）
                                初步解析值 = 自身._解析基础变量值(子值, f"注册阶段.{全名}.{子键}")
                                自身._深度合并属性(初步合并对象, 子键, 初步解析值)
                            
                            # 存储初步合并的结果
                            解析器.组件库[全名] = 初步合并对象
                            
                        else:
                            # 基类尚未注册，先存储原始值和继承信息
                            带继承信息的值 = 值.copy()
                            带继承信息的值['__继承信息__'] = 继承信息
                            解析器.组件库[全名] = 带继承信息的值
                            
                    except Exception as e:
                        print(f"警告：注册组件 {全名} 时处理继承关系出错: {e}")
                        # 出错时回退到存储原始值
                        解析器.组件库[全名] = 值
                else:
                    # 普通组件，直接存储
                    解析器.组件库[全名] = 值
                
                自身.命名空间映射[全名] = 命名空间
                print(f"注册组件: {全名} (原始键: {键})")
    
    def _递归解析对象(自身, 数据: Dict[str, Any], 当前命名空间: str, 
                    父变量表: Optional[Dict[str, Any]], 当前路径: str) -> Dict[str, Any]:
        """
        递归解析JSON对象，处理继承关系和变量作用域链
        """
        if 当前路径 in 自身.解析历史:
            raise ValueError(f"检测到循环引用: {当前路径}")
        
        自身.解析历史.append(当前路径)
        
        try:
            # 创建当前对象的独立变量表（继承父级变量）
            当前变量表 = 父变量表.copy() if 父变量表 else {}
            
            # 提取当前层的变量定义（会更新当前变量表）
            自身._提取局部变量(数据, 当前变量表, 当前路径)
            
            # 处理继承关系（传入当前变量表，子节点可以访问）
            解析后对象 = 自身._处理继承关系(数据, 当前命名空间, 当前变量表, 当前路径)
            
            return 解析后对象
            
        finally:
            自身.解析历史.pop()
    
    def _提取局部变量(自身, 数据: Dict[str, Any], 当前变量表: Dict[str, Any], 当前路径: str):
        """
        提取当前对象的局部变量定义，会修改当前变量表[7](@ref)
        """
        待删除键 = []
        
        for 键, 值 in 数据.items():
            if 键.startswith('$'):
                变量名 = 键[1:]  # 提取变量名（去掉开头的$符号）
                # 变量值需要先进行基本解析（不处理变量引用，避免循环）
                解析值 = 自身._解析基础变量值(值, 当前路径)
                当前变量表[变量名] = 解析值  # 将变量存入当前作用域
                待删除键.append(键)     # 标记该变量键需要被删除
                
        # 清理已处理的变量定义
        for 键 in 待删除键:
            del 数据[键]
    
    def _处理继承关系(自身, 数据: Dict[str, Any], 当前命名空间: str, 
                    当前变量表: Dict[str, Any], 当前路径: str) -> Dict[str, Any]:
        """
        处理对象的继承关系[1,6](@ref)
        """
        结果 = {}
        
        # 先处理普通属性（非继承）
        for 键, 值 in 数据.items():
            if '@' not in 键 and 键 != "namespace" and not 键.startswith('$'):
                结果[键] = 自身._递归解析值(值, 当前命名空间, 当前变量表, f"{当前路径}.{键}")
        # 处理继承关系
        for 键, 值 in 数据.items():
            if '@' in 键:
                继承结果 = 自身._处理单个继承(键, 值, 当前命名空间, 当前变量表, 当前路径)
                结果.update(继承结果)
        
        return 结果
    
    def _处理单个继承(自身, 继承键: str, 继承值: Any, 当前命名空间: str, 
                            父变量表: Dict[str, Any], 当前路径: str) -> Dict[str, Any]:
        """
        优化后的单个继承处理 - 逻辑清晰化
        """
        # 1. 解析继承语法
        部分 = 继承键.split('@')
        if len(部分) != 2:
            raise ValueError(f"无效的继承语法: {继承键}")
        
        实例名, 基类引用 = 部分[0], 部分[1]
        
        # 2. 解析基类引用
        基类全名 = 自身._解析基类引用(基类引用, 当前命名空间)
        
        # 3. 检查并处理延迟继承（在开始处理前）
        if 基类全名 in 解析器.组件库:
            基类值 = 解析器.组件库[基类全名]
            if isinstance(基类值, dict) and '__继承信息__' in 基类值:
                自身._处理延迟继承(基类全名)
        
        if 基类全名 not in 解析器.组件库:
            raise ValueError(f"未找到基类: {基类引用} (全名: {基类全名})")
        
        # 4. 准备继承处理
        基类对象 = deepcopy(解析器.组件库[基类全名])
        当前变量表 = 父变量表.copy() if 父变量表 else {}
        
        # 5. 分离变量定义和属性重写
        子类变量定义, 子类属性重写 = 自身._分离继承数据(继承值, 当前路径)
        
        # 6. 处理变量定义
        for 变量名, 变量值 in 子类变量定义.items():
            解析值 = 自身._递归解析值(变量值, 当前命名空间, 当前变量表, f"{当前路径}.变量.{变量名}")
            当前变量表[变量名] = 解析值
        
        # 7. 在变量作用域中解析基类
        继承对象 = deepcopy(基类对象)
        继承对象 = 自身._递归解析值(继承对象, 当前命名空间, 当前变量表, f"{当前路径}.基类")
        
        # 8. 应用属性重写
        for 子键, 子值 in 子类属性重写.items():
            解析值 = 自身._递归解析值(子值, 当前命名空间, 当前变量表, f"{当前路径}.{实例名}.{子键}")
            自身._深度合并属性(继承对象, 子键, 解析值)
        
        return 继承对象

    def _分离继承数据(自身, 继承值: Any, 当前路径: str) -> tuple:
        """
        分离继承数据中的变量定义和属性重写
        """
        变量定义 = {}
        属性重写 = {}
        
        if isinstance(继承值, dict):
            for 键, 值 in 继承值.items():
                if 键.startswith('$'):
                    变量名 = 键[1:]
                    变量定义[变量名] = 值
                else:
                    属性重写[键] = 值
        elif 继承值 is not None:
            print(f"警告: 在路径 {当前路径} 继承值不是字典类型: {type(继承值)}")
        
        return 变量定义, 属性重写
    
    def _递归解析值(自身, 值: Any, 当前命名空间: str, 当前变量表: Dict[str, Any], 当前路径: str) -> Any:
        """
        递归解析值，处理嵌套结构和变量引用[2](@ref)
        """
        if isinstance(值, dict):
            
            # 对于字典，创建新的作用域并递归解析
            return 自身._递归解析对象(值, 当前命名空间, 当前变量表, 当前路径)
        elif isinstance(值, list):
            # 对于列表，递归解析每个元素（共享当前作用域）
            return [自身._递归解析值(元素, 当前命名空间, 当前变量表, f"{当前路径}[{索引}]") 
                   for 索引, 元素 in enumerate(值)]
        elif isinstance(值, str) and 值.startswith('$'):
            # 对于字符串，进行变量替换
            return 自身._替换变量引用(值, 当前变量表, 当前路径)
        else:
            return 值
    
    def _解析基础变量值(自身, 值: Any, 当前路径: str) -> Any:
        """
        解析基础变量值（不处理变量引用，避免循环依赖）
        用于变量定义的初始解析
        """
        if isinstance(值, dict):
            return {k: 自身._解析基础变量值(v, f"{当前路径}.{k}") for k, v in 值.items()}
        elif isinstance(值, list):
            return [自身._解析基础变量值(元素, f"{当前路径}[{i}]") for i, 元素 in enumerate(值)]
        else:
            return 值
    
    def _替换变量引用(自身, 值: str, 当前变量表: Dict[str, Any], 当前路径: str) -> Any:
        """
        增强的变量引用解析，支持作用域链查找
        """
        if not isinstance(值, str) or not 值.startswith('$'):
            return 值
        
        # 支持 ${变量名} 和 $变量名 两种语法
        变量名 = 值[1:]
        if 变量名.startswith('{') and 变量名.endswith('}'):
            变量名 = 变量名[1:-1]
        
        if 变量名 in 当前变量表:
                变量值 = 当前变量表[变量名]
                
        if not '变量值' in locals():
            return 值

        # 先判断局部变量是否复制
        if '变量值' in locals() and '@' in 变量值:
            # 分割变量值，提取实例名和基类引用
            部分 = 变量值.split('@', 1)  # 限制分割次数为1，提高效率
            实例名, 基类引用 = 部分[0], 部分[1]
            
            # 分割基类引用，提取命名空间和基类名
            部分 = 基类引用.split('.', 1)  # 限制分割次数为1
            命名空间, 基类名 = 部分 if len(部分) == 2 else (部分[0], '')
            
            # 获取基类值并进行递归解析
            基类值 = 解析器.组件库[基类引用]
            变量值 = 自身._递归解析值(基类值, 命名空间, 当前变量表, 当前路径)
        else:
            return deepcopy(变量值)  # 直接返回数据结构本身
        
        return 变量值 
        
    def _深度合并属性(自身, 目标对象: Dict[str, Any], 键: str, 值: Any):
        """
        深度合并属性，支持嵌套结构[7](@ref)
        """
        if 键 in 目标对象 and isinstance(目标对象[键], dict) and isinstance(值, dict):
            # 深度合并字典
            for 子键, 子值 in 值.items():
                自身._深度合并属性(目标对象[键], 子键, 子值)
        else:
            # 直接赋值（覆盖或新增）
            目标对象[键] = 值
    
    def _解析基类引用(自身, 基类引用: str, 当前命名空间: str) -> str:
        """解析基类引用，处理命名空间"""
        if '.' in 基类引用:
            # 完整命名空间引用
            return 基类引用
        else:
            # 相对引用，使用当前命名空间
            return f"{当前命名空间}.{基类引用}"
    
    def 获取解析信息(自身) -> Dict[str, Any]:
        """获取解析器状态信息"""
        return {
            '解析器类型': '支持继承和作用域链的我的世界UI解析器',
            '组件数量': len(解析器.组件库),
            '全局变量数量': len(自身.全局变量表),
            '命名空间映射': 自身.命名空间映射
        }


def 取文件夹所有JSON(folder_path):
    """
    获取指定文件夹内的所有JSON文件（不包含子文件夹）
    
    :param folder_path: 文件夹路径
    :return: JSON文件完整路径列表
    """
    json_files = []
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"文件夹不存在: {folder_path}")
        return json_files
    
    # 获取文件夹内所有文件和文件夹
    try:
        items = os.listdir(folder_path)
    except PermissionError:
        print(f"没有权限访问文件夹: {folder_path}")
        return json_files
    
    # 筛选JSON文件
    for item in items:
        item_path = os.path.join(folder_path, item)
        
        # 只处理文件，忽略文件夹
        if os.path.isfile(item_path) and item.lower().endswith('.json'):
            json_files.append(item_path)
    
    return json_files

# ... 解析器类定义 ...

def 加载并注册所有组件(文件夹路径: str) -> 解析器:
    """
    加载指定文件夹下所有JSON文件，并将其中的组件注册到解析器的全局库中。
    返回一个初始化好的解析器实例。
    """
    文件路径列表 = 取文件夹所有JSON(文件夹路径)
    解析器实例 = 解析器() # 注意：解析器.组件库 是类变量，所有实例共享

    for 文件路径 in 文件路径列表:
        try:
            with open(文件路径, 'r', encoding='utf-8') as f:
                json数据 = json.load(f)
            if not isinstance(json数据, dict):
                print(f"警告：文件 {文件路径} 的根元素不是字典，已跳过。")
                continue
            
            # 提取命名空间并注册组件
            命名空间 = 解析器实例._提取命名空间(json数据, 文件路径)
            解析器实例._注册组件到库(json数据, 命名空间)
            # print(f"已注册命名空间: {命名空间}")
        except Exception as e:
            print(f"加载文件 {文件路径} 时出错: {e}")
    
    return 解析器实例

if __name__ == "__main__":
    folder_path = "720-1280"
    
    # 1. 首先，加载并注册目标文件夹下的所有JSON组件
    解析器实例 = 加载并注册所有组件(folder_path)
    
    # 可选：打印当前已注册的组件，确认"main.main"及其可能依赖的基类都已存在
    #print("已注册的组件键:", list(解析器.组件库.keys()))
    
    # 2. 然后，再解析特定的组件（如"main.main"）
    # 注意：解析指定键 方法内部使用的 组件库 已经是包含所有组件定义的了
    try:
        结果 = 解析器实例.解析指定键("main.main", "main") # 确保命名空间参数正确
        # 保存解析结果
        with open(folder_path + '\\Engine.json', 'w', encoding='utf-8') as f:
            json.dump(结果, f, ensure_ascii=False, indent=2)
        print("✅ 解析成功！结果已保存到 Engine.json")
    except ValueError as e:
        print(f"❌ 解析失败: {e}")
        # 如果是因为基类未找到，检查组件库的键和命名空间映射
        print("调试信息：", 解析器实例.获取解析信息())

      
    