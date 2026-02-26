import 'package:flutter/material.dart';
import '../models/task.dart';
import '../services/api_service.dart';
import 'task_detail_screen.dart';

/// 任务页面
class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
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

  /// 格式化日期为 YYYY-MM-DD
  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  /// 加载任务列表
  Future<void> _loadTasks() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _apiService.getTasks(
        dueDate: _formatDate(_selectedDate),
      );
      setState(() {
        _tasks = response.tasks;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// 切换日期
  void _changeDate(int days) {
    setState(() {
      _selectedDate = _selectedDate.add(Duration(days: days));
    });
    _loadTasks();
  }

  /// 选择日期
  Future<void> _selectDate() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
    );
    if (date != null) {
      setState(() {
        _selectedDate = date;
      });
      _loadTasks();
    }
  }

  /// 切换任务完成状态
  Future<void> _toggleTaskComplete(Task task) async {
    try {
      Task updatedTask;
      if (task.status == TaskStatus.completed) {
        // 标记为未完成
        updatedTask = await _apiService.updateTask(
          task.id,
          status: TaskStatus.pending,
        );
      } else {
        // 完成任务
        updatedTask = await _apiService.completeTask(task.id);
      }

      // 更新本地列表
      setState(() {
        final index = _tasks.indexWhere((t) => t.id == task.id);
        if (index != -1) {
          _tasks[index] = updatedTask;
        }
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

  /// 删除任务
  Future<void> _deleteTask(Task task) async {
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

    if (confirm == true) {
      try {
        await _apiService.deleteTask(task.id);
        setState(() {
          _tasks.removeWhere((t) => t.id == task.id);
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('任务已删除')),
          );
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

  /// 跳转到详情页
  void _navigateToDetail(Task task) async {
    final result = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) => TaskDetailScreen(taskId: task.id),
      ),
    );

    // 如果任务被删除，刷新列表
    if (result == true) {
      _loadTasks();
    } else {
      // 刷新任务状态
      _loadTasks();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('任务'),
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
          // 日期选择器
          _buildDateSelector(),
          // 任务列表
          Expanded(
            child: _buildTaskList(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('创建任务功能开发中'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  /// 构建日期选择器

  /// 构建日期选择器
  Widget _buildDateSelector() {
    final isToday = _isToday(_selectedDate);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        border: Border(
          bottom: BorderSide(color: Colors.grey[300]!),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // 左箭头
          IconButton(
            icon: const Icon(Icons.chevron_left),
            onPressed: () => _changeDate(-1),
          ),
          // 日期显示
          InkWell(
            onTap: _selectDate,
            borderRadius: BorderRadius.circular(8),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: isToday
                    ? Theme.of(context).primaryColor
                    : Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(
                  color: isToday
                      ? Theme.of(context).primaryColor
                      : Colors.grey[300]!,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    Icons.calendar_today,
                    size: 18,
                    color: isToday ? Colors.white : Colors.grey[700],
                  ),
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
          // 右箭头
          IconButton(
            icon: const Icon(Icons.chevron_right),
            onPressed: () => _changeDate(1),
          ),
        ],
      ),
    );
  }

  /// 构建任务列表
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
            ElevatedButton(
              onPressed: _loadTasks,
              child: const Text('重试'),
            ),
          ],
        ),
      );
    }

    if (_tasks.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.inbox,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              '暂无任务',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(8),
      itemCount: _tasks.length,
      itemBuilder: (context, index) {
        return _buildTaskItem(_tasks[index]);
      },
    );
  }

  /// 构建任务项
  Widget _buildTaskItem(Task task) {
    final isCompleted = task.status == TaskStatus.completed;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      child: InkWell(
        onTap: () => _navigateToDetail(task),
        onLongPress: () => _deleteTask(task),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // 复选框
              Checkbox(
                value: isCompleted,
                onChanged: (_) => _toggleTaskComplete(task),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(4),
                ),
                activeColor: Colors.green,
              ),
              // 优先级标志
              Container(
                width: 4,
                height: 40,
                decoration: BoxDecoration(
                  color: _getPriorityColor(task.priority),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
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
                        decoration: isCompleted
                            ? TextDecoration.lineThrough
                            : null,
                        color: isCompleted ? Colors.grey : null,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    if (task.displayTime != null) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Icon(
                            Icons.access_time,
                            size: 14,
                            color: Colors.grey[500],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            task.displayTime!,
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[500],
                            ),
                          ),
                        ],
                      ),
                    ],
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
                  style: TextStyle(
                    fontSize: 12,
                    color: _getPriorityColor(task.priority),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  /// 检查是否是今天
  bool _isToday(DateTime date) {
    final now = DateTime.now();
    return date.year == now.year &&
        date.month == now.month &&
        date.day == now.day;
  }

  /// 获取优先级颜色
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
