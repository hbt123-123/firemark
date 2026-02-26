/// 反思记录数据模型
class ReflectionLog {
  final int id;
  final int goalId;
  final DateTime createdAt;
  final String? analysisSummary;
  final String? adjustmentPlan;
  final bool isApplied;
  final DateTime? appliedAt;

  ReflectionLog({
    required this.id,
    required this.goalId,
    required this.createdAt,
    this.analysisSummary,
    this.adjustmentPlan,
    this.isApplied = false,
    this.appliedAt,
  });

  factory ReflectionLog.fromJson(Map<String, dynamic> json) {
    return ReflectionLog(
      id: json['id'] as int,
      goalId: json['goal_id'] as int,
      createdAt: DateTime.parse(json['created_at'] as String),
      analysisSummary: json['analysis_summary'] as String?,
      adjustmentPlan: json['adjustment_plan'] as String?,
      isApplied: json['is_applied'] as bool? ?? false,
      appliedAt: json['applied_at'] != null
          ? DateTime.parse(json['applied_at'] as String)
          : null,
    );
  }
}

/// 目标大纲数据模型
class GoalOutline {
  final String? title;
  final List<Milestone> milestones;

  GoalOutline({
    this.title,
    this.milestones = const [],
  });

  factory GoalOutline.fromJson(Map<String, dynamic> json) {
    return GoalOutline(
      title: json['title'] as String?,
      milestones: (json['milestones'] as List<dynamic>?)
              ?.map((e) => Milestone.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }

  /// 从字符串解析（如果API返回的是字符串格式）
  factory GoalOutline.parseFromString(String? outlineStr) {
    if (outlineStr == null || outlineStr.isEmpty) {
      return GoalOutline();
    }
    
    // 简单解析：按换行和缩进分组
    final lines = outlineStr.split('\n');
    final milestones = <Milestone>[];
    Milestone? currentMilestone;
    
    for (final line in lines) {
      final trimmed = line.trim();
      if (trimmed.isEmpty) continue;
      
      // 检测章节标题 (以数字或特殊字符开头)
      if (RegExp(r'^[0-9一二三四五六七八九十]+\.?').hasMatch(trimmed)) {
        if (currentMilestone != null) {
          milestones.add(currentMilestone);
        }
        currentMilestone = Milestone(
          title: trimmed.replaceFirst(RegExp(r'^[0-9一二三四五六七八九十]+\.?'), '').trim(),
          tasks: [],
        );
      } else if (currentMilestone != null) {
        // 任务项
        final taskTitle = trimmed.replaceFirst(RegExp(r'^[-*•]'), '').trim();
        if (taskTitle.isNotEmpty) {
          currentMilestone.tasks.add(GoalTask(title: taskTitle));
        }
      }
    }
    
    if (currentMilestone != null) {
      milestones.add(currentMilestone);
    }
    
    return GoalOutline(milestones: milestones);
  }
}

/// 里程碑
class Milestone {
  final String title;
  final List<GoalTask> tasks;
  final bool isCompleted;

  Milestone({
    required this.title,
    this.tasks = const [],
    this.isCompleted = false,
  });

  factory Milestone.fromJson(Map<String, dynamic> json) {
    return Milestone(
      title: json['title'] as String,
      tasks: (json['tasks'] as List<dynamic>?)
              ?.map((e) => GoalTask.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      isCompleted: json['is_completed'] as bool? ?? false,
    );
  }
}

/// 任务
class GoalTask {
  final int id;
  final String title;
  final bool isCompleted;

  GoalTask({
    this.id = 0,
    required this.title,
    this.isCompleted = false,
  });

  factory GoalTask.fromJson(Map<String, dynamic> json) {
    return GoalTask(
      id: json['id'] as int? ?? 0,
      title: json['title'] as String,
      isCompleted: json['is_completed'] as bool? ?? false,
    );
  }
}
