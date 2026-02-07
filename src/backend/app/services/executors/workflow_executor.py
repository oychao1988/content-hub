"""
工作流任务执行器

负责编排多个执行步骤，按顺序执行并传递上下文数据
"""
import time
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.services.scheduler_service import TaskExecutor, TaskExecutionResult
from app.utils.custom_logger import log


class WorkflowExecutor(TaskExecutor):
    """
    工作流任务执行器

    功能：
    1. 按顺序执行多个步骤（steps）
    2. 使用上下文在步骤间传递数据
    3. 支持变量替换（如 ${content_id}）
    4. 任何步骤失败则中断整个工作流
    5. 返回包含所有步骤结果的执行结果

    示例参数：
    {
        "steps": [
            {"type": "content_generation", "params": {"account_id": 49, "topic": "..."}},
            {"type": "approve", "params": {"content_id": "${content_id}"}},
            {"type": "add_to_pool", "params": {"content_id": "${content_id}", "priority": 5}}
        ]
    }
    """

    @property
    def executor_type(self) -> str:
        """返回执行器类型标识"""
        return "workflow"

    def validate_params(self, task_params: Dict[str, Any]) -> bool:
        """
        验证任务参数

        Args:
            task_params: 任务参数字典

        Returns:
            bool: 参数是否有效

        必需参数:
            - steps: 步骤数组（至少包含一个步骤）

        每个步骤必须包含:
            - type: 执行器类型
            - params: 执行参数（可选）
        """
        # 检查 steps 参数
        if "steps" not in task_params:
            log.error("Missing required parameter: steps")
            return False

        steps = task_params.get("steps")
        if not isinstance(steps, list):
            log.error("Parameter 'steps' must be a list")
            return False

        if len(steps) == 0:
            log.error("Parameter 'steps' must contain at least one step")
            return False

        # 验证每个步骤的格式
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                log.error(f"Step {idx} must be a dictionary")
                return False

            if "type" not in step:
                log.error(f"Step {idx} missing required field: type")
                return False

            step_type = step.get("type")
            if not isinstance(step_type, str) or not step_type:
                log.error(f"Step {idx} has invalid type: {step_type}")
                return False

            # params 是可选的，但如果存在必须是字典
            if "params" in step and not isinstance(step["params"], dict):
                log.error(f"Step {idx} params must be a dictionary")
                return False

        log.info(f"Workflow params validation passed: {len(steps)} steps")
        return True

    async def execute(
        self,
        task_id: int,
        task_params: Dict[str, Any],
        db: Session
    ) -> TaskExecutionResult:
        """
        执行工作流任务

        Args:
            task_id: 任务ID
            task_params: 任务参数字典
            db: 数据库会话

        Returns:
            TaskExecutionResult: 任务执行结果

        执行流程:
            1. 遍历 steps 数组
            2. 对每个步骤：
               - 解析变量引用（如 ${content_id}）
               - 获取对应的执行器
               - 执行步骤
               - 将结果数据合并到上下文
            3. 任何步骤失败则中断流程
            4. 返回包含所有步骤结果的执行结果
        """
        start_time = time.time()
        log.info(f"Executing workflow task {task_id}")

        # 初始化上下文（从 task_params 中读取初始 context）
        context: Dict[str, Any] = task_params.get("context", {})
        steps = task_params.get("steps", [])

        # 存储所有步骤的执行结果
        step_results: List[Dict[str, Any]] = []

        try:
            # 遍历执行每个步骤
            for idx, step in enumerate(steps):
                step_type = step.get("type")
                step_params = step.get("params", {})

                log.info(f"Executing step {idx + 1}/{len(steps)}: type={step_type}")

                try:
                    # 1. 解析变量引用
                    resolved_params = self._resolve_variables(step_params, context)
                    log.debug(f"Resolved params for step {idx + 1}: {resolved_params}")

                    # 2. 获取对应类型的执行器
                    from app.services.scheduler_service import scheduler_service
                    executor = scheduler_service.get_executor(step_type)

                    if not executor:
                        error_msg = f"Unknown executor type: {step_type}"
                        log.error(error_msg)
                        duration = time.time() - start_time
                        return TaskExecutionResult.failure_result(
                            message=f"Workflow failed at step {idx + 1}: {error_msg}",
                            error=f"ExecutorNotFound: {step_type}",
                            duration=duration,
                            metadata={
                                "failed_step": idx + 1,
                                "step_type": step_type,
                                "completed_steps": step_results
                            }
                        )

                    # 3. 执行步骤
                    step_result = await executor.execute(task_id, resolved_params, db)

                    # 记录步骤执行结果
                    step_result_data = {
                        "step": idx + 1,
                        "type": step_type,
                        "success": step_result.success,
                        "message": step_result.message,
                        "duration": step_result.duration
                    }
                    step_results.append(step_result_data)

                    # 4. 检查步骤是否成功
                    if not step_result.success:
                        error_msg = f"Step {idx + 1} ({step_type}) failed: {step_result.message}"
                        log.error(error_msg)
                        duration = time.time() - start_time
                        return TaskExecutionResult.failure_result(
                            message=f"Workflow failed at step {idx + 1}: {error_msg}",
                            error=step_result.error,
                            duration=duration,
                            metadata={
                                "failed_step": idx + 1,
                                "step_type": step_type,
                                "step_error": step_result.message,
                                "completed_steps": step_results
                            }
                        )

                    # 5. 将步骤结果数据合并到上下文
                    if step_result.data:
                        context.update(step_result.data)
                        log.info(
                            f"Step {idx + 1} completed successfully, "
                            f"context updated: {list(step_result.data.keys())}"
                        )

                except Exception as e:
                    # 捕获单个步骤的异常
                    error_msg = f"Exception in step {idx + 1} ({step_type}): {str(e)}"
                    log.error(error_msg)
                    log.exception(f"Step {idx + 1} execution error")
                    duration = time.time() - start_time

                    return TaskExecutionResult.failure_result(
                        message=f"Workflow failed at step {idx + 1}: {error_msg}",
                        error=str(e),
                        duration=duration,
                        metadata={
                            "failed_step": idx + 1,
                            "step_type": step_type,
                            "completed_steps": step_results
                        }
                    )

            # 所有步骤执行成功
            duration = time.time() - start_time
            log.info(
                f"Workflow completed successfully: {len(steps)} steps, "
                f"duration={duration:.2f}s"
            )

            return TaskExecutionResult.success_result(
                message=f"Workflow executed successfully: {len(steps)} steps completed",
                data={
                    "total_steps": len(steps),
                    "context": context,
                    "step_results": step_results
                },
                duration=duration,
                metadata={
                    "task_id": task_id,
                    "average_time_per_step": duration / len(steps) if steps else 0
                }
            )

        except Exception as e:
            # 捕获整个工作流的异常
            error_msg = f"Unexpected error during workflow execution: {str(e)}"
            log.error(error_msg)
            log.exception("Workflow execution error")
            duration = time.time() - start_time

            return TaskExecutionResult.failure_result(
                message=error_msg,
                error=str(e),
                duration=duration,
                metadata={
                    "task_id": task_id,
                    "completed_steps": step_results
                }
            )

    def _resolve_variables(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析参数中的变量引用

        Args:
            params: 原始参数字典
            context: 上下文字典

        Returns:
            解析后的参数字典

        支持的变量格式:
            - ${variable_name}: 从上下文中获取值

        示例:
            params = {"content_id": "${content_id}"}
            context = {"content_id": 123}
            返回: {"content_id": 123}
        """
        resolved: Dict[str, Any] = {}

        for key, value in params.items():
            if isinstance(value, str):
                # 检查是否是变量引用（格式：${variable_name}）
                match = re.match(r'^\$\{(.+)\}$', value)
                if match:
                    var_name = match.group(1)
                    # 从上下文中获取变量值
                    if var_name in context:
                        resolved[key] = context[var_name]
                        log.debug(f"Variable resolved: ${var_name} = {context[var_name]}")
                    else:
                        # 变量不存在，保持原样
                        log.warning(f"Variable not found in context: ${var_name}, keeping original value")
                        resolved[key] = value
                else:
                    # 不是变量引用，保持原样
                    resolved[key] = value
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                resolved[key] = self._resolve_variables(value, context)
            elif isinstance(value, list):
                # 递归处理列表中的字典
                resolved[key] = [
                    self._resolve_variables(item, context) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                # 其他类型保持原样
                resolved[key] = value

        return resolved
