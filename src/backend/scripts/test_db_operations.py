#!/usr/bin/env python
"""
数据库操作测试脚本
测试基本的数据库CRUD操作
"""
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models import (
    User, Customer, Platform, ContentTheme,
    Account, WritingStyle, ContentSection, DataSource, PublishConfig,
    Content, TopicHistory,
    ScheduledTask, TaskExecution,
    PublishLog, PublishPool
)


def test_basic_operations():
    """测试基本数据库操作"""

    print("=" * 60)
    print("  数据库操作测试")
    print("=" * 60)

    # 创建数据库会话
    db = SessionLocal()

    try:
        # 1. 创建测试数据
        print("\n1. 创建测试数据...")

        # 创建客户
        customer = Customer(
            name="测试客户",
            contact_name="张三",
            contact_email="zhangsan@example.com",
            contact_phone="13800138000",
            description="这是一个测试客户",
            is_active=True
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"   ✓ 创建客户: {customer.name} (ID: {customer.id})")

        # 创建平台
        platform = Platform(
            name="微信公众号",
            code="wechat",
            type="social_media",
            description="微信公众号平台",
            is_active=True
        )
        db.add(platform)
        db.commit()
        db.refresh(platform)
        print(f"   ✓ 创建平台: {platform.name} (ID: {platform.id})")

        # 创建用户
        user = User(
            username="testuser",
            email="testuser@example.com",
            password_hash="hashed_password_here",
            full_name="测试用户",
            role="operator",
            is_active=True,
            customer_id=customer.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"   ✓ 创建用户: {user.username} (ID: {user.id})")

        # 创建账号
        account = Account(
            customer_id=customer.id,
            platform_id=platform.id,
            name="测试公众号",
            directory_name="test_account",
            description="这是一个测试账号",
            wechat_app_id="wx1234567890",
            is_active=True
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        print(f"   ✓ 创建账号: {account.name} (ID: {account.id})")

        # 创建内容主题
        theme = ContentTheme(
            name="科技主题",
            code="tech",
            description="科技类内容主题",
            type="technology",
            is_system=True
        )
        db.add(theme)
        db.commit()
        db.refresh(theme)
        print(f"   ✓ 创建主题: {theme.name} (ID: {theme.id})")

        # 创建写作风格
        writing_style = WritingStyle(
            name="专业风格",
            code="professional",
            description="专业的写作风格",
            tone="专业",
            persona="行业专家",
            min_words=800,
            max_words=1500,
            emoji_usage="适度",
            is_system=False,
            account_id=account.id
        )
        db.add(writing_style)
        db.commit()
        db.refresh(writing_style)
        print(f"   ✓ 创建写作风格: {writing_style.name} (ID: {writing_style.id})")

        # 创建内容板块
        section = ContentSection(
            account_id=account.id,
            name="技术文章",
            code="tech_article",
            description="技术类文章板块",
            word_count=1200,
            update_frequency="每周",
            modules=["introduction", "analysis", "conclusion"]
        )
        db.add(section)
        db.commit()
        db.refresh(section)
        print(f"   ✓ 创建内容板块: {section.name} (ID: {section.id})")

        # 创建数据源
        data_source = DataSource(
            account_id=account.id,
            name="Tavily搜索",
            type="tavily",
            keywords=["AI", "技术", "编程"],
            scoring_criteria={"freshness": 0.5, "relevance": 0.5}
        )
        db.add(data_source)
        db.commit()
        db.refresh(data_source)
        print(f"   ✓ 创建数据源: {data_source.name} (ID: {data_source.id})")

        # 创建发布配置
        publish_config = PublishConfig(
            account_id=account.id,
            theme_id=theme.id,
            review_mode="auto",
            publish_mode="draft",
            auto_publish=False
        )
        db.add(publish_config)
        db.commit()
        db.refresh(publish_config)
        print(f"   ✓ 创建发布配置: (ID: {publish_config.id})")

        # 创建内容
        content = Content(
            account_id=account.id,
            title="测试文章标题",
            content="# 测试文章内容\n\n这是一篇测试文章。",
            section_code=section.code,
            review_mode="auto",
            review_status="approved",
            publish_status="draft",
            priority=5
        )
        db.add(content)
        db.commit()
        db.refresh(content)
        print(f"   ✓ 创建内容: {content.title} (ID: {content.id})")

        # 创建发布池条目
        pool_entry = PublishPool(
            content_id=content.id,
            priority=5
        )
        db.add(pool_entry)
        db.commit()
        db.refresh(pool_entry)
        print(f"   ✓ 创建发布池条目: (ID: {pool_entry.id})")

        # 创建定时任务
        task = ScheduledTask(
            name="每日内容生成",
            description="每天自动生成内容",
            task_type="content_generation",
            cron_expression="0 9 * * *",
            is_active=True
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        print(f"   ✓ 创建定时任务: {task.name} (ID: {task.id})")

        # 2. 测试查询
        print("\n2. 测试查询操作...")

        # 查询客户的所有账号
        customer_accounts = db.query(Account).filter(Account.customer_id == customer.id).all()
        print(f"   ✓ 客户 '{customer.name}' 的账号数量: {len(customer_accounts)}")

        # 查询平台的所有账号
        platform_accounts = db.query(Account).filter(Account.platform_id == platform.id).all()
        print(f"   ✓ 平台 '{platform.name}' 的账号数量: {len(platform_accounts)}")

        # 查询账号的所有内容
        account_contents = db.query(Content).filter(Content.account_id == account.id).all()
        print(f"   ✓ 账号 '{account.name}' 的内容数量: {len(account_contents)}")

        # 查询用户信息
        db_user = db.query(User).filter(User.username == "testuser").first()
        print(f"   ✓ 用户 '{db_user.username}' 的角色: {db_user.role}")
        print(f"   ✓ 用户所属客户: {db_user.customer.name if db_user.customer else '无'}")

        # 3. 测试关系访问
        print("\n3. 测试关系访问...")

        # 通过账号访问客户
        print(f"   ✓ 账号所属客户: {account.customer.name}")
        # 通过账号访问平台
        print(f"   ✓ 账号所属平台: {account.platform.name}")
        # 通过账号访问写作风格
        print(f"   ✓ 账号写作风格: {account.writing_style.name if account.writing_style else '无'}")
        # 通过账号访问内容板块
        print(f"   ✓ 账号内容板块数量: {len(account.content_sections)}")
        # 通过账号访问发布配置
        print(f"   ✓ 账号发布配置: {'已配置' if account.publish_config else '未配置'}")
        # 通过内容访问账号
        print(f"   ✓ 内容所属账号: {content.account.name}")
        # 通过发布配置访问主题
        print(f"   ✓ 发布配置主题: {publish_config.theme.name if publish_config.theme else '无'}")

        print("\n" + "=" * 60)
        print("  ✓ 所有测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_basic_operations()
