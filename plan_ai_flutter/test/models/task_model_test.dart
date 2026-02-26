/**
 * Flutter Task 模型单元测试
 */
import 'package:flutter_test/flutter_test.dart';

import 'package:plan_ai_flutter/models/task.dart';


void main() {
  group('TaskStatus Enum Tests', () {
    test('apiValue 返回正确的 API 值', () {
      expect(TaskStatus.pending.apiValue, 'pending');
      expect(TaskStatus.completed.apiValue, 'completed');
      expect(TaskStatus.skipped.apiValue, 'skipped');
    });
    
    test('displayName 返回中文显示名称', () {
      expect(TaskStatus.pending.displayName, '待完成');
      expect(TaskStatus.completed.displayName, '已完成');
      expect(TaskStatus.skipped.displayName, '已跳过');
    });
    
    test('fromString 正确解析字符串', () {
      expect(TaskStatusExtension.fromString('pending'), TaskStatus.pending);
      expect(TaskStatusExtension.fromString('completed'), TaskStatus.completed);
      expect(TaskStatusExtension.fromString('skipped'), TaskStatus.skipped);
      expect(TaskStatusExtension.fromString('unknown'), TaskStatus.pending);
      expect(TaskStatusExtension.fromString(null), TaskStatus.pending);
    });
  });
  
  group('TaskPriority Enum Tests', () {
    test('value 返回正确的数值', () {
      expect(TaskPriority.low.value, 0);
      expect(TaskPriority.medium.value, 1);
      expect(TaskPriority.high.value, 2);
    });
    
    test('displayName 返回中文显示名称', () {
      expect(TaskPriority.low.displayName, '低');
      expect(TaskPriority.medium.displayName, '中');
      expect(TaskPriority.high.displayName, '高');
    });
    
    test('fromInt 正确解析整数', () {
      expect(TaskPriorityExtension.fromInt(0), TaskPriority.low);
      expect(TaskPriorityExtension.fromInt(1), TaskPriority.medium);
      expect(TaskPriorityExtension.fromInt(2), TaskPriority.high);
      expect(TaskPriorityExtension.fromInt(99), TaskPriority.medium);
      expect(TaskPriorityExtension.fromInt(null), TaskPriority.medium);
    });
  });
  
  group('Task Model Tests', () {
    test('fromJson 正确解析完整数据', () {
      final json = {
        'id': 1,
        'user_id': 1,
        'goal_id': 1,
        'title': '测试任务',
        'description': '任务描述',
        'due_date': '2026-02-25',
        'due_time': '14:00',
        'status': 'pending',
        'priority': 1,
        'dependencies': [1, 2],
        'created_at': '2026-02-25T10:00:00Z',
      };
      
      final task = Task.fromJson(json);
      
      expect(task.id, 1);
      expect(task.userId, 1);
      expect(task.goalId, 1);
      expect(task.title, '测试任务');
      expect(task.description, '任务描述');
      expect(task.dueDate, '2026-02-25');
      expect(task.dueTime, '14:00');
      expect(task.status, TaskStatus.pending);
      expect(task.priority, TaskPriority.medium);
      expect(task.dependencies, [1, 2]);
      expect(task.createdAt, isNotNull);
    });
    
    test('fromJson 处理可选字段缺失', () {
      final json = {
        'id': 1,
        'title': '测试任务',
      };
      
      final task = Task.fromJson(json);
      
      expect(task.id, 1);
      expect(task.title, '测试任务');
      expect(task.description, isNull);
      expect(task.dueDate, isNull);
      expect(task.status, TaskStatus.pending);
      expect(task.priority, TaskPriority.medium);
      expect(task.dependencies, isEmpty);
    });
    
    test('toJson 正确序列化', () {
      final task = Task(
        id: 1,
        title: '测试任务',
        description: '描述',
        dueDate: '2026-02-25',
        dueTime: '14:00',
        status: TaskStatus.pending,
        priority: TaskPriority.high,
        dependencies: [1, 2],
      );
      
      final json = task.toJson();
      
      expect(json['id'], 1);
      expect(json['title'], '测试任务');
      expect(json['description'], '描述');
      expect(json['due_date'], '2026-02-25');
      expect(json['due_time'], '14:00');
      expect(json['status'], 'pending');
      expect(json['priority'], 2);
      expect(json['dependencies'], [1, 2]);
    });
    
    test('toCreateJson 不包含 id', () {
      final task = Task(
        id: 1,
        userId: 1,
        goalId: 1,
        title: '测试任务',
      );
      
      final json = task.toCreateJson();
      
      expect(json.containsKey('id'), false);
      expect(json['title'], '测试任务');
      expect(json['goal_id'], 1);
    });
    
    test('copyWith 创建副本', () {
      final task = Task(
        id: 1,
        title: '原标题',
        priority: TaskPriority.low,
      );
      
      final copied = task.copyWith(
        title: '新标题',
        priority: TaskPriority.high,
      );
      
      expect(copied.id, 1);
      expect(copied.title, '新标题');
      expect(copied.priority, TaskPriority.high);
      expect(task.title, '原标题'); // 原始对象不变
    });
    
    test('isToday 判断是否今天', () {
      final now = DateTime.now();
      final todayStr = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
      
      final todayTask = Task(id: 1, title: '今天', dueDate: todayStr);
      final tomorrowTask = Task(id: 2, title: '明天', dueDate: '2026-12-31');
      final noDateTask = Task(id: 3, title: '无日期');
      
      expect(todayTask.isToday, true);
      expect(tomorrowTask.isToday, false);
      expect(noDateTask.isToday, false);
    });
    
    test('displayTime 返回时间字符串', () {
      final task = Task(id: 1, title: '测试', dueTime: '14:30');
      final noTimeTask = Task(id: 2, title: '测试2');
      
      expect(task.displayTime, '14:30');
      expect(noTimeTask.displayTime, isNull);
    });
  });
  
  group('TaskListResponse Model Tests', () {
    test('fromJson 正确解析任务列表', () {
      final json = {
        'tasks': [
          {'id': 1, 'title': '任务1'},
          {'id': 2, 'title': '任务2'},
        ],
        'total': 2,
      };
      
      final response = TaskListResponse.fromJson(json);
      
      expect(response.tasks.length, 2);
      expect(response.tasks[0].title, '任务1');
      expect(response.tasks[1].title, '任务2');
      expect(response.total, 2);
    });
    
    test('fromJson 处理空列表', () {
      final json = {
        'tasks': null,
        'total': 0,
      };
      
      final response = TaskListResponse.fromJson(json);
      
      expect(response.tasks, isEmpty);
      expect(response.total, 0);
    });
  });
}
