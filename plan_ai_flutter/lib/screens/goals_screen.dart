import 'package:flutter/material.dart';
import '../models/goal.dart';
import '../services/api_service.dart';
import 'ai_plan_screen.dart';
import 'goal_detail_screen.dart';

/// 目标页面
class GoalsScreen extends StatefulWidget {
  const GoalsScreen({super.key});

  @override
  State<GoalsScreen> createState() => _GoalsScreenState();
}

class _GoalsScreenState extends State<GoalsScreen> {
  final ApiService _apiService = ApiService();
  List<Goal> _goals = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadGoals();
  }

  Future<void> _loadGoals() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final goals = await _apiService.getGoals();
      setState(() {
        _goals = goals;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _navigateToAIPlan() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const AIPlanScreen()),
    ).then((_) {
      // AI计划创建成功后刷新列表
      _loadGoals();
    });
  }

  void _navigateToDetail(Goal goal) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => GoalDetailScreen(goalId: goal.id)),
    ).then((_) {
      _loadGoals();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('目标'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadGoals,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _navigateToAIPlan,
        icon: const Icon(Icons.auto_awesome),
        label: const Text('新建目标'),
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
              onPressed: _loadGoals,
              child: const Text('重试'),
            ),
          ],
        ),
      );
    }

    if (_goals.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.flag_outlined,
              size: 80,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              '暂无目标',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '点击右下角按钮创建新目标',
              style: TextStyle(color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _goals.length,
      itemBuilder: (context, index) {
        return _buildGoalCard(_goals[index]);
      },
    );
  }

  Widget _buildGoalCard(Goal goal) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => _navigateToDetail(goal),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 标题和状态
              Row(
                children: [
                  Expanded(
                    child: Text(
                      goal.title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  _buildStatusChip(goal),
                ],
              ),
              const SizedBox(height: 12),

              // 日期信息
              if (goal.startDate != null || goal.endDate != null)
                Row(
                  children: [
                    Icon(
                      Icons.date_range,
                      size: 16,
                      color: Colors.grey[600],
                    ),
                    const SizedBox(width: 4),
                    Text(
                      _formatDateRange(goal.startDate, goal.endDate),
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              const SizedBox(height: 12),

              // 进度条
              if (goal.progress != null) ...[
                Row(
                  children: [
                    Expanded(
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(4),
                        child: LinearProgressIndicator(
                          value: goal.progress!,
                          minHeight: 8,
                          backgroundColor: Colors.grey[200],
                          valueColor: AlwaysStoppedAnimation<Color>(
                            _getProgressColor(goal.progress!),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Text(
                      '${goal.progressPercent}%',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: _getProgressColor(goal.progress!),
                      ),
                    ),
                  ],
                ),
              ] else
                // 无进度时显示占位
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: 0,
                    minHeight: 8,
                    backgroundColor: Colors.grey[200],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusChip(Goal goal) {
    Color color;
    if (goal.progress != null && goal.progress! >= 1.0) {
      color = Colors.green;
    } else if (!goal.isActive) {
      color = Colors.grey;
    } else {
      color = Colors.blue;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        goal.statusText,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  String _formatDateRange(DateTime? start, DateTime? end) {
    if (start == null && end == null) return '';
    if (start != null && end != null) {
      return '${_formatDate(start)} - ${_formatDate(end)}';
    }
    if (start != null) return '从 ${_formatDate(start)} 开始';
    return '截止至 ${_formatDate(end!)}';
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  Color _getProgressColor(double progress) {
    if (progress >= 1.0) return Colors.green;
    if (progress >= 0.5) return Colors.blue;
    if (progress >= 0.25) return Colors.orange;
    return Colors.red;
  }
}
