import 'package:flutter/material.dart';
import '../models/fixed_schedule.dart';
import '../services/api_service.dart';

/// 日程页面 - 周视图
class ScheduleScreen extends StatefulWidget {
  const ScheduleScreen({super.key});

  @override
  State<ScheduleScreen> createState() => _ScheduleScreenState();
}

class _ScheduleScreenState extends State<ScheduleScreen> {
  final ApiService _apiService = ApiService();
  List<FixedSchedule> _schedules = [];
  bool _isLoading = true;
  String? _error;
  
  // 时间段配置
  static const int startHour = 8;
  static const int endHour = 22;
  static const int totalHours = endHour - startHour;

  @override
  void initState() {
    super.initState();
    _loadSchedules();
  }

  Future<void> _loadSchedules() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final schedules = await _apiService.getFixedSchedules();
      setState(() {
        _schedules = schedules;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// 获取某一天某一时间段的日程
  List<FixedSchedule> _getSchedulesForCell(int dayOfWeek, int hour) {
    return _schedules.where((s) {
      if (s.dayOfWeek != dayOfWeek) return false;
      
      final start = _parseTime(s.startTime);
      final end = _parseTime(s.endTime);
      return hour >= start && hour < end;
    }).toList();
  }

  /// 解析时间字符串 (HH:mm) 为小时整数
  int _parseTime(String timeStr) {
    final parts = timeStr.split(':');
    return int.tryParse(parts[0]) ?? 0;
  }

  /// 处理点击空白格子 - 添加日程
  Future<void> _onTapEmptyCell(int dayOfWeek, int hour) async {
    final result = await showDialog<FixedSchedule>(
      context: context,
      builder: (context) => AddScheduleDialog(
        initialDayOfWeek: dayOfWeek,
        initialStartHour: hour,
      ),
    );

    if (result != null) {
      try {
        await _apiService.createFixedSchedule(
          title: result.title,
          description: result.description,
          dayOfWeek: result.dayOfWeek,
          startTime: result.startTime,
          endTime: result.endTime,
          repeatRule: result.repeatRule,
        );
        await _loadSchedules();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('日程添加成功')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('添加失败: $e'), backgroundColor: Colors.red),
          );
        }
      }
    }
  }

  /// 处理点击已有日程 - 编辑/删除
  Future<void> _onTapSchedule(FixedSchedule schedule) async {
    final result = await showModalBottomSheet<String>(
      context: context,
      builder: (context) => ScheduleOptionsSheet(schedule: schedule),
    );

    if (result == 'edit') {
      final updated = await showDialog<FixedSchedule>(
        context: context,
        builder: (context) => AddScheduleDialog(
          initialDayOfWeek: schedule.dayOfWeek,
          initialStartHour: _parseTime(schedule.startTime),
          schedule: schedule,
        ),
      );

      if (updated != null) {
        try {
          await _apiService.updateFixedSchedule(
            schedule.id,
            title: updated.title,
            description: updated.description,
            dayOfWeek: updated.dayOfWeek,
            startTime: updated.startTime,
            endTime: updated.endTime,
            repeatRule: updated.repeatRule,
          );
          await _loadSchedules();
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('日程更新成功')),
            );
          }
        } catch (e) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('更新失败: $e'), backgroundColor: Colors.red),
            );
          }
        }
      }
    } else if (result == 'delete') {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('确认删除'),
          content: const Text('确定要删除这个日程吗?'),
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
          await _apiService.deleteFixedSchedule(schedule.id);
          await _loadSchedules();
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('日程已删除')),
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
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('日程'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadSchedules,
          ),
        ],
      ),
      body: _buildBody(),
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
              onPressed: _loadSchedules,
              child: const Text('重试'),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        // 星期标题行
        _buildWeekHeader(),
        const Divider(height: 1),
        // 时间表格
        Expanded(
          child: _buildWeekGrid(),
        ),
      ],
    );
  }

  /// 构建星期标题行
  Widget _buildWeekHeader() {
    final weekDates = WeekdayHelper.getWeekDates(DateTime.now());
    final today = DateTime.now().weekday;

    return Container(
      color: Colors.grey[100],
      child: Row(
        children: [
          // 时间列空白
          const SizedBox(width: 50),
          // 星期标题
          ...List.generate(7, (index) {
            final dayOfWeek = index + 1;
            final date = weekDates[index];
            final isToday = date.weekday == today;

            return Expanded(
              child: Container(
                padding: const EdgeInsets.symmetric(vertical: 12),
                decoration: isToday
                    ? BoxDecoration(
                        color: Theme.of(context).primaryColor.withValues(alpha: 0.1),
                        border: Border(
                          bottom: BorderSide(
                            color: Theme.of(context).primaryColor,
                            width: 2,
                          ),
                        ),
                      )
                    : null,
                child: Column(
                  children: [
                    Text(
                      WeekdayHelper.chinese[index],
                      style: TextStyle(
                        fontWeight: isToday ? FontWeight.bold : FontWeight.normal,
                        color: isToday ? Theme.of(context).primaryColor : null,
                      ),
                    ),
                    Text(
                      '${date.day}',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: isToday ? FontWeight.bold : FontWeight.normal,
                        color: isToday ? Theme.of(context).primaryColor : null,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  /// 构建周视图网格
  Widget _buildWeekGrid() {
    return SingleChildScrollView(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 左侧时间列
          SizedBox(
            width: 50,
            child: Column(
              children: List.generate(totalHours, (index) {
                final hour = startHour + index;
                return Container(
                  height: 60,
                  alignment: Alignment.center,
                  child: Text(
                    '${hour.toString().padLeft(2, '0')}:00',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.grey[600],
                    ),
                  ),
                );
              }),
            ),
          ),
          // 右侧日程格子
          Expanded(
            child: Column(
              children: List.generate(totalHours, (hourIndex) {
                final hour = startHour + hourIndex;
                return Row(
                  children: List.generate(7, (dayIndex) {
                    final dayOfWeek = dayIndex + 1;
                    final schedules = _getSchedulesForCell(dayOfWeek, hour);
                    final isStartHour = schedules.any((s) => _parseTime(s.startTime) == hour);

                    return Expanded(
                      child: GestureDetector(
                        onTap: () {
                          if (schedules.isEmpty) {
                            _onTapEmptyCell(dayOfWeek, hour);
                          } else if (isStartHour) {
                            _onTapSchedule(schedules.first);
                          }
                        },
                        child: Container(
                          height: 60,
                          decoration: BoxDecoration(
                            border: Border(
                              right: BorderSide(color: Colors.grey[300]!, width: 0.5),
                              bottom: BorderSide(color: Colors.grey[300]!, width: 0.5),
                            ),
                            color: schedules.isNotEmpty && isStartHour
                                ? _getScheduleColor(schedules.first)
                                : null,
                          ),
                          child: schedules.isNotEmpty && isStartHour
                              ? _buildScheduleCell(schedules.first)
                              : null,
                        ),
                      ),
                    );
                  }),
                );
              }),
            ),
          ),
        ],
      ),
    );
  }

  /// 构建日程单元格
  Widget _buildScheduleCell(FixedSchedule schedule) {
    final startHour = _parseTime(schedule.startTime);
    final endHour = _parseTime(schedule.endTime);
    final duration = endHour - startHour;

    return Container(
      padding: const EdgeInsets.all(4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            schedule.title,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          if (duration > 1)
            Text(
              '${schedule.startTime} - ${schedule.endTime}',
              style: const TextStyle(
                fontSize: 10,
                color: Colors.white70,
              ),
            ),
        ],
      ),
    );
  }

  /// 获取日程颜色
  Color _getScheduleColor(FixedSchedule schedule) {
    // 根据重复规则返回不同颜色
    switch (schedule.repeatRule) {
      case RepeatRule.daily:
        return Colors.blue;
      case RepeatRule.weekly:
        return Colors.purple;
      case RepeatRule.monthly:
        return Colors.orange;
      case RepeatRule.weekday:
        return Colors.green;
      case RepeatRule.weekend:
        return Colors.pink;
      case RepeatRule.none:
        return Colors.teal;
    }
  }
}

/// 添加/编辑日程对话框
class AddScheduleDialog extends StatefulWidget {
  final int initialDayOfWeek;
  final int initialStartHour;
  final FixedSchedule? schedule;

  const AddScheduleDialog({
    super.key,
    required this.initialDayOfWeek,
    required this.initialStartHour,
    this.schedule,
  });

  @override
  State<AddScheduleDialog> createState() => _AddScheduleDialogState();
}

class _AddScheduleDialogState extends State<AddScheduleDialog> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _descriptionController;
  late int _selectedDayOfWeek;
  late TimeOfDay _startTime;
  late TimeOfDay _endTime;
  late RepeatRule _repeatRule;

  bool get isEditing => widget.schedule != null;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController(text: widget.schedule?.title ?? '');
    _descriptionController = TextEditingController(text: widget.schedule?.description ?? '');
    _selectedDayOfWeek = widget.schedule?.dayOfWeek ?? widget.initialDayOfWeek;
    _startTime = widget.schedule != null
        ? _parseTimeOfDay(widget.schedule!.startTime)
        : TimeOfDay(hour: widget.initialStartHour, minute: 0);
    _endTime = widget.schedule != null
        ? _parseTimeOfDay(widget.schedule!.endTime)
        : TimeOfDay(hour: widget.initialStartHour + 1, minute: 0);
    _repeatRule = widget.schedule?.repeatRule ?? RepeatRule.none;
  }

  TimeOfDay _parseTimeOfDay(String timeStr) {
    final parts = timeStr.split(':');
    return TimeOfDay(
      hour: int.tryParse(parts[0]) ?? 0,
      minute: int.tryParse(parts[1]) ?? 0,
    );
  }

  String _formatTimeOfDay(TimeOfDay time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }

  @override
  void dispose() {
    _titleController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _selectTime(bool isStartTime) async {
    final time = await showTimePicker(
      context: context,
      initialTime: isStartTime ? _startTime : _endTime,
    );
    if (time != null) {
      setState(() {
        if (isStartTime) {
          _startTime = time;
          // 确保结束时间晚于开始时间
          if (_timeToMinutes(_endTime) <= _timeToMinutes(_startTime)) {
            _endTime = TimeOfDay(hour: _startTime.hour + 1, minute: _startTime.minute);
          }
        } else {
          _endTime = time;
        }
      });
    }
  }

  int _timeToMinutes(TimeOfDay time) {
    return time.hour * 60 + time.minute;
  }

  void _submit() {
    if (_formKey.currentState!.validate()) {
      final schedule = FixedSchedule(
        id: widget.schedule?.id ?? 0,
        title: _titleController.text.trim(),
        description: _descriptionController.text.trim().isEmpty
            ? null
            : _descriptionController.text.trim(),
        dayOfWeek: _selectedDayOfWeek,
        startTime: _formatTimeOfDay(_startTime),
        endTime: _formatTimeOfDay(_endTime),
        repeatRule: _repeatRule,
      );
      Navigator.pop(context, schedule);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(isEditing ? '编辑日程' : '添加日程'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 标题
              TextFormField(
                controller: _titleController,
                decoration: const InputDecoration(
                  labelText: '标题 *',
                  hintText: '输入日程标题',
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return '请输入标题';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // 描述
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  labelText: '描述',
                  hintText: '输入日程描述(可选)',
                ),
                maxLines: 2,
              ),
              const SizedBox(height: 16),

              // 星期选择
              DropdownButtonFormField<int>(
                value: _selectedDayOfWeek,
                decoration: const InputDecoration(
                  labelText: '星期 *',
                ),
                items: List.generate(7, (index) {
                  final day = index + 1;
                  return DropdownMenuItem(
                    value: day,
                    child: Text(WeekdayHelper.chinese[index]),
                  );
                }),
                onChanged: (value) {
                  setState(() {
                    _selectedDayOfWeek = value!;
                  });
                },
              ),
              const SizedBox(height: 16),

              // 时间选择
              Row(
                children: [
                  Expanded(
                    child: InkWell(
                      onTap: () => _selectTime(true),
                      child: InputDecorator(
                        decoration: const InputDecoration(
                          labelText: '开始时间 *',
                        ),
                        child: Text(_formatTimeOfDay(_startTime)),
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: InkWell(
                      onTap: () => _selectTime(false),
                      child: InputDecorator(
                        decoration: const InputDecoration(
                          labelText: '结束时间 *',
                        ),
                        child: Text(_formatTimeOfDay(_endTime)),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),

              // 重复规则
              DropdownButtonFormField<RepeatRule>(
                value: _repeatRule,
                decoration: const InputDecoration(
                  labelText: '重复规则',
                ),
                items: RepeatRule.values.map((rule) {
                  return DropdownMenuItem(
                    value: rule,
                    child: Text(rule.displayName),
                  );
                }).toList(),
                onChanged: (value) {
                  setState(() {
                    _repeatRule = value!;
                  });
                },
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('取消'),
        ),
        ElevatedButton(
          onPressed: _submit,
          child: Text(isEditing ? '保存' : '添加'),
        ),
      ],
    );
  }
}

/// 日程操作底部 sheet
class ScheduleOptionsSheet extends StatelessWidget {
  final FixedSchedule schedule;

  const ScheduleOptionsSheet({super.key, required this.schedule});

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          ListTile(
            leading: const Icon(Icons.edit),
            title: const Text('编辑'),
            onTap: () => Navigator.pop(context, 'edit'),
          ),
          ListTile(
            leading: const Icon(Icons.delete, color: Colors.red),
            title: const Text('删除', style: TextStyle(color: Colors.red)),
            onTap: () => Navigator.pop(context, 'delete'),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}
