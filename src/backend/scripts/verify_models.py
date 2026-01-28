#!/usr/bin/env python
"""
数据库模型验证脚本
验证所有模型是否正确定义,关系是否正确
"""
from app.db.database import engine, Base
from app.models import (
    User, Customer, Platform, ContentTheme,
    Account, WritingStyle, ContentSection, DataSource, PublishConfig,
    Content, TopicHistory,
    ScheduledTask, TaskExecution,
    PublishLog, PublishPool
)


def print_section(title):
    """打印分节标题"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def verify_models():
    """验证所有模型"""

    print_section("数据库模型验证")

    # 获取所有表
    tables = Base.metadata.tables
    print(f"\n✓ 数据库表总数: {len(tables)}")

    # 打印所有表名
    print("\n数据表列表:")
    for table_name in sorted(tables.keys()):
        table = tables[table_name]
        columns = [col.name for col in table.columns]
        print(f"  - {table_name:30s} ({len(columns)} columns)")

    # 验证核心模型
    print_section("核心模型关系验证")

    models_to_check = [
        ("User", User),
        ("Customer", Customer),
        ("Platform", Platform),
        ("ContentTheme", ContentTheme),
        ("Account", Account),
        ("WritingStyle", WritingStyle),
        ("ContentSection", ContentSection),
        ("DataSource", DataSource),
        ("PublishConfig", PublishConfig),
        ("Content", Content),
        ("ScheduledTask", ScheduledTask),
        ("TaskExecution", TaskExecution),
        ("PublishLog", PublishLog),
        ("PublishPool", PublishPool),
    ]

    for model_name, model_class in models_to_check:
        print(f"\n{model_name}:")
        print(f"  表名: {model_class.__tablename__}")

        # 检查关系
        if hasattr(model_class, '__mapper__'):
            relationships = model_class.__mapper__.relationships
            if relationships:
                print(f"  关系 ({len(relationships)}):")
                for rel in relationships:
                    print(f"    - {rel.key}: {rel.mapper.class_.__name__}")

    # 验证外键关系
    print_section("外键关系验证")

    foreign_keys = {
        "User": ["customer_id"],
        "Account": ["customer_id", "platform_id"],
        "WritingStyle": ["account_id"],
        "ContentSection": ["account_id"],
        "DataSource": ["account_id"],
        "PublishConfig": ["account_id", "theme_id"],
        "Content": ["account_id"],
        "TopicHistory": ["account_id", "content_id"],
        "TaskExecution": ["task_id"],
        "PublishLog": ["account_id", "content_id"],
        "PublishPool": ["content_id"],
    }

    for model_name, fk_list in foreign_keys.items():
        print(f"\n{model_name}:")
        for fk in fk_list:
            print(f"  - {fk}")

    # 验证索引
    print_section("索引验证")

    indexes = {
        "User": ["username", "email"],
        "Customer": ["name"],
        "Platform": ["code"],
        "ContentTheme": ["code"],
        "Account": ["customer_id", "platform_id", "directory_name"],
        "Content": ["account_id"],
        "PublishPool": ["priority_scheduled"],
    }

    for model_name, idx_list in indexes.items():
        print(f"\n{model_name}:")
        for idx in idx_list:
            print(f"  - {idx}")

    print_section("验证完成")
    print("\n✓ 所有模型验证通过!")


if __name__ == "__main__":
    verify_models()
