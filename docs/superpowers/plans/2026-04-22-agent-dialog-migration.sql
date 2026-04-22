-- Agent 对话功能数据库迁移脚本
-- 执行时间: 2026-04-22

-- 扩展 chat_history 表
ALTER TABLE chat_history
ADD COLUMN session_id VARCHAR(64) NOT NULL DEFAULT '' COMMENT '会话ID，关联同一轮对话' AFTER page,
ADD COLUMN message_order INT NOT NULL DEFAULT 0 COMMENT '消息顺序' AFTER session_id,
ADD COLUMN action_type VARCHAR(32) DEFAULT NULL COMMENT '动作类型：query/mutation/optimize/explain' AFTER message_order,
ADD COLUMN action_result TEXT DEFAULT NULL COMMENT '执行结果（JSON）' AFTER action_type,
ADD COLUMN diff_content TEXT DEFAULT NULL COMMENT '变更Diff（JSON）' AFTER action_result;

-- 添加索引
ALTER TABLE chat_history ADD INDEX idx_session_id (session_id);
ALTER TABLE chat_history ADD INDEX idx_user_session (user_id, session_id);
