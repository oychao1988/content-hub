#!/usr/bin/env python3
"""
为"车界显眼包"账号创建每日自动发布工作流任务
"""
import sys
import json
from pathlib import Path

# 添加项目路径到 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.scheduler import ScheduledTask


def create_chejie_daily_task():
    """创建车界显眼包每日7点自动发布任务"""

    # 获取数据库会话
    db = next(get_db())

    try:
        # 检查任务是否已存在
        existing_task = db.query(ScheduledTask).filter(
            ScheduledTask.name == "车界显眼包-每日7点自动发布"
        ).first()

        if existing_task:
            print(f"⚠️  任务已存在: ID={existing_task.id}, 状态={'启用' if existing_task.is_active else '禁用'}")
            print(f"   Cron: {existing_task.cron_expression}")
            print(f"   描述: {existing_task.description}")
            return

        # 定义工作流参数
        workflow_params = {
            "steps": [
                {
                    "type": "content_generation",
                    "params": {
                        "account_id": 49,
                        "topic": "新能源汽车行业最新动态分析",
                        "target_audience": "汽车爱好者和潜在购车者",
                        "tone": "专业但通俗易懂"
                    }
                },
                {
                    "type": "approve",
                    "params": {
                        "content_id": "${content_id}"
                    }
                },
                {
                    "type": "add_to_pool",
                    "params": {
                        "content_id": "${content_id}",
                        "priority": 5,
                        "auto_approve": True
                    }
                }
            ]
        }

        # 创建任务
        task = ScheduledTask(
            name="车界显眼包-每日7点自动发布",
            task_type="workflow",
            cron_expression="0 7 * * *",
            is_active=True,  # 使用 is_active 而不是 enabled
            description="每天早上7点自动生成内容、审核、加入发布池",
            params=workflow_params  # 直接传递字典，SQLAlchemy 会自动序列化为 JSON
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        print("✅ 任务创建成功！")
        print(f"\n任务信息:")
        print(f"  ID: {task.id}")
        print(f"  名称: {task.name}")
        print(f"  类型: {task.task_type}")
        print(f"  Cron: {task.cron_expression}")
        print(f"  状态: {'启用' if task.is_active else '禁用'}")
        print(f"  描述: {task.description}")
        print(f"\n工作流步骤:")
        for i, step in enumerate(workflow_params["steps"], 1):
            print(f"  {i}. {step['type']}")
            print(f"     参数: {json.dumps(step['params'], ensure_ascii=False, indent=6)}")

        print(f"\n下次执行时间: 每天 07:00:00")
        print(f"\n验证命令:")
        print(f"  PYTHONPATH=. python -m cli.main scheduler list --type workflow")
        print(f"  PYTHONPATH=. python -m cli.main scheduler info {task.id}")

    except Exception as e:
        db.rollback()
        print(f"❌ 创建任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 70)
    print('为"车界显眼包"账号创建每日自动发布工作流任务')
    print("=" * 70)
    print()

    create_chejie_daily_task()
