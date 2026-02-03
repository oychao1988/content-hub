"""
阶段 5 CLI 模块测试脚本

测试平台管理、客户管理、配置管理、审计日志、仪表盘和系统管理模块。
"""

import subprocess
import sys
from typing import Dict, List, Tuple

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_section(title: str):
    """打印测试区块标题"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BLUE}{title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg: str):
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.RESET}")

def run_command(cmd: List[str]) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "命令超时"
    except Exception as e:
        return False, str(e)

def test_module_help():
    """测试模块帮助信息"""
    print_section("1. 测试模块帮助信息")

    modules = [
        "platform", "customer", "config", "audit", "dashboard", "system"
    ]

    results = []

    for module in modules:
        success, _ = run_command([
            sys.executable, "-m", "cli.main", module, "--help"
        ])
        status = print_success(f"{module} 模块帮助") if success else print_error(f"{module} 模块帮助")
        results.append(("help", module, success))

    return results

def test_platform_commands():
    """测试平台管理命令"""
    print_section("2. 测试平台管理命令")

    commands = [
        (["platform", "list"], "列出平台"),
        (["platform", "info", "1"], "查看平台详情"),
    ]

    results = []

    for cmd, desc in commands:
        full_cmd = [sys.executable, "-m", "cli.main"] + cmd
        success, _ = run_command(full_cmd)
        status = print_success(desc) if success else print_error(desc)
        results.append(("platform", desc, success))

    return results

def test_customer_commands():
    """测试客户管理命令"""
    print_section("3. 测试客户管理命令")

    commands = [
        (["customer", "list"], "列出客户"),
        (["customer", "info", "1"], "查看客户详情"),
        (["customer", "stats", "1"], "查看客户统计"),
        (["customer", "accounts", "1"], "查看客户账号"),
    ]

    results = []

    for cmd, desc in commands:
        full_cmd = [sys.executable, "-m", "cli.main"] + cmd
        success, _ = run_command(full_cmd)
        status = print_success(desc) if success else print_error(desc)
        results.append(("customer", desc, success))

    return results

def test_config_commands():
    """测试配置管理命令"""
    print_section("4. 测试配置管理命令")

    commands = [
        (["config", "writing-style", "list"], "列出写作风格"),
        (["config", "content-theme", "list"], "列出内容主题"),
        (["config", "system-params", "list"], "列出系统参数"),
        (["config", "platform-config", "list"], "列出平台配置"),
    ]

    results = []

    for cmd, desc in commands:
        full_cmd = [sys.executable, "-m", "cli.main"] + cmd
        success, _ = run_command(full_cmd)
        status = print_success(desc) if success else print_error(desc)
        results.append(("config", desc, success))

    return results

def test_audit_commands():
    """测试审计日志命令"""
    print_section("5. 测试审计日志命令")

    commands = [
        (["audit", "logs", "--page-size", "5"], "查询审计日志"),
        (["audit", "statistics"], "查看审计统计"),
    ]

    results = []

    for cmd, desc in commands:
        full_cmd = [sys.executable, "-m", "cli.main"] + cmd
        success, _ = run_command(full_cmd)
        status = print_success(desc) if success else print_error(desc)
        results.append(("audit", desc, success))

    return results

def test_dashboard_commands():
    """测试仪表盘命令"""
    print_section("6. 测试仪表盘命令")

    commands = [
        (["dashboard", "stats"], "仪表盘统计"),
        (["dashboard", "activities", "--limit", "10"], "最近活动"),
        (["dashboard", "content-trend", "--days", "7"], "内容趋势"),
        (["dashboard", "publish-stats"], "发布统计"),
        (["dashboard", "user-stats"], "用户统计"),
        (["dashboard", "customer-stats"], "客户统计"),
    ]

    results = []

    for cmd, desc in commands:
        full_cmd = [sys.executable, "-m", "cli.main"] + cmd
        success, _ = run_command(full_cmd)
        status = print_success(desc) if success else print_error(desc)
        results.append(("dashboard", desc, success))

    return results

def test_system_commands():
    """测试系统管理命令"""
    print_section("7. 测试系统管理命令")

    commands = [
        (["system", "health"], "健康检查"),
        (["system", "info"], "系统信息"),
        (["system", "version"], "版本信息"),
        (["system", "metrics"], "系统指标"),
        (["system", "cache-stats"], "缓存统计"),
        (["system", "logs", "--lines", "10"], "系统日志"),
    ]

    results = []

    for cmd, desc in commands:
        full_cmd = [sys.executable, "-m", "cli.main"] + cmd
        success, _ = run_command(full_cmd)
        status = print_success(desc) if success else print_error(desc)
        results.append(("system", desc, success))

    return results

def generate_summary(all_results: List[Tuple[str, str, bool]]):
    """生成测试总结"""
    print_section("测试总结")

    total = len(all_results)
    passed = sum(1 for _, _, success in all_results if success)
    failed = total - passed

    print(f"\n总测试数: {total}")
    print_success(f"通过: {passed}")
    print_error(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")

    # 按模块统计
    module_stats = {}
    for module, _, success in all_results:
        if module not in module_stats:
            module_stats[module] = {"total": 0, "passed": 0}
        module_stats[module]["total"] += 1
        if success:
            module_stats[module]["passed"] += 1

    print("\n模块统计:")
    for module, stats in module_stats.items():
        rate = stats["passed"] / stats["total"] * 100
        print(f"  {module}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")

    # 列出失败的测试
    failed_tests = [(module, desc) for module, desc, success in all_results if not success]
    if failed_tests:
        print(f"\n失败的测试:")
        for module, desc in failed_tests:
            print_error(f"  [{module}] {desc}")

    return passed == total

def main():
    """主测试函数"""
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BLUE}阶段 5 CLI 模块测试{Colors.RESET}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.RESET}")

    all_results = []

    # 运行所有测试
    all_results.extend(test_module_help())
    all_results.extend(test_platform_commands())
    all_results.extend(test_customer_commands())
    all_results.extend(test_config_commands())
    all_results.extend(test_audit_commands())
    all_results.extend(test_dashboard_commands())
    all_results.extend(test_system_commands())

    # 生成总结
    all_passed = generate_summary(all_results)

    if all_passed:
        print(f"\n{Colors.GREEN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.GREEN}所有测试通过！{Colors.RESET}")
        print(f"{Colors.GREEN}{'=' * 60}{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.RED}部分测试失败，请查看详细信息{Colors.RESET}")
        print(f"{Colors.RED}{'=' * 60}{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
