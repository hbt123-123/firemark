import 'package:flutter/material.dart';
import '../models/goal.dart';
import '../models/reflection.dart';
import '../services/api_service.dart';

/// 目标详情页面
class GoalDetailScreen extends StatefulWidget {
  final int goalId;

  const GoalDetailScreen({super.key, required this.goalId});

  @override
  State<GoalDetailScreen> createState() => _GoalDetailScreenState();
}

class _GoalDetailScreenState extends State<GoalDetailScreen> with SingleTickerProviderStateMixin {
  final ApiService _apiService = ApiService();
  late TabController _tabController;
  
  Goal? _goal;
  GoalOutline? _outline;
  List<ReflectionLog> _reflectionLogs = [];
  bool _isLoading = true;
  bool _isLoadingReflections = false;
  bool _isRunningReflection = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadGoal();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadGoal() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final goal = await _apiService.getGoal(widget.goalId);
      // 解析大纲
      final outline = goal.description != null 
          ? GoalOutline.parseFromString(goal.description)
          : GoalOutline();
      
      setState(() {
        _goal = goal;
        _outline = outline;
        _isLoading = false;
      });
      
      // 加载反思记录
      _loadReflections();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _loadReflections() async {
    setState(() {
      _isLoadingReflections = true;
    });

    try {
      final logs = await _apiService.getReflectionLogs(widget.goalId);
      setState(() {
        _reflectionLogs = logs;
        _isLoadingReflections = false;
      });
    } catch (e) {
      setState(() {
        _isLoadingReflections = false;
      });
    }
  }

  Future<void> _runReflection() async {
    setState(() {
      _isRunningReflection = true;
    });

    try {
      await _apiService.runReflection(widget.goalId);
      await _loadReflections();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('反思完成！')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('反思失败: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      setState(() {
        _isRunningReflection = false;
      });
    }
  }

  Future<void> _applyAdjustment(ReflectionLog log) async {
    try {
      await _apiService.applyReflection(log.id);
      await _loadReflections();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('调整已应用！')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('应用失败: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('目标详情'),
        centerTitle: true,
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '计划大纲'),
            Tab(text: '反思记录'),
          ],
        ),
      ),
      body: Column(
        children: [
          // 目标信息头部
          _buildHeader(),
          // Tab内容
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildOutlineTab(),
                _buildReflectionTab(),
              ],
            ),
          ),
        ],
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: ElevatedButton.icon(
            onPressed: _isRunningReflection ? null : _runReflection,
            icon: _isRunningReflection
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.psychology),
            label: Text(_isRunningReflection ? '反思中...' : '手动反思'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildHeader() {
    if (_isLoading) {
      return const LinearProgressIndicator();
    }

    if (_goal == null) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.grey.withValues(alpha: 0.1),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 标题和状态
          Row(
            children: [
              Expanded(
                child: Text(
                  _goal!.title,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              _buildStatusChip(),
            ],
          ),
          const SizedBox(height: 8),
          // 日期信息
          if (_goal!.startDate != null || _goal!.endDate != null)
            Row(
              children: [
                Icon(Icons.date_range, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 4),
                Text(
                  _formatDateRange(_goal!.startDate, _goal!.endDate),
                  style: TextStyle(color: Colors.grey[600]),
                ),
              ],
            ),
          // 进度条
          if (_goal!.progress != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: _goal!.progress!,
                      minHeight: 8,
                      backgroundColor: Colors.grey[200],
                      valueColor: AlwaysStoppedAnimation<Color>(
                        _getProgressColor(_goal!.progress!),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Text(
                  '${_goal!.progressPercent}%',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: _getProgressColor(_goal!.progress!),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatusChip() {
    Color color;
    if (_goal!.progress != null && _goal!.progress! >= 1.0) {
      color = Colors.green;
    } else if (!_goal!.isActive) {
      color = Colors.grey;
    } else {
      color = Colors.blue;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        _goal!.statusText,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }

  /// 计划大纲Tab
  Widget _buildOutlineTab() {
    if (_outline == null || _outline!.milestones.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.list_alt, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              '暂无计划大纲',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _outline!.milestones.length,
      itemBuilder: (context, index) {
        return _buildMilestoneCard(_outline!.milestones[index], index);
      },
    );
  }

  Widget _buildMilestoneCard(Milestone milestone, int index) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        leading: CircleAvatar(
          backgroundColor: milestone.isCompleted ? Colors.green : Colors.blue[100],
          child: Text(
            '${index + 1}',
            style: TextStyle(
              color: milestone.isCompleted ? Colors.white : Colors.blue,
            ),
          ),
        ),
        title: Text(
          milestone.title,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        children: milestone.tasks.map((task) {
          return ListTile(
            leading: Icon(
              task.isCompleted ? Icons.check_circle : Icons.circle_outlined,
              color: task.isCompleted ? Colors.green : Colors.grey,
            ),
            title: Text(
              task.title,
              style: TextStyle(
                decoration: task.isCompleted ? TextDecoration.lineThrough : null,
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  /// 反思记录Tab
  Widget _buildReflectionTab() {
    if (_isLoadingReflections) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_reflectionLogs.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.psychology_outlined, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              '暂无反思记录',
              style: TextStyle(color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              '点击下方按钮生成反思',
              style: TextStyle(color: Colors.grey[500], fontSize: 12),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _reflectionLogs.length,
      itemBuilder: (context, index) {
        return _buildReflectionCard(_reflectionLogs[index]);
      },
    );
  }

  Widget _buildReflectionCard(ReflectionLog log) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 时间
            Row(
              children: [
                Icon(Icons.access_time, size: 16, color: Colors.grey[600]),
                const SizedBox(width: 4),
                Text(
                  _formatDateTime(log.createdAt),
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
                const Spacer(),
                if (log.isApplied)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.green.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      '已应用',
                      style: TextStyle(color: Colors.green, fontSize: 12),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            // 分析摘要
            if (log.analysisSummary != null) ...[
              const Text(
                '分析摘要',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text(log.analysisSummary!),
              const SizedBox(height: 12),
            ],
            // 调整方案
            if (log.adjustmentPlan != null) ...[
              const Text(
                '调整方案',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 4),
              Text(log.adjustmentPlan!),
              const SizedBox(height: 12),
            ],
            // 应用按钮
            if (!log.isApplied)
              Align(
                alignment: Alignment.centerRight,
                child: ElevatedButton.icon(
                  onPressed: () => _applyAdjustment(log),
                  icon: const Icon(Icons.check, size: 18),
                  label: const Text('应用调整'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  ),
                ),
              ),
          ],
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

  String _formatDateTime(DateTime dt) {
    return '${dt.year}-${dt.month.toString().padLeft(2, '0')}-${dt.day.toString().padLeft(2, '0')} '
        '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
  }

  Color _getProgressColor(double progress) {
    if (progress >= 1.0) return Colors.green;
    if (progress >= 0.5) return Colors.blue;
    if (progress >= 0.25) return Colors.orange;
    return Colors.red;
  }
}
