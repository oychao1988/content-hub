"""平台管理服务单元测试"""

import pytest
from sqlalchemy.orm import Session
from app.modules.platform.services import PlatformService
from app.models.platform import Platform


class TestPlatformService:
    """平台管理服务测试类"""

    def test_create_platform(self, db_session: Session):
        """测试创建平台"""
        # 准备测试数据
        platform_data = {
            "name": "微信公众号",
            "code": "wechat_official",
            "type": "social_media",
            "description": "微信公众号平台",
            "api_url": "https://api.weixin.qq.com",
            "api_key": "test_api_key",
            "is_active": True
        }

        # 执行测试
        platform = PlatformService.create(db_session, platform_data)

        # 断言结果
        assert platform is not None
        assert platform.name == "微信公众号"
        assert platform.code == "wechat_official"
        assert platform.type == "social_media"
        assert platform.description == "微信公众号平台"
        assert platform.api_url == "https://api.weixin.qq.com"
        assert platform.api_key == "test_api_key"
        assert platform.is_active is True

    def test_get_platform_by_id(self, db_session: Session):
        """测试通过ID获取平台"""
        # 创建测试数据
        platform_data = {
            "name": "微博",
            "code": "weibo",
            "type": "social_media",
            "description": "微博平台",
            "api_url": "https://api.weibo.com",
            "api_key": "weibo_api_key",
            "is_active": True
        }
        platform = PlatformService.create(db_session, platform_data)

        # 执行测试
        retrieved = PlatformService.get_by_id(db_session, platform.id)

        # 断言结果
        assert retrieved is not None
        assert retrieved.id == platform.id
        assert retrieved.name == platform.name

    def test_get_platform_by_code(self, db_session: Session):
        """测试通过代码获取平台"""
        # 创建测试数据
        platform_data = {
            "name": "抖音",
            "code": "douyin",
            "type": "video",
            "description": "抖音短视频平台",
            "api_url": "https://api.douyin.com",
            "api_key": "douyin_api_key",
            "is_active": True
        }
        platform = PlatformService.create(db_session, platform_data)

        # 执行测试
        retrieved = PlatformService.get_by_code(db_session, "douyin")

        # 断言结果
        assert retrieved is not None
        assert retrieved.code == "douyin"
        assert retrieved.name == "抖音"

    def test_get_all_platforms(self, db_session: Session):
        """测试获取平台列表"""
        # 创建多个测试平台
        for i in range(3):
            PlatformService.create(db_session, {
                "name": f"平台{i+1}",
                "code": f"platform{i+1}",
                "type": "social_media",
                "description": f"这是平台{i+1}",
                "api_url": f"https://api.platform{i+1}.com",
                "api_key": f"api_key{i+1}",
                "is_active": True
            })

        # 执行测试
        platforms, total = PlatformService.get_all(db_session)

        # 断言结果
        assert total >= 3
        assert len(platforms) >= 3

    def test_search_platforms(self, db_session: Session):
        """测试搜索平台"""
        # 创建测试数据
        PlatformService.create(db_session, {
            "name": "今日头条",
            "code": "toutiao",
            "type": "news",
            "description": "今日头条新闻平台",
            "api_url": "https://api.toutiao.com",
            "api_key": "toutiao_api_key",
            "is_active": True
        })

        # 执行测试
        platforms, total = PlatformService.get_all(db_session, search="头条")

        # 断言结果
        assert total >= 1
        assert any("头条" in platform.name for platform in platforms)

    def test_update_platform(self, db_session: Session):
        """测试更新平台"""
        # 创建测试数据
        platform_data = {
            "name": "原始平台",
            "code": "original",
            "type": "news",
            "description": "原始平台描述",
            "api_url": "https://api.original.com",
            "api_key": "original_api_key",
            "is_active": True
        }
        platform = PlatformService.create(db_session, platform_data)

        # 执行测试
        update_data = {
            "name": "更新后的平台",
            "code": "updated",
            "type": "social_media",
            "description": "更新后的平台描述",
            "api_url": "https://api.updated.com",
            "api_key": "updated_api_key",
            "is_active": False
        }
        updated = PlatformService.update(db_session, platform.id, update_data)

        # 断言结果
        assert updated is not None
        assert updated.name == "更新后的平台"
        assert updated.code == "updated"
        assert updated.type == "social_media"
        assert updated.description == "更新后的平台描述"
        assert updated.api_url == "https://api.updated.com"
        assert updated.api_key == "updated_api_key"
        assert updated.is_active is False

    def test_delete_platform(self, db_session: Session):
        """测试删除平台"""
        # 创建测试数据
        platform_data = {
            "name": "待删除平台",
            "code": "delete",
            "type": "test",
            "description": "待删除的测试平台",
            "api_url": "https://api.delete.com",
            "api_key": "delete_api_key",
            "is_active": True
        }
        platform = PlatformService.create(db_session, platform_data)

        # 执行测试
        deleted = PlatformService.delete(db_session, platform.id)

        # 断言结果
        assert deleted is True

        # 验证平台已删除
        retrieved = PlatformService.get_by_id(db_session, platform.id)
        assert retrieved is None

    def test_get_nonexistent_platform(self, db_session: Session):
        """测试获取不存在的平台"""
        # 执行测试
        platform = PlatformService.get_by_id(db_session, 9999)

        # 断言结果
        assert platform is None

    def test_update_nonexistent_platform(self, db_session: Session):
        """测试更新不存在的平台"""
        # 执行测试
        updated = PlatformService.update(db_session, 9999, {"name": "不存在的平台"})

        # 断言结果
        assert updated is None

    def test_delete_nonexistent_platform(self, db_session: Session):
        """测试删除不存在的平台"""
        # 执行测试
        deleted = PlatformService.delete(db_session, 9999)

        # 断言结果
        assert deleted is False

    def test_pagination(self, db_session: Session):
        """测试分页功能"""
        # 创建多个平台
        for i in range(5):
            PlatformService.create(db_session, {
                "name": f"分页平台{i+1}",
                "code": f"page{i+1}",
                "type": "social_media",
                "description": f"分页测试平台{i+1}",
                "api_url": f"https://api.page{i+1}.com",
                "api_key": f"page_api_key{i+1}",
                "is_active": True
            })

        # 测试第一页
        platforms1, total1 = PlatformService.get_all(db_session, skip=0, limit=2)
        assert len(platforms1) == 2

        # 测试第二页
        platforms2, total2 = PlatformService.get_all(db_session, skip=2, limit=2)
        assert len(platforms2) == 2

        # 总数量应该一致
        assert total1 == total2
