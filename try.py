from neo4j import GraphDatabase
import json
import os
from datetime import datetime


class Neo4jImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_events(self, file_path):
        """导入事件数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            with self.driver.session() as session:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        text = data.get('text', '')
                        event_list = data.get('event_list', [])

                        for event in event_list:
                            event_type = event.get('event_type', '')
                            trigger = event.get('trigger', '')
                            arguments = event.get('arguments', [])

                            # 创建事件节点
                            session.run(
                                "MERGE (e:Event {trigger: $trigger, type: $type, description: $desc})",
                                trigger=trigger, type=event_type, desc=text
                            )

                            # 处理事件参数
                            for arg in arguments:
                                role = arg.get('role', '')
                                argument = arg.get('argument', '')

                                # 如果是人物参数，创建关系
                                if role == '人物':
                                    session.run(
                                        "MATCH (e:Event {trigger: $trigger}) "
                                        "MERGE (p:Person {name: $name}) "
                                        "MERGE (p)-[:PARTICIPATED_IN {role: $role}]->(e)",
                                        trigger=trigger, name=argument, role=role
                                    )
                                # 如果是地点参数，创建场景关系
                                elif role == '地点':
                                    session.run(
                                        "MATCH (e:Event {trigger: $trigger}) "
                                        "MERGE (s:Scene {name: $name}) "
                                        "MERGE (e)-[:OCCURRED_AT]->(s)",
                                        trigger=trigger, name=argument
                                    )

    def import_relations(self, file_path):
        """导入关系数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            with self.driver.session() as session:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        spo_list = data.get('spo_list', [])

                        for spo in spo_list:
                            subject = spo.get('subject', '')
                            predicate = spo.get('predicate', '')
                            object = spo.get('object', '')

                            # 创建人物节点和关系
                            if subject and predicate and object:
                                # 创建主语节点
                                session.run(
                                    "MERGE (s:Person {name: $name})",
                                    name=subject
                                )

                                # 创建宾语节点
                                session.run(
                                    "MERGE (o:Person {name: $name})",
                                    name=object
                                )

                                # 创建关系
                                session.run(
                                    "MATCH (s:Person {name: $subject}) "
                                    "MATCH (o:Person {name: $object}) "
                                    "MERGE (s)-[r:" + predicate + "]->(o)",
                                    subject=subject, object=object
                                )

    def import_scenes(self, file_path):
        """导入场景数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            with self.driver.session() as session:
                for scene in data:
                    scene_id = scene.get('id', '')
                    description = scene.get('description', '')
                    year = scene.get('year', '')
                    location = scene.get('location', '')

                    # 创建场景节点
                    session.run(
                        "MERGE (s:Scene {id: $id, description: $desc, year: $year, location: $loc})",
                        id=scene_id, desc=description, year=year, loc=location
                    )


def main():
    # Neo4j连接配置
    uri = "neo4j://127.0.0.1:7687"  # 根据你的Neo4j配置修改
    user = "neo4j"  # 根据你的Neo4j配置修改
    password = "12345678"  # 根据你的Neo4j配置修改

    # 文件路径
    events_file = "EE-Hangaozubenji.txt"
    relations_file = "RE-Hangaozubenji.json"
    scenes_file = "汉高祖本纪场景.json"

    # 创建导入器实例
    importer = Neo4jImporter(uri, user, password)

    try:
        print("开始导入场景数据...")
        importer.import_scenes(scenes_file)
        print("场景数据导入完成")

        print("开始导入事件数据...")
        importer.import_events(events_file)
        print("事件数据导入完成")

        print("开始导入关系数据...")
        importer.import_relations(relations_file)
        print("关系数据导入完成")

        print("所有数据导入成功!")

    except Exception as e:
        print(f"导入过程中发生错误: {e}")
    finally:
        importer.close()


if __name__ == "__main__":
    main()