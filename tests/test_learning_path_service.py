"""
学习路径服务单元测试
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.backend.services.learning_path_service import (
    LearningPathService,
    UserProfile,
    LearningTarget,
    StudySession,
    LearningPathNode,
    GeneratedLearningPath,
    DependencyResolver,
    DifficultyCalculator,
    TimeEstimator
)

class TestDependencyResolver(unittest.TestCase):
    """依赖关系解析器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.resolver = DependencyResolver()
    
    def test_add_knowledge_point(self):
        """测试添加知识点"""
        self.resolver.add_knowledge_point(
            'kp1', 
            [], 
            name="基础知识", 
            difficulty_level=1
        )
        
        self.assertIn('kp1', self.resolver.node_data)
        self.assertEqual(self.resolver.node_data['kp1']['name'], "基础知识")
    
    def test_topological_sort_simple(self):
        """测试简单拓扑排序"""
        # 添加知识点: A -> B -> C
        self.resolver.add_knowledge_point('A', [])
        self.resolver.add_knowledge_point('B', ['A'])
        self.resolver.add_knowledge_point('C', ['B'])
        
        result = self.resolver.topological_sort(['A', 'B', 'C'])
        
        # A应该在B之前，B应该在C之前
        self.assertEqual(result.index('A'), 0)
        self.assertTrue(result.index('A') < result.index('B'))
        self.assertTrue(result.index('B') < result.index('C'))
    
    def test_topological_sort_complex(self):
        """测试复杂拓扑排序"""
        # 复杂依赖图
        # A    D
        # |    |
        # B -> E
        # |    |
        # C -> F
        
        self.resolver.add_knowledge_point('A', [])
        self.resolver.add_knowledge_point('B', ['A'])
        self.resolver.add_knowledge_point('C', ['B'])
        self.resolver.add_knowledge_point('D', [])
        self.resolver.add_knowledge_point('E', ['B', 'D'])
        self.resolver.add_knowledge_point('F', ['C', 'E'])
        
        result = self.resolver.topological_sort(['A', 'B', 'C', 'D', 'E', 'F'])
        
        # 验证依赖关系
        self.assertTrue(result.index('A') < result.index('B'))
        self.assertTrue(result.index('B') < result.index('C'))
        self.assertTrue(result.index('B') < result.index('E'))
        self.assertTrue(result.index('D') < result.index('E'))
        self.assertTrue(result.index('C') < result.index('F'))
        self.assertTrue(result.index('E') < result.index('F'))
    
    def test_get_critical_path(self):
        """测试关键路径获取"""
        # 线性路径: A -> B -> C -> D
        self.resolver.add_knowledge_point('A', [])
        self.resolver.add_knowledge_point('B', ['A'])
        self.resolver.add_knowledge_point('C', ['B'])
        self.resolver.add_knowledge_point('D', ['C'])
        
        critical_path = self.resolver.get_critical_path(['A', 'B', 'C', 'D'])
        
        # 在线性路径中，最后一个节点应该在关键路径上
        self.assertIn('D', critical_path)


class TestDifficultyCalculator(unittest.TestCase):
    """难度计算器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.calculator = DifficultyCalculator()
        self.user_profile = UserProfile(
            user_id="test_user",
            current_knowledge_levels={"kp1": 0.8, "kp2": 0.3, "kp3": 0.0},
            learning_preferences={},
            available_study_hours_per_day=2.0,
            target_completion_date=None,
            difficulty_preference=3,
            learning_style="visual",
            weak_areas=["kp3"],
            strong_areas=["kp1"]
        )
    
    def test_calculate_adaptive_difficulty(self):
        """测试适应性难度计算"""
        # 已掌握的知识点
        difficulty1 = self.calculator.calculate_adaptive_difficulty(
            self.user_profile, "kp1", 3
        )
        
        # 部分掌握的知识点
        difficulty2 = self.calculator.calculate_adaptive_difficulty(
            self.user_profile, "kp2", 3
        )
        
        # 未掌握的知识点
        difficulty3 = self.calculator.calculate_adaptive_difficulty(
            self.user_profile, "kp3", 3
        )
        
        # 已掌握的应该更容易
        self.assertTrue(difficulty1 < difficulty3)
        # 部分掌握的应该在中间
        self.assertTrue(difficulty2 < difficulty3)
        self.assertTrue(difficulty1 < difficulty2)
    
    def test_calculate_priority_score(self):
        """测试优先级分数计算"""
        target = LearningTarget(
            target_knowledge_points=["kp1", "kp2"],
            target_mastery_level=0.8,
            priority_level=3,
            deadline=datetime.now() + timedelta(days=30)
        )
        
        # 目标知识点应该有更高优先级
        score1 = self.calculator.calculate_priority_score(
            "kp1", self.user_profile, target, 0, 0
        )
        
        score2 = self.calculator.calculate_priority_score(
            "kp3", self.user_profile, target, 0, 0
        )
        
        self.assertTrue(score1 > score2)
    
    def test_priority_score_with_dependencies(self):
        """测试带依赖的优先级分数"""
        target = LearningTarget(
            target_knowledge_points=["kp2"],
            target_mastery_level=0.8,
            priority_level=3,
            deadline=None
        )
        
        # 依赖完成度高的应该有更高优先级
        score_high_deps = self.calculator.calculate_priority_score(
            "kp2", self.user_profile, target, 2, 2  # 依赖全部完成
        )
        
        score_low_deps = self.calculator.calculate_priority_score(
            "kp2", self.user_profile, target, 1, 2  # 依赖部分完成
        )
        
        self.assertTrue(score_high_deps > score_low_deps)


class TestTimeEstimator(unittest.TestCase):
    """时间估算器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.estimator = TimeEstimator()
        self.user_profile = UserProfile(
            user_id="test_user",
            current_knowledge_levels={"kp1": 0.8, "kp2": 0.3, "kp3": 0.0},
            learning_preferences={},
            available_study_hours_per_day=2.0,
            target_completion_date=None,
            difficulty_preference=3,
            learning_style="visual",
            weak_areas=[],
            strong_areas=[]
        )
    
    def test_estimate_study_time(self):
        """测试学习时间估算"""
        # 已掌握的知识点
        kp_data1 = {
            'id': 'kp1',
            'estimated_study_hours': 2.0,
            'difficulty_level': 3
        }
        
        time1 = self.estimator.estimate_study_time(kp_data1, self.user_profile)
        
        # 未掌握的知识点
        kp_data2 = {
            'id': 'kp3',
            'estimated_study_hours': 2.0,
            'difficulty_level': 3
        }
        
        time2 = self.estimator.estimate_study_time(kp_data2, self.user_profile)
        
        # 已掌握的应该需要更少时间
        self.assertTrue(time1 < time2)
        
        # 时间应该大于0
        self.assertTrue(time1 > 0)
        self.assertTrue(time2 > 0)
    
    def test_schedule_study_sessions(self):
        """测试学习会话安排"""
        start_date = datetime(2024, 1, 1)
        
        sessions = self.estimator.schedule_study_sessions(
            total_hours=6.0,
            daily_hours=2.0,
            start_date=start_date
        )
        
        # 应该有3天的会话
        self.assertEqual(len(sessions), 3)
        
        # 检查日期顺序
        for i in range(1, len(sessions)):
            self.assertTrue(sessions[i] > sessions[i-1])
    
    def test_schedule_with_excluded_dates(self):
        """测试排除特定日期的会话安排"""
        start_date = datetime(2024, 1, 1)  # 星期一
        excluded_dates = [datetime(2024, 1, 2)]  # 排除星期二
        
        sessions = self.estimator.schedule_study_sessions(
            total_hours=4.0,
            daily_hours=2.0,
            start_date=start_date,
            excluded_dates=excluded_dates
        )
        
        # 不应该包含被排除的日期
        session_dates = [s.date() for s in sessions]
        self.assertNotIn(excluded_dates[0].date(), session_dates)


class TestLearningPathService(unittest.TestCase):
    """学习路径服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.service = LearningPathService()
        
        # 创建测试用户档案
        self.user_profile = UserProfile(
            user_id="test_user",
            current_knowledge_levels={"java_basic": 0.8, "oop": 0.3, "design_patterns": 0.0},
            learning_preferences={"style": "practical"},
            available_study_hours_per_day=2.0,
            target_completion_date=datetime.now() + timedelta(days=60),
            difficulty_preference=3,
            learning_style="visual",
            weak_areas=["design_patterns"],
            strong_areas=["java_basic"]
        )
        
        # 创建测试学习目标
        self.target = LearningTarget(
            target_knowledge_points=["java_basic", "oop", "design_patterns"],
            target_mastery_level=0.8,
            priority_level=3,
            deadline=datetime.now() + timedelta(days=45)
        )
        
        # 初始化知识图谱
        knowledge_points = [
            {
                'id': 'java_basic',
                'name': 'Java基础',
                'prerequisites': [],
                'estimated_study_hours': 10.0,
                'difficulty_level': 2
            },
            {
                'id': 'oop',
                'name': '面向对象编程',
                'prerequisites': ['java_basic'],
                'estimated_study_hours': 15.0,
                'difficulty_level': 3
            },
            {
                'id': 'design_patterns',
                'name': '设计模式',
                'prerequisites': ['java_basic', 'oop'],
                'estimated_study_hours': 20.0,
                'difficulty_level': 4
            }
        ]
        
        self.service.initialize_knowledge_graph(knowledge_points)
    
    def test_generate_learning_path(self):
        """测试学习路径生成"""
        path = self.service.generate_learning_path(self.user_profile, self.target)
        
        self.assertIsInstance(path, GeneratedLearningPath)
        self.assertEqual(path.user_id, "test_user")
        self.assertTrue(len(path.nodes) > 0)
        self.assertTrue(len(path.study_sessions) > 0)
        self.assertTrue(path.total_estimated_hours > 0)
        self.assertIsNotNone(path.estimated_completion_date)
    
    def test_learning_path_dependency_order(self):
        """测试学习路径依赖顺序"""
        path = self.service.generate_learning_path(self.user_profile, self.target)
        
        # 找到各知识点在路径中的位置
        node_positions = {}
        for i, node in enumerate(path.nodes):
            node_positions[node.knowledge_point_id] = i
        
        # 验证依赖顺序
        if 'java_basic' in node_positions and 'oop' in node_positions:
            self.assertTrue(node_positions['java_basic'] < node_positions['oop'])
        
        if 'oop' in node_positions and 'design_patterns' in node_positions:
            self.assertTrue(node_positions['oop'] < node_positions['design_patterns'])
    
    def test_optimize_learning_order(self):
        """测试学习顺序优化"""
        # 创建测试节点
        nodes = [
            LearningPathNode(
                knowledge_point_id='java_basic',
                knowledge_point_name='Java基础',
                estimated_study_time=5.0,
                difficulty_level=2,
                prerequisites=[],
                dependents=['oop'],
                priority_score=8.0,
                recommended_order=0
            ),
            LearningPathNode(
                knowledge_point_id='oop',
                knowledge_point_name='面向对象',
                estimated_study_time=8.0,
                difficulty_level=3,
                prerequisites=['java_basic'],
                dependents=['design_patterns'],
                priority_score=6.0,
                recommended_order=1
            ),
            LearningPathNode(
                knowledge_point_id='design_patterns',
                knowledge_point_name='设计模式',
                estimated_study_time=12.0,
                difficulty_level=4,
                prerequisites=['java_basic', 'oop'],
                dependents=[],
                priority_score=10.0,
                recommended_order=2
            )
        ]
        
        optimized = self.service._optimize_learning_order(nodes)
        
        # 应该保持依赖顺序
        positions = {node.knowledge_point_id: i for i, node in enumerate(optimized)}
        self.assertTrue(positions['java_basic'] < positions['oop'])
        self.assertTrue(positions['oop'] < positions['design_patterns'])
    
    def test_generate_study_sessions(self):
        """测试学习会话生成"""
        nodes = [
            LearningPathNode(
                knowledge_point_id='test_kp',
                knowledge_point_name='测试知识点',
                estimated_study_time=2.5,  # 2.5小时，应该分解为多个会话
                difficulty_level=3,
                prerequisites=[],
                dependents=[],
                priority_score=5.0,
                recommended_order=0
            )
        ]
        
        sessions = self.service._generate_study_sessions(nodes, self.user_profile)
        
        self.assertTrue(len(sessions) > 1)  # 应该分解为多个会话
        
        # 检查会话属性
        for session in sessions:
            self.assertIsInstance(session, StudySession)
            self.assertEqual(session.knowledge_point_id, 'test_kp')
            self.assertTrue(session.estimated_duration_minutes > 0)
            self.assertIn(session.session_type, ['learn', 'practice', 'review'])
    
    def test_generate_milestones(self):
        """测试里程碑生成"""
        nodes = [
            LearningPathNode(
                knowledge_point_id=f'kp_{i}',
                knowledge_point_name=f'知识点{i}',
                estimated_study_time=2.0,
                difficulty_level=2,
                prerequisites=[],
                dependents=[],
                priority_score=5.0,
                recommended_order=i
            ) for i in range(10)
        ]
        
        completion_date = datetime.now() + timedelta(days=30)
        milestones = self.service._generate_milestones(nodes, completion_date)
        
        self.assertTrue(len(milestones) > 0)
        
        # 检查里程碑格式
        for milestone in milestones:
            self.assertIn('percentage', milestone)
            self.assertIn('knowledge_point_id', milestone)
            self.assertIn('estimated_date', milestone)
            self.assertTrue(0 < milestone['percentage'] <= 100)
    
    def test_update_learning_progress(self):
        """测试学习进度更新"""
        progress_update = self.service.update_learning_progress(
            path_id="test_path",
            knowledge_point_id="java_basic",
            new_mastery_level=0.9,
            study_time_minutes=120
        )
        
        self.assertIn('path_id', progress_update)
        self.assertIn('knowledge_point_id', progress_update)
        self.assertIn('new_mastery_level', progress_update)
        self.assertIn('recommendations', progress_update)
        self.assertEqual(progress_update['new_mastery_level'], 0.9)
    
    def test_generate_review_schedule(self):
        """测试复习计划生成"""
        completed_kps = ["java_basic", "oop"]
        
        review_schedule = self.service.generate_review_schedule(
            self.user_profile, completed_kps
        )
        
        self.assertIsInstance(review_schedule, list)
        
        # 检查复习项目
        for review_item in review_schedule:
            self.assertIn('knowledge_point_id', review_item)
            self.assertIn('review_date', review_item)
            self.assertIn('duration_minutes', review_item)
            self.assertIn('interval_days', review_item)
            self.assertIn(review_item['knowledge_point_id'], completed_kps)
    
    def test_analyze_learning_efficiency(self):
        """测试学习效率分析"""
        completed_sessions = [
            {
                'knowledge_point_id': 'java_basic',
                'actual_duration_minutes': 90,
                'difficulty_level': 2,
                'time_of_day': 'morning',
                'effectiveness_score': 0.8
            },
            {
                'knowledge_point_id': 'oop',
                'actual_duration_minutes': 120,
                'difficulty_level': 3,
                'time_of_day': 'afternoon',
                'effectiveness_score': 0.6
            },
            {
                'knowledge_point_id': 'design_patterns',
                'actual_duration_minutes': 150,
                'difficulty_level': 4,
                'time_of_day': 'morning',
                'effectiveness_score': 0.9
            }
        ]
        
        analysis = self.service.analyze_learning_efficiency(
            self.user_profile, completed_sessions
        )
        
        self.assertIn('total_sessions', analysis)
        self.assertIn('total_study_time_hours', analysis)
        self.assertIn('efficiency_score', analysis)
        self.assertIn('by_status', analysis)
        self.assertIn('recommendations', analysis)
        
        self.assertEqual(analysis['total_sessions'], 3)
        self.assertTrue(analysis['total_study_time_hours'] > 0)
        self.assertTrue(0 <= analysis['efficiency_score'] <= 1)


class TestLearningPathIntegration(unittest.TestCase):
    """学习路径集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.service = LearningPathService()
    
    def test_complex_dependency_graph(self):
        """测试复杂依赖图的路径生成"""
        # 创建复杂的知识图谱
        knowledge_points = [
            {'id': 'math', 'name': '数学基础', 'prerequisites': [], 'estimated_study_hours': 20, 'difficulty_level': 2},
            {'id': 'programming', 'name': '编程基础', 'prerequisites': [], 'estimated_study_hours': 15, 'difficulty_level': 2},
            {'id': 'algorithms', 'name': '算法', 'prerequisites': ['math', 'programming'], 'estimated_study_hours': 25, 'difficulty_level': 4},
            {'id': 'data_structures', 'name': '数据结构', 'prerequisites': ['programming'], 'estimated_study_hours': 20, 'difficulty_level': 3},
            {'id': 'system_design', 'name': '系统设计', 'prerequisites': ['algorithms', 'data_structures'], 'estimated_study_hours': 30, 'difficulty_level': 5}
        ]
        
        self.service.initialize_knowledge_graph(knowledge_points)
        
        user_profile = UserProfile(
            user_id="advanced_user",
            current_knowledge_levels={},
            learning_preferences={},
            available_study_hours_per_day=3.0,
            target_completion_date=datetime.now() + timedelta(days=90),
            difficulty_preference=4,
            learning_style="reading",
            weak_areas=[],
            strong_areas=[]
        )
        
        target = LearningTarget(
            target_knowledge_points=['system_design'],
            target_mastery_level=0.8,
            priority_level=4,
            deadline=datetime.now() + timedelta(days=75)
        )
        
        path = self.service.generate_learning_path(user_profile, target)
        
        # 验证路径包含所有必要的知识点
        node_ids = [node.knowledge_point_id for node in path.nodes]
        self.assertIn('math', node_ids)
        self.assertIn('programming', node_ids)
        self.assertIn('algorithms', node_ids)
        self.assertIn('data_structures', node_ids)
        self.assertIn('system_design', node_ids)
        
        # 验证依赖顺序
        positions = {node_id: node_ids.index(node_id) for node_id in node_ids}
        
        # math和programming应该在algorithms之前
        self.assertTrue(positions['math'] < positions['algorithms'])
        self.assertTrue(positions['programming'] < positions['algorithms'])
        
        # programming应该在data_structures之前
        self.assertTrue(positions['programming'] < positions['data_structures'])
        
        # algorithms和data_structures应该在system_design之前
        self.assertTrue(positions['algorithms'] < positions['system_design'])
        self.assertTrue(positions['data_structures'] < positions['system_design'])


if __name__ == '__main__':
    unittest.main() 