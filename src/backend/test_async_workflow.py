#!/usr/bin/env python
"""
异步内容生成工作流演示

演示完整的异步内容生成工作流程：
1. 提交异步任务
2. 查询任务状态
3. 列出所有任务
4. 查看统计信息
"""

import subprocess
import sys
import time


def run_command(cmd: list, description: str) -> bool:
    """运行命令并显示结果"""
    print(f"\n{'='*80}")
    print(f"📝 {description}")
    print(f"{'='*80}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'-'*80}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("错误输出:", result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ 命令执行超时")
        return False
    except Exception as e:
        print(f"❌ 命令执行异常: {e}")
        return False


def main():
    """主工作流"""
    print("\n" + "="*80)
    print("ContentHub 异步内容生成工作流演示")
    print("="*80)

    # 步骤 1: 查看当前任务统计
    success = run_command(
        [sys.executable, "-m", "cli.main", "task", "stats"],
        "步骤 1: 查看当前任务统计"
    )

    if not success:
        print("⚠️  无法获取任务统计")

    # 步骤 2: 列出所有任务
    success = run_command(
        [sys.executable, "-m", "cli.main", "task", "list", "-n", "5"],
        "步骤 2: 列出最近 5 个任务"
    )

    if not success:
        print("⚠️  无法列出任务")

    # 步骤 3: 查询任务状态（使用已存在的任务）
    # 先获取一个任务 ID
    try:
        from app.db.sql_db import get_session_local
        from app.models import ContentGenerationTask

        db = get_session_local()()
        task = db.query(ContentGenerationTask).first()

        if task:
            task_id = task.task_id
            print(f"\n✅ 找到任务: {task_id}")

            success = run_command(
                [sys.executable, "-m", "cli.main", "task", "status", task_id],
                f"步骤 3: 查询任务状态 ({task_id})"
            )

            if not success:
                print("⚠️  无法查询任务状态")
        else:
            print("\n⚠️  数据库中没有任务记录")

    except Exception as e:
        print(f"\n⚠️  无法获取任务 ID: {e}")

    # 步骤 4: 列出失败的任务
    success = run_command(
        [sys.executable, "-m", "cli.main", "task", "list", "-s", "failed"],
        "步骤 4: 列出失败的任务"
    )

    if not success:
        print("⚠️  无法列出失败的任务")

    # 步骤 5: 列出待处理的任务
    success = run_command(
        [sys.executable, "-m", "cli.main", "task", "list", "-s", "pending"],
        "步骤 5: 列出待处理的任务"
    )

    if not success:
        print("⚠️  无法列出待处理的任务")

    # 步骤 6: 显示最终统计
    success = run_command(
        [sys.executable, "-m", "cli.main", "task", "stats"],
        "步骤 6: 显示最终统计"
    )

    if not success:
        print("⚠️  无法获取最终统计")

    # 总结
    print("\n" + "="*80)
    print("✅ 工作流演示完成")
    print("="*80)
    print("\n📋 常用命令总结:")
    print("  • 提交异步任务: contenthub content generate -a <账号ID> -t <选题> --async")
    print("  • 查询任务状态: contenthub task status <任务ID>")
    print("  • 列出所有任务: contenthub task list")
    print("  • 列出失败任务: contenthub task list -s failed")
    print("  • 取消任务:     contenthub task cancel <任务ID>")
    print("  • 重试任务:     contenthub task retry <任务ID>")
    print("  • 查看统计:     contenthub task stats")
    print("  • 清理旧任务:   contenthub task cleanup --days 7")
    print("\n📚 获取帮助:")
    print("  • contenthub task --help")
    print("  • contenthub task <命令> --help")
    print("\n📖 文档:")
    print("  • 快速参考: /docs/guides/async-content-cli-quick-reference.md")
    print("  • 实施总结: /docs/development/STAGE3-CLI-IMPLEMENTATION-SUMMARY.md")

    return 0


if __name__ == "__main__":
    sys.exit(main())
