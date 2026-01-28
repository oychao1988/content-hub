import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional

from aiolimiter import AsyncLimiter

from app.utils.custom_logger import log


class RateLimiter:
    """基于aiolimiter的速率限制器，提供类似接口以便于替换旧版的AdaptiveRateLimiter

    主要功能：
    1. 使用aiolimiter库的漏桶算法实现精确的速率控制
    2. 保持单例模式以确保全局使用同一个限流器实例
    3. 兼容旧版API以便于平滑过渡
    4. 支持统计和状态报告
    5. 可配置的burst容量和速率

    使用方法：
    1. 获取单例实例：limiter = RateLimiter.get_instance()
    2. 在请求前获取许可：await limiter.acquire()
    3. 请求完成后释放许可：limiter.release() (可选，自动释放)
    4. 报告请求结果：await limiter.report_success() 或 await limiter.report_error()
    """

    # 单例实例
    _instance = None

    @classmethod
    def get_instance(
        cls,
        rate=20,  # 每秒最多处理的请求数 (取代旧版的initial_concurrency)
        max_rate=50,  # 最大速率 (取代旧版的max_concurrency)
        min_rate=5,  # 最小速率 (取代旧版的min_concurrency)
        time_period=60,  # 时间周期，单位秒
        enabled=True,  # 是否启用速率限制器
    ):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(rate, max_rate, min_rate, time_period, enabled)
        else:
            # 允许动态更新 enabled 状态
            cls._instance.enabled = enabled
        return cls._instance

    def __init__(self, rate=20, max_rate=50, min_rate=5, time_period=60, enabled=True):
        """
        初始化速率限制器

        Args:
            rate: 每秒请求速率，相当于旧版的initial_concurrency
            max_rate: 最大请求速率，相当于旧版的max_concurrency
            min_rate: 最小请求速率，相当于旧版的min_concurrency
            time_period: 时间周期，单位秒
            enabled: 是否启用速率限制，设为False时所有acquire调用都会立即成功
        """
        self.rate = rate
        self.max_rate = max_rate
        self.min_rate = min_rate
        self.time_period = time_period
        self.enabled = enabled

        # 创建aiolimiter实例，允许burst请求
        self.limiter = AsyncLimiter(rate, time_period)

        # 添加初始容量预热，避免冷启动问题
        # 预先释放一些令牌，这样系统启动时就能立即使用
        initial_capacity = min(rate // 2, 10)  # 初始预热容量，不超过10个

        # AsyncLimiter不直接暴露添加容量的方法，我们使用另一种方式预热
        # 将内部计数器调整为稍早的时间，这样相当于已经积累了一些令牌
        # 注意：这是一种hack方法，实际使用时应谨慎
        try:
            if hasattr(self.limiter, "_tokens"):
                # 检查aiolimiter版本，处理向后兼容性
                self.limiter._tokens.set_value(initial_capacity)
                log.info(f"初始令牌桶预热完成，添加了{initial_capacity}个令牌")
            else:
                # 较新版本可能有不同实现，使用更保守的设置
                log.info("跳过令牌桶预热，当前aiolimiter版本不支持此操作")
        except Exception as e:
            log.warning(f"令牌桶预热失败: {e}，这不会影响正常运行")

        # 兼容旧版API的属性
        self.concurrency = rate
        self.max_concurrency = max_rate
        self.min_concurrency = min_rate

        # 统计数据
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.total_success = 0
        self.total_errors = 0
        self.consecutive_errors = 0
        self.window_start_time = datetime.now()
        self.last_adjustment_time = datetime.now()
        self.active_requests = 0
        self.last_activity_time = datetime.now()
        self.rate_limit_reset = 0

        # 错误类型统计
        self.error_types_count = {
            "server_disconnected": 0,
            "rate_limit": 0,
            "timeout": 0,
            "other": 0,
        }

        # 用于锁保护的互斥锁
        self.lock = asyncio.Lock()

        # 日志相关
        self.last_status_log_time = datetime.now()
        self.status_log_interval = 300  # 每5分钟记录一次状态

        log.info(
            f"初始化基于aiolimiter的速率限制器，速率: {rate}/秒，最大: {max_rate}，最小: {min_rate}，周期: {time_period}秒"
        )

    async def acquire(self):
        """获取许可，如果达到速率限制则等待"""
        # 更新最后活动时间
        self.last_activity_time = datetime.now()

        # 如果速率限制器被禁用，直接返回，不进行任何限制
        if not self.enabled:
            # 仅更新基本计数，保持统计数据的一致性
            async with self.lock:
                self.request_count += 1
                self.active_requests += 1
            return

        # 检查是否需要等待速率限制重置
        current_time = datetime.now().timestamp()
        if current_time < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - current_time
            log.info(f"等待速率限制重置，休眠 {wait_time:.2f} 秒")
            await asyncio.sleep(wait_time)

        # 更新请求计数
        async with self.lock:
            self.request_count += 1
            self.active_requests += 1

        # 检查是否需要重置时间窗口
        now = datetime.now()
        window_size = 60  # 时间窗口大小，单位秒
        need_log = False
        need_reset = False

        # 检查是否需要重置时间窗口（避免在锁内调用异步方法）
        if (now - self.window_start_time).total_seconds() > window_size:
            need_log = True
            need_reset = True

        # 在锁外记录状态
        if need_log:
            # 先记录状态（不在锁内调用可能阻塞的操作）
            try:
                await self.log_status()
            except Exception as e:
                log.error(f"记录状态时发生错误: {e}")

        # 然后重置窗口
        if need_reset:
            async with self.lock:
                # 再次检查，防止在等待锁的过程中其他线程已经重置了
                if (now - self.window_start_time).total_seconds() > window_size:
                    self.window_start_time = now
                    self.request_count = 1

        try:
            # 改进aiolimiter超时处理，避免卡住
            # 1. 先尝试非阻塞方式获取许可
            if self.limiter.has_capacity():
                await self.limiter.acquire()
            else:
                # 2. 如果没有容量，使用短超时周期性尝试
                max_wait_time = 60  # 最大等待时间(秒)
                wait_interval = 1  # 初始等待时间(秒)
                total_waited = 0  # 已等待时间

                log.info(f"当前无可用容量，开始等待获取许可，最大等待{max_wait_time}秒")
                while total_waited < max_wait_time:
                    try:
                        # 使用短超时等待，避免永久阻塞
                        await asyncio.wait_for(
                            self.limiter.acquire(), timeout=wait_interval
                        )
                        # 获取成功，跳出循环
                        log.info(f"等待{total_waited}秒后成功获取许可")
                        break
                    except asyncio.TimeoutError:
                        # 短时间超时后，增加等待时间并继续
                        total_waited += wait_interval
                        # 指数回退策略增加等待间隔(最大5秒)
                        wait_interval = min(wait_interval * 1.5, 5)

                        # 定期输出等待信息
                        if total_waited % 5 < wait_interval:
                            log.info(
                                f"等待许可中: 已等待{total_waited}秒/{max_wait_time}秒..."
                            )

                        # 检查是否有容量 - 如果现在有，可能是速率限制被调整了
                        if self.limiter.has_capacity():
                            log.info(f"检测到有可用容量，立即尝试获取许可")
                            await self.limiter.acquire()
                            log.info(f"等待{total_waited}秒后成功获取许可")
                            break

                # 如果循环结束后还是没获取到许可，则强制继续执行
                if total_waited >= max_wait_time:
                    log.warning(f"获取许可超时(已等待{max_wait_time}秒)，强制继续执行")
                    # 在超时后，降低当前速率，以减轻系统负担
                    await self._reduce_rate(factor=0.8)
        except Exception as e:
            log.error(f"获取许可过程中发生意外错误: {e}，强制继续执行")
            # 超时后更新统计信息
            async with self.lock:
                self.active_requests -= 1  # 减少活跃请求计数
                self.error_count += 1
                self.total_errors += 1
                self.error_types_count["timeout"] = (
                    self.error_types_count.get("timeout", 0) + 1
                )

    def release(self):
        """释放许可（兼容旧API，实际上aiolimiter不需要手动释放）"""
        # 更新最后活动时间
        self.last_activity_time = datetime.now()

        # 减少活跃请求计数
        if self.active_requests > 0:
            self.active_requests -= 1

    async def report_success(self):
        """报告成功请求"""
        # 更新最后活动时间
        self.last_activity_time = datetime.now()

        # 预先检查是否需要调整速率（提取判断条件）
        need_adjust = False

        # 统计成功次数
        async with self.lock:
            self.success_count += 1
            self.total_success += 1
            self.consecutive_errors = 0
            # 只有在启用限流时才调整速率
            need_adjust = self.enabled

        # 在锁外部调用可能引起死锁的方法
        if need_adjust:
            await self._maybe_adjust_rate()

    async def report_error(self, error_type=None, retry_after=None):
        """
        报告错误请求

        Args:
            error_type: 错误类型，如 'server_disconnected', 'rate_limit' 等
            retry_after: 如果服务器返回了重试时间，则传入
        """
        # 更新最后活动时间
        self.last_activity_time = datetime.now()

        # 用于存储锁外需要执行的操作
        need_reduce_rate = False
        reduce_factor = 0.0
        need_log_status = False
        need_adjust_rate = False
        # 存储是否禁用
        is_enabled = False
        # 存储连续错误计数
        consecutive_errors_count = 0
        # 存储冷却期
        cooling_period = 0

        async with self.lock:
            self.error_count += 1
            self.total_errors += 1
            self.consecutive_errors += 1
            consecutive_errors_count = self.consecutive_errors
            is_enabled = self.enabled

            # 记录错误类型
            if error_type:
                if error_type not in self.error_types_count:
                    self.error_types_count[error_type] = 0
                self.error_types_count[error_type] = (
                    self.error_types_count.get(error_type, 0) + 1
                )
            else:
                self.error_types_count["other"] = (
                    self.error_types_count.get("other", 0) + 1
                )

            # 如果限流被禁用，只记录统计信息但不执行限流动作
            if not is_enabled:
                return

            # 处理速率限制错误 - 记录需要的操作，稍后锁外执行
            if error_type == "rate_limit" and retry_after:
                self.rate_limit_reset = datetime.now().timestamp() + retry_after
                # 速率限制时立即减少速率 - 锁外执行
                need_reduce_rate = True
                reduce_factor = 0.5

            # 处理服务器断开连接错误
            elif error_type == "server_disconnected":
                # 连续错误超过阈值，更激进地降低速率
                if consecutive_errors_count >= 3:
                    need_reduce_rate = True
                    reduce_factor = 0.5
                    # 设置短暂的冷却期
                    cooling_period = 15
                else:
                    need_reduce_rate = True
                    reduce_factor = 0.8

            # 其他错误
            else:
                # 连续错误过多时降低速率
                if consecutive_errors_count >= 5:
                    need_reduce_rate = True
                    reduce_factor = 0.8

            # 在连续错误达到特定阈值时强制记录状态
            if consecutive_errors_count in [5, 10, 20]:
                need_log_status = True

            # 记录是否需要调整速率
            need_adjust_rate = True

        # 在锁外部执行可能引起死锁的操作
        if is_enabled:
            if need_reduce_rate:
                await self._reduce_rate(factor=reduce_factor)
                if error_type == "rate_limit" and retry_after:
                    log.warning(
                        f"达到速率限制，将速率减少到 {self.rate}/秒，等待 {retry_after} 秒"
                    )
                elif (
                    error_type == "server_disconnected"
                    and consecutive_errors_count >= 3
                ):
                    log.warning(
                        f"连续 {consecutive_errors_count} 次服务器断开连接，将速率减少到 {self.rate}/秒"
                    )
                    if cooling_period > 0:
                        # 安全地设置冷却期（可能需要锁，但单纯赋值操作原子性强）
                        async with self.lock:
                            self.rate_limit_reset = (
                                datetime.now().timestamp() + cooling_period
                            )
                elif error_type == "server_disconnected":
                    log.warning(f"服务器断开连接，将速率减少到 {self.rate}/秒")
                elif consecutive_errors_count >= 5:
                    log.warning(
                        f"连续 {consecutive_errors_count} 次错误，将速率减少到 {self.rate}/秒"
                    )

            if need_log_status:
                await self.log_status(force=True)

            if need_adjust_rate:
                await self._maybe_adjust_rate()

    async def _maybe_adjust_rate(self):
        """根据成功/失败比例调整请求速率

        提升负载与性能指标对调整的影响，更加灵活地适应各种场景:
        - 负载高时，更快响应调整，避免系统过载
        - 连续错误时，立即减小速率，避免请求雪崩
        - 使用快照数据避免在锁中执行过多逻辑
        """
        # 记录开始时间
        now = datetime.now()

        # 避免死锁：从锁中提取需要的数据到快照，然后在锁外处理判断逻辑
        # 这样可以显著减少锁的持有时间，降低死锁风险
        snapshot = {}
        try:
            # 尝试获取快照，用短周期锁
            async with self.lock:
                snapshot = {
                    "consecutive_errors": self.consecutive_errors,
                    "active_requests": self.active_requests,
                    "rate": self.rate,
                    "last_adjustment_time": self.last_adjustment_time,
                    "success_count": self.success_count,
                    "error_count": self.error_count,
                    # 这里不修改状态，只复制值
                }
        except Exception as e:
            log.error(f"获取速率调整快照时出错: {e}")
            return  # 出错时直接返回，不调整速率

        # 在锁外执行所有判断逻辑
        # 检查连续错误，如果连续错误超过3次，立即减小速率
        if snapshot["consecutive_errors"] >= 3:
            try:
                log.warning(
                    f"检测到连续错误({snapshot['consecutive_errors']}个)，立即减小速率"
                )
                await self._reduce_rate(factor=0.8)
                # 在锁外重置连续错误计数
                async with self.lock:
                    # 双重检查，确保仍然需要重置
                    if self.consecutive_errors >= 3:
                        self.consecutive_errors = 0
            except Exception as e:
                log.error(f"处理连续错误时出现异常: {e}")
            # 提前返回，不执行其它调整
            return

        # 确定是否需要根据成功率调整速率
        # 根据负载动态调整检查间隔 - 负载高时更频繁检查
        adjustment_interval = (
            30 if snapshot["active_requests"] > snapshot["rate"] * 0.8 else 60
        )

        # 检查是否到达调整时间间隔
        time_since_last = (now - snapshot["last_adjustment_time"]).total_seconds()
        if time_since_last < adjustment_interval:
            return  # 没达到调整间隔，直接返回

        # 计算成功率、样本数等衍生数据
        total_sample = snapshot["success_count"] + snapshot["error_count"]

        # 动态调整所需样本数 - 负载高时更快反应
        required_samples = (
            30 if snapshot["active_requests"] > snapshot["rate"] * 0.5 else 50
        )

        # 样本数不够时不调整
        if total_sample < required_samples:
            return

        # 计算成功率
        success_rate = (
            snapshot["success_count"] / total_sample if total_sample > 0 else 0
        )

        # 记录当前状态
        log.info(
            f"速率调整检查: 成功率={success_rate*100:.2f}%, 样本数={total_sample}, 活跃请求={snapshot['active_requests']}"
        )

        try:
            # 根据成功率确定调整动作
            if success_rate > 0.98:
                # 成功率非常高，可以更激进地增加速率
                await self._increase_rate(factor=1.15)
            elif success_rate > 0.95:
                # 成功率高，尝试增加速率
                await self._increase_rate(factor=1.1)
            elif success_rate < 0.7:
                # 成功率很低，更激进地减少速率
                await self._reduce_rate(factor=0.7)
            elif success_rate < 0.85:
                # 成功率低，减少速率
                await self._reduce_rate(factor=0.9)

            # 重置计数器 - 必须在调整完速率后执行，避免中途速率调整失败后统计数据丢失
            async with self.lock:
                self.success_count = 0
                self.error_count = 0
                self.last_adjustment_time = now
        except Exception as e:
            log.error(f"调整速率时出现异常: {e}")

    async def _increase_rate(self, factor=1.1):
        """增加请求速率"""
        # 使用超时锁并添加错误处理，避免死锁
        try:
            # 尝试获取锁，添加超时机制 (3秒)
            lock_acquired = False
            try:
                # 使用锁的acquire方法并设置超时
                lock_acquired = await asyncio.wait_for(self.lock.acquire(), timeout=3)
            except asyncio.TimeoutError:
                log.warning("获取锁超时，跳过增加速率操作")
                return

            if lock_acquired:
                try:
                    # 检查当前错误计数 - 只有当错误很少时才增加速率
                    if (
                        self.consecutive_errors > 0
                        or self.error_count > self.success_count * 0.05
                    ):
                        log.info(
                            f"存在错误，暂不增加速率: 连续错误={self.consecutive_errors}, 错误率={(self.error_count/(self.success_count+self.error_count+0.001))*100:.2f}%"
                        )
                        return

                    old_rate = self.rate
                    # 增加速率，但不超过最大值 - 使用更保守的增长方式
                    # 在初始阶段快速增长，接近上限时慢速增长
                    if self.rate < self.max_rate * 0.5:  # 小于最大值的一半时
                        self.rate = min(int(self.rate * factor) + 1, self.max_rate)
                    else:  # 接近上限时更谨慎
                        self.rate = min(int(self.rate * 1.05) + 1, self.max_rate)

                    if self.rate > old_rate:
                        # 如果之前降低了时间周期，逐步恢复到原始设置
                        original_period = 60  # 默认周期
                        if self.time_period < original_period:
                            new_period = min(self.time_period * 1.2, original_period)
                            if new_period > self.time_period:
                                log.info(
                                    f"恢复时间周期: {self.time_period} -> {new_period}秒"
                                )
                                self.time_period = new_period

                        # 创建新的limiter
                        self.limiter = AsyncLimiter(self.rate, self.time_period)

                        # 更新兼容属性
                        self.concurrency = self.rate

                        log.info(f"增加请求速率: {old_rate} -> {self.rate}/秒")
                finally:
                    # 确保锁始终被释放
                    self.lock.release()
        except Exception as e:
            log.error(f"增加速率时出现异常: {e}")

    async def _reduce_rate(self, factor=0.9):
        """减少请求速率"""
        # 使用超时锁并添加错误处理，避免死锁
        try:
            # 尝试获取锁，添加超时机制 (3秒)
            lock_acquired = False
            try:
                # 使用锁的acquire方法并设置超时
                lock_acquired = await asyncio.wait_for(self.lock.acquire(), timeout=3)
            except asyncio.TimeoutError:
                log.warning("获取锁超时，跳过减少速率操作")
                return

            if lock_acquired:
                try:
                    old_rate = self.rate
                    # 减少速率，但不低于最小值
                    self.rate = max(int(self.rate * factor), self.min_rate)

                    if self.rate < old_rate:
                        # 创建新的limiter - 在高压力下使用更短的时间周期来加速许可的获取
                        # 当速率被降低时，我们采用更短的时间周期，有助于更快恢复
                        adjusted_period = max(
                            int(self.time_period * factor), 10
                        )  # 最小10秒
                        log.info(
                            f"调整时间周期: {self.time_period} -> {adjusted_period}秒"
                        )
                        self.time_period = adjusted_period

                        # 重新创建limiter
                        self.limiter = AsyncLimiter(self.rate, self.time_period)

                        # 更新兼容属性
                        self.concurrency = self.rate

                        log.info(f"减少请求速率: {old_rate} -> {self.rate}/秒")
                finally:
                    # 确保锁始终被释放
                    self.lock.release()
        except Exception as e:
            log.error(f"减少速率时出现异常: {e}")

    async def log_status(self, force=False):
        """记录当前状态到日志"""
        now = datetime.now()
        # 首先检查是否需要记录状态
        should_log = False
        time_since_last = 0

        # 在锁外检查，减少锁竞争
        try:
            time_since_last = (now - self.last_status_log_time).total_seconds()
            should_log = force or time_since_last >= self.status_log_interval
        except Exception as e:
            log.error(f"检查日志时间时出错: {e}")

        if should_log:
            try:
                # 获取状态（避免死锁）
                status = await self.get_status()
                log.info(
                    f"速率限制器状态: {json.dumps(status, ensure_ascii=False, indent=2)}"
                )
                # 更新最后记录时间
                self.last_status_log_time = now
            except Exception as e:
                log.error(f"记录状态日志时出错: {e}")

    async def get_status(self):
        """获取当前限流器状态信息"""
        # 创建一个快照，尽可能减少锁的持有时间
        # 为了减少死锁风险，只在锁内捕获需要的数据，然后在锁外处理
        snapshot = {}
        try:
            # 使用短时间的锁获取必要数据
            async with self.lock:
                # 复制必要的属性到快照
                snapshot = {
                    "enabled": self.enabled,
                    "rate": self.rate,
                    "min_rate": self.min_rate,
                    "max_rate": self.max_rate,
                    "time_period": self.time_period,
                    "success_count": self.success_count,
                    "error_count": self.error_count,
                    "request_count": self.request_count,
                    "total_success": self.total_success,
                    "total_errors": self.total_errors,
                    "error_types_count": self.error_types_count.copy(),
                    "window_start_time": self.window_start_time,
                    "consecutive_errors": self.consecutive_errors,
                    "active_requests": self.active_requests,
                    "last_activity_time": self.last_activity_time,
                }
        except Exception as e:
            log.error(f"获取状态快照时出错: {e}")
            return {"error": f"获取状态失败: {e}"}

        # 在锁外处理数据
        now = datetime.now()
        try:
            # 计算衍生数据
            runtime = (now - snapshot["window_start_time"]).total_seconds()
            current_rate = snapshot["request_count"] / runtime if runtime > 0 else 0

            total = snapshot["success_count"] + snapshot["error_count"]
            success_rate = snapshot["success_count"] / total * 100 if total > 0 else 0

            # 构建状态对象
            status = {
                "是否启用限流": snapshot["enabled"],
                "当前速率": f"{snapshot['rate']}/秒",
                "最小速率": snapshot["min_rate"],
                "最大速率": snapshot["max_rate"],
                "时间周期": f"{snapshot['time_period']}秒",
                "当前成功率": f"{success_rate:.2f}%",
                "当前窗口请求数": snapshot["request_count"],
                "当前窗口成功数": snapshot["success_count"],
                "当前窗口错误数": snapshot["error_count"],
                "总成功请求": snapshot["total_success"],
                "总错误请求": snapshot["total_errors"],
                "错误类型统计": snapshot["error_types_count"],
                "窗口开始时间": snapshot["window_start_time"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "当前请求速率": f"{current_rate:.2f} 请求/秒",
                "连续错误数": snapshot["consecutive_errors"],
                "当前活跃请求数": snapshot["active_requests"],
                "最后活动时间": snapshot["last_activity_time"].strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "距离最后活动": f"{(now - snapshot['last_activity_time']).total_seconds():.2f}秒",
                "是否有容量": self.limiter.has_capacity(),
            }

            return status
        except Exception as e:
            log.error(f"处理状态数据时出错: {e}")
            return {"error": f"处理状态数据失败: {e}", "raw_data": snapshot}

    async def force_reset(self):
        """强制重置限流器状态，用于从异常状态恢复"""
        log.warning("强制重置速率限制器状态...")

        # 先获取重置前状态（在锁外部）
        try:
            status_before = await self.get_status()
            log.warning(f"重置前状态: {json.dumps(status_before, ensure_ascii=False)}")
        except Exception as e:
            log.error(f"获取重置前状态失败: {e}")
            status_before = {"error": str(e)}

        # 使用超时锁，避免死锁
        lock_acquired = False
        try:
            try:
                # 使用锁的acquire方法并设置超时
                lock_acquired = await asyncio.wait_for(self.lock.acquire(), timeout=5)
            except asyncio.TimeoutError:
                log.error("获取锁超时，强制重置失败")
                return {"error": "获取锁超时，强制重置失败"}

            if lock_acquired:
                try:
                    # 重置计数器和状态
                    self.success_count = 0
                    self.error_count = 0
                    self.consecutive_errors = 0
                    self.request_count = 0
                    self.active_requests = 0
                    self.window_start_time = datetime.now()
                    self.last_adjustment_time = datetime.now()
                    self.last_activity_time = datetime.now()
                    self.rate_limit_reset = 0

                    # 重置limiter
                    self.limiter = AsyncLimiter(self.rate, self.time_period)
                finally:
                    # 确保锁被释放
                    self.lock.release()
        except Exception as e:
            log.error(f"重置过程中出现异常: {e}")
            return {"error": f"重置失败: {e}"}

        # 获取重置后状态（在锁外部）
        try:
            status_after = await self.get_status()
            log.warning(f"重置后状态: {json.dumps(status_after, ensure_ascii=False)}")
        except Exception as e:
            log.error(f"获取重置后状态失败: {e}")
            status_after = {"error": str(e)}

        return {
            "success": True,
            "message": "已强制重置限流器状态",
            "before": status_before,
            "after": status_after,
        }


# 全局函数，用于获取速率限制器实例
def get_rate_limiter():
    """获取全局速率限制器实例"""
    from app.core.config import settings

    return RateLimiter.get_instance(
        rate=getattr(settings, "INITIAL_CONCURRENCY", 20),
        max_rate=getattr(settings, "MAX_CONCURRENCY", 50),
        min_rate=getattr(settings, "MIN_CONCURRENCY", 5),
        enabled=getattr(settings, "RATE_LIMITER_ENABLED", True),
    )


# 管理速率限制器的工具函数
async def manage_rate_limiter(action="status", **kwargs):
    """
    管理速率限制器的工具函数

    Args:
        action: 要执行的操作，可以是：
               - status: 获取当前状态
               - set_concurrency: 设置当前速率
               - set_min: 设置最小速率
               - set_max: 设置最大速率
               - reset: 重置错误计数和统计
               - force_reset: 强制重置限流器状态，用于从异常状态恢复
               - enable: 启用速率限制器
               - disable: 禁用速率限制器
               - toggle: 切换限流器启用状态
        **kwargs: 其他参数，根据action不同而不同

    Returns:
        dict: 操作结果
    """
    limiter = get_rate_limiter()

    if action == "status":
        return await limiter.get_status()

    elif action == "set_concurrency":
        rate = int(kwargs.get("concurrency", limiter.rate))
        if rate < limiter.min_rate or rate > limiter.max_rate:
            return {
                "error": f"速率必须在 {limiter.min_rate} 和 {limiter.max_rate} 之间"
            }

        async with limiter.lock:
            old_rate = limiter.rate
            limiter.rate = rate
            limiter.concurrency = rate  # 兼容旧API

            # 创建新的limiter实例
            limiter.limiter = AsyncLimiter(rate, limiter.time_period)

            log.info(f"手动调整速率: {old_rate} -> {rate}/秒")
            return {
                "success": True,
                "message": f"速率已从 {old_rate} 调整为 {rate}/秒",
            }

    elif action == "set_min":
        min_rate = int(kwargs.get("min_concurrency", limiter.min_rate))
        if min_rate < 1 or min_rate > limiter.max_rate:
            return {"error": f"最小速率必须在 1 和 {limiter.max_rate} 之间"}

        need_adjust = False
        actual_rate = 0

        async with limiter.lock:
            old_min = limiter.min_rate
            limiter.min_rate = min_rate
            limiter.min_concurrency = min_rate  # 兼容旧API
            log.info(f"手动调整最小速率: {old_min} -> {min_rate}/秒")

            # 检查是否需要调整当前速率
            if limiter.rate < min_rate:
                need_adjust = True
                actual_rate = min_rate

        # 在锁外部调用其他函数
        if need_adjust:
            # 如果当前速率小于新的最小值，调整它
            return await manage_rate_limiter(
                action="set_concurrency", concurrency=actual_rate
            )

        return {
            "success": True,
            "message": f"最小速率已从 {old_min} 调整为 {min_rate}/秒",
        }

    elif action == "set_max":
        max_rate = int(kwargs.get("max_concurrency", limiter.max_rate))
        if max_rate < limiter.min_rate:
            return {"error": f"最大速率必须大于等于最小速率 {limiter.min_rate}"}

        need_adjust = False
        actual_rate = 0

        async with limiter.lock:
            old_max = limiter.max_rate
            limiter.max_rate = max_rate
            limiter.max_concurrency = max_rate  # 兼容旧API
            log.info(f"手动调整最大速率: {old_max} -> {max_rate}/秒")

            # 检查是否需要调整当前速率
            if limiter.rate > max_rate:
                need_adjust = True
                actual_rate = max_rate

        # 在锁外部调用其他函数
        if need_adjust:
            # 如果当前速率大于新的最大值，调整它
            return await manage_rate_limiter(
                action="set_concurrency", concurrency=actual_rate
            )

        return {
            "success": True,
            "message": f"最大速率已从 {old_max} 调整为 {max_rate}/秒",
        }

    elif action == "reset":
        async with limiter.lock:
            limiter.success_count = 0
            limiter.error_count = 0
            limiter.consecutive_errors = 0
            limiter.request_count = 0
            limiter.window_start_time = datetime.now()
            limiter.last_adjustment_time = datetime.now()
            limiter.rate_limit_reset = 0
            limiter.error_types_count = {
                "server_disconnected": 0,
                "rate_limit": 0,
                "timeout": 0,
                "other": 0,
            }
            log.info("已重置速率限制器的统计数据")
            return {"success": True, "message": "已重置限流器状态"}

    elif action == "force_reset":
        log.warning("执行强制重置操作，尝试从异常状态恢复...")
        result = await limiter.force_reset()
        log.warning(f"强制重置结果: {result}")
        return result

    elif action == "enable":
        old_state = None
        # 添加超时锁获取，避免死锁
        try:
            # 尝试获取锁，但最多等待3秒
            lock_acquired = await asyncio.wait_for(limiter.lock.acquire(), timeout=3)
            if lock_acquired:
                try:
                    old_state = limiter.enabled
                    limiter.enabled = True
                    log.info("已启用速率限制器")
                finally:
                    # 确保锁被释放
                    limiter.lock.release()
            else:
                log.error("获取锁超时，无法启用速率限制器")
                return {"error": "获取锁超时，操作失败"}
        except asyncio.TimeoutError:
            log.error("获取锁超时，无法启用速率限制器")
            return {"error": "获取锁超时，操作失败"}
        except Exception as e:
            log.error(f"启用速率限制器时出错: {e}")
            return {"error": f"操作失败: {e}"}

        # 尝试获取状态，但即使失败也返回成功结果
        try:
            # 获取锁外的状态
            status = await limiter.get_status()
            return {
                "success": True,
                "message": f"速率限制器已启用，原状态: {old_state}",
                "status": status,
            }
        except Exception as e:
            log.warning(f"获取状态时出错: {e}")
            return {
                "success": True,
                "message": f"速率限制器已启用，原状态: {old_state}",
                "error_getting_status": str(e),
            }

    elif action == "disable":
        old_state = None
        # 添加超时锁获取，避免死锁
        try:
            # 尝试获取锁，但最多等待3秒
            lock_acquired = await asyncio.wait_for(limiter.lock.acquire(), timeout=3)
            if lock_acquired:
                try:
                    old_state = limiter.enabled
                    limiter.enabled = False
                    log.warning("已禁用速率限制器 - 请谨慎使用，可能导致请求过载")
                finally:
                    # 确保锁被释放
                    limiter.lock.release()
            else:
                log.error("获取锁超时，无法禁用速率限制器")
                return {"error": "获取锁超时，操作失败"}
        except asyncio.TimeoutError:
            log.error("获取锁超时，无法禁用速率限制器")
            return {"error": "获取锁超时，操作失败"}
        except Exception as e:
            log.error(f"禁用速率限制器时出错: {e}")
            return {"error": f"操作失败: {e}"}

        # 尝试获取状态，但即使失败也返回成功结果
        try:
            # 获取锁外的状态
            status = await limiter.get_status()
            return {
                "success": True,
                "message": f"速率限制器已禁用，原状态: {old_state}",
                "status": status,
            }
        except Exception as e:
            log.warning(f"获取状态时出错: {e}")
            return {
                "success": True,
                "message": f"速率限制器已禁用，原状态: {old_state}",
                "error_getting_status": str(e),
            }

    elif action == "toggle":
        old_state = None
        new_state = None
        # 添加超时锁获取，避免死锁
        try:
            # 尝试获取锁，但最多等待3秒
            lock_acquired = await asyncio.wait_for(limiter.lock.acquire(), timeout=3)
            if lock_acquired:
                try:
                    old_state = limiter.enabled
                    limiter.enabled = not limiter.enabled
                    new_state = limiter.enabled
                    if new_state:
                        log.info("已启用速率限制器")
                    else:
                        log.warning("已禁用速率限制器 - 请谨慎使用，可能导致请求过载")
                finally:
                    # 确保锁被释放
                    limiter.lock.release()
            else:
                log.error("获取锁超时，无法切换速率限制器状态")
                return {"error": "获取锁超时，操作失败"}
        except asyncio.TimeoutError:
            log.error("获取锁超时，无法切换速率限制器状态")
            return {"error": "获取锁超时，操作失败"}
        except Exception as e:
            log.error(f"切换速率限制器状态时出错: {e}")
            return {"error": f"操作失败: {e}"}

        # 尝试获取状态，但即使失败也返回成功结果
        try:
            # 获取锁外的状态
            status = await limiter.get_status()
            return {
                "success": True,
                "message": f"速率限制器状态已切换: {old_state} -> {new_state}",
                "status": status,
            }
        except Exception as e:
            log.warning(f"获取状态时出错: {e}")
            return {
                "success": True,
                "message": f"速率限制器状态已切换: {old_state} -> {new_state}",
                "error_getting_status": str(e),
            }

    else:
        return {"error": f"未知操作: {action}"}
