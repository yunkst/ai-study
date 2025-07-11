"""Initial knowledge system tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 知识域表
    op.create_table('knowledge_domains',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('exam_weight', sa.Float(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # 知识点表
    op.create_table('knowledge_points',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('exam_weight', sa.Float(), nullable=True),
        sa.Column('estimated_study_hours', sa.Float(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('references', sa.JSON(), nullable=True),
        sa.Column('examples', sa.Text(), nullable=True),
        sa.Column('exercises', sa.JSON(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('domain_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['domain_id'], ['knowledge_domains.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 技能点表
    op.create_table('skill_points',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('skill_type', sa.String(length=50), nullable=True),
        sa.Column('mastery_criteria', sa.Text(), nullable=True),
        sa.Column('practice_methods', sa.JSON(), nullable=True),
        sa.Column('assessment_questions', sa.JSON(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('estimated_practice_hours', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('knowledge_point_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_point_id'], ['knowledge_points.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 用户知识点学习进度表
    op.create_table('user_knowledge_progress',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('knowledge_point_id', sa.String(), nullable=True),
        sa.Column('mastery_level', sa.Float(), nullable=True),
        sa.Column('study_time_minutes', sa.Integer(), nullable=True),
        sa.Column('last_reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('correct_answers', sa.Integer(), nullable=True),
        sa.Column('total_answers', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_bookmarked', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_point_id'], ['knowledge_points.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 学习路径表
    op.create_table('learning_paths',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_exam', sa.String(length=100), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('estimated_total_hours', sa.Float(), nullable=True),
        sa.Column('prerequisites_description', sa.Text(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 用户学习计划表
    op.create_table('user_learning_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('learning_path_id', sa.String(), nullable=True),
        sa.Column('plan_name', sa.String(length=200), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('target_completion_date', sa.DateTime(), nullable=True),
        sa.Column('daily_study_hours', sa.Float(), nullable=True),
        sa.Column('current_knowledge_point_id', sa.String(), nullable=True),
        sa.Column('completion_percentage', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['current_knowledge_point_id'], ['knowledge_points.id'], ),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 每日学习计划表
    op.create_table('daily_learning_plans',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_plan_id', sa.String(), nullable=True),
        sa.Column('plan_date', sa.DateTime(), nullable=False),
        sa.Column('planned_knowledge_points', sa.JSON(), nullable=True),
        sa.Column('planned_study_hours', sa.Float(), nullable=True),
        sa.Column('actual_study_hours', sa.Float(), nullable=True),
        sa.Column('completed_knowledge_points', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('mood_rating', sa.Integer(), nullable=True),
        sa.Column('difficulty_rating', sa.Integer(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_plan_id'], ['user_learning_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 学习推荐记录表
    op.create_table('learning_recommendations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('knowledge_point_id', sa.String(), nullable=True),
        sa.Column('recommendation_type', sa.String(length=50), nullable=True),
        sa.Column('priority_score', sa.Float(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('recommended_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_accepted', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_point_id'], ['knowledge_points.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # RAG文档分块表
    op.create_table('document_chunks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_file', sa.String(length=500), nullable=False),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('chapter', sa.String(length=200), nullable=True),
        sa.Column('section', sa.String(length=200), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('embedding_vector', sa.JSON(), nullable=True),
        sa.Column('chunk_length', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 导入任务表
    op.create_table('import_tasks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_name', sa.String(length=200), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=True),
        sa.Column('source_path', sa.String(length=500), nullable=True),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('progress', sa.Float(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('result_summary', sa.JSON(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 系统配置表
    op.create_table('system_configs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('config_key', sa.String(length=100), nullable=False),
        sa.Column('config_value', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('config_key')
    )
    
    # 知识点依赖关系关联表
    op.create_table('knowledge_dependencies',
        sa.Column('prerequisite_id', sa.String(), nullable=False),
        sa.Column('dependent_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['dependent_id'], ['knowledge_points.id'], ),
        sa.ForeignKeyConstraint(['prerequisite_id'], ['knowledge_points.id'], ),
        sa.PrimaryKeyConstraint('prerequisite_id', 'dependent_id')
    )
    
    # 学习路径知识点关联表
    op.create_table('learning_path_knowledge_points',
        sa.Column('learning_path_id', sa.String(), nullable=False),
        sa.Column('knowledge_point_id', sa.String(), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_point_id'], ['knowledge_points.id'], ),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ),
        sa.PrimaryKeyConstraint('learning_path_id', 'knowledge_point_id')
    )
    
    # 创建索引
    op.create_index('idx_knowledge_points_domain_id', 'knowledge_points', ['domain_id'])
    op.create_index('idx_knowledge_points_difficulty', 'knowledge_points', ['difficulty_level'])
    op.create_index('idx_skill_points_knowledge_point_id', 'skill_points', ['knowledge_point_id'])
    op.create_index('idx_user_progress_user_id', 'user_knowledge_progress', ['user_id'])
    op.create_index('idx_user_progress_knowledge_point_id', 'user_knowledge_progress', ['knowledge_point_id'])
    op.create_index('idx_document_chunks_source_file', 'document_chunks', ['source_file'])
    op.create_index('idx_document_chunks_content_type', 'document_chunks', ['content_type'])
    op.create_index('idx_import_tasks_status', 'import_tasks', ['status'])
    op.create_index('idx_learning_recommendations_user_id', 'learning_recommendations', ['user_id'])

def downgrade():
    # 删除索引
    op.drop_index('idx_learning_recommendations_user_id')
    op.drop_index('idx_import_tasks_status')
    op.drop_index('idx_document_chunks_content_type')
    op.drop_index('idx_document_chunks_source_file')
    op.drop_index('idx_user_progress_knowledge_point_id')
    op.drop_index('idx_user_progress_user_id')
    op.drop_index('idx_skill_points_knowledge_point_id')
    op.drop_index('idx_knowledge_points_difficulty')
    op.drop_index('idx_knowledge_points_domain_id')
    
    # 删除关联表
    op.drop_table('learning_path_knowledge_points')
    op.drop_table('knowledge_dependencies')
    
    # 删除主表
    op.drop_table('system_configs')
    op.drop_table('import_tasks')
    op.drop_table('document_chunks')
    op.drop_table('learning_recommendations')
    op.drop_table('daily_learning_plans')
    op.drop_table('user_learning_plans')
    op.drop_table('learning_paths')
    op.drop_table('user_knowledge_progress')
    op.drop_table('skill_points')
    op.drop_table('knowledge_points')
    op.drop_table('knowledge_domains') 