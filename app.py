from flask import Flask, request, jsonify
from flask_cors import CORS
from neo4j import GraphDatabase
import logging

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j 连接配置
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"

# 初始化 Neo4j 驱动
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_session():
    """获取 Neo4j 会话"""
    return driver.session()


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    try:
        with get_session() as session:
            session.run("RETURN 1")
        return jsonify({'status': 'success', 'message': 'Neo4j 连接正常'})
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return jsonify({'status': 'error', 'message': '数据库连接失败'}), 500


@app.route('/api/node/<node_name>', methods=['GET'])
def get_node(node_name):
    """
    获取特定节点的详细信息
    参数: node_name (节点名称，URL 路径参数)
    """
    try:
        with get_session() as session:
            # 查询节点信息
            result = session.run(
                """
                MATCH (n {name: $name})
                RETURN n.name AS name, labels(n) AS labels, properties(n) AS props
                """,
                name=node_name
            )
            
            node = result.single()
            if not node:
                return jsonify({'status': 'error', 'message': '节点不存在'}), 404

            node_data = {
                'name': node['name'],
                'labels': node['labels'],
                'properties': dict(node['props']) if node['props'] else {}
            }

            return jsonify({
                'status': 'success',
                'data': node_data
            })

    except Exception as e:
        logger.error(f"获取节点信息出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/person', methods=['GET', 'POST'])
def search_person():
    """
    查询人物信息及其所有关系
    参数: name (人物名称)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        name = data.get('name', '')

        if not name:
            return jsonify({'status': 'error', 'message': '请提供人物名称'}), 400

        with get_session() as session:
            # 查询人物节点
            result = session.run(
                """
                MATCH (p:Person {name: $name})
                RETURN p.name AS name, labels(p) AS labels, properties(p) AS props
                """,
                name=name
            )
            
            person = result.single()
            if not person:
                return jsonify({'status': 'success', 'data': None, 'message': '未找到该人物'})

            # 查询人物的所有关系（出度和入度）
            relations = session.run(
                """
                MATCH (p:Person {name: $name})-[r]->(other)
                RETURN p.name AS source, other.name AS target, type(r) AS relation_type, 
                       labels(other) AS target_labels, properties(other) AS target_props, 
                       properties(r) AS rel_props, 'outgoing' AS direction
                UNION ALL
                MATCH (other)-[r]->(p:Person {name: $name})
                RETURN other.name AS source, p.name AS target, type(r) AS relation_type, 
                       labels(other) AS target_labels, properties(other) AS target_props,
                       properties(r) AS rel_props, 'incoming' AS direction
                """,
                name=name
            )

            edges_list = []
            for record in relations:
                edges_list.append({
                    'source': record['source'],
                    'target': record['target'],
                    'relation_type': record['relation_type'],
                    'direction': record['direction'],
                    'target_labels': record['target_labels'],
                    'properties': dict(record['rel_props']) if record['rel_props'] else {}
                })

            return jsonify({
                'status': 'success',
                'data': {
                    'node': {
                        'name': person['name'],
                        'labels': person['labels'],
                        'properties': dict(person['props']) if person['props'] else {}
                    },
                    'edges': edges_list,
                    'edge_count': len(edges_list)
                }
            })

    except Exception as e:
        logger.error(f"查询人物出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/location', methods=['GET', 'POST'])
def search_location():
    """
    查询地点信息
    参数: name (地点名称)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        name = data.get('name', '')

        if not name:
            return jsonify({'status': 'error', 'message': '请提供地点名称'}), 400

        with get_session() as session:
            # 查询地点节点
            result = session.run(
                """
                MATCH (l:Location {name: $name})
                RETURN l.name AS name, labels(l) AS labels
                """,
                name=name
            )
            
            location = result.single()
            if not location:
                return jsonify({'status': 'success', 'data': None, 'message': '未找到该地点'})

            # 查询与该地点相关的所有关系
            relations = session.run(
                """
                MATCH (l:Location {name: $name})-[r]->(other)
                RETURN other.name AS target, type(r) AS relation_type, labels(other) AS target_labels
                UNION ALL
                MATCH (other)-[r]->(l:Location {name: $name})
                RETURN other.name AS target, type(r) AS relation_type, labels(other) AS target_labels
                """,
                name=name
            )

            relations_list = [
                {
                    'target': record['target'],
                    'relation_type': record['relation_type'],
                    'target_labels': record['target_labels']
                }
                for record in relations
            ]

            return jsonify({
                'status': 'success',
                'data': {
                    'name': location['name'],
                    'labels': location['labels'],
                    'relations': relations_list
                }
            })

    except Exception as e:
        logger.error(f"查询地点出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/relations', methods=['GET', 'POST'])
def search_relations():
    """
    查询两个节点之间的关系
    参数: source (源节点), target (目标节点)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        source = data.get('source', '')
        target = data.get('target', '')

        if not source or not target:
            return jsonify({'status': 'error', 'message': '请提供源节点和目标节点'}), 400

        with get_session() as session:
            # 查询直接关系
            direct = session.run(
                """
                MATCH (s)-[r]->(t)
                WHERE s.name = $source AND t.name = $target
                RETURN s.name AS source, type(r) AS relation_type, t.name AS target
                """,
                source=source, target=target
            )

            direct_list = [
                {
                    'source': record['source'],
                    'relation_type': record['relation_type'],
                    'target': record['target']
                }
                for record in direct
            ]

            # 查询最短路径
            paths = session.run(
                """
                MATCH path = shortestPath((s)-[*]-(t))
                WHERE s.name = $source AND t.name = $target
                RETURN [node in nodes(path) | node.name] AS path_nodes,
                       [rel in relationships(path) | type(rel)] AS relation_types
                LIMIT 5
                """,
                source=source, target=target
            )

            paths_list = [
                {
                    'path_nodes': record['path_nodes'],
                    'relation_types': record['relation_types']
                }
                for record in paths
            ]

            return jsonify({
                'status': 'success',
                'data': {
                    'direct_relations': direct_list,
                    'shortest_paths': paths_list
                }
            })

    except Exception as e:
        logger.error(f"查询关系出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/search/all', methods=['GET', 'POST'])
def search_all():
    """
    全局搜索：搜索包含关键词的所有节点
    参数: keyword (关键词)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        keyword = data.get('keyword', '')

        if not keyword:
            return jsonify({'status': 'error', 'message': '请提供搜索关键词'}), 400

        with get_session() as session:
            # 查询所有包含关键词的节点
            result = session.run(
                """
                MATCH (n)
                WHERE n.name CONTAINS $keyword
                RETURN n.name AS name, labels(n) AS labels
                LIMIT 50
                """,
                keyword=keyword
            )

            nodes = [
                {
                    'name': record['name'],
                    'labels': record['labels']
                }
                for record in result
            ]

            return jsonify({
                'status': 'success',
                'data': nodes,
                'total': len(nodes)
            })

    except Exception as e:
        logger.error(f"全局搜索出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/graph/neighbors', methods=['GET', 'POST'])
def get_neighbors():
    """
    获取节点的邻接节点（一度关系）
    参数: name (节点名称), limit (返回数量限制，默认20)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        name = data.get('name', '')
        limit = int(data.get('limit', 20))

        if not name:
            return jsonify({'status': 'error', 'message': '请提供节点名称'}), 400

        with get_session() as session:
            # 查询中心节点
            center_node = session.run(
                """
                MATCH (n {name: $name})
                RETURN n.name AS name, labels(n) AS labels, properties(n) AS props
                """,
                name=name
            ).single()

            if not center_node:
                return jsonify({'status': 'error', 'message': '节点不存在'}), 404

            # 查询邻接节点和边
            result = session.run(
                """
                MATCH (n {name: $name})-[r]-(neighbor)
                RETURN neighbor.name AS neighbor_name, labels(neighbor) AS neighbor_labels, 
                       properties(neighbor) AS neighbor_props, type(r) AS relation_type,
                       properties(r) AS rel_props
                LIMIT $limit
                """,
                name=name, limit=limit
            )

            nodes = []
            edges = []
            
            for i, record in enumerate(result):
                neighbor_name = record['neighbor_name']
                nodes.append({
                    'id': neighbor_name,
                    'name': neighbor_name,
                    'labels': record['neighbor_labels'],
                    'properties': dict(record['neighbor_props']) if record['neighbor_props'] else {}
                })
                
                edges.append({
                    'source': name,
                    'target': neighbor_name,
                    'relation_type': record['relation_type'],
                    'properties': dict(record['rel_props']) if record['rel_props'] else {}
                })

            # 添加中心节点
            nodes.insert(0, {
                'id': center_node['name'],
                'name': center_node['name'],
                'labels': center_node['labels'],
                'properties': dict(center_node['props']) if center_node['props'] else {},
                'is_center': True
            })

            return jsonify({
                'status': 'success',
                'data': {
                    'nodes': nodes,
                    'edges': edges,
                    'node_count': len(nodes),
                    'edge_count': len(edges)
                }
            })

    except Exception as e:
        logger.error(f"获取邻接节点出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/graph/subgraph', methods=['GET', 'POST'])
def get_subgraph():
    """
    获取子图 - 以指定节点为中心的多度关系子图
    参数: 
      - center (中心节点名称)
      - depth (查询深度，默认2，最多5)
      - limit (返回节点数限制，默认50)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        center = data.get('center', '')
        depth = min(int(data.get('depth', 2)), 5)  # 最多 5 度
        limit = int(data.get('limit', 50))

        if not center:
            return jsonify({'status': 'error', 'message': '请提供中心节点名称'}), 400

        if depth < 1:
            return jsonify({'status': 'error', 'message': '深度必须 >= 1'}), 400

        with get_session() as session:
            # 检查中心节点是否存在
            center_node = session.run(
                """
                MATCH (n {name: $name})
                RETURN n.name AS name, labels(n) AS labels, properties(n) AS props
                """,
                name=center
            ).single()

            if not center_node:
                return jsonify({'status': 'error', 'message': '中心节点不存在'}), 404

            # 构建动态查询，获取指定深度的所有节点和关系
            query_str = f"""
            MATCH path = (center {{name: $center}})-[*1..{depth}]-(connected)
            WITH center, connected, relationships(path) AS rels
            RETURN DISTINCT 
                center.name AS center_name,
                labels(center) AS center_labels,
                properties(center) AS center_props,
                connected.name AS connected_name,
                labels(connected) AS connected_labels,
                properties(connected) AS connected_props
            LIMIT $limit
            """

            result = session.run(query_str, center=center, limit=limit)

            # 收集所有节点和边
            nodes_dict = {}
            edges_set = set()
            
            # 添加中心节点
            nodes_dict[center] = {
                'id': center,
                'name': center,
                'labels': center_node['labels'],
                'properties': dict(center_node['props']) if center_node['props'] else {},
                'is_center': True
            }

            # 处理查询结果
            for record in result:
                connected_name = record['connected_name']
                
                # 添加连接节点
                if connected_name not in nodes_dict:
                    nodes_dict[connected_name] = {
                        'id': connected_name,
                        'name': connected_name,
                        'labels': record['connected_labels'],
                        'properties': dict(record['connected_props']) if record['connected_props'] else {}
                    }

            # 获取节点之间的所有关系
            if len(nodes_dict) > 1:
                node_names = list(nodes_dict.keys())
                relationships = session.run(
                    """
                    MATCH (n1)-[r]-(n2)
                    WHERE n1.name IN $names AND n2.name IN $names
                    RETURN n1.name AS source, n2.name AS target, type(r) AS relation_type,
                           properties(r) AS rel_props
                    """,
                    names=node_names
                )

                edges = []
                for record in relationships:
                    edge_key = (record['source'], record['target'], record['relation_type'])
                    edges_set.add(edge_key)
                    edges.append({
                        'source': record['source'],
                        'target': record['target'],
                        'relation_type': record['relation_type'],
                        'properties': dict(record['rel_props']) if record['rel_props'] else {}
                    })
            else:
                edges = []

            return jsonify({
                'status': 'success',
                'data': {
                    'center': center,
                    'depth': depth,
                    'nodes': list(nodes_dict.values()),
                    'edges': edges,
                    'node_count': len(nodes_dict),
                    'edge_count': len(edges)
                }
            })

    except Exception as e:
        logger.error(f"获取子图出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/graph/path', methods=['GET', 'POST'])
def find_path():
    """
    查找两个节点之间的最短路径
    参数: 
      - source (源节点)
      - target (目标节点)
      - max_length (最大路径长度，默认5)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        source = data.get('source', '')
        target = data.get('target', '')
        max_length = int(data.get('max_length', 5))

        if not source or not target:
            return jsonify({'status': 'error', 'message': '请提供源节点和目标节点'}), 400

        with get_session() as session:
            # 查找最短路径
            path_query = f"""
            MATCH path = shortestPath((s)-[*..{max_length}]-(t))
            WHERE s.name = $source AND t.name = $target
            WITH path, [node IN nodes(path) | node.name] AS node_names,
                 [rel IN relationships(path) | type(rel)] AS rel_types
            RETURN node_names, rel_types, length(path) AS path_length
            LIMIT 1
            """
            result = session.run(
                path_query,
                source=source, target=target
            )

            path_data = result.single()
            
            if not path_data:
                return jsonify({
                    'status': 'success',
                    'data': None,
                    'message': '未找到连接路径'
                })

            # 获取路径中的所有节点和边信息
            node_names = path_data['node_names']
            nodes = []
            edges = []

            # 获取节点详情
            for name in node_names:
                node = session.run(
                    """
                    MATCH (n {name: $name})
                    RETURN n.name AS name, labels(n) AS labels, properties(n) AS props
                    """,
                    name=name
                ).single()
                
                if node:
                    nodes.append({
                        'id': node['name'],
                        'name': node['name'],
                        'labels': node['labels'],
                        'properties': dict(node['props']) if node['props'] else {}
                    })

            # 获取路径中的边信息
            for i in range(len(node_names) - 1):
                edge_result = session.run(
                    """
                    MATCH (n1 {name: $source})-[r]-(n2 {name: $target})
                    RETURN type(r) AS relation_type, properties(r) AS rel_props
                    LIMIT 1
                    """,
                    source=node_names[i], target=node_names[i+1]
                ).single()

                if edge_result:
                    edges.append({
                        'source': node_names[i],
                        'target': node_names[i+1],
                        'relation_type': edge_result['relation_type'],
                        'properties': dict(edge_result['rel_props']) if edge_result['rel_props'] else {}
                    })

            return jsonify({
                'status': 'success',
                'data': {
                    'source': source,
                    'target': target,
                    'path_length': path_data['path_length'],
                    'nodes': nodes,
                    'edges': edges,
                    'node_count': len(nodes),
                    'edge_count': len(edges)
                }
            })

    except Exception as e:
        logger.error(f"查找路径出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/graph/stats', methods=['GET'])
def get_graph_stats():
    """
    获取图数据库统计信息
    """
    try:
        with get_session() as session:
            # 获取节点统计
            node_stats = session.run(
                """
                MATCH (n)
                RETURN labels(n)[0] AS label, count(*) AS count
                """
            )

            # 获取关系统计
            relation_stats = session.run(
                """
                MATCH ()-[r]-()
                RETURN type(r) AS relation_type, count(*) AS count
                """
            )

            nodes_by_label = {}
            for record in node_stats:
                label = record['label'] if record['label'] else 'Unknown'
                nodes_by_label[label] = record['count']

            relations_by_type = {}
            for record in relation_stats:
                rel_type = record['relation_type']
                relations_by_type[rel_type] = record['count']

            return jsonify({
                'status': 'success',
                'data': {
                    'nodes_by_label': nodes_by_label,
                    'relations_by_type': relations_by_type
                }
            })

    except Exception as e:
        logger.error(f"获取统计信息出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/edge/relations', methods=['GET', 'POST'])
def get_edge_relations():
    """
    查询两个节点之间的所有关系（边）
    参数: 
      - source (源节点名称)
      - target (目标节点名称)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        source = data.get('source', '')
        target = data.get('target', '')

        if not source or not target:
            return jsonify({'status': 'error', 'message': '请提供源节点和目标节点'}), 400

        with get_session() as session:
            # 查询两个节点之间的所有关系
            relations = session.run(
                """
                MATCH (s {name: $source})-[r]-(t {name: $target})
                RETURN s.name AS source, t.name AS target, type(r) AS relation_type,
                       properties(r) AS rel_props
                """,
                source=source, target=target
            )

            edges = []
            for record in relations:
                edges.append({
                    'source': record['source'],
                    'target': record['target'],
                    'relation_type': record['relation_type'],
                    'properties': dict(record['rel_props']) if record['rel_props'] else {}
                })

            return jsonify({
                'status': 'success',
                'data': {
                    'source': source,
                    'target': target,
                    'edges': edges,
                    'edge_count': len(edges)
                }
            })

    except Exception as e:
        logger.error(f"查询关系出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/edge/by-type/<relation_type>', methods=['GET', 'POST'])
def get_edges_by_type(relation_type):
    """
    查询特定类型的所有关系（边）
    参数:
      - relation_type (URL 路径参数：关系类型)
      - limit (返回数量限制，默认50)
    """
    try:
        data = request.args if request.method == 'GET' else request.get_json() or {}
        limit = int(data.get('limit', 50))

        with get_session() as session:
            # 查询特定类型的所有关系
            type_query = f"""
            MATCH (s)-[r:{relation_type}]->(t)
            RETURN s.name AS source, s AS source_node,
                   t.name AS target, t AS target_node,
                   type(r) AS relation_type, properties(r) AS rel_props
            LIMIT $limit
            """
            result = session.run(
                type_query,
                limit=limit
            )

            edges = []
            for record in result:
                edges.append({
                    'source': record['source'],
                    'target': record['target'],
                    'relation_type': record['relation_type'],
                    'properties': dict(record['rel_props']) if record['rel_props'] else {}
                })

            return jsonify({
                'status': 'success',
                'data': {
                    'relation_type': relation_type,
                    'edges': edges,
                    'total_count': len(edges)
                }
            })

    except Exception as e:
        logger.error(f"查询关系类型出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """处理 404 错误"""
    return jsonify({'status': 'error', 'message': '请求的接口不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500


def close_driver():
    """关闭数据库连接"""
    if driver:
        driver.close()


if __name__ == '__main__':
    try:
        # 测试 Neo4j 连接
        with get_session() as session:
            session.run("RETURN 1")
        logger.info("Neo4j 数据库连接成功")
    except Exception as e:
        logger.error(f"无法连接到 Neo4j 数据库: {e}")
        logger.error("请确保 Neo4j 数据库已启动，且凭证正确")

    # 启动 Flask 应用
    app.run(host='0.0.0.0', port=5007, debug=True)
