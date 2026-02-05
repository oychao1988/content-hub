"""
ContentHub CLI - 主应用入口

使用 typer 框架实现命令行界面。
"""

import typer
from cli.modules import (
    db, users, accounts, content, scheduler, publisher, publish_pool,
    platform, customer, config, audit, dashboard, system
)

# 创建主应用 - 禁用 rich 输出以避免兼容性问题
app = typer.Typer(
    name="contenthub",
    help="ContentHub 内容运营管理系统 CLI",
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

# 注册子模块
app.add_typer(db.app, name="db", help="数据库管理")
app.add_typer(users.app, name="users", help="用户管理")
app.add_typer(accounts.app, name="accounts", help="账号管理")
app.add_typer(content.app, name="content", help="内容管理")
app.add_typer(scheduler.app, name="scheduler", help="定时任务管理")
app.add_typer(publisher.app, name="publisher", help="发布管理")
app.add_typer(publish_pool.app, name="publish-pool", help="发布池管理")
app.add_typer(platform.app, name="platform", help="平台管理")
app.add_typer(customer.app, name="customer", help="客户管理")
app.add_typer(config.app, name="config", help="配置管理")
app.add_typer(audit.app, name="audit", help="审计日志")
app.add_typer(dashboard.app, name="dashboard", help="仪表盘")
app.add_typer(system.app, name="system", help="系统管理")


@app.callback()
def main(
    ctx: typer.Context,
    format: str = typer.Option("table", "--format", help="输出格式 (table/json/csv)"),
    debug: bool = typer.Option(False, "--debug", help="调试模式"),
    quiet: bool = typer.Option(False, "--quiet", help="静默模式（仅输出错误）"),
    user: str = typer.Option("cli-user", "--user", help="操作用户（用于审计）"),
):
    """
    ContentHub 内容运营管理系统 CLI

    使用 'contenthub <module> --help' 查看模块帮助
    使用 'contenthub <module> <command> --help' 查看命令帮助
    """
    # 将全局选项存储到 context 中，供子模块使用
    ctx.ensure_object(dict)
    ctx.obj.update({
        "format": format,
        "debug": debug,
        "quiet": quiet,
        "user": user,
    })


@app.command()
def version():
    """显示版本信息"""
    typer.echo("ContentHub CLI v1.0.0")


if __name__ == "__main__":
    app()
