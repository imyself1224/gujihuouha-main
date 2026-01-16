import csv
import py2neo
from py2neo import Graph, Node, Relationship, NodeMatcher

# 账号密码改为自己的即可
g = Graph('neo4j://127.0.0.1:7687', user='neo4j', password='12345678')

# 检查连接
try:
    print("连接Neo4j...")
    print("连接成功！")
except Exception as e:
    print(f"连接失败: {e}")
    exit(1)


# 定义节点类型判断函数
def get_node_type(name):
    # 这里列出一些明显是地点的关键词
    location_keywords = ['邑', '阳', '关', '郡', '县', '城', '宫', '水', '山', '谷', '陵', '丰', '沛', '咸阳', '单父',
                         '砀', '睢阳','太原','楚地']

    # 如果名称包含地点关键词，则认为是地点
    for keyword in location_keywords:
        if keyword in name:
            return "Location"

    # 明显是人物的节点
    person_names = ['高祖', '太公', '刘媪', '吕公', '吕后', '孝惠帝', '鲁元公主', '陈胜', '萧何','赵王歇','黄帝','子婴','楚怀王',
                    '曹参', '刘季', '樊哙', '周章', '雍齿', '项羽', '项梁', '章邯', '张良', '韩信','刘邦','怀王','鲁公','曹咎',
                    '王','皇帝','祖']

    if name in person_names:
        return "Person"

    # 默认认为是Other（官职、称号等）
    return "Other"


with open('re.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    count = 0
    for item in reader:
        if reader.line_num == 1:
            continue
        print(f"当前行数：{reader.line_num}，当前内容：{item}")

        # 确定节点类型
        start_node_type = get_node_type(item[0])
        end_node_type = get_node_type(item[1])

        # 创建节点
        start_node = Node(start_node_type, name=item[0])
        end_node = Node(end_node_type, name=item[1])

        # 创建关系
        relation = Relationship(start_node, item[2], end_node)

        # 合并节点和关系
        g.merge(start_node, start_node_type, "name")
        g.merge(end_node, end_node_type, "name")
        g.create(relation)
        #g.merge(relation, start_node_type, "name")
        count += 1

print(f"导入完成！共导入 {count} 条关系")