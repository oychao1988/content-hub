"""
列出 Content-Hub 所有可用的 CLI 命令
"""
import os
import sys
import inspect
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '.')

def list_cli_modules():
    """列出所有 CLI 模块"""
    cli_dir = Path("cli/modules")
    modules = []
    
    if cli_dir.exists():
        for file in cli_dir.glob("*.py"):
            if file.name != "__init__.py":
                modules.append(file.stem)
    
    return sorted(modules)

def get_module_commands(module_name):
    """获取模块中的命令"""
    try:
        module = __import__(f"cli.modules.{module_name}", fromlist=["app"])
        app = getattr(module, "app", None)
        
        if app and hasattr(app, "registered_commands"):
            commands = []
            for cmd in app.registered_commands:
                if hasattr(cmd, "name"):
                    commands.append(cmd.name)
            return commands
    except Exception as e:
        return []
    
    return []

def main():
    """主函数"""
    print("📋 Content-Hub CLI 命令列表")
    print("=" * 60)
    
    modules = list_cli_modules()
    
    if not modules:
        print("❌ 没有找到 CLI 模块")
        return
    
    print(f"找到 {len(modules)} 个 CLI 模块:")
    print()
    
    for module in modules:
        print(f"🔹 {module}")
        
        # 尝试读取模块文件来获取命令信息
        module_path = f"cli/modules/{module}.py"
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 查找 @app.command 装饰器
                import re
                commands = re.findall(r'@app\.command\(["\']([^"\']+)["\']\)', content)
                
                if commands:
                    for cmd in commands:
                        print(f"   └── {cmd}")
                else:
                    # 查找没有参数的 @app.command()
                    commands = re.findall(r'@app\.command\(\)\s*\n\s*def\s+(\w+)', content)
                    if commands:
                        for cmd in commands:
                            print(f"   └── {cmd}")
                    else:
                        print("   └── (需要查看具体实现)")
        except Exception as e:
            print(f"   └── 读取失败: {e}")
        
        print()
    
    print("=" * 60)
    print("📖 使用示例:")
    print("  python -m cli accounts list          # 列出所有账号")
    print("  python -m cli accounts info <id>     # 查看账号详情")
    print("  python -m cli platforms list         # 列出所有平台")
    print("  python -m cli customers list         # 列出所有客户")
    print("  python -m cli db status              # 查看数据库状态")
    print()
    print("💡 提示: 使用 'python -m cli <模块> --help' 查看具体帮助")

if __name__ == "__main__":
    main()