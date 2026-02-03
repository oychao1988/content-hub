#!/usr/bin/env python3
"""
ContentHub CLI 简单测试脚本

快速测试核心功能
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_test(name: str):
    """打印测试名称"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}测试: {name}{Colors.END}")
    print("-" * 60)


def print_success(message: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """打印错误消息"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def run_command(args: list) -> bool:
    """运行 CLI 命令"""
    cmd = [sys.executable, "-m", "cli.main"] + args
    print_info(f"执行: {' '.join(['contenthub'] + args)}")

    result = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True
    )

    # 只显示关键输出
    if "✓" in result.stdout or "✗" in result.stdout or "成功" in result.stdout or "失败" in result.stdout:
        for line in result.stdout.split('\n'):
            if any(marker in line for marker in ['✓', '✗', '成功', '失败', '错误', 'ID:', '名称:']):
                print(f"  {line}")

    return result.returncode == 0


def print_info(message: str):
    """打印信息"""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


def main():
    """主测试函数"""
    print(f"\n{Colors.BOLD}ContentHub CLI 快速测试{Colors.END}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = []

    # 测试 1: 版本信息
    print_test("版本信息")
    if run_command(["version"]):
        print_success("版本命令正常")
        results.append(True)
    else:
        print_error("版本命令失败")
        results.append(False)

    # 测试 2: 数据库统计
    print_test("数据库统计")
    if run_command(["db", "stats"]):
        print_success("数据库统计正常")
        results.append(True)
    else:
        print_error("数据库统计失败")
        results.append(False)

    # 测试 3: 列出用户
    print_test("用户列表")
    if run_command(["users", "list"]):
        print_success("用户列表正常")
        results.append(True)
    else:
        print_error("用户列表失败")
        results.append(False)

    # 测试 4: 列出平台
    print_test("平台列表")
    if run_command(["platform", "list"]):
        print_success("平台列表正常")
        results.append(True)
    else:
        print_error("平台列表失败")
        results.append(False)

    # 测试 5: 列出客户
    print_test("客户列表")
    if run_command(["customer", "list"]):
        print_success("客户列表正常")
        results.append(True)
    else:
        print_error("客户列表失败")
        results.append(False)

    # 测试 6: 列出账号
    print_test("账号列表")
    if run_command(["accounts", "list"]):
        print_success("账号列表正常")
        results.append(True)
    else:
        print_error("账号列表失败")
        results.append(False)

    # 测试 7: 系统健康
    print_test("系统健康检查")
    if run_command(["system", "health"]):
        print_success("健康检查正常")
        results.append(True)
    else:
        print_error("健康检查失败")
        results.append(False)

    # 测试 8: 配置列表
    print_test("配置列表")
    if run_command(["config", "list"]):
        print_success("配置列表正常")
        results.append(True)
    else:
        print_error("配置列表失败")
        results.append(False)

    # 测试 9: 审计日志
    print_test("审计日志")
    if run_command(["audit", "list", "--limit", "5"]):
        print_success("审计日志正常")
        results.append(True)
    else:
        print_error("审计日志失败")
        results.append(False)

    # 测试 10: 仪表盘统计
    print_test("仪表盘统计")
    if run_command(["dashboard", "stats"]):
        print_success("仪表盘统计正常")
        results.append(True)
    else:
        print_error("仪表盘统计失败")
        results.append(False)

    # 打印总结
    print("\n" + "=" * 60)
    print(f"{Colors.BOLD}测试总结{Colors.END}")
    print("=" * 60)

    passed = sum(results)
    total = len(results)
    failed = total - passed

    print(f"\n总测试数: {total}")
    print(f"{Colors.GREEN}通过: {passed}{Colors.END}")
    print(f"{Colors.RED}失败: {failed}{Colors.END}")
    print(f"通过率: {passed / total * 100:.1f}%")

    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ 所有测试通过！{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ 部分测试失败{Colors.END}\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
