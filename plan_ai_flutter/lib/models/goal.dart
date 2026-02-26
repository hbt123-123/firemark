/// 目标数据模型
class Goal {
  final int id;
  final int? userId;
  final String title;
  final String? description;
  final DateTime? startDate;
  final DateTime? endDate;
  final double? progress;  // 0.0 - 1.0
  final String? status;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  Goal({
    required this.id,
    this.userId,
    required this.title,
    this.description,
    this.startDate,
    this.endDate,
    this.progress,
    this.status,
    this.createdAt,
    this.updatedAt,
  });

  factory Goal.fromJson(Map<String, dynamic> json) {
    return Goal(
      id: json['id'] as int,
      userId: json['user_id'] as int?,
      title: json['title'] as String,
      description: json['description'] as String?,
      startDate: json['start_date'] != null
          ? DateTime.parse(json['start_date'] as String)
          : null,
      endDate: json['end_date'] != null
          ? DateTime.parse(json['end_date'] as String)
          : null,
      progress: (json['progress'] as num?)?.toDouble(),
      status: json['status'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
      updatedAt: json['updated_at'] != null
          ? DateTime.parse(json['updated_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'start_date': startDate?.toIso8601String().split('T')[0],
      'end_date': endDate?.toIso8601String().split('T')[0],
      'progress': progress,
      'status': status,
    };
  }

  /// 获取进度百分比
  int get progressPercent => ((progress ?? 0) * 100).round();

  /// 检查是否在时间范围内
  bool get isActive {
    if (startDate == null && endDate == null) return true;
    final now = DateTime.now();
    if (startDate != null && now.isBefore(startDate!)) return false;
    if (endDate != null && now.isAfter(endDate!)) return false;
    return true;
  }

  /// 获取状态文本
  String get statusText {
    if (progress != null && progress! >= 1.0) return '已完成';
    if (!isActive) return '已过期';
    return '进行中';
  }
}

/// AI对话消息
class AIMessage {
  final String role;  // 'user' or 'assistant'
  final String content;
  final bool isPlanPreview;
  final Map<String, dynamic>? planData;

  AIMessage({
    required this.role,
    required this.content,
    this.isPlanPreview = false,
    this.planData,
  });

  bool get isUser => role == 'user';
  bool get isAssistant => role == 'assistant';
}

/// AI计划响应
class AIPlanResponse {
  final String sessionId;
  final String message;
  final bool hasPlanPreview;
  final Map<String, dynamic>? planPreview;

  AIPlanResponse({
    required this.sessionId,
    required this.message,
    this.hasPlanPreview = false,
    this.planPreview,
  });

  factory AIPlanResponse.fromJson(Map<String, dynamic> json) {
    return AIPlanResponse(
      sessionId: json['session_id'] as String,
      message: json['message'] as String,
      hasPlanPreview: json['has_plan_preview'] as bool? ?? false,
      planPreview: json['plan_preview'] as Map<String, dynamic>?,
    );
  }
}
