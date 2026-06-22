const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  running: "处理中",
  awaiting_review: "待人工复核",
  resolved: "已完成",
  failed: "处理失败",
};

const STAGE_LABELS: Record<string, string> = {
  draft: "待启动",
  intent: "意图识别",
  retrieval: "证据检索",
  generation: "方案生成",
  validation: "规则校验",
  manual: "人工复核",
  resolved: "已完成",
  failed: "失败结束",
};

const VALIDATION_LABELS: Record<string, string> = {
  passed: "通过",
  failed: "未通过",
  warning: "需关注",
};

const RISK_LEVEL_LABELS: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
};

const FEEDBACK_ACTION_LABELS: Record<string, string> = {
  accept: "已采纳",
  edited: "编辑后采纳",
  rejected: "已驳回",
};

const SOURCE_LABELS: Record<string, string> = {
  milvus: "向量检索",
  elasticsearch: "关键词检索",
};

const INTENT_LABELS: Record<string, string> = {
  billing_dispute: "账单争议",
  billing: "账单争议",
  service_impact_economic_loss: "服务影响与经济损失",
  unknown: "待识别",
};

const EMOTION_LABELS: Record<string, string> = {
  angry: "不满",
  neutral: "平稳",
  anxious: "焦虑",
  sad: "失望",
  unknown: "待识别",
};

export function formatStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export function formatStageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? stage;
}

export function formatValidationLabel(status: string): string {
  return VALIDATION_LABELS[status] ?? status;
}

export function formatRiskLevelLabel(level: string): string {
  return RISK_LEVEL_LABELS[level] ?? level;
}

export function formatFeedbackActionLabel(action: string): string {
  return FEEDBACK_ACTION_LABELS[action] ?? action;
}

export function formatSourceLabel(source: string): string {
  return SOURCE_LABELS[source] ?? source;
}

export function formatIntentLabel(intent: string): string {
  return INTENT_LABELS[intent] ?? intent;
}

export function formatEmotionLabel(emotion: string): string {
  return EMOTION_LABELS[emotion] ?? emotion;
}
