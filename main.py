import csv
import py2neo
from py2neo import Graph,Node,Relationship,NodeMatcher
#账号密码改为自己的即可
g=Graph('neo4j://127.0.0.1:7687',user='neo4j',password='12345678')
with open('all.csv','r',encoding='utf-8',errors='ignore') as f:
    reader=csv.reader(f)
    for item in reader:
        if reader.line_num==1:
            continue
        print("当前行数：",reader.line_num,"当前内容：",item)
        start_node=Node("Person",name=item[0])
        end_node=Node("Person",name=item[1])
        relation=Relationship(start_node,item[2],end_node)
        g.merge(start_node,"Person","name")
        g.merge(end_node,"Person","name")
        g.merge(relation,"Person","name")
#以下为neo4j代码，如需代码运行，请放入g.run(...)内运行，将...替换为下列代码
#MATCH (p: Person {name:"贾宝玉"})-[k:丫鬟]-(r)
#return p,k,r
#MATCH (p1:Person {name:"贾宝玉"}),(p2:Person{name:"香菱"}),p=shortestpath((p1)-[*..10]-(p2))
#RETURN p