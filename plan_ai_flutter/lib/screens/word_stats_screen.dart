import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../services/api_service.dart';

/// 单词学习统计页面
class WordStatsScreen extends StatefulWidget {
  const WordStatsScreen({super.key});

  @override
  State<WordStatsScreen> createState() => _WordStatsScreenState();
}

class _WordStatsScreenState extends State<WordStatsScreen> {
  final ApiService _apiService = ApiService();

  late DateTime _startDate;
  late DateTime _endDate;
  bool _isLoading = true;
  String? _error;
  Map<String, dynamic>? _stats;

  @override
  void initState() {
    super.initState();
    // 默认最近30天
    _endDate = DateTime.now();
    _startDate = _endDate.subtract(const Duration(days: 29));
    _loadData();
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final response = await _apiService.getWordStats(
        startDate: _formatDate(_startDate),
        endDate: _formatDate(_endDate),
      );

      setState(() {
        _stats = response;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  Future<void> _selectDateRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      initialDateRange: DateTimeRange(start: _startDate, end: _endDate),
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: ColorScheme.light(
              primary: Theme.of(context).primaryColor,
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null) {
      setState(() {
        _startDate = picked.start;
        _endDate = picked.end;
      });
      _loadData();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('学习统计'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildErrorView()
              : _buildContent(),
    );
  }

  Widget _buildErrorView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text('加载失败: $_error', style: const TextStyle(color: Colors.red)),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: _loadData,
            child: const Text('重试'),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    if (_stats == null) {
      return const Center(child: Text('暂无数据'));
    }

    final dailyData = _stats!['daily'] as List<dynamic>? ?? [];
    final totalDays = _stats!['total_days'] as int? ?? 0;
    final totalWords = _stats!['total_words'] as int? ?? 0;
    final avgWordsPerDay = _stats!['avg_words_per_day'] as num? ?? 0;
    final completionRate = _stats!['completion_rate'] as num? ?? 0;

    return RefreshIndicator(
      onRefresh: _loadData,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 日期选择器
            _buildDateRangeSelector(),
            const SizedBox(height: 24),

            // 总计信息卡片
            _buildSummaryCards(totalDays, totalWords, avgWordsPerDay.toDouble(), completionRate.toDouble()),
            const SizedBox(height: 24),

            // 完成率
            _buildCompletionRateChart(completionRate.toDouble()),
            const SizedBox(height: 24),

            // 每日完成柱状图
            _buildDailyChart(dailyData),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildDateRangeSelector() {
    return Card(
      child: ListTile(
        leading: const Icon(Icons.date_range, color: Colors.teal),
        title: const Text('时间范围'),
        subtitle: Text('${_formatDate(_startDate)} ~ ${_formatDate(_endDate)}'),
        trailing: const Icon(Icons.arrow_drop_down),
        onTap: _selectDateRange,
      ),
    );
  }

  Widget _buildSummaryCards(int totalDays, int totalWords, double avgWordsPerDay, double completionRate) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _buildStatCard(
                '总学习天数',
                '$totalDays',
                '天',
                Icons.calendar_today,
                Colors.blue,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildStatCard(
                '总单词数',
                '$totalWords',
                '个',
                Icons.book,
                Colors.green,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildStatCard(
                '平均每日',
                avgWordsPerDay.toStringAsFixed(1),
                '个/天',
                Icons.trending_up,
                Colors.orange,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildStatCard(
                '完成率',
                '${(completionRate * 100).toStringAsFixed(1)}',
                '%',
                Icons.check_circle,
                Colors.purple,
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, String unit, IconData icon, Color color) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 8),
            Text(
              title,
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
                const SizedBox(width: 4),
                Text(
                  unit,
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCompletionRateChart(double completionRate) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '总体完成率',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 200,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  PieChart(
                    PieChartData(
                      sectionsSpace: 2,
                      centerSpaceRadius: 60,
                      sections: [
                        PieChartSectionData(
                          value: completionRate * 100,
                          color: Colors.green,
                          title: '',
                          radius: 30,
                        ),
                        PieChartSectionData(
                          value: (1 - completionRate) * 100,
                          color: Colors.grey[300]!,
                          title: '',
                          radius: 30,
                        ),
                      ],
                    ),
                  ),
                  Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        '${(completionRate * 100).toStringAsFixed(1)}%',
                        style: const TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Text('完成率', style: TextStyle(color: Colors.grey)),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDailyChart(List<dynamic> dailyData) {
    if (dailyData.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Center(
            child: Text(
              '该时间段暂无数据',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ),
        ),
      );
    }

    // 转换数据
    final spots = <FlSpot>[];
    final maxY = dailyData.fold<int>(0, (max, item) {
      final count = item['count'] as int? ?? 0;
      if (count > max) return count;
      return max;
    });

    for (var i = 0; i < dailyData.length; i++) {
      final count = dailyData[i]['count'] as int? ?? 0;
      spots.add(FlSpot(i.toDouble(), count.toDouble()));
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '每日完成单词数',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 24),
            SizedBox(
              height: 200,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  maxY: (maxY + 5).toDouble(),
                  barTouchData: BarTouchData(
                    enabled: true,
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipItem: (group, groupIndex, rod, rodIndex) {
                        final date = dailyData[group.x.toInt()]['date'] ?? '';
                        final count = rod.toY.toInt();
                        return BarTooltipItem(
                          '$date\n$count 个',
                          const TextStyle(color: Colors.white, fontSize: 12),
                        );
                      },
                    ),
                  ),
                  titlesData: FlTitlesData(
                    show: true,
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        getTitlesWidget: (value, meta) {
                          if (value.toInt() >= dailyData.length) return const Text('');
                          final date = dailyData[value.toInt()]['date'] as String? ?? '';
                          // 只显示部分日期标签
                          if (dailyData.length > 7) {
                            if (value.toInt() % (dailyData.length ~/ 5) != 0) {
                              return const Text('');
                            }
                          }
                          return Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Text(
                              date.length > 5 ? date.substring(5) : date,
                              style: const TextStyle(fontSize: 10),
                            ),
                          );
                        },
                        reservedSize: 30,
                      ),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 30,
                        getTitlesWidget: (value, meta) {
                          return Text(
                            value.toInt().toString(),
                            style: const TextStyle(fontSize: 10),
                          );
                        },
                      ),
                    ),
                    topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                    rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: List.generate(dailyData.length, (index) {
                    final count = dailyData[index]['count'] as int? ?? 0;
                    return BarChartGroupData(
                      x: index,
                      barRods: [
                        BarChartRodData(
                          toY: count.toDouble(),
                          color: Theme.of(context).primaryColor,
                          width: dailyData.length > 15 ? 8 : 16,
                          borderRadius: const BorderRadius.vertical(top: Radius.circular(4)),
                        ),
                      ],
                    );
                  }),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
