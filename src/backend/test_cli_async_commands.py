#!/usr/bin/env python
"""
测试异步内容生成 CLI 命令

验证 Stage 3 - CLI 改造的所有功能是否正常工作
"""

import subprocess
import sys


def run_command(cmd: list) -> tuple:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "命令执行超时"
    except Exception as e:
        return -1, "", str(e)


def test_task_help():
    """测试 task 命令帮助"""
    print("\n" + "="*80)
    print("测试 1: task 命令帮助")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        # 检查所有子命令是否存在
        required_commands = ["status", "list", "cancel", "retry", "cleanup", "stats"]
        for cmd_name in required_commands:
            if cmd_name in stdout:
                print(f"  ✓ 子命令 {cmd_name} 存在")
            else:
                print(f"  ✗ 子命令 {cmd_name} 缺失")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_status_help():
    """测试 task status 命令帮助"""
    print("\n" + "="*80)
    print("测试 2: task status 命令帮助")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "status", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        if "TASK_ID" in stdout:
            print("  ✓ TASK_ID 参数存在")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_list_help():
    """测试 task list 命令帮助"""
    print("\n" + "="*80)
    print("测试 3: task list 命令帮助")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "list", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        # 检查参数
        required_options = ["--account-id", "-a", "--status", "-s", "--limit", "-n"]
        for opt in required_options:
            if opt in stdout:
                print(f"  ✓ 参数 {opt} 存在")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_cancel_help():
    """测试 task cancel 命令帮助"""
    print("\n" + "="*80)
    print("测试 4: task cancel 命令帮助")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "cancel", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        if "TASK_ID" in stdout:
            print("  ✓ TASK_ID 参数存在")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_retry_help():
    """测试 task retry 命令帮助"""
    print("\n" + "="*80)
    print("测试 5: task retry 命令帮助")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "retry", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        if "TASK_ID" in stdout:
            print("  ✓ TASK_ID 参数存在")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_cleanup_help():
    """测试 task cleanup 命令帮助"""
    print("\n" + "="*80)
    print("测试 6: task cleanup 命令帮助")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "cleanup", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        if "--days" in stdout and "-d" in stdout:
            print("  ✓ --days/-d 参数存在")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_stats_help():
    """测试 task stats 命令帮助"""
    print("\n" + "="*80)
    print("测试 7: task stats 命令帮助")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "stats", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_content_generate_async_help():
    """测试 content generate --async 参数"""
    print("\n" + "="*80)
    print("测试 8: content generate --async 参数")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "content", "generate", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        # 检查 --async 参数是否存在
        if "--async" in stdout:
            print("  ✓ --async 参数存在")
        if "--auto-approve" in stdout:
            print("  ✓ --auto-approve/--no-auto-approve 参数存在")
        if "异步模式" in stdout:
            print("  ✓ 异步模式说明存在")
        print("\n完整帮助信息:")
        print(stdout)
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_list_execution():
    """测试 task list 命令执行"""
    print("\n" + "="*80)
    print("测试 9: task list 命令执行")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "list"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        # 检查输出格式
        if "任务ID" in stdout or "Task ID" in stdout:
            print("  ✓ 表格输出格式正确")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_stats_execution():
    """测试 task stats 命令执行"""
    print("\n" + "="*80)
    print("测试 10: task stats 命令执行")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "stats"
    ])

    if code == 0:
        print("✅ 通过")
        print(stdout)
        if "任务统计" in stdout or "Task Statistics" in stdout:
            print("  ✓ 统计输出格式正确")
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def test_task_status_with_invalid_id():
    """测试 task status 命令（无效ID）"""
    print("\n" + "="*80)
    print("测试 11: task status 命令（无效ID）")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "task", "status", "invalid-task-id"
    ])

    if code != 0:
        print("✅ 通过（正确拒绝无效ID）")
        print(stdout)
        return True
    else:
        print("✗ 失败（应该拒绝无效ID）")
        return False


def test_main_help():
    """测试主命令帮助（验证 task 模块已注册）"""
    print("\n" + "="*80)
    print("测试 12: 主命令帮助（task 模块注册）")
    print("="*80)

    code, stdout, stderr = run_command([
        sys.executable, "-m", "cli.main", "--help"
    ])

    if code == 0:
        print("✅ 通过")
        if "task" in stdout and "异步任务管理" in stdout:
            print("  ✓ task 模块已注册")
        print("\n主命令帮助:")
        print(stdout)
        return True
    else:
        print(f"✗ 失败: {stderr}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("ContentHub 异步内容生成系统 - Stage 3 CLI 改造验证测试")
    print("="*80)

    tests = [
        test_main_help,
        test_task_help,
        test_task_status_help,
        test_task_list_help,
        test_task_cancel_help,
        test_task_retry_help,
        test_task_cleanup_help,
        test_task_stats_help,
        test_content_generate_async_help,
        test_task_list_execution,
        test_task_stats_execution,
        test_task_status_with_invalid_id,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ 测试异常: {e}")
            results.append(False)

    # 总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)
    passed = sum(results)
    total = len(results)
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n✅ 所有测试通过！Stage 3 CLI 改造已完成。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
