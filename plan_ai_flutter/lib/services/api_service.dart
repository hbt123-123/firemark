import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/user.dart';
import '../models/fixed_schedule.dart';
import '../models/task.dart';
import '../models/comment.dart';
import '../models/goal.dart';
import '../models/reflection.dart';
import '../utils/constants.dart';

/// API异常类
class ApiException implements Exception {
  final String message;
  final int? statusCode;

  ApiException(this.message, {this.statusCode});

  @override
  String toString() => message;

  bool get isUnauthorized => statusCode == 401;
}

/// API服务客户端
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  String? _token;
  final http.Client _client = http.Client();
  
  // Timeout duration
  static const Duration _timeout = Duration(seconds: 30);

  // Callback for 401 unauthorized
  Function()? onUnauthorized;

  void setToken(String? token) {
    _token = token;
  }

  Map<String, String> get _headers {
    final headers = <String, String>{
      'Content-Type': 'application/json',
    };
    if (_token != null && _token!.isNotEmpty) {
      headers['Authorization'] = 'Bearer $_token';
    }
    return headers;
  }

  Future<dynamic> get(String endpoint) async {
    try {
      final response = await _client.get(
        Uri.parse('${ApiConstants.baseUrl}$endpoint'),
        headers: _headers,
      ).timeout(_timeout);
      return _handleResponse(response);
    } on TimeoutException {
      throw ApiException('请求超时，请检查网络');
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> post(String endpoint, {Map<String, dynamic>? data}) async {
    try {
      final response = await _client.post(
        Uri.parse('${ApiConstants.baseUrl}$endpoint'),
        headers: _headers,
        body: data != null ? jsonEncode(data) : null,
      ).timeout(_timeout);
      return _handleResponse(response);
    } on TimeoutException {
      throw ApiException('请求超时，请检查网络');
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> put(String endpoint, {Map<String, dynamic>? data}) async {
    try {
      final response = await _client.put(
        Uri.parse('${ApiConstants.baseUrl}$endpoint'),
        headers: _headers,
        body: data != null ? jsonEncode(data) : null,
      ).timeout(_timeout);
      return _handleResponse(response);
    } on TimeoutException {
      throw ApiException('请求超时，请检查网络');
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> delete(String endpoint) async {
    try {
      final response = await _client.delete(
        Uri.parse('${ApiConstants.baseUrl}$endpoint'),
        headers: _headers,
      ).timeout(_timeout);
      return _handleResponse(response);
    } on TimeoutException {
      throw ApiException('请求超时，请检查网络');
    } catch (e) {
      throw _handleError(e);
    }
  }

  Future<dynamic> postForm(String endpoint, Map<String, String> formData) async {
    try {
      final headers = <String, String>{
        'Content-Type': 'application/x-www-form-urlencoded',
      };
      if (_token != null && _token!.isNotEmpty) {
        headers['Authorization'] = 'Bearer $_token';
      }
      
      final response = await _client.post(
        Uri.parse('${ApiConstants.baseUrl}$endpoint'),
        headers: headers,
        body: formData,
      ).timeout(_timeout);
      return _handleResponse(response);
    } on TimeoutException {
      throw ApiException('请求超时，请检查网络');
    } catch (e) {
      throw _handleError(e);
    }
  }

  dynamic _handleResponse(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      if (response.body.isEmpty) {
        return {'success': true};
      }
      return jsonDecode(response.body);
    } else {
      // Handle 401 - Token expired
      if (response.statusCode == 401) {
        final exception = _parseError(response);
        onUnauthorized?.call();
        throw exception;
      }
      throw _parseError(response);
    }
  }

  ApiException _parseError(http.Response response) {
    String message;
    try {
      final body = jsonDecode(response.body);
      message = body['detail'] ?? body['error'] ?? body['message'] ?? '请求失败';
    } catch (_) {
      message = '请求失败 (${response.statusCode})';
    }
    return ApiException(message, statusCode: response.statusCode);
  }

  ApiException _handleError(dynamic error) {
    if (error is ApiException) {
      return error;
    }
    return ApiException('网络错误: ${error.toString()}');
  }

  // ============ 认证相关API ============
  Future<UserResponse> register(String username, String password) async {
    final response = await post(ApiConstants.register, data: {'username': username, 'password': password});
    if (response is Map<String, dynamic>) {
      if (response.containsKey('detail')) throw ApiException(response['detail'].toString());
      return UserResponse.fromJson(response);
    }
    throw ApiException('注册失败: 未知错误');
  }

  Future<TokenResponse> login(String username, String password) async {
    final response = await post(ApiConstants.login, data: {'username': username, 'password': password});
    if (response is Map<String, dynamic>) {
      if (response.containsKey('detail')) throw ApiException(response['detail'].toString());
      if (response.containsKey('error')) throw ApiException(response['error'].toString());
      return TokenResponse.fromJson(response);
    }
    throw ApiException('登录失败: 未知错误');
  }

  Future<TokenResponse> loginForm(String username, String password) async {
    final response = await postForm(ApiConstants.loginForm, {'username': username, 'password': password});
    if (response is Map<String, dynamic>) {
      if (response.containsKey('detail')) throw ApiException(response['detail'].toString());
      if (response.containsKey('error')) throw ApiException(response['error'].toString());
      return TokenResponse.fromJson(response);
    }
    throw ApiException('登录失败: 未知错误');
  }

  Future<UserResponse> getCurrentUser() async {
    final response = await get(ApiConstants.me);
    if (response is Map<String, dynamic>) return UserResponse.fromJson(response);
    throw ApiException('获取用户信息失败');
  }

  // ============ 固定日程相关API ============
  Future<List<FixedSchedule>> getFixedSchedules() async {
    final response = await get(ApiConstants.fixedSchedules);
    if (response is List) {
      return response.map((item) => FixedSchedule.fromJson(item as Map<String, dynamic>)).toList();
    }
    throw ApiException('获取固定日程失败');
  }

  Future<FixedSchedule> getFixedSchedule(int id) async {
    final response = await get('${ApiConstants.fixedSchedules}/$id');
    if (response is Map<String, dynamic>) return FixedSchedule.fromJson(response);
    throw ApiException('获取固定日程失败');
  }

  Future<FixedSchedule> createFixedSchedule({
    required String title, String? description, required int dayOfWeek,
    required String startTime, required String endTime, RepeatRule repeatRule = RepeatRule.none,
  }) async {
    final response = await post(ApiConstants.fixedSchedules, data: {
      'title': title, 'description': description, 'day_of_week': dayOfWeek,
      'start_time': startTime, 'end_time': endTime, 'repeat_rule': repeatRule.apiValue,
    });
    if (response is Map<String, dynamic>) return FixedSchedule.fromJson(response);
    throw ApiException('创建固定日程失败');
  }

  Future<FixedSchedule> updateFixedSchedule(int id, {String? title, String? description, int? dayOfWeek, String? startTime, String? endTime, RepeatRule? repeatRule}) async {
    final data = <String, dynamic>{};
    if (title != null) data['title'] = title;
    if (description != null) data['description'] = description;
    if (dayOfWeek != null) data['day_of_week'] = dayOfWeek;
    if (startTime != null) data['start_time'] = startTime;
    if (endTime != null) data['end_time'] = endTime;
    if (repeatRule != null) data['repeat_rule'] = repeatRule.apiValue;
    final response = await put('${ApiConstants.fixedSchedules}/$id', data: data);
    if (response is Map<String, dynamic>) return FixedSchedule.fromJson(response);
    throw ApiException('更新固定日程失败');
  }

  Future<bool> deleteFixedSchedule(int id) async {
    final response = await delete('${ApiConstants.fixedSchedules}/$id');
    if (response is Map<String, dynamic>) return response['success'] == true;
    return true;
  }

  // ============ 任务相关API ============
  Future<TaskListResponse> getTasks({String? status, String? dueDate, int? goalId, int? priority, int skip = 0, int limit = 20}) async {
    final queryParams = <String, String>{};
    if (status != null) queryParams['status'] = status;
    if (dueDate != null) queryParams['due_date'] = dueDate;
    if (goalId != null) queryParams['goal_id'] = goalId.toString();
    if (priority != null) queryParams['priority'] = priority.toString();
    queryParams['skip'] = skip.toString();
    queryParams['limit'] = limit.toString();
    final queryString = queryParams.entries.map((e) => '${e.key}=${e.value}').join('&');
    final response = await get('${ApiConstants.tasks}?$queryString');
    if (response is Map<String, dynamic>) return TaskListResponse.fromJson(response);
    throw ApiException('获取任务列表失败');
  }

  Future<TaskListResponse> getTodayTasks() async {
    final response = await get('${ApiConstants.tasks}/today');
    if (response is Map<String, dynamic>) return TaskListResponse.fromJson(response);
    throw ApiException('获取今日任务失败');
  }

  Future<Task> getTask(int id) async {
    final response = await get('${ApiConstants.tasks}/$id');
    if (response is Map<String, dynamic>) return Task.fromJson(response);
    throw ApiException('获取任务失败');
  }

  Future<Task> createTask({required String title, String? description, String? dueDate, String? dueTime, int? goalId, TaskPriority priority = TaskPriority.medium, List<int> dependencies = const []}) async {
    final response = await post(ApiConstants.tasks, data: {
      'title': title, 'description': description, 'due_date': dueDate, 'due_time': dueTime,
      'goal_id': goalId, 'priority': priority.value, 'dependencies': dependencies,
    });
    if (response is Map<String, dynamic>) return Task.fromJson(response);
    throw ApiException('创建任务失败');
  }

  Future<Task> updateTask(int id, {String? title, String? description, String? dueDate, String? dueTime, TaskStatus? status, TaskPriority? priority}) async {
    final data = <String, dynamic>{};
    if (title != null) data['title'] = title;
    if (description != null) data['description'] = description;
    if (dueDate != null) data['due_date'] = dueDate;
    if (dueTime != null) data['due_time'] = dueTime;
    if (status != null) data['status'] = status.apiValue;
    if (priority != null) data['priority'] = priority.value;
    final response = await put('${ApiConstants.tasks}/$id', data: data);
    if (response is Map<String, dynamic>) return Task.fromJson(response);
    throw ApiException('更新任务失败');
  }

  Future<bool> deleteTask(int id) async {
    final response = await delete('${ApiConstants.tasks}/$id');
    if (response is Map<String, dynamic>) return response['success'] == true;
    return true;
  }

  Future<Task> completeTask(int id) async {
    final response = await post('${ApiConstants.tasks}/$id/complete');
    if (response is Map<String, dynamic>) return Task.fromJson(response);
    throw ApiException('完成任务失败');
  }

  Future<Task> skipTask(int id) async {
    final response = await post('${ApiConstants.tasks}/$id/skip');
    if (response is Map<String, dynamic>) return Task.fromJson(response);
    throw ApiException('跳过任务失败');
  }

  // ============ 评论相关API ============
  Future<List<Comment>> getTaskComments(int taskId) async {
    final response = await get('${ApiConstants.tasks}/$taskId${ApiConstants.comments}');
    if (response is List) return response.map((item) => Comment.fromJson(item as Map<String, dynamic>)).toList();
    throw ApiException('获取评论列表失败');
  }

  Future<Comment> createComment(int taskId, {required String content, CommentType type = CommentType.comment}) async {
    final response = await post('${ApiConstants.tasks}/$taskId${ApiConstants.comments}', data: {'content': content, 'type': type.apiValue});
    if (response is Map<String, dynamic>) return Comment.fromJson(response);
    throw ApiException('发表评论失败');
  }

  Future<bool> deleteComment(int taskId, int commentId) async {
    final response = await delete('${ApiConstants.tasks}/$taskId${ApiConstants.comments}/$commentId');
    if (response is Map<String, dynamic>) return response['success'] == true;
    return true;
  }

  // ============ 目标相关API ============
  Future<List<Goal>> getGoals() async {
    final response = await get(ApiConstants.goals);
    if (response is List) return response.map((item) => Goal.fromJson(item as Map<String, dynamic>)).toList();
    throw ApiException('获取目标列表失败');
  }

  Future<Goal> getGoal(int id) async {
    final response = await get('${ApiConstants.goals}/$id');
    if (response is Map<String, dynamic>) return Goal.fromJson(response);
    throw ApiException('获取目标失败');
  }

  Future<Goal> createGoal({required String title, String? description, DateTime? startDate, DateTime? endDate}) async {
    final response = await post(ApiConstants.goals, data: {
      'title': title, 'description': description,
      'start_date': startDate?.toIso8601String().split('T')[0],
      'end_date': endDate?.toIso8601String().split('T')[0],
    });
    if (response is Map<String, dynamic>) return Goal.fromJson(response);
    throw ApiException('创建目标失败');
  }

  Future<Goal> updateGoal(int id, {String? title, String? description, DateTime? startDate, DateTime? endDate, double? progress}) async {
    final data = <String, dynamic>{};
    if (title != null) data['title'] = title;
    if (description != null) data['description'] = description;
    if (startDate != null) data['start_date'] = startDate.toIso8601String().split('T')[0];
    if (endDate != null) data['end_date'] = endDate.toIso8601String().split('T')[0];
    if (progress != null) data['progress'] = progress;
    final response = await put('${ApiConstants.goals}/$id', data: data);
    if (response is Map<String, dynamic>) return Goal.fromJson(response);
    throw ApiException('更新目标失败');
  }

  Future<bool> deleteGoal(int id) async {
    final response = await delete('${ApiConstants.goals}/$id');
    if (response is Map<String, dynamic>) return response['success'] == true;
    return true;
  }

  // ============ AI计划相关API ============
  Future<AIPlanResponse> startAIPlan(String initialGoal) async {
    final response = await post(ApiConstants.aiStartPlan, data: {'goal': initialGoal});
    if (response is Map<String, dynamic>) return AIPlanResponse.fromJson(response);
    throw ApiException('AI计划启动失败');
  }

  Future<AIPlanResponse> continueAIPlan(String sessionId, String userResponse) async {
    final response = await post(ApiConstants.aiContinuePlan, data: {'session_id': sessionId, 'message': userResponse});
    if (response is Map<String, dynamic>) return AIPlanResponse.fromJson(response);
    throw ApiException('AI对话失败');
  }

  Future<Goal> confirmAIPlan(String sessionId) async {
    final response = await post(ApiConstants.aiConfirmPlan, data: {'session_id': sessionId});
    if (response is Map<String, dynamic>) return Goal.fromJson(response);
    throw ApiException('确认计划失败');
  }

  // ============ 反思相关API ============
  Future<List<ReflectionLog>> getReflectionLogs(int goalId) async {
    final response = await get('${ApiConstants.reflectionLogs}?goal_id=$goalId');
    if (response is List) return response.map((item) => ReflectionLog.fromJson(item as Map<String, dynamic>)).toList();
    throw ApiException('获取反思记录失败');
  }

  Future<ReflectionLog> runReflection(int goalId) async {
    final response = await post('${ApiConstants.reflectionRun}?goal_id=$goalId');
    if (response is Map<String, dynamic>) return ReflectionLog.fromJson(response);
    throw ApiException('反思生成失败');
  }

  Future<ReflectionLog> applyReflection(int reflectionId) async {
    final response = await post('${ApiConstants.reflectionLogs}/$reflectionId/apply');
    if (response is Map<String, dynamic>) return ReflectionLog.fromJson(response);
    throw ApiException('应用调整失败');
  }

  // ============ 好友相关API ============
  Future<List<Map<String, dynamic>>> getFriends() async {
    final response = await get(ApiConstants.friends);
    if (response is List) return response.map((item) => item as Map<String, dynamic>).toList();
    throw ApiException('获取好友列表失败');
  }

  Future<List<Task>> getFriendTasks(int friendId, String date) async {
    final response = await get('${ApiConstants.friendTasks}/$friendId/tasks?date=$date');
    if (response is List) return response.map((item) => Task.fromJson(item as Map<String, dynamic>)).toList();
    throw ApiException('获取好友任务失败');
  }

  Future<Map<String, dynamic>> getFriendTaskDetail(int friendId, int taskId) async {
    final response = await get('${ApiConstants.friendTasks}/$friendId/tasks/$taskId');
    if (response is Map<String, dynamic>) return response;
    throw ApiException('获取任务详情失败');
  }

  // ============ 反馈相关API ============
  Future<bool> submitFeedback({required String type, required String content, int? rating, String? featureId}) async {
    final response = await post(ApiConstants.feedback, data: {
      'type': type, 'content': content, 'rating': rating, 'feature_id': featureId,
    });
    if (response is Map<String, dynamic>) return response['success'] == true;
    return true;
  }

  // ============ 单词学习相关API ============
  Future<List<String>> getWordBankTypes() async {
    final response = await get('/words/bank-types');
    if (response is List) return response.map((e) => e.toString()).toList();
    throw ApiException('获取词库类型失败');
  }

  Future<Map<String, dynamic>> getWordSettings() async {
    final response = await get('/words/settings');
    if (response is Map<String, dynamic>) return response;
    throw ApiException('获取设置失败');
  }

  Future<bool> saveWordSettings({
    required List<String> bankTypes, required int dailyCount,
    required int englishRepeat, required int chineseRepeat, bool enableReminder = false,
  }) async {
    final response = await post('/words/settings', data: {
      'bank_types': bankTypes, 'daily_count': dailyCount,
      'english_repeat': englishRepeat, 'chinese_repeat': chineseRepeat,
      'enable_reminder': enableReminder,
    });
    if (response is Map<String, dynamic>) return response['success'] == true;
    return true;
  }

  Future<Map<String, dynamic>> getDailyWords({String? date}) async {
    final endpoint = date != null ? '/words/daily?date=$date' : '/words/daily';
    final response = await get(endpoint);
    if (response is Map<String, dynamic>) return response;
    throw ApiException('获取每日单词失败');
  }

  Future<bool> completeWord({required int wordId, required String date}) async {
    final response = await post('/words/daily/complete', data: {'word_id': wordId, 'date': date});
    if (response is Map<String, dynamic>) return response['success'] == true;
    return true;
  }

  Future<bool> hasWordSettings() async {
    try {
      final response = await get('/words/settings');
      if (response is Map<String, dynamic>) {
        final bankTypes = response['bank_types'] as List<dynamic>?;
        return bankTypes != null && bankTypes.isNotEmpty;
      }
    } catch (e) {
      // ignore
    }
    return false;
  }

  // ============ 单词统计相关API ============
  Future<Map<String, dynamic>> getWordStats({required String startDate, required String endDate}) async {
    final response = await get('/words/stats?start_date=$startDate&end_date=$endDate');
    if (response is Map<String, dynamic>) return response;
    throw ApiException('获取统计数据失败');
  }
}
