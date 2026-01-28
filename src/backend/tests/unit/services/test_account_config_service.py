"""
账号配置服务单元测试
"""
import pytest
from sqlalchemy.orm import Session
import tempfile
import os

from app.services.account_config_service import account_config_service
from app.models.account import AccountConfig, WritingStyle, ContentSection, DataSource, PublishConfig
from app.models.account import Account
from app.models.customer import Customer
from app.models.platform import Platform


@pytest.mark.unit
def test_create_and_get_account_config(db_session: Session, test_customer: Customer):
    """测试创建和获取账号配置"""
    # 创建测试平台和账号
    platform = Platform(
        name="测试平台",
        code="test_platform",
        type="social_media",
        description="用于测试的平台",
        api_url="https://api.test.com",
        api_key="test_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="测试账号",
        directory_name="test_account_dir",
        description="这是一个测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建配置
    config_data = {
        "key1": "value1",
        "key2": "value2",
        "settings": {"option1": True, "option2": "test"}
    }

    config = account_config_service.create_config(
        db_session,
        account_id=account.id,
        config_type="general",
        config_name="通用配置",
        config_data=config_data,
        markdown_content="# 通用配置\n\n这是一个测试配置"
    )

    # 验证配置创建
    assert config is not None
    assert config.id is not None
    assert config.account_id == account.id
    assert config.config_type == "general"
    assert config.config_name == "通用配置"
    assert config.config_data == config_data
    assert config.markdown_content == "# 通用配置\n\n这是一个测试配置"

    # 测试按类型获取配置
    retrieved_config = account_config_service.get_config_by_type(
        db_session, account.id, "general"
    )
    assert retrieved_config is not None
    assert retrieved_config.id == config.id

    # 测试获取账号所有配置
    all_configs = account_config_service.get_account_configs(db_session, account.id)
    assert len(all_configs) == 1
    assert all_configs[0].id == config.id

    print(f"✓ 账号配置创建和查询测试通过 (ID: {config.id})")


@pytest.mark.unit
def test_update_account_config(db_session: Session, test_customer: Customer):
    """测试更新账号配置"""
    # 创建测试平台和账号
    platform = Platform(
        name="更新测试平台",
        code="update_platform",
        type="social_media",
        description="用于更新测试的平台",
        api_url="https://api.update.com",
        api_key="update_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="更新测试账号",
        directory_name="update_account_dir",
        description="这是一个更新测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建初始配置
    config_data = {"key1": "value1"}
    config = account_config_service.create_config(
        db_session,
        account_id=account.id,
        config_type="general",
        config_name="初始配置",
        config_data=config_data
    )

    # 更新配置
    new_data = {"key1": "updated_value", "key3": "new_value"}
    updated_config = account_config_service.update_config(
        db_session,
        config_id=config.id,
        config_data=new_data,
        markdown_content="# 更新后的配置\n\n配置已更新"
    )

    # 验证更新
    assert updated_config is not None
    assert updated_config.config_data == new_data
    assert updated_config.markdown_content == "# 更新后的配置\n\n配置已更新"

    print(f"✓ 账号配置更新测试通过 (ID: {config.id})")


@pytest.mark.unit
def test_delete_account_config(db_session: Session, test_customer: Customer):
    """测试删除账号配置"""
    # 创建测试平台和账号
    platform = Platform(
        name="删除测试平台",
        code="delete_platform",
        type="social_media",
        description="用于删除测试的平台",
        api_url="https://api.delete.com",
        api_key="delete_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="删除测试账号",
        directory_name="delete_account_dir",
        description="这是一个删除测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建配置
    config = account_config_service.create_config(
        db_session,
        account_id=account.id,
        config_type="general",
        config_name="待删除配置",
        config_data={"key": "value"}
    )

    config_id = config.id

    # 删除配置
    result = account_config_service.delete_config(db_session, config_id)
    assert result is True

    # 验证配置已删除
    deleted_config = account_config_service.get_config_by_type(
        db_session, account.id, "general"
    )
    assert deleted_config is None

    print("✓ 账号配置删除测试通过")


@pytest.mark.unit
def test_writing_style_config(db_session: Session, test_customer: Customer):
    """测试写作风格配置"""
    # 创建测试平台和账号
    platform = Platform(
        name="写作风格测试平台",
        code="writing_style_platform",
        type="social_media",
        description="用于写作风格测试的平台",
        api_url="https://api.writing.com",
        api_key="writing_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="写作风格测试账号",
        directory_name="writing_style_account_dir",
        description="这是一个写作风格测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 更新写作风格配置（不存在时会创建）
    style_data = {
        "name": "正式风格",
        "code": "formal_style",
        "description": "适合官方发布的正式写作风格",
        "tone": "专业",
        "persona": "企业官方发言人",
        "min_words": 800,
        "max_words": 1500,
        "emoji_usage": "适度",
        "forbidden_words": ["敏感词1", "敏感词2"]
    }

    writing_style = account_config_service.update_writing_style(
        db_session, account.id, style_data
    )

    # 验证写作风格配置
    assert writing_style is not None
    assert writing_style.account_id == account.id
    assert writing_style.name == "正式风格"
    assert writing_style.code == "formal_style"
    assert writing_style.description == "适合官方发布的正式写作风格"
    assert writing_style.tone == "专业"
    assert writing_style.persona == "企业官方发言人"
    assert writing_style.min_words == 800
    assert writing_style.max_words == 1500
    assert writing_style.emoji_usage == "适度"
    assert writing_style.forbidden_words == ["敏感词1", "敏感词2"]

    # 获取写作风格配置
    retrieved_style = account_config_service.get_writing_style(
        db_session, account.id
    )
    assert retrieved_style is not None
    assert retrieved_style.id == writing_style.id

    print(f"✓ 写作风格配置测试通过 (ID: {writing_style.id})")


@pytest.mark.unit
def test_content_section_config(db_session: Session, test_customer: Customer):
    """测试内容板块配置"""
    # 创建测试平台和账号
    platform = Platform(
        name="内容板块测试平台",
        code="content_section_platform",
        type="social_media",
        description="用于内容板块测试的平台",
        api_url="https://api.content.com",
        api_key="content_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="内容板块测试账号",
        directory_name="content_section_account_dir",
        description="这是一个内容板块测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建内容板块
    section_data = {
        "name": "新闻摘要",
        "code": "news_summary",
        "description": "每日新闻摘要板块",
        "word_count": 1000,
        "update_frequency": "每日",
        "publish_time": "08:00",
        "modules": ["标题", "摘要", "正文"]
    }

    section = account_config_service.create_content_section(
        db_session, account.id, section_data
    )

    # 验证内容板块创建
    assert section is not None
    assert section.account_id == account.id
    assert section.name == "新闻摘要"
    assert section.code == "news_summary"
    assert section.description == "每日新闻摘要板块"
    assert section.word_count == 1000
    assert section.update_frequency == "每日"
    assert section.publish_time == "08:00"
    assert section.modules == ["标题", "摘要", "正文"]

    # 获取内容板块列表
    sections = account_config_service.get_content_sections(db_session, account.id)
    assert len(sections) == 1
    assert sections[0].id == section.id

    # 更新内容板块
    update_data = {"name": "每日新闻摘要", "word_count": 1200}
    updated_section = account_config_service.update_content_section(
        db_session, section.id, update_data
    )
    assert updated_section is not None
    assert updated_section.name == "每日新闻摘要"
    assert updated_section.word_count == 1200

    # 删除内容板块
    delete_result = account_config_service.delete_content_section(
        db_session, section.id
    )
    assert delete_result is True

    # 验证删除
    deleted_sections = account_config_service.get_content_sections(
        db_session, account.id
    )
    assert len(deleted_sections) == 0

    print("✓ 内容板块配置测试通过")


@pytest.mark.unit
def test_data_source_config(db_session: Session, test_customer: Customer):
    """测试数据源配置"""
    # 创建测试平台和账号
    platform = Platform(
        name="数据源测试平台",
        code="data_source_platform",
        type="social_media",
        description="用于数据源测试的平台",
        api_url="https://api.data.com",
        api_key="data_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="数据源测试账号",
        directory_name="data_source_account_dir",
        description="这是一个数据源测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建数据源
    source_data = {
        "name": "腾讯新闻",
        "type": "rss",
        "url": "https://news.qq.com/rss",
        "strategy": "每日抓取重要新闻",
        "keywords": ["科技", "财经", "社会"],
        "scoring_criteria": {"时效性": 0.4, "相关性": 0.3, "重要性": 0.3}
    }

    data_source = account_config_service.create_data_source(
        db_session, account.id, source_data
    )

    # 验证数据源创建
    assert data_source is not None
    assert data_source.account_id == account.id
    assert data_source.name == "腾讯新闻"
    assert data_source.type == "rss"
    assert data_source.url == "https://news.qq.com/rss"
    assert data_source.strategy == "每日抓取重要新闻"
    assert data_source.keywords == ["科技", "财经", "社会"]
    assert data_source.scoring_criteria == {"时效性": 0.4, "相关性": 0.3, "重要性": 0.3}

    # 获取数据源列表
    sources = account_config_service.get_data_sources(db_session, account.id)
    assert len(sources) == 1
    assert sources[0].id == data_source.id

    print(f"✓ 数据源配置测试通过 (ID: {data_source.id})")


@pytest.mark.unit
def test_publish_config(db_session: Session, test_customer: Customer):
    """测试发布配置"""
    # 创建测试平台和账号
    platform = Platform(
        name="发布配置测试平台",
        code="publish_config_platform",
        type="social_media",
        description="用于发布配置测试的平台",
        api_url="https://api.publish.com",
        api_key="publish_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="发布配置测试账号",
        directory_name="publish_config_account_dir",
        description="这是一个发布配置测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 更新发布配置（不存在时会创建）
    config_data = {
        "theme_id": None,
        "review_mode": "auto",
        "publish_mode": "draft",
        "auto_publish": False,
        "publish_times": ["08:00", "12:00", "18:00"],
        "section_theme_map": {"news": 1, "tech": 2},
        "batch_settings": {"size": 5, "interval": 300}
    }

    publish_config = account_config_service.update_publish_config(
        db_session, account.id, config_data
    )

    # 验证发布配置
    assert publish_config is not None
    assert publish_config.account_id == account.id
    assert publish_config.theme_id is None
    assert publish_config.review_mode == "auto"
    assert publish_config.publish_mode == "draft"
    assert publish_config.auto_publish is False
    assert publish_config.publish_times == ["08:00", "12:00", "18:00"]
    assert publish_config.section_theme_map == {"news": 1, "tech": 2}
    assert publish_config.batch_settings == {"size": 5, "interval": 300}

    # 获取发布配置
    retrieved_config = account_config_service.get_publish_config(
        db_session, account.id
    )
    assert retrieved_config is not None
    assert retrieved_config.id == publish_config.id

    print(f"✓ 发布配置测试通过 (ID: {publish_config.id})")


@pytest.mark.unit
def test_import_export_markdown(db_session: Session, test_customer: Customer):
    """测试 Markdown 导入和导出"""
    # 创建测试平台和账号
    platform = Platform(
        name="Markdown测试平台",
        code="markdown_platform",
        type="social_media",
        description="用于Markdown导入导出测试的平台",
        api_url="https://api.markdown.com",
        api_key="markdown_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="Markdown测试账号",
        directory_name="markdown_account_dir",
        description="这是一个Markdown测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建临时Markdown文件用于导入
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
        temp_file.write("# 测试配置\n\n这是一个从Markdown导入的配置文件\n\n## 配置项\n\n- 选项1: 值1\n- 选项2: 值2")
        temp_file_path = temp_file.name

    try:
        # 测试导入Markdown
        import_result = account_config_service.import_from_markdown(
            db_session, account.id, temp_file_path
        )

        assert import_result["success"] is True
        assert import_result["imported"] == 1

        # 测试导出Markdown
        exported_content = account_config_service.export_to_markdown(
            db_session, account.id
        )

        assert exported_content is not None
        assert len(exported_content) > 0
        assert "# 账号配置" in exported_content
        assert "markdown_config" in exported_content

        print("✓ Markdown导入导出测试通过")

    finally:
        # 清理临时文件
        os.unlink(temp_file_path)


@pytest.mark.unit
def test_account_config_comprehensive(db_session: Session, test_customer: Customer):
    """综合测试账号配置服务"""
    # 创建测试平台和账号
    platform = Platform(
        name="综合测试平台",
        code="comprehensive_platform",
        type="social_media",
        description="用于综合测试的平台",
        api_url="https://api.comprehensive.com",
        api_key="comprehensive_api_key",
        is_active=True
    )
    db_session.add(platform)
    db_session.commit()

    account = Account(
        customer_id=test_customer.id,
        platform_id=platform.id,
        name="综合测试账号",
        directory_name="comprehensive_account_dir",
        description="这是一个综合测试账号",
        is_active=True
    )
    db_session.add(account)
    db_session.commit()

    # 创建多种类型的配置
    # 1. 通用配置
    general_config = account_config_service.create_config(
        db_session,
        account_id=account.id,
        config_type="general",
        config_name="通用配置",
        config_data={"setting1": "value1"},
        markdown_content="# 通用配置"
    )

    # 2. 写作风格配置
    writing_style = account_config_service.update_writing_style(
        db_session, account.id, {"name": "测试风格", "code": "test_style"}
    )

    # 3. 内容板块配置
    content_section = account_config_service.create_content_section(
        db_session, account.id, {"name": "测试板块", "code": "test_section"}
    )

    # 4. 数据源配置
    data_source = account_config_service.create_data_source(
        db_session, account.id, {"name": "测试数据源", "type": "tavily"}
    )

    # 5. 发布配置
    publish_config = account_config_service.update_publish_config(
        db_session, account.id, {"auto_publish": False}
    )

    # 验证所有配置创建成功
    assert general_config is not None
    assert writing_style is not None
    assert content_section is not None
    assert data_source is not None
    assert publish_config is not None

    # 验证查询方法
    assert len(account_config_service.get_account_configs(db_session, account.id)) == 1
    assert account_config_service.get_writing_style(db_session, account.id) is not None
    assert len(account_config_service.get_content_sections(db_session, account.id)) == 1
    assert len(account_config_service.get_data_sources(db_session, account.id)) == 1
    assert account_config_service.get_publish_config(db_session, account.id) is not None

    print("✓ 账号配置服务综合测试通过")
