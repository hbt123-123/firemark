import 'package:flutter/material.dart';
import '../models/task.dart';
import '../models/comment.dart';
import '../services/api_service.dart';

/// 任务详情页面
class TaskDetailScreen extends StatefulWidget {
  final int taskId;

  const TaskDetailScreen({super.key, required this.taskId});

  @override
  State<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends State<TaskDetailScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _commentController = TextEditingController();
  
  Task? _task;
  List<Comment> _comments = [];
  bool _isLoading = true;
  bool _isLoadingComments = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTask();
    _loadComments();
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  Future<void> _loadTask() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final task = await _apiService.getTask(widget.taskId);
      setState(() {
        _task = task;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _loadComments() async {
    setState(() {
      _isLoadingComments = true;
    });

    try {
      final comments = await _apiService.getTaskComments(widget.taskId);
      setState(() {
        _comments = comments;
        _isLoadingComments = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingComments = false;
      });
      // 静默失败，不影响主流程
    }
  }

  Future<void> _toggleComplete() async {
    if (_task == null) return;

    try {
      Task updatedTask;
      if (_task!.status == TaskStatus.completed) {
        updatedTask = await _apiService.updateTask(
          _task!.id,
          status: TaskStatus.pending,
        );
      } else {
        updatedTask = await _apiService.completeTask(_task!.id);
      }
      setState(() {
        _task = updatedTask;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(updatedTask.status == TaskStatus.completed
                ? '任务已完成'
                : '任务已标记为未完成'),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('操作失败: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _deleteTask() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认删除'),
        content: const Text('确定要删除这个任务吗?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('删除', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true && mounted) {
      try {
        await _apiService.deleteTask(widget.taskId);
        if (mounted) {
          Navigator.pop(context, true);
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('删除失败: $e'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  Future<void> _postComment() async {
    final content = _commentController.text.trim();
    if (content.isEmpty) return;

    try {
      await _apiService.createComment(
        widget.taskId,
        content: content,
        type: CommentType.comment,
      );
      _commentController.clear();
      await _loadComments();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('评论已发布')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('发布失败: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _postLike() async {
    try {
      await _apiService.createComment(
        widget.taskId,
        content: '👍',
        type: CommentType.like,
      );
      await _loadComments();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('点赞成功')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('点赞失败: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('任务详情'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete),
            onPressed: _deleteTask,
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: _buildBody(),
          ),
          _buildCommentInput(),
        ],
      ),
    );
  }

  Widget _buildBody() {
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
            ElevatedButton(
              onPressed: _loadTask,
              child: const Text('重试'),
            ),
          ],
        ),
      );
    }

    if (_task == null) {
      return const Center(child: Text('任务不存在'));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 状态和优先级
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _getStatusColor(_task!.status).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: _getStatusColor(_task!.status),
                  ),
                ),
                child: Text(
                  _task!.status.displayName,
                  style: TextStyle(
                    color: _getStatusColor(_task!.status),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: _getPriorityColor(_task!.priority).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.flag,
                      size: 16,
                      color: _getPriorityColor(_task!.priority),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      '${_task!.priority.displayName}优先级',
                      style: TextStyle(
                        color: _getPriorityColor(_task!.priority),
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // 标题
          Text(
            _task!.title,
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),

          // 时间信息
          if (_task!.dueDate != null || _task!.dueTime != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Icon(
                      Icons.access_time,
                      color: Theme.of(context).primaryColor,
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (_task!.dueDate != null)
                          Text(
                            '截止日期: ${_task!.dueDate}',
                            style: const TextStyle(fontWeight: FontWeight.w500),
                          ),
                        if (_task!.dueTime != null)
                          Text(
                            '截止时间: ${_task!.dueTime}',
                            style: TextStyle(color: Colors.grey[600]),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 16),

          // 描述
          if (_task!.description != null && _task!.description!.isNotEmpty) ...[
            Text(
              '描述',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Text(_task!.description!),
              ),
            ),
            const SizedBox(height: 16),
          ],

          // 创建时间
          if (_task!.createdAt != null) ...[
            Text(
              '创建时间',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _formatDateTime(_task!.createdAt!),
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 24),
          ],

          // 评论列表
          _buildCommentsSection(),
        ],
      ),
    );
  }

  Widget _buildCommentsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              '评论',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(width: 8),
            if (_comments.isNotEmpty)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.grey[200],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  '${_comments.length}',
                  style: const TextStyle(fontSize: 12),
                ),
              ),
          ],
        ),
        const SizedBox(height: 12),

        if (_isLoadingComments)
          const Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            ),
          )
        else if (_comments.isEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Center(
                child: Column(
                  children: [
                    Icon(Icons.chat_bubble_outline, size: 40, color: Colors.grey[400]),
                    const SizedBox(height: 8),
                    Text(
                      '暂无评论',
                      style: TextStyle(color: Colors.grey[600]),
                    ),
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
            itemBuilder: (context, index) {
              return _buildCommentItem(_comments[index]);
            },
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
                style: TextStyle(
                  fontSize: 14,
                  color: isLike ? Colors.red : Colors.blue,
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        comment.username ?? '用户',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(width: 8),
                      if (isLike)
                        const Text('👍', style: TextStyle(fontSize: 16)),
                      const Spacer(),
                      if (comment.createdAt != null)
                        Text(
                          _formatDateTime(comment.createdAt!),
                          style: TextStyle(fontSize: 12, color: Colors.grey[500]),
                        ),
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

  Widget _buildCommentInput() {
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          top: BorderSide(color: Colors.grey[300]!),
        ),
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _commentController,
                decoration: InputDecoration(
                  hintText: '发表评论...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                ),
                maxLines: null,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _postComment(),
              ),
            ),
            const SizedBox(width: 8),
            // 点赞按钮
            IconButton(
              icon: const Text('👍', style: TextStyle(fontSize: 24)),
              onPressed: _postLike,
              tooltip: '点赞',
            ),
            // 发送按钮
            IconButton(
              icon: Icon(
                Icons.send,
                color: Theme.of(context).primaryColor,
              ),
              onPressed: _postComment,
              tooltip: '发送',
            ),
          ],
        ),
      ),
    );
  }

  String _formatDateTime(DateTime dt) {
    final now = DateTime.now();
    final diff = now.difference(dt);

    if (diff.inMinutes < 1) {
      return '刚刚';
    } else if (diff.inHours < 1) {
      return '${diff.inMinutes}分钟前';
    } else if (diff.inDays < 1) {
      return '${diff.inHours}小时前';
    } else if (diff.inDays < 7) {
      return '${diff.inDays}天前';
    } else {
      return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')}';
    }
  }

  Color _getStatusColor(TaskStatus status) {
    switch (status) {
      case TaskStatus.completed:
        return Colors.green;
      case TaskStatus.skipped:
        return Colors.grey;
      case TaskStatus.pending:
        return Colors.orange;
    }
  }

  Color _getPriorityColor(TaskPriority priority) {
    switch (priority) {
      case TaskPriority.high:
        return Colors.red;
      case TaskPriority.medium:
        return Colors.orange;
      case TaskPriority.low:
        return Colors.blue;
    }
  }
}
