"""
定时任务管理服务单元测试
"""
import pytest
from sqlalchemy.orm import Session

from app.modules.scheduler.services import scheduler_manager_service
from app.models.scheduler import ScheduledTask


@pytest.mark.unit
def test_create_task(db_session: Session):
    """测试创建定时任务"""
    # 创建定时任务
    task_data = {
        "name": "测试定时任务",
        "description": "这是一个测试定时任务",
        "task_type": "content_generation",
        "cron_expression": "0 0 * * *",
        "is_active": True
    }

    task = scheduler_manager_service.create_task(db_session, task_data)

    # 验证任务创建
    assert task is not None
    assert task.id is not None
    assert task.name == "测试定时任务"
    assert task.description == "这是一个测试定时任务"
    assert task.task_type == "content_generation"
    assert task.cron_expression == "0 0 * * *"
    assert task.is_active is True

    print(f"✓ 定时任务创建测试通过 (ID: {task.id})")


@pytest.mark.unit
def test_get_task_detail(db_session: Session):
    """测试获取定时任务详情"""
    # 创建测试任务
    task = ScheduledTask(
        name="详情测试任务",
        description="这是一个详情测试任务",
        task_type="publishing",
        cron_expression="0 12 * * *",
        is_active=True
    )
    db_session.add(task)
    db_session.commit()

    # 获取任务详情
    retrieved = scheduler_manager_service.get_task_detail(db_session, task.id)

    # 验证任务详情
    assert retrieved is not None
    assert retrieved.id == task.id
    assert retrieved.name == "详情测试任务"
    assert retrieved.task_type == "publishing"

    print(f"✓ 定时任务详情查询测试通过 (ID: {task.id})")


@pytest.mark.unit
def test_get_task_list(db_session: Session):
    """测试获取定时任务列表"""
    # 创建多个测试任务
    tasks_data = [
        {
            "name": f"测试任务{i}",
            "description": f"这是第{i}个测试任务",
            "task_type": "content_generation" if i % 2 == 0 else "publishing",
            "cron_expression": "0 0 * * *",
            "is_active": True
        }
        for i in range(3)
    ]

    for data in tasks_data:
        task = ScheduledTask(**data)
        db_session.add(task)

    db_session.commit()

    # 获取任务列表
    task_list = scheduler_manager_service.get_task_list(db_session)

    # 验证任务列表
    assert len(task_list) >= 3

    # 检查是否包含我们创建的任务
    created_names = [f"测试任务{i}" for i in range(3)]
    for task in task_list:
        if task.name in created_names:
            created_names.remove(task.name)

    assert len(created_names) == 0

    print(f"✓ 定时任务列表查询测试通过 (共 {len(task_list)} 个任务)")


@pytest.mark.unit
def test_update_task(db_session: Session):
    """测试更新定时任务"""
    # 创建测试任务
    task = ScheduledTask(
        name="初始任务名称",
        description="这是一个初始任务",
        task_type="content_generation",
        cron_expression="0 0 * * *",
        is_active=True
    )
    db_session.add(task)
    db_session.commit()

    # 更新任务信息
    update_data = {
        "name": "更新后的任务名称",
        "description": "这是一个更新后的任务",
        "task_type": "publishing",
        "cron_expression": "0 12 * * *",
        "is_active": False
    }

    updated_task = scheduler_manager_service.update_task(db_session, task.id, update_data)

    # 验证更新
    assert updated_task is not None
    assert updated_task.name == "更新后的任务名称"
    assert updated_task.task_type == "publishing"
    assert updated_task.cron_expression == "0 12 * * *"
    assert updated_task.is_active is False

    print(f"✓ 定时任务更新测试通过 (ID: {task.id})")


@pytest.mark.unit
def test_delete_task(db_session: Session):
    """测试删除定时任务"""
    # 创建测试任务
    task = ScheduledTask(
        name="待删除任务",
        description="这是一个待删除任务",
        task_type="content_generation",
        cron_expression="0 0 * * *",
        is_active=True
    )
    db_session.add(task)
    db_session.commit()

    # 记录任务ID
    task_id = task.id

    # 删除任务
    result = scheduler_manager_service.delete_task(db_session, task_id)

    # 验证删除
    assert result is True

    # 验证任务已不存在
    deleted_task = scheduler_manager_service.get_task_detail(db_session, task_id)
    assert deleted_task is None

    print("✓ 定时任务删除测试通过")


@pytest.mark.unit
def test_scheduler_service_operations(db_session: Session):
    """综合测试定时任务管理服务操作"""
    # 创建任务
    task_data = {
        "name": "综合测试任务",
        "description": "这是一个综合测试任务",
        "task_type": "content_generation",
        "cron_expression": "0 0 * * *",
        "is_active": True
    }

    task = scheduler_manager_service.create_task(db_session, task_data)
    assert task is not None

    # 查询任务列表
    task_list = scheduler_manager_service.get_task_list(db_session)
    assert len(task_list) >= 1

    # 更新任务
    update_data = {"description": "这是一个已更新的综合测试任务"}
    updated_task = scheduler_manager_service.update_task(db_session, task.id, update_data)
    assert updated_task is not None

    print("✓ 定时任务管理服务综合测试通过")
