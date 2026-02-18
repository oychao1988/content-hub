-- 添加发布池扫描任务
-- 这个任务会每5分钟扫描一次发布池，自动发布待发布的内容

INSERT INTO scheduled_tasks (
    name,
    task_type,
    cron_expression,
    task_params,
    is_active,
    description,
    created_at,
    updated_at
) VALUES (
    '发布池自动扫描',
    'publish_pool_scanner',
    '*/5 * * * *',
    '{}',
    1,
    '每5分钟自动扫描发布池并发布待发布的内容',
    datetime('now'),
    datetime('now')
);

-- 验证插入
SELECT * FROM scheduled_tasks WHERE name = '发布池自动扫描';
