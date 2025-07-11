"""
学习路径规划服务 - 个性化学习路径生成和管理
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

@dataclass
class UserProfile:
    """用户学习档案"""
    user_id: str
    current_knowledge_levels: Dict[str, float]  # 知识点ID -> 掌握程度(0-1)
    learning_preferences: Dict[str, Any]
    available_study_hours_per_day: float
    target_completion_date: Optional[datetime]
    difficulty_preference: int  # 1-5, 偏好的难度级别
    learning_style: str  # visual, auditory, kinesthetic, reading
    weak_areas: List[str]  # 薄弱领域
    strong_areas: List[str]  # 擅长领域

@dataclass
class LearningTarget:
    """学习目标"""
    target_knowledge_points: List[str]
    target_mastery_level: float
    priority_level: int  # 1-5
    deadline: Optional[datetime]

@dataclass
class StudySession:
    """学习会话"""
    knowledge_point_id: str
    estimated_duration_minutes: int
    difficulty_level: int
    session_type: str  # learn, review, practice, test
    prerequisites_completed: bool
    recommended_time_of_day: str  # morning, afternoon, evening

@dataclass
class LearningPathNode:
    """学习路径节点"""
    knowledge_point_id: str
    knowledge_point_name: str
    estimated_study_time: float
    difficulty_level: int
    prerequisites: List[str]
    dependents: List[str]
    priority_score: float
    recommended_order: int

@dataclass
class GeneratedLearningPath:
    """生成的学习路径"""
    path_id: str
    user_id: str
    target: LearningTarget
    nodes: List[LearningPathNode]
    study_sessions: List[StudySession]
    total_estimated_hours: float
    estimated_completion_date: datetime
    difficulty_progression: List[int]
    milestones: List[Dict[str, Any]]

class DependencyResolver:
    """依赖关系解析器"""
    
    def __init__(self):
        self.graph = defaultdict(list)
        self.reverse_graph = defaultdict(list)
        self.node_data = {}
    
    def add_knowledge_point(self, kp_id: str, prerequisites: List[str], **node_data):
        """添加知识点到依赖图"""
        self.node_data[kp_id] = node_data
        
        for prereq in prerequisites:
            self.graph[prereq].append(kp_id)
            self.reverse_graph[kp_id].append(prereq)
    
    def topological_sort(self, target_nodes: List[str]) -> List[str]:
        """拓扑排序，确定学习顺序"""
        # 只包含目标节点及其依赖的子图
        relevant_nodes = self._get_relevant_nodes(target_nodes)
        
        # 计算入度
        in_degree = defaultdict(int)
        for node in relevant_nodes:
            in_degree[node] = len([p for p in self.reverse_graph[node] if p in relevant_nodes])
        
        # 拓扑排序
        queue = deque([node for node in relevant_nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            node = queue.popleft()
            result.append(node)
            
            for dependent in self.graph[node]:
                if dependent in relevant_nodes:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        # 检查循环依赖
        if len(result) != len(relevant_nodes):
            logger.warning("检测到循环依赖，使用部分排序结果")
        
        return result
    
    def _get_relevant_nodes(self, target_nodes: List[str]) -> Set[str]:
        """获取与目标节点相关的所有节点（包括依赖）"""
        relevant = set(target_nodes)
        
        # BFS遍历所有依赖
        queue = deque(target_nodes)
        while queue:
            node = queue.popleft()
            for prereq in self.reverse_graph[node]:
                if prereq not in relevant:
                    relevant.add(prereq)
                    queue.append(prereq)
        
        return relevant
    
    def get_critical_path(self, target_nodes: List[str]) -> List[str]:
        """获取关键路径（最长依赖链）"""
        relevant_nodes = self._get_relevant_nodes(target_nodes)
        
        # 计算每个节点的最长路径
        longest_path = {}
        sorted_nodes = self.topological_sort(list(relevant_nodes))
        
        for node in sorted_nodes:
            if not self.reverse_graph[node]:
                longest_path[node] = 1
            else:
                max_prereq_path = max(
                    longest_path.get(prereq, 0) 
                    for prereq in self.reverse_graph[node]
                    if prereq in relevant_nodes
                )
                longest_path[node] = max_prereq_path + 1
        
        # 找到最长路径
        max_length = max(longest_path.values())
        critical_nodes = [node for node, length in longest_path.items() if length == max_length]
        
        return critical_nodes

class DifficultyCalculator:
    """难度计算器"""
    
    @staticmethod
    def calculate_adaptive_difficulty(user_profile: UserProfile, knowledge_point_id: str, 
                                    base_difficulty: int) -> float:
        """计算适应性难度"""
        current_level = user_profile.current_knowledge_levels.get(knowledge_point_id, 0.0)
        preference = user_profile.difficulty_preference
        
        # 基础难度调整
        adaptive_difficulty = base_difficulty
        
        # 根据当前掌握程度调整
        if current_level > 0.8:
            adaptive_difficulty *= 0.7  # 已掌握的内容降低难度
        elif current_level > 0.5:
            adaptive_difficulty *= 0.9
        elif current_level < 0.2:
            adaptive_difficulty *= 1.2  # 完全陌生的内容增加难度
        
        # 根据用户偏好调整
        preference_factor = preference / 3.0  # 将1-5映射到0.33-1.67
        adaptive_difficulty *= preference_factor
        
        return max(1.0, min(5.0, adaptive_difficulty))
    
    @staticmethod
    def calculate_priority_score(knowledge_point_id: str, user_profile: UserProfile,
                               target: LearningTarget, dependencies_completed: int,
                               total_dependencies: int) -> float:
        """计算优先级分数"""
        score = 0.0
        
        # 目标相关性
        if knowledge_point_id in target.target_knowledge_points:
            score += 10.0 * target.priority_level
        
        # 依赖完成度
        if total_dependencies > 0:
            dependency_ratio = dependencies_completed / total_dependencies
            score += 5.0 * dependency_ratio
        else:
            score += 5.0  # 无依赖的基础知识点
        
        # 当前掌握程度（掌握程度低的优先）
        current_level = user_profile.current_knowledge_levels.get(knowledge_point_id, 0.0)
        score += 3.0 * (1.0 - current_level)
        
        # 薄弱领域加权
        if knowledge_point_id in user_profile.weak_areas:
            score += 2.0
        
        # 截止日期压力
        if target.deadline:
            days_left = (target.deadline - datetime.now()).days
            if days_left > 0:
                urgency = min(2.0, 30.0 / days_left)  # 30天内的紧迫性
                score += urgency
        
        return score

class TimeEstimator:
    """时间估算器"""
    
    @staticmethod
    def estimate_study_time(knowledge_point_data: Dict[str, Any], 
                          user_profile: UserProfile) -> float:
        """估算学习时间"""
        base_time = knowledge_point_data.get('estimated_study_hours', 1.0)
        difficulty = knowledge_point_data.get('difficulty_level', 2)
        current_level = user_profile.current_knowledge_levels.get(
            knowledge_point_data.get('id', ''), 0.0
        )
        
        # 根据当前掌握程度调整时间
        if current_level > 0.7:
            time_factor = 0.3  # 已基本掌握，只需复习
        elif current_level > 0.3:
            time_factor = 0.6  # 有一定基础
        else:
            time_factor = 1.0  # 从零开始学习
        
        # 根据难度调整
        difficulty_factor = 0.5 + (difficulty - 1) * 0.2  # 0.5 - 1.3
        
        # 根据学习风格调整
        style_factor = 1.0
        if user_profile.learning_style == 'visual':
            style_factor = 0.9  # 视觉学习者通常更快
        elif user_profile.learning_style == 'reading':
            style_factor = 0.8  # 阅读学习者更高效
        
        estimated_time = base_time * time_factor * difficulty_factor * style_factor
        
        return max(0.25, estimated_time)  # 最少15分钟
    
    @staticmethod
    def schedule_study_sessions(total_hours: float, daily_hours: float,
                              start_date: datetime, excluded_dates: List[datetime] = None) -> List[datetime]:
        """安排学习会话时间"""
        if excluded_dates is None:
            excluded_dates = []
        
        sessions = []
        current_date = start_date
        remaining_hours = total_hours
        
        while remaining_hours > 0:
            # 跳过排除的日期
            if current_date.date() in [d.date() for d in excluded_dates]:
                current_date += timedelta(days=1)
                continue
            
            # 跳过周末（可配置）
            if current_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                current_date += timedelta(days=1)
                continue
            
            session_hours = min(remaining_hours, daily_hours)
            sessions.append(current_date)
            
            remaining_hours -= session_hours
            current_date += timedelta(days=1)
        
        return sessions

class LearningPathService:
    """学习路径规划服务"""
    
    def __init__(self):
        self.dependency_resolver = DependencyResolver()
        self.difficulty_calculator = DifficultyCalculator()
        self.time_estimator = TimeEstimator()
    
    def initialize_knowledge_graph(self, knowledge_points: List[Dict[str, Any]]):
        """初始化知识图谱"""
        for kp in knowledge_points:
            self.dependency_resolver.add_knowledge_point(
                kp['id'],
                kp.get('prerequisites', []),
                **kp
            )
    
    def generate_learning_path(self, user_profile: UserProfile, 
                             target: LearningTarget) -> GeneratedLearningPath:
        """生成个性化学习路径"""
        logger.info(f"为用户 {user_profile.user_id} 生成学习路径")
        
        # 1. 确定需要学习的知识点
        target_nodes = target.target_knowledge_points
        learning_order = self.dependency_resolver.topological_sort(target_nodes)
        
        # 2. 计算每个知识点的优先级和学习时间
        path_nodes = []
        total_estimated_hours = 0.0
        
        for i, kp_id in enumerate(learning_order):
            kp_data = self.dependency_resolver.node_data[kp_id]
            
            # 计算依赖完成度
            prerequisites = self.dependency_resolver.reverse_graph[kp_id]
            completed_prereqs = sum(
                1 for prereq in prerequisites
                if user_profile.current_knowledge_levels.get(prereq, 0.0) >= target.target_mastery_level
            )
            
            # 计算优先级
            priority_score = self.difficulty_calculator.calculate_priority_score(
                kp_id, user_profile, target, completed_prereqs, len(prerequisites)
            )
            
            # 估算学习时间
            study_time = self.time_estimator.estimate_study_time(kp_data, user_profile)
            total_estimated_hours += study_time
            
            # 创建路径节点
            node = LearningPathNode(
                knowledge_point_id=kp_id,
                knowledge_point_name=kp_data.get('name', kp_id),
                estimated_study_time=study_time,
                difficulty_level=kp_data.get('difficulty_level', 2),
                prerequisites=prerequisites,
                dependents=self.dependency_resolver.graph[kp_id],
                priority_score=priority_score,
                recommended_order=i
            )
            path_nodes.append(node)
        
        # 3. 根据优先级重新排序（在满足依赖的前提下）
        optimized_nodes = self._optimize_learning_order(path_nodes)
        
        # 4. 生成学习会话
        study_sessions = self._generate_study_sessions(optimized_nodes, user_profile)
        
        # 5. 计算完成时间
        start_date = datetime.now()
        if user_profile.available_study_hours_per_day > 0:
            estimated_days = math.ceil(total_estimated_hours / user_profile.available_study_hours_per_day)
            estimated_completion = start_date + timedelta(days=estimated_days)
        else:
            estimated_completion = target.deadline or (start_date + timedelta(days=30))
        
        # 6. 生成里程碑
        milestones = self._generate_milestones(optimized_nodes, estimated_completion)
        
        # 7. 计算难度进展
        difficulty_progression = [node.difficulty_level for node in optimized_nodes]
        
        return GeneratedLearningPath(
            path_id=f"path_{user_profile.user_id}_{int(datetime.now().timestamp())}",
            user_id=user_profile.user_id,
            target=target,
            nodes=optimized_nodes,
            study_sessions=study_sessions,
            total_estimated_hours=total_estimated_hours,
            estimated_completion_date=estimated_completion,
            difficulty_progression=difficulty_progression,
            milestones=milestones
        )
    
    def _optimize_learning_order(self, nodes: List[LearningPathNode]) -> List[LearningPathNode]:
        """优化学习顺序"""
        # 创建依赖图
        node_map = {node.knowledge_point_id: node for node in nodes}
        available = []
        waiting = []
        result = []
        completed = set()
        
        # 初始化：找出所有无依赖的节点
        for node in nodes:
            if not node.prerequisites or all(prereq in completed for prereq in node.prerequisites):
                available.append(node)
            else:
                waiting.append(node)
        
        # 贪心算法：每次选择优先级最高的可用节点
        while available or waiting:
            if available:
                # 按优先级排序
                available.sort(key=lambda n: n.priority_score, reverse=True)
                
                # 选择优先级最高的节点
                selected = available.pop(0)
                result.append(selected)
                completed.add(selected.knowledge_point_id)
                
                # 检查等待列表中是否有新的可用节点
                newly_available = []
                still_waiting = []
                
                for node in waiting:
                    if all(prereq in completed for prereq in node.prerequisites):
                        newly_available.append(node)
                    else:
                        still_waiting.append(node)
                
                available.extend(newly_available)
                waiting = still_waiting
            else:
                # 如果没有可用节点但还有等待的节点，说明有循环依赖
                # 选择依赖最少的节点强制推进
                if waiting:
                    waiting.sort(key=lambda n: len([p for p in n.prerequisites if p not in completed]))
                    forced = waiting.pop(0)
                    result.append(forced)
                    completed.add(forced.knowledge_point_id)
                    logger.warning(f"强制推进节点 {forced.knowledge_point_name} 以打破循环依赖")
        
        return result
    
    def _generate_study_sessions(self, nodes: List[LearningPathNode], 
                               user_profile: UserProfile) -> List[StudySession]:
        """生成详细的学习会话"""
        sessions = []
        
        for node in nodes:
            study_hours = node.estimated_study_time
            current_level = user_profile.current_knowledge_levels.get(node.knowledge_point_id, 0.0)
            
            # 根据学习时间和内容难度分解为多个会话
            if study_hours <= 1.0:
                # 短时间内容，一次会话
                sessions.append(StudySession(
                    knowledge_point_id=node.knowledge_point_id,
                    estimated_duration_minutes=int(study_hours * 60),
                    difficulty_level=node.difficulty_level,
                    session_type='learn' if current_level < 0.3 else 'review',
                    prerequisites_completed=True,
                    recommended_time_of_day=self._recommend_time_of_day(node.difficulty_level)
                ))
            else:
                # 长时间内容，分解为多个会话
                remaining_hours = study_hours
                session_count = 0
                
                while remaining_hours > 0:
                    session_duration = min(1.0, remaining_hours)  # 最多1小时一次
                    session_type = 'learn'
                    
                    if session_count == 0:
                        session_type = 'learn'
                    elif remaining_hours <= 0.5:
                        session_type = 'review'
                    else:
                        session_type = 'practice'
                    
                    sessions.append(StudySession(
                        knowledge_point_id=node.knowledge_point_id,
                        estimated_duration_minutes=int(session_duration * 60),
                        difficulty_level=node.difficulty_level,
                        session_type=session_type,
                        prerequisites_completed=True,
                        recommended_time_of_day=self._recommend_time_of_day(node.difficulty_level)
                    ))
                    
                    remaining_hours -= session_duration
                    session_count += 1
        
        return sessions
    
    def _recommend_time_of_day(self, difficulty_level: int) -> str:
        """推荐学习时间段"""
        if difficulty_level >= 4:
            return 'morning'  # 高难度内容建议上午学习
        elif difficulty_level >= 2:
            return 'afternoon'
        else:
            return 'evening'  # 简单内容可以晚上学习
    
    def _generate_milestones(self, nodes: List[LearningPathNode], 
                           completion_date: datetime) -> List[Dict[str, Any]]:
        """生成学习里程碑"""
        milestones = []
        total_nodes = len(nodes)
        
        # 25%, 50%, 75%, 100% 完成点
        milestone_percentages = [0.25, 0.5, 0.75, 1.0]
        
        for percentage in milestone_percentages:
            milestone_index = int(total_nodes * percentage) - 1
            if milestone_index >= 0 and milestone_index < total_nodes:
                node = nodes[milestone_index]
                
                # 估算里程碑日期
                hours_to_milestone = sum(n.estimated_study_time for n in nodes[:milestone_index + 1])
                milestone_date = datetime.now() + timedelta(hours=hours_to_milestone)
                
                milestones.append({
                    'percentage': int(percentage * 100),
                    'knowledge_point_id': node.knowledge_point_id,
                    'knowledge_point_name': node.knowledge_point_name,
                    'estimated_date': milestone_date,
                    'description': f'完成 {int(percentage * 100)}% 的学习目标'
                })
        
        return milestones
    
    def update_learning_progress(self, path_id: str, knowledge_point_id: str, 
                               new_mastery_level: float, study_time_minutes: int) -> Dict[str, Any]:
        """更新学习进度"""
        # 这里应该更新数据库中的进度信息
        # 并可能重新计算后续的学习路径
        
        progress_update = {
            'path_id': path_id,
            'knowledge_point_id': knowledge_point_id,
            'new_mastery_level': new_mastery_level,
            'study_time_minutes': study_time_minutes,
            'updated_at': datetime.now(),
            'recommendations': []
        }
        
        # 基于新的掌握程度生成建议
        if new_mastery_level < 0.3:
            progress_update['recommendations'].append({
                'type': 'additional_study',
                'message': '建议增加学习时间或寻求额外资源'
            })
        elif new_mastery_level > 0.8:
            progress_update['recommendations'].append({
                'type': 'advance',
                'message': '掌握良好，可以进入下一个知识点'
            })
        
        return progress_update
    
    def generate_review_schedule(self, user_profile: UserProfile, 
                               completed_knowledge_points: List[str]) -> List[Dict[str, Any]]:
        """生成复习计划（基于遗忘曲线）"""
        review_schedule = []
        current_date = datetime.now()
        
        # 艾宾浩斯遗忘曲线间隔：1天、3天、7天、15天、30天
        review_intervals = [1, 3, 7, 15, 30]
        
        for kp_id in completed_knowledge_points:
            mastery_level = user_profile.current_knowledge_levels.get(kp_id, 0.0)
            
            if mastery_level > 0.5:  # 只为已掌握的知识点安排复习
                for interval in review_intervals:
                    # 根据掌握程度调整复习强度
                    if mastery_level > 0.8 and interval <= 3:
                        continue  # 高掌握度跳过短期复习
                    
                    review_date = current_date + timedelta(days=interval)
                    review_duration = 15 if mastery_level > 0.8 else 30  # 分钟
                    
                    review_schedule.append({
                        'knowledge_point_id': kp_id,
                        'review_date': review_date,
                        'duration_minutes': review_duration,
                        'review_type': 'maintenance',
                        'interval_days': interval
                    })
        
        return sorted(review_schedule, key=lambda x: x['review_date'])
    
    def analyze_learning_efficiency(self, user_profile: UserProfile,
                                  completed_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析学习效率"""
        analysis = {
            'total_sessions': len(completed_sessions),
            'total_study_time_hours': 0.0,
            'average_session_duration': 0.0,
            'efficiency_score': 0.0,
            'difficulty_performance': defaultdict(list),
            'time_of_day_performance': defaultdict(list),
            'recommendations': []
        }
        
        if not completed_sessions:
            return analysis
        
        total_minutes = sum(session.get('actual_duration_minutes', 0) for session in completed_sessions)
        analysis['total_study_time_hours'] = total_minutes / 60.0
        analysis['average_session_duration'] = total_minutes / len(completed_sessions)
        
        # 分析不同难度和时间段的表现
        for session in completed_sessions:
            difficulty = session.get('difficulty_level', 2)
            time_of_day = session.get('time_of_day', 'unknown')
            effectiveness = session.get('effectiveness_score', 0.5)  # 0-1
            
            analysis['difficulty_performance'][difficulty].append(effectiveness)
            analysis['time_of_day_performance'][time_of_day].append(effectiveness)
        
        # 计算整体效率分数
        all_effectiveness = []
        for session in completed_sessions:
            all_effectiveness.append(session.get('effectiveness_score', 0.5))
        
        if all_effectiveness:
            analysis['efficiency_score'] = sum(all_effectiveness) / len(all_effectiveness)
        
        # 生成优化建议
        self._generate_efficiency_recommendations(analysis)
        
        return analysis
    
    def _generate_efficiency_recommendations(self, analysis: Dict[str, Any]):
        """生成效率优化建议"""
        recommendations = []
        
        # 分析最佳学习时间
        time_performance = analysis['time_of_day_performance']
        if time_performance:
            best_time = max(time_performance.keys(), 
                          key=lambda t: sum(time_performance[t]) / len(time_performance[t]))
            recommendations.append({
                'type': 'optimal_time',
                'message': f'您在{best_time}时段学习效果最佳，建议安排重要内容在此时学习'
            })
        
        # 分析难度适应性
        difficulty_performance = analysis['difficulty_performance']
        if difficulty_performance:
            low_performance_difficulties = [
                diff for diff, scores in difficulty_performance.items()
                if sum(scores) / len(scores) < 0.6
            ]
            
            if low_performance_difficulties:
                recommendations.append({
                    'type': 'difficulty_adjustment',
                    'message': f'建议在难度级别{low_performance_difficulties}上投入更多时间'
                })
        
        # 学习时间建议
        avg_duration = analysis['average_session_duration']
        if avg_duration > 90:
            recommendations.append({
                'type': 'session_length',
                'message': '建议将学习会话控制在90分钟以内，以提高注意力集中度'
            })
        elif avg_duration < 30:
            recommendations.append({
                'type': 'session_length',
                'message': '建议延长学习会话至30分钟以上，以获得更好的学习效果'
            })
        
        analysis['recommendations'] = recommendations 