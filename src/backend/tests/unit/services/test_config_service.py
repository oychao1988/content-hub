"""
系统配置模块服务单元测试
"""

import pytest
from sqlalchemy.orm import Session
from app.modules.config.services import WritingStyleService, ContentThemeService
from app.models.account import WritingStyle
from app.models.theme import ContentTheme


@pytest.mark.unit
class TestWritingStyleService:
    """写作风格管理服务测试类"""

    def test_create_writing_style(self, db_session: Session):
        """测试创建系统级写作风格"""
        # 准备测试数据
        style_data = {
            "name": "专业技术风格",
            "code": "tech_professional",
            "description": "适合技术博客的专业写作风格",
            "tone": "专业",
            "persona": "技术专家",
            "min_words": 800,
            "max_words": 1500,
            "emoji_usage": "适度",
            "forbidden_words": ["非常好的", "特别棒的"],
            "is_system": True,
            "account_id": None
        }

        # 执行测试
        writing_style = WritingStyleService.create_writing_style(db_session, style_data)

        # 断言结果
        assert writing_style is not None
        assert writing_style.name == "专业技术风格"
        assert writing_style.code == "tech_professional"
        assert writing_style.description == "适合技术博客的专业写作风格"
        assert writing_style.tone == "专业"
        assert writing_style.persona == "技术专家"
        assert writing_style.min_words == 800
        assert writing_style.max_words == 1500
        assert writing_style.emoji_usage == "适度"
        assert writing_style.forbidden_words == ["非常好的", "特别棒的"]
        assert writing_style.is_system is True
        assert writing_style.account_id is None
        assert writing_style.id is not None

    def test_get_writing_style_list(self, db_session: Session):
        """测试获取写作风格列表"""
        # 创建多个测试数据
        styles = [
            {
                "name": "技术风格",
                "code": "tech_style",
                "description": "技术博客风格",
                "is_system": True,
                "account_id": None
            },
            {
                "name": "娱乐风格",
                "code": "entertainment_style",
                "description": "娱乐内容风格",
                "is_system": False,
                "account_id": None
            },
            {
                "name": "教育风格",
                "code": "education_style",
                "description": "教育内容风格",
                "is_system": True,
                "account_id": None
            }
        ]

        for style_data in styles:
            WritingStyleService.create_writing_style(db_session, style_data)

        # 执行测试 - 获取全部
        all_styles = WritingStyleService.get_writing_styles(db_session)
        assert len(all_styles) >= 3

        # 执行测试 - 分页
        page_styles = WritingStyleService.get_writing_styles(db_session, skip=0, limit=2)
        assert len(page_styles) == 2

        # 验证按创建时间降序排列
        assert all_styles[0].created_at >= all_styles[1].created_at

    def test_get_writing_style_detail(self, db_session: Session):
        """测试获取写作风格详情"""
        # 创建测试数据
        style_data = {
            "name": "商务风格",
            "code": "business_style",
            "description": "商务写作风格",
            "tone": "正式",
            "persona": "商务顾问",
            "min_words": 1000,
            "max_words": 2000,
            "is_system": False,
            "account_id": None
        }
        created_style = WritingStyleService.create_writing_style(db_session, style_data)

        # 执行测试 - 通过 ID 获取
        retrieved_by_id = WritingStyleService.get_writing_style_by_id(db_session, created_style.id)
        assert retrieved_by_id is not None
        assert retrieved_by_id.id == created_style.id
        assert retrieved_by_id.name == "商务风格"
        assert retrieved_by_id.code == "business_style"

        # 执行测试 - 通过代码获取
        retrieved_by_code = WritingStyleService.get_writing_style_by_code(db_session, "business_style")
        assert retrieved_by_code is not None
        assert retrieved_by_code.id == created_style.id
        assert retrieved_by_code.name == "商务风格"

        # 测试获取不存在的风格
        nonexistent = WritingStyleService.get_writing_style_by_id(db_session, 9999)
        assert nonexistent is None

    def test_update_writing_style(self, db_session: Session):
        """测试更新写作风格"""
        # 创建测试数据
        style_data = {
            "name": "原始风格",
            "code": "original_style",
            "description": "原始描述",
            "tone": "正式",
            "min_words": 800,
            "max_words": 1500,
            "is_system": False,
            "account_id": None
        }
        created_style = WritingStyleService.create_writing_style(db_session, style_data)

        # 执行测试 - 更新部分字段
        update_data = {
            "name": "更新后的风格",
            "description": "更新后的描述",
            "tone": "轻松",
            "min_words": 1000,
            "max_words": 2000
        }
        updated_style = WritingStyleService.update_writing_style(db_session, created_style.id, update_data)

        # 断言结果
        assert updated_style is not None
        assert updated_style.id == created_style.id
        assert updated_style.name == "更新后的风格"
        assert updated_style.description == "更新后的描述"
        assert updated_style.tone == "轻松"
        assert updated_style.min_words == 1000
        assert updated_style.max_words == 2000
        # 验证未更新的字段保持不变
        assert updated_style.code == "original_style"
        assert updated_style.is_system is False

        # 测试更新不存在的风格
        nonexistent_update = WritingStyleService.update_writing_style(
            db_session, 9999, {"name": "不存在"}
        )
        assert nonexistent_update is None

        # 测试更新代码为已存在的代码
        style_data2 = {
            "name": "第二个风格",
            "code": "second_style",
            "is_system": False,
            "account_id": None
        }
        WritingStyleService.create_writing_style(db_session, style_data2)

        # 尝试将第一个风格的代码更新为第二个风格的代码
        with pytest.raises(ValueError) as exc_info:
            WritingStyleService.update_writing_style(
                db_session, created_style.id, {"code": "second_style"}
            )
        assert "已存在" in str(exc_info.value)

    def test_delete_writing_style(self, db_session: Session):
        """测试删除写作风格"""
        # 创建自定义风格
        style_data = {
            "name": "待删除的自定义风格",
            "code": "custom_to_delete",
            "description": "这是一个自定义风格",
            "is_system": False,
            "account_id": None
        }
        created_style = WritingStyleService.create_writing_style(db_session, style_data)

        # 执行测试 - 删除自定义风格
        result = WritingStyleService.delete_writing_style(db_session, created_style.id)

        # 断言结果
        assert result is True

        # 验证已删除
        retrieved = WritingStyleService.get_writing_style_by_id(db_session, created_style.id)
        assert retrieved is None

        # 创建系统级风格
        system_style_data = {
            "name": "系统级风格",
            "code": "system_style",
            "description": "系统级风格",
            "is_system": True,
            "account_id": None
        }
        system_style = WritingStyleService.create_writing_style(db_session, system_style_data)

        # 测试删除系统级风格 - 应该抛出异常
        with pytest.raises(ValueError) as exc_info:
            WritingStyleService.delete_writing_style(db_session, system_style.id)
        assert "系统级写作风格不允许删除" in str(exc_info.value)

        # 测试删除不存在的风格
        result_nonexistent = WritingStyleService.delete_writing_style(db_session, 9999)
        assert result_nonexistent is False

    def test_get_system_writing_styles(self, db_session: Session):
        """测试获取系统级写作风格列表"""
        # 创建系统级和自定义风格
        WritingStyleService.create_writing_style(db_session, {
            "name": "系统风格1",
            "code": "system1",
            "is_system": True,
            "account_id": None
        })
        WritingStyleService.create_writing_style(db_session, {
            "name": "系统风格2",
            "code": "system2",
            "is_system": True,
            "account_id": None
        })
        WritingStyleService.create_writing_style(db_session, {
            "name": "自定义风格",
            "code": "custom1",
            "is_system": False,
            "account_id": None
        })

        # 执行测试
        system_styles = WritingStyleService.get_system_writing_styles(db_session)
        custom_styles = WritingStyleService.get_custom_writing_styles(db_session)

        # 断言结果
        assert len(system_styles) == 2
        assert len(custom_styles) == 1
        assert all(style.is_system for style in system_styles)
        assert all(not style.is_system for style in custom_styles)

    def test_create_duplicate_code(self, db_session: Session):
        """测试创建重复代码的写作风格"""
        # 创建第一个风格
        style_data = {
            "name": "第一个风格",
            "code": "duplicate_code",
            "is_system": False,
            "account_id": None
        }
        WritingStyleService.create_writing_style(db_session, style_data)

        # 尝试创建相同代码的风格 - 应该抛出异常
        duplicate_data = {
            "name": "第二个风格",
            "code": "duplicate_code",  # 相同的代码
            "is_system": False,
            "account_id": None
        }
        with pytest.raises(ValueError) as exc_info:
            WritingStyleService.create_writing_style(db_session, duplicate_data)
        assert "已存在" in str(exc_info.value)


@pytest.mark.unit
class TestContentThemeService:
    """内容主题管理服务测试类"""

    def test_create_content_theme(self, db_session: Session):
        """测试创建系统级内容主题"""
        # 准备测试数据
        theme_data = {
            "name": "技术教程",
            "code": "tech_tutorial",
            "description": "技术教程类内容主题",
            "type": "技术",
            "is_system": True
        }

        # 执行测试
        content_theme = ContentThemeService.create_content_theme(db_session, theme_data)

        # 断言结果
        assert content_theme is not None
        assert content_theme.name == "技术教程"
        assert content_theme.code == "tech_tutorial"
        assert content_theme.description == "技术教程类内容主题"
        assert content_theme.type == "技术"
        assert content_theme.is_system is True
        assert content_theme.id is not None

    def test_get_content_theme_list(self, db_session: Session):
        """测试获取内容主题列表"""
        # 创建多个测试数据
        themes = [
            {
                "name": "技术主题",
                "code": "tech_theme",
                "description": "技术类主题",
                "type": "技术",
                "is_system": True
            },
            {
                "name": "娱乐主题",
                "code": "entertainment_theme",
                "description": "娱乐类主题",
                "type": "娱乐",
                "is_system": False
            },
            {
                "name": "教育主题",
                "code": "education_theme",
                "description": "教育类主题",
                "type": "教育",
                "is_system": True
            }
        ]

        for theme_data in themes:
            ContentThemeService.create_content_theme(db_session, theme_data)

        # 执行测试 - 获取全部
        all_themes = ContentThemeService.get_content_themes(db_session)
        assert len(all_themes) >= 3

        # 执行测试 - 分页
        page_themes = ContentThemeService.get_content_themes(db_session, skip=0, limit=2)
        assert len(page_themes) == 2

        # 验证按创建时间降序排列
        assert all_themes[0].created_at >= all_themes[1].created_at

    def test_get_content_theme_detail(self, db_session: Session):
        """测试获取内容主题详情"""
        # 创建测试数据
        theme_data = {
            "name": "商务主题",
            "code": "business_theme",
            "description": "商务类内容主题",
            "type": "商务",
            "is_system": False
        }
        created_theme = ContentThemeService.create_content_theme(db_session, theme_data)

        # 执行测试 - 通过 ID 获取
        retrieved_by_id = ContentThemeService.get_content_theme_by_id(db_session, created_theme.id)
        assert retrieved_by_id is not None
        assert retrieved_by_id.id == created_theme.id
        assert retrieved_by_id.name == "商务主题"
        assert retrieved_by_id.code == "business_theme"

        # 执行测试 - 通过代码获取
        retrieved_by_code = ContentThemeService.get_content_theme_by_code(db_session, "business_theme")
        assert retrieved_by_code is not None
        assert retrieved_by_code.id == created_theme.id
        assert retrieved_by_code.name == "商务主题"

        # 测试获取不存在的主题
        nonexistent = ContentThemeService.get_content_theme_by_id(db_session, 9999)
        assert nonexistent is None

    def test_update_content_theme(self, db_session: Session):
        """测试更新内容主题"""
        # 创建测试数据
        theme_data = {
            "name": "原始主题",
            "code": "original_theme",
            "description": "原始描述",
            "type": "技术",
            "is_system": False
        }
        created_theme = ContentThemeService.create_content_theme(db_session, theme_data)

        # 执行测试 - 更新部分字段
        update_data = {
            "name": "更新后的主题",
            "description": "更新后的描述",
            "type": "教育"
        }
        updated_theme = ContentThemeService.update_content_theme(
            db_session, created_theme.id, update_data
        )

        # 断言结果
        assert updated_theme is not None
        assert updated_theme.id == created_theme.id
        assert updated_theme.name == "更新后的主题"
        assert updated_theme.description == "更新后的描述"
        assert updated_theme.type == "教育"
        # 验证未更新的字段保持不变
        assert updated_theme.code == "original_theme"
        assert updated_theme.is_system is False

        # 测试更新不存在的主题
        nonexistent_update = ContentThemeService.update_content_theme(
            db_session, 9999, {"name": "不存在"}
        )
        assert nonexistent_update is None

        # 测试更新代码为已存在的代码
        theme_data2 = {
            "name": "第二个主题",
            "code": "second_theme",
            "is_system": False
        }
        ContentThemeService.create_content_theme(db_session, theme_data2)

        # 尝试将第一个主题的代码更新为第二个主题的代码
        with pytest.raises(ValueError) as exc_info:
            ContentThemeService.update_content_theme(
                db_session, created_theme.id, {"code": "second_theme"}
            )
        assert "已存在" in str(exc_info.value)

    def test_delete_content_theme(self, db_session: Session):
        """测试删除内容主题"""
        # 创建自定义主题
        theme_data = {
            "name": "待删除的自定义主题",
            "code": "custom_to_delete",
            "description": "这是一个自定义主题",
            "type": "其他",
            "is_system": False
        }
        created_theme = ContentThemeService.create_content_theme(db_session, theme_data)

        # 执行测试 - 删除自定义主题
        result = ContentThemeService.delete_content_theme(db_session, created_theme.id)

        # 断言结果
        assert result is True

        # 验证已删除
        retrieved = ContentThemeService.get_content_theme_by_id(db_session, created_theme.id)
        assert retrieved is None

        # 创建系统级主题
        system_theme_data = {
            "name": "系统级主题",
            "code": "system_theme",
            "description": "系统级主题",
            "type": "系统",
            "is_system": True
        }
        system_theme = ContentThemeService.create_content_theme(db_session, system_theme_data)

        # 测试删除系统级主题 - 应该抛出异常
        with pytest.raises(ValueError) as exc_info:
            ContentThemeService.delete_content_theme(db_session, system_theme.id)
        assert "系统级内容主题不允许删除" in str(exc_info.value)

        # 测试删除不存在的主题
        result_nonexistent = ContentThemeService.delete_content_theme(db_session, 9999)
        assert result_nonexistent is False

    def test_get_system_content_themes(self, db_session: Session):
        """测试获取系统级内容主题列表"""
        # 创建系统级和自定义主题
        ContentThemeService.create_content_theme(db_session, {
            "name": "系统主题1",
            "code": "system_theme1",
            "type": "技术",
            "is_system": True
        })
        ContentThemeService.create_content_theme(db_session, {
            "name": "系统主题2",
            "code": "system_theme2",
            "type": "教育",
            "is_system": True
        })
        ContentThemeService.create_content_theme(db_session, {
            "name": "自定义主题",
            "code": "custom_theme1",
            "type": "娱乐",
            "is_system": False
        })

        # 执行测试
        system_themes = ContentThemeService.get_system_content_themes(db_session)
        custom_themes = ContentThemeService.get_custom_content_themes(db_session)

        # 断言结果
        assert len(system_themes) == 2
        assert len(custom_themes) == 1
        assert all(theme.is_system for theme in system_themes)
        assert all(not theme.is_system for theme in custom_themes)

    def test_create_duplicate_theme_code(self, db_session: Session):
        """测试创建重复代码的内容主题"""
        # 创建第一个主题
        theme_data = {
            "name": "第一个主题",
            "code": "duplicate_theme_code",
            "type": "技术",
            "is_system": False
        }
        ContentThemeService.create_content_theme(db_session, theme_data)

        # 尝试创建相同代码的主题 - 应该抛出异常
        duplicate_data = {
            "name": "第二个主题",
            "code": "duplicate_theme_code",  # 相同的代码
            "type": "教育",
            "is_system": False
        }
        with pytest.raises(ValueError) as exc_info:
            ContentThemeService.create_content_theme(db_session, duplicate_data)
        assert "已存在" in str(exc_info.value)
