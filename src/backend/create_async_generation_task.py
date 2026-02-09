"""
创建异步内容生成定时任务示例

演示如何使用 CLI 或 API 创建定时任务
"""
import sys
import json

sys.path.insert(0, '/Users/Oychao/Documents/Projects/content-hub/src/backend')

from app.db.database import SessionLocal
from app.models.scheduler import ScheduledTask
from app.utils.custom_logger import log


def create_example_task():
    """创建示例定时任务"""
    print("=" * 70)
    print("创建异步内容生成定时任务")
    print("=" * 70)

    db = SessionLocal()

    try:
        # 示例任务参数
        task_params = {
            'account_ids': [49, 50, 51],  # 账号ID列表
            'count_per_account': 3,  # 每个账号生成 3 篇文章
            'category': '技术',  # 内容板块
            'auto_approve': False,  # 不自动审核
            'priority': 8  # 优先级
        }

        # 创建定时任务
        task = ScheduledTask(
            name='每日技术内容生成',
            description='每天早上 8 点为 3 个账号各生成 3 篇技术类内容',
            task_type='async_content_generation',  # 使用异步内容生成执行器
            cron_expression='0 8 * * *',  # 每天 8:00
            params=task_params,  # 任务参数（会被自动序列化为 JSON）
            is_active=True  # 启用任务
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"\n✓ 定时任务创建成功！")
        print(f"\n任务详情:")
        print(f"  ID: {task.id}")
        print(f"  名称: {task.name}")
        print(f"  描述: {task.description}")
        print(f"  类型: {task.task_type}")
        print(f"  Cron 表达式: {task.cron_expression}")
        print(f"  状态: {'启用' if task.is_active else '禁用'}")
        print(f"\n任务参数:")
        print(f"  账号: {task_params['account_ids']}")
        print(f"  每账号数量: {task_params['count_per_account']}")
        print(f"  板块: {task_params['category']}")
        print(f"  自动审核: {task_params['auto_approve']}")
        print(f"  优先级: {task_params['priority']}")

        print(f"\n提示:")
        print(f"  1. 重启服务后，此任务会自动加载到调度器")
        print(f"  2. 可以通过 API 手动触发任务进行测试")
        print(f"  3. 可以在数据库中查看任务执行历史")

        return task

    except Exception as e:
        log.error(f"创建任务失败: {str(e)}")
        db.rollback()
        return None
    finally:
        db.close()


def create_multiple_examples():
    """创建多个示例任务"""
    print("\n" + "=" * 70)
    print("创建多个示例定时任务")
    print("=" * 70)

    db = SessionLocal()

    try:
        examples = [
            {
                'name': '每日早间内容生成',
                'description': '每天早上 8 点为所有账号生成内容',
                'cron': '0 8 * * *',
                'params': {
                    'account_ids': [49, 50],
                    'count_per_account': 2,
                    'category': '技术',
                    'auto_approve': True,
                    'priority': 5
                }
            },
            {
                'name': '每周内容汇总',
                'description': '每周一早上 9 点生成深度内容',
                'cron': '0 9 * * 1',  # 每周一 9:00
                'params': {
                    'account_ids': [49],
                    'count_per_account': 5,
                    'category': '产品',
                    'auto_approve': False,
                    'priority': 7
                }
            },
            {
                'name': '每两小时内容更新',
                'description': '每两小时生成一篇内容',
                'cron': None,  # 不使用 cron
                'interval': 2,
                'interval_unit': 'hours',
                'params': {
                    'account_ids': [50, 51],
                    'count_per_account': 1,
                    'category': '运营',
                    'auto_approve': True,
                    'priority': 3
                }
            }
        ]

        created_tasks = []

        for idx, example in enumerate(examples, 1):
            print(f"\n创建示例 {idx}: {example['name']}")

            task = ScheduledTask(
                name=example['name'],
                description=example['description'],
                task_type='async_content_generation',
                cron_expression=example.get('cron'),
                interval=example.get('interval'),
                interval_unit=example.get('interval_unit'),
                params=example['params'],
                is_active=True
            )

            db.add(task)
            db.commit()
            db.refresh(task)

            created_tasks.append(task)

            print(f"  ✓ 创建成功 (ID: {task.id})")
            if example.get('cron'):
                print(f"    调度: {example['cron']}")
            else:
                print(f"    调度: 每 {example['interval']} {example['interval_unit']}")

        print(f"\n✓ 成功创建 {len(created_tasks)} 个示例任务")

        return created_tasks

    except Exception as e:
        log.error(f"创建示例任务失败: {str(e)}")
        db.rollback()
        return []
    finally:
        db.close()


def show_usage_examples():
    """显示使用示例"""
    print("\n" + "=" * 70)
    print("使用示例")
    print("=" * 70)

    print("\n1. 通过 API 创建定时任务:")
    print("""
POST /api/v1/scheduler/tasks
Content-Type: application/json

{
  "name": "每日内容生成",
  "description": "每天生成内容",
  "task_type": "async_content_generation",
  "cron_expression": "0 8 * * *",
  "params": {
    "account_ids": [49, 50, 51],
    "count_per_account": 3,
    "category": "技术",
    "auto_approve": false,
    "priority": 5
  },
  "is_active": true
}
    """)

    print("\n2. 通过 API 手动触发任务:")
    print("""
POST /api/v1/scheduler/tasks/{task_id}/trigger
    """)

    print("\n3. 查看任务执行历史:")
    print("""
GET /api/v1/scheduler/executions
    """)

    print("\n4. 查看调度器状态:")
    print("""
GET /api/v1/scheduler/status
    """)

    print("\n5. 通过 CLI 创建任务（如果已实现）:")
    print("""
scheduler create \\
  --name "每日内容生成" \\
  --type async_content_generation \\
  --cron "0 8 * * *" \\
  --params '{"account_ids": [49, 50], "count_per_account": 3}'
    """)

    print("\n6. Cron 表达式示例:")
    cron_examples = [
        ("0 8 * * *", "每天 8:00"),
        ("0 */2 * * *", "每 2 小时"),
        ("0 0 * * 1", "每周一 0:00"),
        ("0 8 * * 1-5", "周一到周五 8:00"),
        ("0 8,12,18 * * *", "每天 8:00, 12:00, 18:00"),
        ("0 0 1 * *", "每月 1 号 0:00"),
    ]

    print(f"\n  {'表达式':<20} {'说明'}")
    print(f"  {'-'*20} {'-'*40}")
    for expr, desc in cron_examples:
        print(f"  {expr:<20} {desc}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='创建异步内容生成定时任务')
    parser.add_argument('--multiple', action='store_true', help='创建多个示例任务')
    parser.add_argument('--usage', action='store_true', help='显示使用示例')
    parser.add_argument('--no-create', action='store_true', help='不创建任务，仅显示使用示例')

    args = parser.parse_args()

    if args.usage or args.no_create:
        show_usage_examples()
    else:
        if args.multiple:
            create_multiple_examples()
        else:
            create_example_task()

        # 总是显示使用示例
        show_usage_examples()
