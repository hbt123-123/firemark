/// 重复规则枚举
enum RepeatRule {
  none,       // 不重复
  daily,      // 每天
  weekly,     // 每周
  monthly,    // 每月
  weekday,    // 工作日 (周一到周五)
  weekend,    // 周末 (周六日)
}

extension RepeatRuleExtension on RepeatRule {
  String get displayName {
    switch (this) {
      case RepeatRule.none:
        return '不重复';
      case RepeatRule.daily:
        return '每天';
      case RepeatRule.weekly:
        return '每周';
      case RepeatRule.monthly:
        return '每月';
      case RepeatRule.weekday:
        return '工作日';
      case RepeatRule.weekend:
        return '周末';
    }
  }

  String get apiValue {
    switch (this) {
      case RepeatRule.none:
        return 'none';
      case RepeatRule.daily:
        return 'daily';
      case RepeatRule.weekly:
        return 'weekly';
      case RepeatRule.monthly:
        return 'monthly';
      case RepeatRule.weekday:
        return 'weekday';
      case RepeatRule.weekend:
        return 'weekend';
    }
  }

  static RepeatRule fromString(String? value) {
    switch (value?.toLowerCase()) {
      case 'daily':
        return RepeatRule.daily;
      case 'weekly':
        return RepeatRule.weekly;
      case 'monthly':
        return RepeatRule.monthly;
      case 'weekday':
        return RepeatRule.weekday;
      case 'weekend':
        return RepeatRule.weekend;
      default:
        return RepeatRule.none;
    }
  }
}

/// 固定日程数据模型
class FixedSchedule {
  final int id;
  final String title;
  final String? description;
  final int dayOfWeek;       // 1-7 (周一到周日)
  final String startTime;    // HH:mm 格式
  final String endTime;      // HH:mm 格式
  final RepeatRule repeatRule;
  final DateTime? createdAt;

  FixedSchedule({
    required this.id,
    required this.title,
    this.description,
    required this.dayOfWeek,
    required this.startTime,
    required this.endTime,
    this.repeatRule = RepeatRule.none,
    this.createdAt,
  });

  factory FixedSchedule.fromJson(Map<String, dynamic> json) {
    return FixedSchedule(
      id: json['id'] as int,
      title: json['title'] as String,
      description: json['description'] as String?,
      dayOfWeek: json['day_of_week'] as int? ?? json['dayOfWeek'] as int,
      startTime: json['start_time'] as String? ?? json['startTime'] as String,
      endTime: json['end_time'] as String? ?? json['endTime'] as String,
      repeatRule: RepeatRuleExtension.fromString(
        json['repeat_rule'] as String? ?? json['repeatRule'] as String?,
      ),
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
      'day_of_week': dayOfWeek,
      'start_time': startTime,
      'end_time': endTime,
      'repeat_rule': repeatRule.apiValue,
    };
  }

  /// 创建新日程时的请求数据 (不含id)
  Map<String, dynamic> toCreateJson() {
    return {
      'title': title,
      'description': description,
      'day_of_week': dayOfWeek,
      'start_time': startTime,
      'end_time': endTime,
      'repeat_rule': repeatRule.apiValue,
    };
  }

  FixedSchedule copyWith({
    int? id,
    String? title,
    String? description,
    int? dayOfWeek,
    String? startTime,
    String? endTime,
    RepeatRule? repeatRule,
    DateTime? createdAt,
  }) {
    return FixedSchedule(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      dayOfWeek: dayOfWeek ?? this.dayOfWeek,
      startTime: startTime ?? this.startTime,
      endTime: endTime ?? this.endTime,
      repeatRule: repeatRule ?? this.repeatRule,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}

/// 星期几帮助类
class WeekdayHelper {
  static const List<String> chinese = [
    '周一',
    '周二',
    '周三',
    '周四',
    '周五',
    '周六',
    '周日',
  ];

  static const List<String> english = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
  ];

  static String getChinese(int dayOfWeek) {
    if (dayOfWeek >= 1 && dayOfWeek <= 7) {
      return chinese[dayOfWeek - 1];
    }
    return '';
  }

  static int getCurrentDayOfWeek() {
    // Dart的DateTime.weekday: 1=Monday, 7=Sunday
    return DateTime.now().weekday;
  }

  /// 获取本周的起始日期 (周一)
  static DateTime getWeekStart(DateTime date) {
    return date.subtract(Duration(days: date.weekday - 1));
  }

  /// 获取本周的日期列表 (周一到周日)
  static List<DateTime> getWeekDates(DateTime date) {
    final weekStart = getWeekStart(date);
    return List.generate(7, (index) => weekStart.add(Duration(days: index)));
  }
}
