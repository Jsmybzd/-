"""
安全工具模块
负责密码加密、用户注册、权限校验等核心安全功能
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session
import hashlib

# 导入模型（确保路径正确）
from app.core import models


def hash_password_sha256(password: str) -> str:
    """
    SHA256加密密码
    :param password: 明文密码
    :return: 加密后的哈希字符串
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(
        db: Session,
        phone: str,
        name: str,
        password: str,
        role_type: str
) -> Optional[Dict]:
    """
    用户注册：新增用户到用户表（纯ORM写法，无原生SQL）
    :param db: 数据库会话
    :param phone: 手机号
    :param name: 姓名
    :param password: 明文密码
    :param role_type: 角色类型
    :return: 新用户信息字典，手机号已存在返回None
    """
    try:
        # 1. 检查手机号是否已注册
        existing_user = db.query(models.User).filter(models.User.phone == phone).first()
        if existing_user:
            return None
        
        # 2. 哈希密码
        pwd_hash = hash_password_sha256(password)
        
        # 3. ORM创建用户（自动匹配models.py的字段映射）
        new_user = models.User(
            name=name,
            phone=phone,
            role_type=role_type,
            password_hash=pwd_hash,    # 对应数据库：密码哈希
            failed_login_count=0,      # 对应数据库：登录失败次数
            is_locked=False            # 对应数据库：是否锁定
        )
        db.add(new_user)
        db.commit()       # 提交后生成id
        db.refresh(new_user)  # 刷新获取完整用户信息
        
        # 4. 返回用户信息
        return {
            "user_id": new_user.id,
            "name": new_user.name,
            "phone": new_user.phone,
            "role_type": new_user.role_type
        }
    
    except Exception as e:
        db.rollback()
        raise e  # 抛出异常便于调试


def verify_user_password(db: Session, phone: str, password: str) -> Optional[models.User]:
    """
    验证用户密码
    :param db: 数据库会话
    :param phone: 手机号
    :param password: 明文密码
    :return: 验证成功返回用户对象，失败返回None
    """
    user = db.query(models.User).filter(models.User.phone == phone).first()
    if not user:
        return None
    
    # 验证密码哈希
    pwd_hash = hash_password_sha256(password)
    if pwd_hash != user.password_hash:
        return None
    
    return user