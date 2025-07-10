#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统架构设计师考试数据爬虫
功能：收集题库、考点、教材和真题数据
"""

import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import re
from urllib.parse import urljoin, urlparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemArchitectCrawler:
    """系统架构设计师考试数据爬虫"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 创建数据目录
        self.data_dir = 'system_architect_data'
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(f'{self.data_dir}/questions', exist_ok=True)
        os.makedirs(f'{self.data_dir}/exam_points', exist_ok=True)
        os.makedirs(f'{self.data_dir}/materials', exist_ok=True)
        os.makedirs(f'{self.data_dir}/real_exams', exist_ok=True)
        
        # GitHub仓库资源
        self.github_repos = [
            {
                'name': 'hakusai22/System_Architect',
                'url': 'https://api.github.com/repos/hakusai22/System_Architect',
                'description': '最全面的系统架构设计师资料库',
                'stars': 549
            },
            {
                'name': 'anyushun/SystemArchitectureDesigner',
                'url': 'https://api.github.com/repos/anyushun/SystemArchitectureDesigner',
                'description': '个人备考经验分享',
                'stars': 4
            },
            {
                'name': '1216361723/-',
                'url': 'https://api.github.com/repos/1216361723/-',
                'description': '软考证书学习资料',
                'stars': 1
            },
            {
                'name': 'litsen-wind/system-architect',
                'url': 'https://api.github.com/repos/litsen-wind/system-architect',
                'description': '2022系统架构设计师精品班学习资料',
                'stars': 3
            },
            {
                'name': 'xiaomabenten/system-analyst',
                'url': 'https://api.github.com/repos/xiaomabenten/system-analyst',
                'description': '系统分析师备考资源库',
                'stars': 636
            }
        ]
        
        # 官方和权威网站
        self.official_sites = [
            {
                'name': '希赛网',
                'base_url': 'https://www.educity.cn',
                'exam_url': 'https://www.educity.cn/rk/zhenti/jiagou/',
                'description': '软考官方合作网站'
            },
            {
                'name': '软考官网',
                'base_url': 'http://www.ruankao.org.cn',
                'description': '官方考试网站'
            }
        ]
    
    def fetch_github_repo_content(self, repo_info: Dict) -> Dict[str, Any]:
        """获取GitHub仓库内容"""
        try:
            logger.info(f"正在获取仓库: {repo_info['name']}")
            
            # 获取仓库基本信息
            response = self.session.get(repo_info['url'])
            if response.status_code != 200:
                logger.error(f"无法访问仓库API: {repo_info['name']}")
                return {}
            
            repo_data = response.json()
            
            # 获取文件列表
            contents_url = repo_data.get('contents_url', '').replace('{+path}', '')
            contents_response = self.session.get(contents_url)
            
            if contents_response.status_code == 200:
                contents = contents_response.json()
                repo_info['contents'] = contents
                repo_info['updated_at'] = repo_data.get('updated_at')
                repo_info['description'] = repo_data.get('description', repo_info.get('description', ''))
                
            time.sleep(1)  # 避免请求过于频繁
            return repo_info
            
        except Exception as e:
            logger.error(f"获取仓库内容失败 {repo_info['name']}: {str(e)}")
            return {}
    
    def extract_exam_questions(self) -> List[Dict]:
        """提取考试题库"""
        questions_data = []
        
        # 定义题库类型
        question_types = {
            '综合知识': '上午选择题，75道，150分钟',
            '案例分析': '下午问答题，5选3，90分钟',
            '论文': '论文写作，4选1，120分钟'
        }
        
        # 从GitHub资源中提取题库信息
        for repo in self.github_repos:
            repo_data = self.fetch_github_repo_content(repo)
            if not repo_data:
                continue
                
            # 查找真题和题库相关文件
            for content in repo_data.get('contents', []):
                filename = content.get('name', '').lower()
                if any(keyword in filename for keyword in ['真题', '题库', 'zhenti', 'question', '模拟']):
                    questions_data.append({
                        'source': repo['name'],
                        'type': self._classify_question_type(filename),
                        'filename': content.get('name'),
                        'url': content.get('download_url'),
                        'description': f"来自{repo['description']}",
                        'collected_at': datetime.now().isoformat()
                    })
        
        # 保存题库数据
        self._save_data(questions_data, 'questions/question_bank.json')
        logger.info(f"已收集 {len(questions_data)} 个题库资源")
        
        return questions_data
    
    def extract_exam_points_2025(self) -> Dict[str, Any]:
        """提取2025年考点数据"""
        exam_points = {
            'year': 2025,
            'exam_outline': {
                '信息系统综合知识': {
                    'duration': '150分钟',
                    'questions': 75,
                    'type': '选择题',
                    'passing_score': 45,
                    'topics': [
                        '计算机组成与体系结构',
                        '操作系统基本原理',
                        '系统配置与性能评价',
                        '计算机网络',
                        '数据库系统',
                        '系统安全性与保密性',
                        '标准化和知识产权',
                        '应用数学',
                        '软件工程',
                        '项目管理',
                        '专业英语'
                    ]
                },
                '系统架构设计案例分析': {
                    'duration': '90分钟',
                    'questions': '5选3',
                    'type': '问答题',
                    'passing_score': 45,
                    'topics': [
                        '软件架构设计',
                        '分布式系统设计',
                        '系统建模',
                        '软件产品线',
                        '基于架构的软件开发方法',
                        '软件质量属性',
                        '企业集成平台',
                        '面向服务架构'
                    ]
                },
                '系统架构设计论文': {
                    'duration': '120分钟',
                    'questions': '4选1',
                    'type': '论文题',
                    'passing_score': 45,
                    'word_count': '2000-2500字',
                    'topics': [
                        '论软件系统架构评估',
                        '论基于架构的软件可靠性分析',
                        '论软件系统的安全性设计',
                        '论基于构件的软件开发',
                        '论软件系统的性能优化',
                        '论企业集成平台的设计'
                    ]
                }
            },
            'key_technologies': [
                '微服务架构',
                '分布式系统',
                '云计算架构',
                '大数据处理',
                '容器化技术',
                'DevOps',
                '系统安全',
                '性能优化'
            ],
            'preparation_tips': [
                '重点掌握软件架构设计理论',
                '熟悉主流技术架构模式',
                '积累实际项目经验',
                '练习论文写作',
                '刷历年真题'
            ],
            'collected_at': datetime.now().isoformat()
        }
        
        # 保存2025考点数据
        self._save_data(exam_points, 'exam_points/2025_exam_outline.json')
        logger.info("已整理2025年考点数据")
        
        return exam_points
    
    def extract_materials_and_textbooks(self) -> List[Dict]:
        """提取最新教材和教辅资料"""
        materials = []
        
        # 官方教材
        official_materials = [
            {
                'title': '系统架构设计师教程（第5版）',
                'author': '希赛教育软考学院',
                'publisher': '清华大学出版社',
                'year': 2023,
                'type': '官方教程',
                'description': '软考官方指定教材，涵盖最新考试大纲',
                'isbn': '978-7-302-62xxx-x',
                'price': '89元',
                'recommendation': '必备'
            },
            {
                'title': '系统架构设计师考试32小时通关',
                'author': '薛大龙',
                'publisher': '机械工业出版社',
                'year': 2024,
                'type': '备考指南',
                'description': '快速通关指南，适合短期备考',
                'price': '69元',
                'recommendation': '推荐'
            },
            {
                'title': '系统架构设计师历年真题解析',
                'publisher': '希赛网',
                'year': 2024,
                'type': '真题解析',
                'description': '2009-2024年真题及详细解析',
                'price': '59元',
                'recommendation': '必备'
            }
        ]
        
        # 在线资源
        online_resources = [
            {
                'title': '希赛网系统架构设计师',
                'url': 'https://www.educity.cn/rk/jiagou/',
                'type': '在线课程',
                'description': '视频课程+在线题库+直播辅导',
                'price': '698元',
                'recommendation': '推荐'
            },
            {
                'title': '芝士架构红宝书',
                'url': 'https://docs.cheko.cc/bible/system_architectural_designer_bible.html',
                'type': '在线文档',
                'description': '免费的知识点整理',
                'price': '免费',
                'recommendation': '推荐'
            },
            {
                'title': '软考通APP',
                'type': '移动应用',
                'description': '免费刷题神器',
                'price': '免费',
                'recommendation': '必备'
            }
        ]
        
        materials.extend(official_materials)
        materials.extend(online_resources)
        
        # 从GitHub仓库中提取教材信息
        for repo in self.github_repos:
            repo_data = self.fetch_github_repo_content(repo)
            if not repo_data:
                continue
                
            for content in repo_data.get('contents', []):
                filename = content.get('name', '').lower()
                if any(keyword in filename for keyword in ['教材', '教程', 'book', 'material', '课件']):
                    materials.append({
                        'title': content.get('name'),
                        'source': repo['name'],
                        'url': content.get('download_url'),
                        'type': 'GitHub资源',
                        'description': f"来自{repo['description']}",
                        'price': '免费',
                        'recommendation': '参考',
                        'collected_at': datetime.now().isoformat()
                    })
        
        # 保存教材数据
        self._save_data(materials, 'materials/textbooks_and_materials.json')
        logger.info(f"已收集 {len(materials)} 个教材和教辅资源")
        
        return materials
    
    def extract_real_exams(self) -> List[Dict]:
        """提取历年真题"""
        real_exams = []
        
        # 历年真题信息（基于已知信息）
        exam_years = [
            {'year': 2024, 'sessions': ['上半年', '下半年'], 'format': '机考'},
            {'year': 2023, 'sessions': ['上半年'], 'format': '机考'},
            {'year': 2022, 'sessions': ['上半年'], 'format': '机考'},
            {'year': 2021, 'sessions': ['上半年'], 'format': '机考'},
            {'year': 2020, 'sessions': ['上半年'], 'format': '纸质'},
            {'year': 2019, 'sessions': ['上半年'], 'format': '纸质'},
            {'year': 2018, 'sessions': ['上半年'], 'format': '纸质'},
            {'year': 2017, 'sessions': ['上半年'], 'format': '纸质'},
            {'year': 2016, 'sessions': ['上半年'], 'format': '纸质'},
            {'year': 2015, 'sessions': ['上半年'], 'format': '纸质'},
        ]
        
        for exam_info in exam_years:
            for session in exam_info['sessions']:
                real_exams.append({
                    'year': exam_info['year'],
                    'session': session,
                    'format': exam_info['format'],
                    'subjects': [
                        '信息系统综合知识',
                        '系统架构设计案例分析', 
                        '系统架构设计论文'
                    ],
                    'availability': '可获取' if exam_info['year'] >= 2015 else '较难获取',
                    'sources': [
                        '希赛网',
                        'GitHub资源',
                        '软考通APP'
                    ]
                })
        
        # 从GitHub资源中提取真题链接
        for repo in self.github_repos:
            repo_data = self.fetch_github_repo_content(repo)
            if not repo_data:
                continue
                
            for content in repo_data.get('contents', []):
                filename = content.get('name', '').lower()
                if any(keyword in filename for keyword in ['真题', 'zhenti', 'exam', '历年']):
                    # 尝试从文件名中提取年份
                    year_match = re.search(r'(20\d{2})', filename)
                    year = int(year_match.group(1)) if year_match else None
                    
                    real_exams.append({
                        'title': content.get('name'),
                        'year': year,
                        'source': repo['name'],
                        'url': content.get('download_url'),
                        'type': 'GitHub资源',
                        'description': f"来自{repo['description']}",
                        'collected_at': datetime.now().isoformat()
                    })
        
        # 保存真题数据
        self._save_data(real_exams, 'real_exams/historical_exams.json')
        logger.info(f"已收集 {len(real_exams)} 个真题资源")
        
        return real_exams
    
    def _classify_question_type(self, filename: str) -> str:
        """根据文件名分类题目类型"""
        filename = filename.lower()
        
        if any(keyword in filename for keyword in ['综合', 'comprehensive', '上午', 'morning']):
            return '综合知识'
        elif any(keyword in filename for keyword in ['案例', 'case', '下午', 'afternoon']):
            return '案例分析'
        elif any(keyword in filename for keyword in ['论文', 'paper', 'essay']):
            return '论文'
        elif any(keyword in filename for keyword in ['模拟', 'mock', 'simulation']):
            return '模拟题'
        else:
            return '其他'
    
    def _save_data(self, data: Any, filename: str) -> None:
        """保存数据到JSON文件"""
        filepath = os.path.join(self.data_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据已保存到: {filepath}")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """生成汇总报告"""
        summary = {
            'generated_at': datetime.now().isoformat(),
            'data_sources': len(self.github_repos) + len(self.official_sites),
            'github_repos': self.github_repos,
            'official_sites': self.official_sites,
            'data_categories': [
                '题库数据',
                '2025考点',
                '教材资料',
                '历年真题'
            ],
            'usage_guide': {
                '题库练习': '使用questions目录下的题库进行日常练习',
                '考点复习': '参考exam_points目录下的考试大纲',
                '教材学习': '查看materials目录下的推荐教材',
                '真题训练': '使用real_exams目录下的历年真题'
            },
            'next_steps': [
                '下载相关教材进行系统学习',
                '使用软考通APP进行日常刷题',
                '关注官方网站获取最新考试信息',
                '参加在线课程或培训班',
                '制定详细的备考计划'
            ]
        }
        
        self._save_data(summary, 'summary_report.json')
        return summary
    
    def run_crawler(self) -> None:
        """运行爬虫程序"""
        logger.info("开始收集系统架构设计师考试数据...")
        
        try:
            # 1. 收集题库
            questions = self.extract_exam_questions()
            
            # 2. 整理2025考点
            exam_points = self.extract_exam_points_2025()
            
            # 3. 收集教材资料
            materials = self.extract_materials_and_textbooks()
            
            # 4. 收集真题
            real_exams = self.extract_real_exams()
            
            # 5. 生成汇总报告
            summary = self.generate_summary_report()
            
            logger.info("数据收集完成！")
            logger.info(f"题库资源: {len(questions)} 个")
            logger.info(f"教材资料: {len(materials)} 个") 
            logger.info(f"真题资源: {len(real_exams)} 个")
            logger.info(f"数据保存在: {self.data_dir} 目录")
            
            return summary
            
        except Exception as e:
            logger.error(f"爬虫运行失败: {str(e)}")
            raise

def main():
    """主函数"""
    crawler = SystemArchitectCrawler()
    summary = crawler.run_crawler()
    
    print("\n" + "="*50)
    print("系统架构设计师考试数据收集完成")
    print("="*50)
    print(f"数据目录: {crawler.data_dir}")
    print(f"收集时间: {summary['generated_at']}")
    print(f"数据来源: {summary['data_sources']} 个")
    print("\n建议下一步:")
    for step in summary['next_steps']:
        print(f"• {step}")

if __name__ == "__main__":
    main() 