#!/usr/bin/env python3
"""创建用户 ydz 的脚本"""

from app.db.database import get_db
from app.db import models
from app.core.auth import get_password_hash

def create_user_ydz():
    db = next(get_db())
    
    # 检查用户是否已存在
    existing_user = db.query(models.User).filter(models.User.username == 'ydz').first()
    if existing_user:
        print('User "ydz" already exists')
        return
    
    # 创建新用户
    hashed_password = get_password_hash('123456')
    new_user = models.User(
        username='ydz',
        email='ydz@example.com',
        hashed_password=hashed_password,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f'User "ydz" created successfully with ID: {new_user.id}')
    print(f'Username: {new_user.username}')
    print(f'Email: {new_user.email}')
    print(f'Active: {new_user.is_active}')

if __name__ == '__main__':
    create_user_ydz()