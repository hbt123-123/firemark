import 'package:flutter_dotenv/flutter_dotenv.dart';

/// API 常量配置
class ApiConstants {
  // 基础URL - 从环境变量读取，默认开发环境
  static String get baseUrl => dotenv.env['API_BASE_URL'] ?? 'http://10.0.2.2:8000/api/v1';
  
  // 认证相关接口
  static const String register = '/auth/register';
  static const String login = '/auth/login';
  static const String loginForm = '/auth/login/form';
  static const String me = '/auth/me';
  
  // 固定日程相关接口
  static const String fixedSchedules = '/fixed-schedules';
  
  // 任务相关接口
  static const String tasks = '/tasks';
  
  // 评论相关接口
  static const String comments = '/comments';
  
  // 目标相关接口
  static const String goals = '/goals';
  
  // AI计划相关接口
  static const String aiStartPlan = '/ai/start-plan';
  static const String aiContinuePlan = '/ai/continue-plan';
  static const String aiConfirmPlan = '/ai/confirm-plan';
  
  // 反思相关接口
  static const String reflectionLogs = '/reflection/logs';
  static const String reflectionRun = '/reflection/run';
  
  // 好友相关接口
  static const String friends = '/friends';
  static const String friendTasks = '/friends';
  
  // 反馈相关接口
  static const String feedback = '/feedback';
}

/// 存储键名
class StorageKeys {
  static const String accessToken = 'access_token';
  static const String tokenType = 'token_type';
  static const String userId = 'user_id';
  static const String username = 'username';
}
