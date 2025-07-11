#!/usr/bin/env python3
"""
系统架构师知识体系导入脚本
使用方法: python import_knowledge.py
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import SessionLocal
from services.knowledge_extractor import KnowledgeExtractor

def main():
    """主函数"""
    
    print("=" * 60)
    print("🎓 系统架构师知识体系导入工具")
    print("=" * 60)
    
    # 检查资料目录是否存在
    resource_path = Path("System_Architect")
    if not resource_path.exists():
        print("❌ 错误: 找不到 System_Architect 资料目录")
        print("   请确保学习资料放在项目根目录下的 System_Architect 文件夹中")
        return False
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 创建知识提取器
        extractor = KnowledgeExtractor(db, str(resource_path))
        
        # 执行提取和导入
        result = extractor.extract_and_import()
        
        # 显示结果统计
        print("\n" + "=" * 60)
        print("📊 导入结果统计:")
        print("=" * 60)
        
        import_result = result["import_result"]
        print(f"✅ 知识域: {import_result['domains_created']} 个")
        print(f"✅ 知识点: {import_result['knowledge_points_created']} 个")
        print(f"✅ 技能点: {import_result['skill_points_created']} 个")
        print(f"✅ 依赖关系: {import_result['dependencies_created']} 个")
        
        if import_result['errors']:
            print(f"\n⚠️  警告: {len(import_result['errors'])} 个错误")
            for error in import_result['errors'][:5]:  # 只显示前5个错误
                print(f"   - {error}")
            if len(import_result['errors']) > 5:
                print(f"   ... 还有 {len(import_result['errors']) - 5} 个错误")
        
        # 显示知识体系概览
        knowledge_structure = result["knowledge_structure"]
        print(f"\n📚 知识体系概览:")
        print("-" * 40)
        for domain in knowledge_structure["domains"]:
            kp_count = len([kp for kp in knowledge_structure["knowledge_points"] 
                           if kp["domain"] == domain["name"]])
            print(f"📖 {domain['name']}: {kp_count} 个知识点 (权重: {domain['exam_weight']:.1%})")
        
        print(f"\n🎯 总计: {len(knowledge_structure['knowledge_points'])} 个知识点")
        print(f"🔗 依赖关系: {len(knowledge_structure['dependencies'])} 条")
        
        print("\n" + "=" * 60)
        print("🎉 知识体系导入完成！")
        print("💡 提示: 可以通过前端界面查看完整的知识图谱")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 导入过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

def preview_structure():
    """预览知识结构（不导入数据库）"""
    
    print("🔍 预览知识体系结构...")
    
    resource_path = Path("System_Architect")
    if not resource_path.exists():
        print("❌ 找不到 System_Architect 资料目录")
        return
    
    # 创建临时会话用于预览
    db = SessionLocal()
    try:
        extractor = KnowledgeExtractor(db, str(resource_path))
        knowledge_structure = extractor.extract_base_knowledge_structure()
        
        print("\n📊 知识体系预览:")
        print("=" * 50)
        
        # 显示知识域
        for domain in knowledge_structure["domains"]:
            print(f"\n📚 {domain['name']} (权重: {domain['exam_weight']:.1%})")
            print(f"   {domain['description']}")
            
            # 显示该域下的知识点
            domain_kps = [kp for kp in knowledge_structure["knowledge_points"] 
                         if kp["domain"] == domain["name"]]
            
            for kp in domain_kps[:3]:  # 只显示前3个知识点
                print(f"   └─ {kp['name']} (难度: {kp['difficulty_level']}/5)")
            
            if len(domain_kps) > 3:
                print(f"   └─ ... 还有 {len(domain_kps) - 3} 个知识点")
        
        # 显示依赖关系示例
        print(f"\n🔗 依赖关系示例:")
        for dep in knowledge_structure["dependencies"][:5]:
            print(f"   {dep['prerequisite']} → {dep['dependent']}")
        
        print(f"\n📈 总体统计:")
        print(f"   - 知识域: {len(knowledge_structure['domains'])} 个")
        print(f"   - 知识点: {len(knowledge_structure['knowledge_points'])} 个")
        print(f"   - 技能点: {len(knowledge_structure['skill_points'])} 个")
        print(f"   - 依赖关系: {len(knowledge_structure['dependencies'])} 条")
        
    finally:
        db.close()

if __name__ == "__main__":
    
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        # 预览模式
        preview_structure()
    else:
        # 导入模式
        success = main()
        sys.exit(0 if success else 1) 