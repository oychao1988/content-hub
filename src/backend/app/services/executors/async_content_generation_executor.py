"""
异步内容生成任务执行器

负责批量提交异步内容生成任务到调度系统
"""
import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from app.services.async_content_generation_service import AsyncContentGenerationService
from app.models.account import Account
from app.utils.custom_logger import log


class AsyncContentGenerationExecutor(TaskExecutor):
    """
    异步内容生成任务执行器

    功能：
    1. 从任务配置中读取参数（账号ID列表、生成数量等）
    2. 为每个账号生成选题列表
    3. 批量提交异步生成任务
    4. 返回提交结果统计
    """

    @property
    def executor_type(self) -> str:
        """返回执行器类型标识"""
        return "async_content_generation"

    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        """
        验证任务参数

        Args:
            task_params: 任务参数字典

        Returns:
            bool: 参数是否有效

        必需参数:
            - account_ids: 账号ID列表（必需）
            - count_per_account: 每个账号生成的文章数量（必需）

        可选参数:
            - category: 内容板块（可选）
            - auto_approve: 是否自动审核通过（可选，默认：True）
            - priority: 任务优先级（可选，默认：5）
            - topics: 自定义选题列表（可选，如果不提供则自动生成）
        """
        # 检查必需的参数
        if "account_ids" not in task_params:
            log.error("Missing required parameter: account_ids")
            return False

        account_ids = task_params.get("account_ids")
        if not isinstance(account_ids, list) or len(account_ids) == 0:
            log.error(f"Invalid account_ids: must be a non-empty list")
            return False

        # 验证账号ID都是正整数
        for account_id in account_ids:
            if not isinstance(account_id, int) or account_id <= 0:
                log.error(f"Invalid account_id in list: {account_id}")
                return False

        # 检查生成数量
        count_per_account = task_params.get("count_per_account", 1)
        if not isinstance(count_per_account, int) or count_per_account <= 0:
            log.error(f"Invalid count_per_account: {count_per_account}")
            return False

        # 检查可选参数
        auto_approve = task_params.get("auto_approve", True)
        if not isinstance(auto_approve, bool):
            log.error(f"Invalid auto_approve: must be boolean")
            return False

        priority = task_params.get("priority", 5)
        if not isinstance(priority, int) or priority < 1 or priority > 10:
            log.error(f"Invalid priority: {priority}, must be between 1 and 10")
            return False

        log.info(
            f"Task params validation passed: account_ids={account_ids}, "
            f"count_per_account={count_per_account}, priority={priority}"
        )
        return True

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行批量异步内容生成任务

        Args:
            task_id: 任务ID
            task_params: 任务参数字典
            db: 数据库会话

        Returns:
            TaskExecutionResult: 任务执行结果

        执行流程:
            1. 提取任务参数
            2. 为每个账号生成选题
            3. 批量提交异步任务
            4. 统计提交结果
        """
        start_time = time.time()
        log.info(f"Executing async content generation task {task_id}")

        try:
            # 1. 提取任务参数
            account_ids = task_params.get("account_ids", [])
            count_per_account = task_params.get("count_per_account", 1)
            category = task_params.get("category")
            auto_approve = task_params.get("auto_approve", True)
            priority = task_params.get("priority", 5)
            custom_topics = task_params.get("topics")  # 可选的自定义选题列表

            log.info(
                f"Task params: account_ids={account_ids}, "
                f"count_per_account={count_per_account}, category={category}"
            )

            # 2. 创建异步内容生成服务
            async_service = AsyncContentGenerationService(db)

            # 3. 统计结果
            results = {
                "success": True,
                "total_submitted": 0,
                "total_failed": 0,
                "tasks": [],
                "errors": [],
                "account_stats": {}
            }

            # 4. 为每个账号生成任务
            for account_id in account_ids:
                try:
                    # 获取账号配置
                    account = db.query(Account).filter_by(id=account_id).first()
                    if not account:
                        error_msg = f"账号 {account_id} 不存在"
                        results['errors'].append(error_msg)
                        results['total_failed'] += count_per_account
                        log.error(error_msg)
                        continue

                    log.info(f"Processing account {account_id}: {account.name}")

                    # 生成选题列表
                    if custom_topics and isinstance(custom_topics, list):
                        # 使用自定义选题
                        topics = custom_topics[:count_per_account]
                        log.info(f"Using {len(topics)} custom topics for account {account_id}")
                    else:
                        # 自动生成选题
                        topics = self._generate_topics(account, count_per_account, category)
                        log.info(f"Generated {len(topics)} topics for account {account_id}")

                    # 为每个选题提交任务
                    account_success_count = 0
                    account_failed_count = 0

                    for idx, topic_data in enumerate(topics, 1):
                        try:
                            submitted_task_id = async_service.submit_task(
                                account_id=account_id,
                                topic=topic_data['topic'],
                                keywords=topic_data.get('keywords'),
                                category=category,
                                requirements=topic_data.get('requirements'),
                                tone=topic_data.get('tone'),
                                priority=priority,
                                auto_approve=auto_approve
                            )

                            results['tasks'].append({
                                'task_id': submitted_task_id,
                                'account_id': account_id,
                                'account_name': account.name,
                                'topic': topic_data['topic'],
                                'category': category
                            })
                            results['total_submitted'] += 1
                            account_success_count += 1

                            log.info(
                                f"Submitted task {submitted_task_id} for account {account_id} "
                                f"({idx}/{len(topics)}): {topic_data['topic']}"
                            )

                        except Exception as e:
                            error_msg = f"Failed to submit task for account {account_id}: {str(e)}"
                            results['errors'].append(error_msg)
                            results['total_failed'] += 1
                            account_failed_count += 1
                            log.error(error_msg)

                    # 记录账号统计
                    results['account_stats'][str(account_id)] = {
                        'account_name': account.name,
                        'success': account_success_count,
                        'failed': account_failed_count,
                        'total': account_success_count + account_failed_count
                    }

                except Exception as e:
                    error_msg = f"Error processing account {account_id}: {str(e)}"
                    results['errors'].append(error_msg)
                    results['total_failed'] += count_per_account
                    log.error(error_msg)
                    log.exception("Account processing error")

            # 5. 判断整体是否成功
            # 至少成功提交了一个任务就算成功
            overall_success = results['total_submitted'] > 0

            # 6. 返回执行结果
            duration = time.time() - start_time

            if overall_success:
                message = (
                    f"Successfully submitted {results['total_submitted']} async tasks "
                    f"for {len(account_ids)} accounts"
                )
                if results['total_failed'] > 0:
                    message += f" ({results['total_failed']} failed)"

                return TaskExecutionResult.success_result(
                    message=message,
                    data=results,
                    duration=duration,
                    metadata={
                        "account_ids": account_ids,
                        "count_per_account": count_per_account,
                        "category": category
                    }
                )
            else:
                # 全部失败
                error_msg = f"Failed to submit any tasks: {'; '.join(results['errors'][:3])}"
                return TaskExecutionResult.failure_result(
                    message=error_msg,
                    error="AllTasksFailed",
                    duration=duration,
                    metadata={
                        "errors": results['errors'],
                        "account_ids": account_ids
                    }
                )

        except Exception as e:
            # 捕获所有未处理的异常
            error_msg = f"Unexpected error during async content generation: {str(e)}"
            log.error(error_msg)
            log.exception("Async content generation execution error")
            duration = time.time() - start_time
            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=str(e),
                duration=duration
            )

    def _generate_topics(
        self,
        account: Account,
        count: int,
        category: str = None
    ) -> List[Dict[str, Any]]:
        """
        生成选题列表

        Args:
            account: 账号对象
            count: 生成数量
            category: 内容板块

        Returns:
            选题列表

        TODO: 未来可以集成智能选题逻辑
            - 使用 Tavily API 搜索热门话题
            - 根据账号定位和历史生成个性化选题
            - 使用配置的选题模板
            - 考虑时效性和趋势
        """
        topics = []

        # 简化实现：基于账号信息生成示例选题
        account_name = account.name or "账号"
        account_desc = account.description or "内容创作"

        # 根据板块生成不同类型的选题
        category_suffix_map = {
            "技术": ["技术解析", "实践指南", "趋势分析"],
            "产品": ["产品评测", "使用体验", "功能介绍"],
            "运营": ["运营策略", "增长技巧", "案例分析"],
            "营销": ["营销方法", "获客策略", "转化优化"],
        }

        suffixes = category_suffix_map.get(category, ["深度解析", "实战分享", "经验总结"])

        for i in range(count):
            # 循环使用后缀
            suffix = suffixes[i % len(suffixes)]

            topics.append({
                'topic': f"{account_name} - {suffix} {i+1}",
                'keywords': f"{account_name},{category or '内容'},{suffix}",
                'requirements': f"为{account_name}创作关于{suffix}的高质量内容",
                'tone': account_desc
            })

        log.debug(f"Generated {len(topics)} topics for account {account.id}")

        return topics
