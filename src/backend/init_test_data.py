"""
初始化测试数据
创建示例写作风格和内容主题
"""
import sys
sys.path.insert(0, '.')

from app.db.database import SessionLocal, init_db
from app.models.account import WritingStyle
from app.models.theme import ContentTheme

def init_test_data():
    """初始化测试数据"""
    # 初始化数据库表
    print("正在初始化数据库...")
    init_db()
    print("✓ 数据库初始化完成")

    db = SessionLocal()

    try:
        # 检查是否已有数据
        existing_styles = db.query(WritingStyle).count()
        existing_themes = db.query(ContentTheme).count()

        if existing_styles > 0 or existing_themes > 0:
            print(f"\n数据库中已有数据:")
            print(f"  - 写作风格: {existing_styles} 个")
            print(f"  - 内容主题: {existing_themes} 个")
            return

        # 创建示例写作风格
        print("\n正在创建示例写作风格...")
        writing_styles = [
            WritingStyle(
                name="专业技术风格",
                code="tech_professional",
                description="适合技术博客的专业写作风格，注重技术深度和实践",
                tone="专业",
                persona="技术专家",
                min_words=800,
                max_words=1500,
                emoji_usage="适度",
                forbidden_words=["非常好的", "特别棒的"],
                is_system=True
            ),
            WritingStyle(
                name="轻松教程风格",
                code="tutorial_casual",
                description="适合初学者的轻松教程风格，语言通俗易懂",
                tone="轻松",
                persona="友善的老师",
                min_words=600,
                max_words=1200,
                emoji_usage="频繁",
                forbidden_words=[],
                is_system=True
            ),
            WritingStyle(
                name="幽默博客风格",
                code="blog_humor",
                description="带有幽默感的博客风格，适合轻松话题",
                tone="幽默",
                persona="风趣的博主",
                min_words=500,
                max_words=1000,
                emoji_usage="频繁",
                forbidden_words=["严重", "严峻"],
                is_system=True
            )
        ]

        for style in writing_styles:
            db.add(style)
        db.commit()
        print(f"✓ 创建了 {len(writing_styles)} 个写作风格")

        # 创建示例内容主题
        print("\n正在创建示例内容主题...")
        content_themes = [
            ContentTheme(
                name="技术教程",
                code="tech_tutorial",
                description="技术教程类内容，包括编程、开发工具等",
                type="技术",
                is_system=True
            ),
            ContentTheme(
                name="生活随笔",
                code="life_essay",
                description="生活感悟、随笔杂谈类内容",
                type="生活",
                is_system=True
            ),
            ContentTheme(
                name="产品评测",
                code="product_review",
                description="科技产品评测、使用体验分享",
                type="科技",
                is_system=True
            ),
            ContentTheme(
                name="行业分析",
                code="industry_analysis",
                description="行业趋势分析、商业洞察",
                type="商业",
                is_system=True
            ),
            ContentTheme(
                name="学习笔记",
                code="learning_notes",
                description="学习过程中的笔记和总结",
                type="教育",
                is_system=True
            )
        ]

        for theme in content_themes:
            db.add(theme)
        db.commit()
        print(f"✓ 创建了 {len(content_themes)} 个内容主题")

        # 显示创建的数据
        print("\n" + "=" * 60)
        print("创建的写作风格:")
        all_styles = db.query(WritingStyle).all()
        for style in all_styles:
            print(f"  • {style.name} ({style.code})")

        print("\n创建的内容主题:")
        all_themes = db.query(ContentTheme).all()
        for theme in all_themes:
            print(f"  • {theme.name} ({theme.code}) - {theme.type}")
        print("=" * 60)

        print("\n✓ 测试数据初始化完成")

    except Exception as e:
        print(f"\n✗ 初始化失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_test_data()
