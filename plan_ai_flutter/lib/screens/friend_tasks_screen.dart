import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/task.dart';
import '../models/comment.dart';
import 'task_detail_screen.dart';

/// 好友任务页面
class FriendTasksScreen extends StatefulWidget {
  final int friendId;
  final String friendName;

  const FriendTasksScreen({
    super.key,
    required this.friendId,
    required this.friendName,
  });

  @override
  State<FriendTasksScreen> createState() => _FriendTasksScreenState();
}

class _FriendTasksScreenState extends State<FriendTasksScreen> {
  final ApiService _apiService = ApiService();
  List<Task> _tasks = [];
  bool _isLoading = true;
  String? _error;
  DateTime _selectedDate = DateTime.now();

  @override
  void initState() {
    super.initState();
    _loadTasks();
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  Future<void> _loadTasks() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final tasks = await _apiService.getFriendTasks(
        widget.friendId,
        _formatDate(_selectedDate),
      );
      setState(() {
        _tasks = tasks;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _changeDate(int days) {
    setState(() {
      _selectedDate = _selectedDate.add(Duration(days: days));
    });
    _loadTasks();
  }

  void _navigateToDetail(Task task) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => FriendTaskDetailScreen(
          friendId: widget.friendId,
          friendName: widget.friendName,
          taskId: task.id,
        ),
      ),
    );
    // 刷新任务列表
    _loadTasks();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.friendName}的任务'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadTasks,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildDateSelector(),
          Expanded(child: _buildTaskList()),
        ],
      ),
    );
  }

  Widget _buildDateSelector() {
    final isToday = _isToday(_selectedDate);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        border: Border(bottom: BorderSide(color: Colors.grey[300]!)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            onPressed: () => _changeDate(-1),
          ),
          InkWell(
            onTap: () async {
              final date = await showDatePicker(
                context: context,
                initialDate: _selectedDate,
                firstDate: DateTime(2020),
                lastDate: DateTime(2030),
              );
              if (date != null) {
                setState(() => _selectedDate = date);
                _loadTasks();
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: isToday ? Theme.of(context).primaryColor : Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: isToday ? Theme.of(context).primaryColor : Colors.grey[300]!,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.calendar_today, size: 18, color: isToday ? Colors.white : Colors.grey[700]),
                  const SizedBox(width: 8),
                  Text(
                    isToday ? '今天' : _formatDate(_selectedDate),
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: isToday ? Colors.white : Colors.grey[700],
                    ),
                  ),
                ],
              ),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            onPressed: () => _changeDate(1),
          ),
        ],
      ),
    );
  }

  Widget _buildTaskList() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('加载失败: $_error', style: const TextStyle(color: Colors.red)),
            const SizedBox(height: 16),
            ElevatedButton(onPressed: _loadTasks, child: const Text('重试')),
          ],
        ),
      );
    }

    if (_tasks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.task_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text('今日暂无任务', style: TextStyle(fontSize: 18, color: Colors.grey[600])),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: _tasks.length,
      itemBuilder: (context, index) => _buildTaskItem(_tasks[index]),
    );
  }

  Widget _buildTaskItem(Task task) {
    final isCompleted = task.status == TaskStatus.completed;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        onTap: () => _navigateToDetail(task),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // 状态图标
              Icon(
                isCompleted ? Icons.check_circle : Icons.circle_outlined,
                color: isCompleted ? Colors.green : Colors.grey,
              ),
              const SizedBox(width: 12),
              // 优先级标志
              Container(width: 4, height: 40, decoration: BoxDecoration(
                color: _getPriorityColor(task.priority),
                borderRadius: BorderRadius.circular(2),
              )),
              const SizedBox(width: 12),
              // 任务信息
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                        decoration: isCompleted ? TextDecoration.lineThrough : null,
                        color: isCompleted ? Colors.grey : null,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (task.displayTime != null)
                      Row(
                        children: [
                          Icon(Icons.access_time, size: 14, color: Colors.grey[500]),
                          const SizedBox(width: 4),
                          Text(task.displayTime!, style: TextStyle(fontSize: 12, color: Colors.grey[500])),
                        ],
                      ),
                  ],
                ),
              ),
              // 优先级标签
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getPriorityColor(task.priority).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  task.priority.displayName,
                  style: TextStyle(fontSize: 12, color: _getPriorityColor(task.priority), fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  bool _isToday(DateTime date) {
    final now = DateTime.now();
    return date.year == now.year && date.month == now.month && date.day == now.day;
  }

  Color _getPriorityColor(TaskPriority priority) {
    switch (priority) {
      case TaskPriority.high: return Colors.red;
      case TaskPriority.medium: return Colors.orange;
      case TaskPriority.low: return Colors.blue;
    }
  }
}

/// 好友任务详情页面（含评论点赞列表）
class FriendTaskDetailScreen extends StatefulWidget {
  final int friendId;
  final String friendName;
  final int taskId;

  const FriendTaskDetailScreen({
    super.key,
    required this.friendId,
    required this.friendName,
    required this.taskId,
  });

  @override
  State<FriendTaskDetailScreen> createState() => _FriendTaskDetailScreenState();
}

class _FriendTaskDetailScreenState extends State<FriendTaskDetailScreen> {
  final ApiService _apiService = ApiService();
  Task? _task;
  List<Comment> _comments = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTaskDetail();
  }

  Future<void> _loadTaskDetail() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _apiService.getFriendTaskDetail(widget.friendId, widget.taskId);
      setState(() {
        _task = Task.fromJson(response['task'] as Map<String, dynamic>);
        _comments = (response['comments'] as List<dynamic>?)
                ?.map((e) => Comment.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [];
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('任务详情'),
        centerTitle: true,
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text('加载失败: $_error', style: const TextStyle(color: Colors.red)));
    if (_task == null) return const Center(child: Text('任务不存在'));

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 任务信息
          _buildTaskInfo(),
          const SizedBox(height: 24),
          // 评论列表
          _buildCommentsSection(),
        ],
      ),
    );
  }

  Widget _buildTaskInfo() {
    final isCompleted = _task!.status == TaskStatus.completed;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 状态标签
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: (isCompleted ? Colors.green : Colors.orange).withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: isCompleted ? Colors.green : Colors.orange),
          ),
          child: Text(
            _task!.status.displayName,
            style: TextStyle(
              color: isCompleted ? Colors.green : Colors.orange,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        const SizedBox(height: 16),
        // 标题
        Text(
          _task!.title,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        // 时间信息
        if (_task!.dueDate != null || _task!.dueTime != null)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(Icons.access_time, color: Theme.of(context).primaryColor),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (_task!.dueDate != null) Text('截止日期: ${_task!.dueDate}', style: const TextStyle(fontWeight: FontWeight.w500)),
                      if (_task!.dueTime != null) Text('截止时间: ${_task!.dueTime}', style: TextStyle(color: Colors.grey[600])),
                    ],
                  ),
                ],
              ),
            ),
          ),
        // 描述
        if (_task!.description != null && _task!.description!.isNotEmpty) ...[
          const SizedBox(height: 16),
          Text('描述', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Card(child: Padding(padding: const EdgeInsets.all(16), child: Text(_task!.description!))),
        ],
      ],
    );
  }

  Widget _buildCommentsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text('评论与点赞', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(width: 8),
            if (_comments.isNotEmpty)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(color: Colors.grey[200], borderRadius: BorderRadius.circular(12)),
                child: Text('${_comments.length}', style: const TextStyle(fontSize: 12)),
              ),
          ],
        ),
        const SizedBox(height: 12),
        if (_comments.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Center(
                child: Column(
                  children: [
                    Icon(Icons.chat_bubble_outline, size: 40, color: Colors.grey[400]),
                    const SizedBox(height: 8),
                    Text('暂无评论', style: TextStyle(color: Colors.grey[600])),
                  ],
                ),
              ),
            ),
          )
        else
          ListView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _comments.length,
            itemBuilder: (context, index) => _buildCommentItem(_comments[index]),
          ),
      ],
    );
  }

  Widget _buildCommentItem(Comment comment) {
    final isLike = comment.isLike;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              radius: 16,
              backgroundColor: isLike ? Colors.red[100] : Colors.blue[100],
              child: Text(
                (comment.username ?? 'U')[0].toUpperCase(),
                style: TextStyle(fontSize: 14, color: isLike ? Colors.red : Colors.blue),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(comment.username ?? '用户', style: const TextStyle(fontWeight: FontWeight.bold)),
                      const SizedBox(width: 8),
                      if (isLike) const Text('👍', style: TextStyle(fontSize: 16)),
                      const Spacer(),
                      if (comment.createdAt != null)
                        Text(_formatDateTime(comment.createdAt!), style: TextStyle(fontSize: 12, color: Colors.grey[500])),
                    ],
                  ),
                  if (!isLike) ...[
                    const SizedBox(height: 4),
                    Text(comment.content),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);
    if (diff.inMinutes < 1) return '刚刚';
    if (diff.inHours < 1) return '${diff.inMinutes}分钟前';
    if (diff.inDays < 1) return '${diff.inHours}小时前';
    if (diff.inDays < 7) return '${diff.inDays}天前';
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
  }
}
