/// 任务状态枚举
enum TaskStatus {
  pending,    // 待完成
  completed,  // 已完成
  skipped,    // 已跳过
}

extension TaskStatusExtension on TaskStatus {
  String get apiValue {
    switch (this) {
      case TaskStatus.pending:
        return 'pending';
      case TaskStatus.completed:
        return 'completed';
      case TaskStatus.skipped:
        return 'skipped';
    }
  }

  String get displayName {
    switch (this) {
      case TaskStatus.pending:
        return '待完成';
      case TaskStatus.completed:
        return '已完成';
      case TaskStatus.skipped:
        return '已跳过';
    }
  }

  static TaskStatus fromString(String? value) {
    switch (value?.toLowerCase()) {
      case 'completed':
        return TaskStatus.completed;
      case 'skipped':
        return TaskStatus.skipped;
      default:
        return TaskStatus.pending;
    }
  }
}

/// 任务优先级枚举
enum TaskPriority {
  low,     // 低优先级 (0)
  medium,  // 中优先级 (1)
  high,    // 高优先级 (2)
}

extension TaskPriorityExtension on TaskPriority {
  int get value {
    switch (this) {
      case TaskPriority.low:
        return 0;
      case TaskPriority.medium:
        return 1;
      case TaskPriority.high:
        return 2;
    }
  }

  String get displayName {
    switch (this) {
      case TaskPriority.low:
        return '低';
      case TaskPriority.medium:
        return '中';
      case TaskPriority.high:
        return '高';
    }
  }

  static TaskPriority fromInt(int? value) {
    switch (value) {
      case 0:
        return TaskPriority.low;
      case 2:
        return TaskPriority.high;
      default:
        return TaskPriority.medium;
    }
  }
}

/// 任务数据模型
class Task {
  final int id;
  final int? userId;
  final int? goalId;
  final String title;
  final String? description;
  final String? dueDate;       // YYYY-MM-DD
  final String? dueTime;       // HH:mm
  final TaskStatus status;
  final TaskPriority priority;
  final List<int> dependencies;
  final DateTime? createdAt;

  Task({
    required this.id,
    this.userId,
    this.goalId,
    required this.title,
    this.description,
    this.dueDate,
    this.dueTime,
    this.status = TaskStatus.pending,
    this.priority = TaskPriority.medium,
    this.dependencies = const [],
    this.createdAt,
  });

  factory Task.fromJson(Map<String, dynamic> json) {
    return Task(
      id: json['id'] as int,
      userId: json['user_id'] as int?,
      goalId: json['goal_id'] as int?,
      title: json['title'] as String,
      description: json['description'] as String?,
      dueDate: json['due_date'] as String?,
      dueTime: json['due_time'] as String?,
      status: TaskStatusExtension.fromString(json['status'] as String?),
      priority: TaskPriorityExtension.fromInt(json['priority'] as int?),
      dependencies: (json['dependencies'] as List<dynamic>?)
              ?.map((e) => e as int)
              .toList() ??
          [],
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'description': description,
      'due_date': dueDate,
      'due_time': dueTime,
      'status': status.apiValue,
      'priority': priority.value,
      'dependencies': dependencies,
    };
  }

  /// 创建新任务时的请求数据
  Map<String, dynamic> toCreateJson() {
    return {
      'title': title,
      'description': description,
      'due_date': dueDate,
      'due_time': dueTime,
      'priority': priority.value,
      'dependencies': dependencies,
      'goal_id': goalId,
    };
  }

  Task copyWith({
    int? id,
    int? userId,
    int? goalId,
    String? title,
    String? description,
    String? dueDate,
    String? dueTime,
    TaskStatus? status,
    TaskPriority? priority,
    List<int>? dependencies,
    DateTime? createdAt,
  }) {
    return Task(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      goalId: goalId ?? this.goalId,
      title: title ?? this.title,
      description: description ?? this.description,
      dueDate: dueDate ?? this.dueDate,
      dueTime: dueTime ?? this.dueTime,
      status: status ?? this.status,
      priority: priority ?? this.priority,
      dependencies: dependencies ?? this.dependencies,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  /// 检查是否是今天
  bool get isToday {
    if (dueDate == null) return false;
    final now = DateTime.now();
    return dueDate == '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
  }

  /// 获取显示的时间字符串
  String? get displayTime {
    if (dueTime != null) {
      return dueTime;
    }
    return null;
  }
}

/// 任务列表响应
class TaskListResponse {
  final List<Task> tasks;
  final int total;

  TaskListResponse({
    required this.tasks,
    required this.total,
  });

  factory TaskListResponse.fromJson(Map<String, dynamic> json) {
    return TaskListResponse(
      tasks: (json['tasks'] as List<dynamic>?)
              ?.map((e) => Task.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      total: json['total'] as int? ?? 0,
    );
  }
}
