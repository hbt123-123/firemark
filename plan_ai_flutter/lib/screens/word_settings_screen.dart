import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'word_practice_screen.dart';
import 'word_stats_screen.dart';

/// 单词设置页面
class WordSettingsScreen extends StatefulWidget {
  const WordSettingsScreen({super.key});

  @override
  State<WordSettingsScreen> createState() => _WordSettingsScreenState();
}

class _WordSettingsScreenState extends State<WordSettingsScreen> {
  final ApiService _apiService = ApiService();
  
  List<String> _availableBankTypes = [];
  List<String> _selectedBankTypes = [];
  int _dailyCount = 10;
  int _englishRepeat = 2;
  int _chineseRepeat = 1;
  bool _enableReminder = false;
  
  bool _isLoading = true;
  bool _isSaving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final results = await Future.wait([
        _apiService.getWordBankTypes(),
        _apiService.getWordSettings(),
      ]);

      final bankTypes = results[0] as List<String>;
      final settings = results[1] as Map<String, dynamic>;

      setState(() {
        _availableBankTypes = bankTypes;
        _selectedBankTypes = (settings['bank_types'] as List<dynamic>?)
                ?.map((e) => e.toString())
                .toList() ?? [];
        _dailyCount = settings['daily_count'] ?? 10;
        _englishRepeat = settings['english_repeat'] ?? 2;
        _chineseRepeat = settings['chinese_repeat'] ?? 1;
        _enableReminder = settings['enable_reminder'] ?? false;
        _isLoading = false;
      });
    } catch (e) {
      try {
        final bankTypes = await _apiService.getWordBankTypes();
        setState(() {
          _availableBankTypes = bankTypes;
          _selectedBankTypes = [];
          _isLoading = false;
        });
      } catch (_) {
        setState(() {
          _error = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _saveSettings() async {
    if (_selectedBankTypes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('请至少选择一个词库类型'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }

    setState(() => _isSaving = true);

    try {
      final success = await _apiService.saveWordSettings(
        bankTypes: _selectedBankTypes,
        dailyCount: _dailyCount,
        englishRepeat: _englishRepeat,
        chineseRepeat: _chineseRepeat,
        enableReminder: _enableReminder,
      );

      if (success && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('设置保存成功'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context);
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('设置保存失败'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('保存失败: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('单词设置'),
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildErrorView()
              : _buildSettingsForm(),
      bottomNavigationBar: _isLoading || _error != null
          ? null
          : _buildSaveButton(),
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

  Widget _buildSettingsForm() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildSectionTitle('选择词库类型'),
          const SizedBox(height: 8),
          _buildBankTypeSelector(),
          const SizedBox(height: 24),
          _buildSectionTitle('每日单词数量'),
          const SizedBox(height: 8),
          _buildDailyCountSlider(),
          const SizedBox(height: 24),
          _buildSectionTitle('英文重复次数'),
          const SizedBox(height: 8),
          _buildRepeatSelector('英文', _englishRepeat, (value) {
            setState(() => _englishRepeat = value);
          }),
          const SizedBox(height: 24),
          _buildSectionTitle('中文重复次数'),
          const SizedBox(height: 8),
          _buildRepeatSelector('中文', _chineseRepeat, (value) {
            setState(() => _chineseRepeat = value);
          }),
          const SizedBox(height: 24),
          _buildReminderSwitch(),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
    );
  }

  Widget _buildBankTypeSelector() {
    if (_availableBankTypes.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Text('暂无可用词库', style: TextStyle(color: Colors.grey[600])),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _availableBankTypes.map((type) {
            final isSelected = _selectedBankTypes.contains(type);
            return FilterChip(
              label: Text(type),
              selected: isSelected,
              onSelected: (selected) {
                setState(() {
                  if (selected) {
                    _selectedBankTypes.add(type);
                  } else {
                    _selectedBankTypes.remove(type);
                  }
                });
              },
              selectedColor: Theme.of(context).primaryColor.withValues(alpha: 0.2),
              checkmarkColor: Theme.of(context).primaryColor,
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildDailyCountSlider() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('每天学习'),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: Theme.of(context).primaryColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '$_dailyCount 个',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).primaryColor,
                    ),
                  ),
                ),
              ],
            ),
            Slider(
              value: _dailyCount.toDouble(),
              min: 1,
              max: 50,
              divisions: 49,
              label: _dailyCount.toString(),
              onChanged: (value) {
                setState(() => _dailyCount = value.round());
              },
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('1', style: TextStyle(color: Colors.grey[600])),
                Text('50', style: TextStyle(color: Colors.grey[600])),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRepeatSelector(String label, int value, Function(int) onChanged) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('$label 重复'),
            Row(
              children: [
                IconButton(
                  onPressed: value > 1 ? () => onChanged(value - 1) : null,
                  icon: const Icon(Icons.remove_circle_outline),
                  color: Theme.of(context).primaryColor,
                ),
                Container(
                  width: 40,
                  alignment: Alignment.center,
                  child: Text(
                    '$value',
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
                IconButton(
                  onPressed: value < 5 ? () => onChanged(value + 1) : null,
                  icon: const Icon(Icons.add_circle_outline),
                  color: Theme.of(context).primaryColor,
                ),
                Text('次', style: TextStyle(color: Colors.grey[600])),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReminderSwitch() {
    return Card(
      child: SwitchListTile(
        title: const Text('每日提醒'),
        subtitle: Text(
          _enableReminder ? '已开启每日学习提醒' : '关闭后将不再收到提醒',
          style: TextStyle(color: Colors.grey[600], fontSize: 12),
        ),
        value: _enableReminder,
        onChanged: (value) {
          setState(() => _enableReminder = value);
        },
        secondary: Icon(
          _enableReminder ? Icons.notifications_active : Icons.notifications_off,
          color: _enableReminder ? Theme.of(context).primaryColor : Colors.grey,
        ),
      ),
    );
  }

  Widget _buildSaveButton() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 50,
                    child: OutlinedButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const WordPracticeScreen()),
                        );
                      },
                      style: OutlinedButton.styleFrom(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text('开始学习', style: TextStyle(fontSize: 16)),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: SizedBox(
                    height: 50,
                    child: OutlinedButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const WordStatsScreen()),
                        );
                      },
                      style: OutlinedButton.styleFrom(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: const Text('学习统计', style: TextStyle(fontSize: 16)),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: _isSaving ? null : _saveSettings,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).primaryColor,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: _isSaving
                    ? const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : const Text('保存设置', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
