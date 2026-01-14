import os
# 设置环境变量以抑制警告
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["LOKY_MAX_CPU_COUNT"] = "1"

import json
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re
from datetime import datetime
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
import matplotlib.cm as cm
import matplotlib

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False


class HistoricalTimeMapper:
    """历史时间映射器 - 实现历史记录对照功能"""

    def __init__(self):
        # 秦朝到汉初的历史时间对照表
        self.dynasty_timeline = {
            '秦': (-221, -207),
            '秦二世': (-209, -207),
            '楚汉相争': (-206, -202),
            '西汉': (-202, 8)
        }

        # 常见历史时间表达模式
        self.time_patterns = {
            '年号模式': re.compile(r'[一二三四五六七八九十]+年'),
            '帝王模式': re.compile(r'[文武昭宣元成哀平]帝|[始二世]皇帝'),
            '季节模式': re.compile(r'[春夏秋冬]'),
            '干支模式': re.compile(r'[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]'),
            '数字年份': re.compile(r'\d+年')
        }

        # 历史事件时间对照表
        self.historical_events = {
            '秦统一': (-221, '秦始皇统一六国'),
            '陈胜起义': (-209, '大泽乡起义'),
            '巨鹿之战': (-207, '项羽破秦军主力'),
            '鸿门宴': (-206, '刘邦项羽会面'),
            '垓下之战': (-202, '楚汉决战'),
            '汉朝建立': (-202, '刘邦称帝')
        }

    def parse_time_expression(self, time_expr):
        """解析时间表达式，映射到标准历史时间"""
        time_expr = str(time_expr).strip()

        # 匹配年号模式
        if re.search(r'[一二三四五六七八九十]+年', time_expr):
            return self._parse_chinese_year(time_expr)

        # 匹配季节模式
        elif re.search(r'[春夏秋冬]', time_expr):
            return self._parse_season(time_expr)

        # 匹配帝王时期
        elif any(emperor in time_expr for emperor in ['始皇', '二世', '高祖', '怀王']):
            return self._parse_emperor_period(time_expr)

        # 默认返回原始表达式
        return {'original': time_expr, 'standardized': time_expr, 'period': '未知'}

    def _parse_chinese_year(self, time_expr):
        """解析中文年份"""
        year_mapping = {
            '元': 1, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }

        match = re.search(r'([一二三四五六七八九十元]+)年', time_expr)
        if match:
            year_str = match.group(1)
            year_num = year_mapping.get(year_str, 1)
            return {
                'original': time_expr,
                'standardized': f'第{year_str}年',
                'period': f'帝王纪年{year_num}',
                'year_value': year_num
            }
        return {'original': time_expr, 'standardized': time_expr, 'period': '未知'}

    def _parse_season(self, time_expr):
        """解析季节"""
        season_map = {'春': '春季', '夏': '夏季', '秋': '秋季', '冬': '冬季'}
        for char, season in season_map.items():
            if char in time_expr:
                return {
                    'original': time_expr,
                    'standardized': season,
                    'period': season,
                    'season': season
                }
        return {'original': time_expr, 'standardized': time_expr, 'period': '未知'}

    def _parse_emperor_period(self, time_expr):
        """解析帝王时期"""
        emperor_periods = {
            '始皇': {'period': '秦始皇时期', 'years': (-221, -210)},
            '二世': {'period': '秦二世时期', 'years': (-209, -207)},
            '高祖': {'period': '汉高祖时期', 'years': (-206, -195)},
            '怀王': {'period': '楚怀王时期', 'years': (-208, -205)}
        }

        for emperor, info in emperor_periods.items():
            if emperor in time_expr:
                return {
                    'original': time_expr,
                    'standardized': info['period'],
                    'period': info['period'],
                    'years': info['years']
                }

        return {'original': time_expr, 'standardized': time_expr, 'period': '未知'}

    def map_to_dynasty(self, time_info):
        """将时间信息映射到朝代"""
        if 'years' in time_info:
            years = time_info['years']
            if isinstance(years, tuple):
                for dynasty, (start, end) in self.dynasty_timeline.items():
                    if start <= years[0] <= end:
                        return dynasty
        return '未知朝代'

    def get_historical_context(self, time_expr):
        """获取历史背景信息"""
        time_info = self.parse_time_expression(time_expr)
        dynasty = self.map_to_dynasty(time_info)

        # 查找相近的历史事件
        nearby_events = []
        if 'years' in time_info:
            event_year = time_info['years'][0] if isinstance(time_info['years'], tuple) else -200
            for event, (year, desc) in self.historical_events.items():
                if abs(year - event_year) <= 5:  # 5年内的历史事件
                    nearby_events.append((event, desc, year))

        return {
            'time_info': time_info,
            'dynasty': dynasty,
            'nearby_events': nearby_events
        }


class TimeWindowManager:
    """时间窗口管理器 - 实现时间窗口设置功能"""

    def __init__(self):
        self.window_types = {
            'yearly': '按年划分',
            'dynasty': '按朝代划分',
            'seasonal': '按季节划分',
            'decade': '按十年划分',
            'custom': '自定义时间范围'
        }

    def create_time_windows(self, time_data, window_type='dynasty', custom_range=None):
        """创建时间窗口"""

        if window_type == 'dynasty':
            return self._create_dynasty_windows(time_data)
        elif window_type == 'yearly':
            return self._create_yearly_windows(time_data)
        elif window_type == 'seasonal':
            return self._create_seasonal_windows(time_data)
        elif window_type == 'decade':
            return self._create_decade_windows(time_data)
        elif window_type == 'custom' and custom_range:
            return self._create_custom_windows(time_data, custom_range)
        else:
            return self._create_dynasty_windows(time_data)  # 默认按朝代划分

    def _create_dynasty_windows(self, time_data):
        """按朝代划分时间窗口"""
        dynasty_windows = {
            '秦朝': {'start': -221, 'end': -207, 'events': []},
            '楚汉相争': {'start': -206, 'end': -202, 'events': []},
            '西汉初期': {'start': -202, 'end': -180, 'events': []}
        }

        for event in time_data:
            time_info = event.get('time_info', {})
            if 'years' in time_info:
                year = time_info['years'][0] if isinstance(time_info['years'], tuple) else -200

                for dynasty, window in dynasty_windows.items():
                    if window['start'] <= year <= window['end']:
                        window['events'].append(event)
                        break

        return dynasty_windows

    def _create_yearly_windows(self, time_data):
        """按年划分时间窗口"""
        yearly_windows = {}

        for event in time_data:
            time_info = event.get('time_info', {})
            if 'years' in time_info:
                year = time_info['years'][0] if isinstance(time_info['years'], tuple) else -200
                year_key = f"{abs(year)}BC" if year < 0 else f"{year}AD"

                if year_key not in yearly_windows:
                    yearly_windows[year_key] = {'year': year, 'events': []}
                yearly_windows[year_key]['events'].append(event)

        return yearly_windows

    def _create_seasonal_windows(self, time_data):
        """按季节划分时间窗口"""
        seasonal_windows = {
            '春季': {'events': []},
            '夏季': {'events': []},
            '秋季': {'events': []},
            '冬季': {'events': []},
            '未知季节': {'events': []}
        }

        for event in time_data:
            time_info = event.get('time_info', {})
            season = time_info.get('season', '未知季节')

            if season in seasonal_windows:
                seasonal_windows[season]['events'].append(event)
            else:
                seasonal_windows['未知季节']['events'].append(event)

        return seasonal_windows

    def _create_decade_windows(self, time_data):
        """按十年划分时间窗口"""
        decade_windows = {}

        for event in time_data:
            time_info = event.get('time_info', {})
            if 'years' in time_info:
                year = time_info['years'][0] if isinstance(time_info['years'], tuple) else -200
                decade = (year // 10) * 10
                decade_key = f"{abs(decade)}sBC" if decade < 0 else f"{decade}sAD"

                if decade_key not in decade_windows:
                    decade_windows[decade_key] = {'decade': decade, 'events': []}
                decade_windows[decade_key]['events'].append(event)

        return decade_windows

    def _create_custom_windows(self, time_data, custom_range):
        """自定义时间范围窗口"""
        start_year, end_year = custom_range
        custom_window = {
            'custom_range': f"{start_year}BC-{end_year}BC",
            'start': start_year,
            'end': end_year,
            'events': []
        }

        for event in time_data:
            time_info = event.get('time_info', {})
            if 'years' in time_info:
                year = time_info['years'][0] if isinstance(time_info['years'], tuple) else -200
                if start_year <= year <= end_year:
                    custom_window['events'].append(event)

        return {'custom_window': custom_window}

    def analyze_window_statistics(self, windows):
        """分析时间窗口统计信息"""
        stats = {}

        for window_name, window_data in windows.items():
            events = window_data.get('events', [])
            stats[window_name] = {
                'event_count': len(events),
                'event_types': Counter([event.get('event_type', '未知') for event in events]),
                'time_patterns': Counter([event.get('time_info', {}).get('period', '未知') for event in events])
            }

        return stats


class TimeExpressionClusterAnalyzer:
    """
    时间表达式聚类分析器 - 基础版本
    """

    def __init__(self, data):
        """
        时间表达式聚类分析器
        """
        self.data = data
        self.time_expressions = self._extract_time_expressions()
        self.df = self._create_time_dataframe()
        self.cluster_results = None

    def _extract_time_expressions(self):
        """从数据中提取所有时间表达式"""
        time_expressions = []

        for item in self.data:
            text = item['text']
            event_list = item['event_list']

            for event in event_list:
                for arg in event['arguments']:
                    if arg['role'] == '时间':
                        time_expressions.append({
                            'text': text,
                            'time_expression': arg['argument'],
                            'event_type': event['event_type'],
                            'trigger': event['trigger'],
                            'affiliated': item.get('affiliated', '-1')
                        })

        return time_expressions

    def _create_time_dataframe(self):
        """创建时间表达式数据框"""
        return pd.DataFrame(self.time_expressions)

    def analyze_time_expression_patterns(self):
        """分析时间表达式的模式"""
        time_exprs = self.df['time_expression'].tolist()

        # 分析时间表达式的长度分布
        length_dist = [len(str(expr)) for expr in time_exprs]

        # 分析时间表达式的词汇特征
        word_patterns = Counter()
        for expr in time_exprs:
            words = re.findall(r'[\u4e00-\u9fff]+', str(expr))
            for word in words:
                word_patterns[word] += 1

        # 分析时间表达式的事件类型分布
        event_type_dist = self.df['event_type'].value_counts()

        return {
            'total_time_expressions': len(time_exprs),
            'avg_length': np.mean(length_dist),
            'unique_expressions': len(set(time_exprs)),
            'common_words': word_patterns.most_common(20),
            'event_type_distribution': event_type_dist,
            'length_distribution': length_dist
        }

    def extract_time_features(self):
        """提取时间表达式的特征"""
        time_exprs = self.df['time_expression'].tolist()

        # 特征1: 时间表达式长度
        length_features = [len(str(expr)) for expr in time_exprs]

        # 特征2: 是否包含数字
        has_digit = [1 if re.search(r'\d', str(expr)) else 0 for expr in time_exprs]

        # 特征3: 是否包含时间关键词
        time_keywords = ['年', '月', '日', '春', '夏', '秋', '冬', '朝', '夕', '夜']
        keyword_features = []
        for expr in time_exprs:
            keyword_count = sum(1 for keyword in time_keywords if keyword in str(expr))
            keyword_features.append(keyword_count)

        # 特征4: 词汇丰富度（独特字符数）
        vocab_richness = [len(set(str(expr))) for expr in time_exprs]

        # 特征5: 事件类型编码（简化版）
        event_type_mapping = {et: i for i, et in enumerate(self.df['event_type'].unique())}
        event_type_features = [event_type_mapping[et] for et in self.df['event_type']]

        # 创建特征矩阵
        feature_matrix = np.column_stack([
            length_features,
            has_digit,
            keyword_features,
            vocab_richness,
            event_type_features
        ])

        return feature_matrix, time_exprs

    def perform_time_clustering(self, n_clusters=5, method='kmeans'):
        """执行时间表达式聚类"""
        # 提取特征
        feature_matrix, time_exprs = self.extract_time_features()

        # 标准化特征
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(feature_matrix)

        # 选择聚类方法
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=n_clusters, random_state=42)
        elif method == 'hierarchical':
            clusterer = AgglomerativeClustering(n_clusters=n_clusters)
        elif method == 'dbscan':
            clusterer = DBSCAN(eps=0.5, min_samples=2)
        else:
            clusterer = KMeans(n_clusters=n_clusters, random_state=42)

        # 执行聚类
        clusters = clusterer.fit_predict(features_scaled)

        # 计算轮廓系数
        if len(np.unique(clusters)) > 1:
            silhouette_avg = silhouette_score(features_scaled, clusters)
        else:
            silhouette_avg = -1  # 无法计算单一簇的轮廓系数

        # 保存结果
        self.cluster_results = {
            'time_expressions': time_exprs,
            'clusters': clusters,
            'features': features_scaled,
            'silhouette_score': silhouette_avg,
            'feature_matrix': feature_matrix,
            'event_types': self.df['event_type'].tolist(),
            'original_texts': self.df['text'].tolist()
        }

        return self.cluster_results

    def visualize_time_clusters(self, output_file='output/image/time_clusters.png'):
        """可视化时间表达式聚类结果 - 显示所有时间点"""
        if self.cluster_results is None:
            return

        # PCA降维可视化
        pca = PCA(n_components=2)
        features_2d = pca.fit_transform(self.cluster_results['features'])

        plt.figure(figsize=(16, 12))

        # 创建散点图
        scatter = plt.scatter(features_2d[:, 0], features_2d[:, 1],
                              c=self.cluster_results['clusters'],
                              cmap='tab10', s=80, alpha=0.7)

        # 添加所有时间表达式标签
        for i, (x, y) in enumerate(features_2d):
            plt.annotate(self.cluster_results['time_expressions'][i],
                         (x, y),
                         xytext=(5, 5), textcoords='offset points',
                         fontsize=6, alpha=0.7,  # 减小字体大小
                         bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3))

        plt.colorbar(scatter, label='聚类编号')
        plt.title(f'时间表达式聚类分析\n轮廓系数: {self.cluster_results["silhouette_score"]:.3f}')
        plt.xlabel('PCA主成分1')
        plt.ylabel('PCA主成分2')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)

    def analyze_cluster_time_patterns(self):
        """分析每个聚类的时间模式特征"""
        if self.cluster_results is None:
            return None

        results = []
        unique_clusters = np.unique(self.cluster_results['clusters'])

        for cluster_id in unique_clusters:
            cluster_indices = np.where(self.cluster_results['clusters'] == cluster_id)[0]
            cluster_times = [self.cluster_results['time_expressions'][i] for i in cluster_indices]
            cluster_events = [self.cluster_results['event_types'][i] for i in cluster_indices]

            # 计算聚类统计特征
            cluster_features = self.cluster_results['feature_matrix'][cluster_indices]

            if len(cluster_features) > 0:
                centroid = np.mean(cluster_features, axis=0)

                # 分析时间表达式模式
                time_patterns = {
                    'avg_length': centroid[0],
                    'digit_ratio': np.mean([1 if re.search(r'\d', str(t)) else 0
                                            for t in cluster_times]),
                    'common_words': self._extract_common_words(cluster_times),
                    'event_type_dist': Counter(cluster_events).most_common(5)
                }

                results.append({
                    'cluster_id': cluster_id,
                    'num_expressions': len(cluster_times),
                    'example_times': cluster_times[:5],  # 显示前5个例子
                    'time_patterns': time_patterns
                })

        return results

    def _extract_common_words(self, time_expressions, top_n=5):
        """提取时间表达式中的常见词汇"""
        all_words = []
        for expr in time_expressions:
            words = re.findall(r'[\u4e00-\u9fff]+', str(expr))
            all_words.extend(words)

        return Counter(all_words).most_common(top_n)

    def generate_time_analysis_report(self):
        """生成时间维度分析报告"""
        # 时间表达式模式分析
        patterns = self.analyze_time_expression_patterns()

        if self.cluster_results is not None:
            cluster_analysis = self.analyze_cluster_time_patterns()

    def plot_time_length_distribution(self):
        """绘制时间表达式长度分布图"""
        patterns = self.analyze_time_expression_patterns()

        plt.figure(figsize=(12, 6))
        plt.hist(patterns['length_distribution'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        plt.xlabel('时间表达式长度（字符数）')
        plt.ylabel('频次')
        plt.title('时间表达式长度分布')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('output/image/time_length_distribution.png')

    def save_cluster_results(self, filename='output/csv/time_expression_clusters.csv'):
        """保存聚类结果到文件"""
        if self.cluster_results is None:
            return

        output_df = pd.DataFrame({
            'time_expression': self.cluster_results['time_expressions'],
            'cluster_id': self.cluster_results['clusters'],
            'event_type': self.cluster_results['event_types'],
            'original_text': self.cluster_results['original_texts']
        })

        output_df.to_csv(filename, index=False, encoding='utf-8-sig')


class EnhancedTimeExpressionClusterAnalyzer(TimeExpressionClusterAnalyzer):
    """增强版时间表达式聚类分析器 - 整合历史对照和时间窗口功能"""

    def __init__(self, data):
        super().__init__(data)
        self.time_mapper = HistoricalTimeMapper()
        self.window_manager = TimeWindowManager()
        self.historical_data = None

    def enhance_with_historical_context(self):
        """用历史背景信息增强时间数据"""
        enhanced_data = []

        for i, time_expr in enumerate(self.time_expressions):
            historical_context = self.time_mapper.get_historical_context(time_expr['time_expression'])

            enhanced_event = {
                **time_expr,
                'time_info': historical_context['time_info'],
                'dynasty': historical_context['dynasty'],
                'nearby_events': historical_context['nearby_events'],
                'historical_period': historical_context['time_info'].get('period', '未知')
            }
            enhanced_data.append(enhanced_event)

        self.historical_data = enhanced_data
        return enhanced_data

    def analyze_time_windows(self, window_type='dynasty'):
        """分析时间窗口"""
        if self.historical_data is None:
            self.enhance_with_historical_context()

        windows = self.window_manager.create_time_windows(self.historical_data, window_type)
        statistics = self.window_manager.analyze_window_statistics(windows)

        return {
            'windows': windows,
            'statistics': statistics,
            'window_type': window_type
        }

    def visualize_historical_timeline(self, output_file='output/image/historical_timeline.png'):
        """可视化历史时间线 - 显示所有时间点"""
        if self.historical_data is None:
            self.enhance_with_historical_context()
        
        if self.historical_data is None:
            return

        # 提取时间信息
        time_points = []
        for event in self.historical_data:
            time_info = event.get('time_info', {})
            if 'years' in time_info:
                year = time_info['years'][0] if isinstance(time_info['years'], tuple) else -200
                time_points.append({
                    'year': year,
                    'event_type': event['event_type'],
                    'time_expression': event['time_expression'],
                    'dynasty': event.get('dynasty', '未知')
                })

        if not time_points:
            return

        # 创建时间线图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))

        # 时间点分布图 - 改进版本
        years = [point['year'] for point in time_points]
        event_types = [point['event_type'] for point in time_points]
        time_expressions = [point['time_expression'] for point in time_points]

        # 按事件类型着色
        unique_event_types = list(set(event_types))
        # colors = plt.cm.Set3(np.linspace(0, 1, len(unique_event_types)))
        cmap = plt.get_cmap('Set3')
        colors = cmap(np.linspace(0, 1, len(unique_event_types)))
        color_map = dict(zip(unique_event_types, colors))

        # 使用不同的y位置来避免重叠
        y_positions = np.linspace(0, len(unique_event_types) - 1, len(years))

        for i, (year, event_type, time_expr, y_pos) in enumerate(
                zip(years, event_types, time_expressions, y_positions)):
            ax1.scatter(year, y_pos, color=color_map[event_type],
                        s=100, alpha=0.7)

            # 为每个点添加标签
            ax1.annotate(f"{time_expr} ({event_type})",
                         (year, y_pos),
                         xytext=(8, 0), textcoords='offset points',
                         fontsize=7, alpha=0.8,
                         bbox=dict(boxstyle='round,pad=0.2', fc='white', alpha=0.7))

        ax1.set_xlabel('年份 (BC)', fontsize=12)
        ax1.set_ylabel('事件位置', fontsize=12)
        ax1.set_title('历史事件时间线分布 (显示所有时间点)', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)

        # 添加图例
        legend_elements = [Line2D([0], [0], marker='o', color='w',
                                      markerfacecolor=color_map[et], markersize=8, label=et)
                           for et in unique_event_types]
        ax1.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')

        # 事件密度图 - 改进版本
        dynasty_order = ['秦', '楚汉相争', '西汉', '未知朝代']
        dynasty_data = {dynasty: [] for dynasty in dynasty_order}
        dynasty_time_exprs = {dynasty: [] for dynasty in dynasty_order}

        for point in time_points:
            dynasty = point['dynasty']
            if dynasty in dynasty_data:
                dynasty_data[dynasty].append(point['year'])
                dynasty_time_exprs[dynasty].append(point['time_expression'])

        dynasty_labels = []
        dynasty_values = []
        for dynasty in dynasty_order:
            if dynasty_data[dynasty]:
                dynasty_labels.append(dynasty)
                dynasty_values.append(len(dynasty_data[dynasty]))

        bars = ax2.bar(dynasty_labels, dynasty_values, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])

        # 在柱状图上添加数值和时间表达式数量
        for bar, dynasty in zip(bars, dynasty_labels):
            height = bar.get_height()
            time_expr_count = len(set(dynasty_time_exprs[dynasty]))  # 唯一时间表达式数量
            ax2.text(bar.get_x() + bar.get_width() / 2., height + 0.1,
                     f'{height}事件\n{time_expr_count}种时间表达',
                     ha='center', va='bottom', fontsize=9)

        ax2.set_ylabel('事件数量', fontsize=12)
        ax2.set_title('各朝代事件数量分布', fontsize=14, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300)

    def visualize_time_windows(self, window_type='dynasty'):
        """可视化时间窗口分析结果 - 显示详细信息"""
        output_file = f'output/image/time_windows_{window_type}.png'
        window_analysis = self.analyze_time_windows(window_type)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

        # 窗口事件数量分布
        window_names = list(window_analysis['statistics'].keys())
        event_counts = [stats['event_count'] for stats in window_analysis['statistics'].values()]

        bars = ax1.barh(window_names, event_counts, color='skyblue')

        # 在条形图上添加数值标签
        for bar, count in zip(bars, event_counts):
            width = bar.get_width()
            ax1.text(width + 0.1, bar.get_y() + bar.get_height() / 2.,
                     f'{count}事件', ha='left', va='center', fontsize=10)

        ax1.set_xlabel('事件数量')
        ax1.set_title(f'{window_type}时间窗口事件分布', fontsize=14, fontweight='bold')

        # 事件类型分布（堆叠柱状图）
        if window_analysis['statistics']:
            # 收集所有事件类型
            all_event_types = set()
            for stats in window_analysis['statistics'].values():
                all_event_types.update(stats['event_types'].keys())
            event_types = sorted(list(all_event_types))

            window_event_data = []
            window_names_list = []
            for window_name, stats in window_analysis['statistics'].items():
                if stats['event_count'] > 0:  # 只显示有事件的窗口
                    type_counts = [stats['event_types'].get(event_type, 0) for event_type in event_types]
                    window_event_data.append(type_counts)
                    window_names_list.append(window_name)

            if window_event_data:
                window_event_data = np.array(window_event_data)
                bottom = np.zeros(len(window_names_list))

                cmap = plt.get_cmap('Paired')
                colors = cmap(np.linspace(0, 1, len(event_types)))
                for i, (event_type, color) in enumerate(zip(event_types, colors)):
                    ax2.barh(window_names_list, window_event_data[:, i], left=bottom,
                             label=event_type, color=color, alpha=0.8)
                    bottom += window_event_data[:, i]

                ax2.set_xlabel('事件数量')
                ax2.set_title('时间窗口内事件类型分布', fontsize=14, fontweight='bold')
                ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300)

    def generate_comprehensive_report(self):
        """生成完整的时间维度分析报告"""
        print("=" * 80)
        print("完整时间维度群像建模分析报告")
        print("=" * 80)

        # 基础分析
        patterns = self.analyze_time_expression_patterns()

        # 历史对照分析
        if self.historical_data is None:
            self.enhance_with_historical_context()

        if self.historical_data is None:
            return

        dynasty_dist = Counter([event.get('dynasty', '未知') for event in self.historical_data])
        period_dist = Counter([event.get('historical_period', '未知') for event in self.historical_data])

        # 时间窗口分析
        window_types = ['dynasty', 'yearly', 'seasonal']
        for window_type in window_types:
            window_analysis = self.analyze_time_windows(window_type)

        # 聚类分析
        if self.cluster_results is not None:
            cluster_analysis = self.analyze_cluster_time_patterns()


# 主程序
def main():
    # 读取数据
    with open("output/historical_relations/EE-Hangaozubenji_updated.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 创建增强版时间分析器
    enhanced_analyzer = EnhancedTimeExpressionClusterAnalyzer(data)

    # 1. 基础聚类分析
    enhanced_analyzer.perform_time_clustering(n_clusters=5, method='kmeans')

    # 2. 历史记录对照
    enhanced_analyzer.enhance_with_historical_context()

    # 3. 时间窗口分析
    window_analysis = enhanced_analyzer.analyze_time_windows('dynasty')

    # 4. 生成完整报告
    enhanced_analyzer.generate_comprehensive_report()

    # 5. 可视化分析
    enhanced_analyzer.visualize_time_clusters()
    enhanced_analyzer.visualize_historical_timeline()
    enhanced_analyzer.visualize_time_windows('dynasty')
    enhanced_analyzer.visualize_time_windows('seasonal')

    # 6. 保存结果
    enhanced_analyzer.save_cluster_results('output/csv/enhanced_time_analysis_results.csv')


if __name__ == "__main__":
    main()