import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'word_settings_screen.dart';
import 'word_practice_screen.dart';
import 'word_stats_screen.dart';

/// 功能中心页面
class FeaturesScreen extends StatefulWidget {
  const FeaturesScreen({super.key});

  @override
  State<FeaturesScreen> createState() => _FeaturesScreenState();
}

class _FeaturesScreenState extends State<FeaturesScreen> {
  final ApiService _apiService = ApiService();
  bool _hasSettings = false;
  bool _isChecking = true;

  @override
  void initState() {
    super.initState();
    _checkSettings();
  }

  Future<void> _checkSettings() async {
    try {
      final hasSettings = await _apiService.hasWordSettings();
      if (mounted) {
        setState(() {
          _hasSettings = hasSettings;
          _isChecking = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isChecking = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('功能中心'),
        centerTitle: true,
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // 英语单词跟读功能卡片
          FeatureCard(
            name: '英语单词跟读',
            description: 'AI驱动的英语单词学习，通过跟读练习提升发音和听力能力',
            icon: Icons.record_voice_over,
            statusLabel: '新上线',
            statusColor: Colors.green,
            featureId: 'english_word',
          ),
          const SizedBox(height: 16),

          // 今日练习快捷入口
          _buildQuickEntry(),
          const SizedBox(height: 16),

          // 更多功能占位符
          const FeatureCard(
            name: '更多功能开发中',
            description: '敬请期待更多智能学习功能',
            icon: Icons.construction,
            statusLabel: '规划中',
            statusColor: Colors.orange,
            featureId: null,
            enabled: false,
          ),
        ],
      ),
    );
  }

  Widget _buildQuickEntry() {
    if (_isChecking) {
      return const Card(
        child: ListTile(
          leading: Icon(Icons.hourglass_empty, color: Colors.grey),
          title: Text('检查设置中...'),
        ),
      );
    }

    return Card(
      elevation: 2,
      color: _hasSettings ? Colors.green[50] : Colors.orange[50],
      child: ListTile(
        leading: Icon(
          _hasSettings ? Icons.today : Icons.settings,
          color: _hasSettings ? Colors.green : Colors.orange,
        ),
        title: Text(
          _hasSettings ? '今日练习' : '请先设置学习偏好',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: _hasSettings ? Colors.green[700] : Colors.orange[700],
          ),
        ),
        subtitle: Text(
          _hasSettings ? '点击开始今日单词学习' : '设置每日单词数量和词库',
        ),
        trailing: Icon(
          _hasSettings ? Icons.arrow_forward_ios : Icons.arrow_forward_ios,
          color: _hasSettings ? Colors.green : Colors.orange,
          size: 16,
        ),
        onTap: () {
          if (_hasSettings) {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const WordPracticeScreen()),
            );
          } else {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const WordSettingsScreen()),
            ).then((_) => _checkSettings());
          }
        },
      ),
    );
  }
}

/// 功能卡片组件
class FeatureCard extends StatelessWidget {
  final String name;
  final String description;
  final IconData icon;
  final String statusLabel;
  final Color statusColor;
  final String? featureId;
  final bool enabled;

  const FeatureCard({
    super.key,
    required this.name,
    required this.description,
    required this.icon,
    required this.statusLabel,
    required this.statusColor,
    this.featureId,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: enabled ? () => _navigateToFeature(context) : null,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).primaryColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      icon,
                      color: Theme.of(context).primaryColor,
                      size: 28,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          name,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                          decoration: BoxDecoration(
                            color: statusColor.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            statusLabel,
                            style: TextStyle(
                              fontSize: 12,
                              color: statusColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  if (enabled)
                    const Icon(Icons.chevron_right, color: Colors.grey),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                description,
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 14,
                ),
              ),
              const SizedBox(height: 12),
              if (enabled)
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton.icon(
                    onPressed: () => _showFeedbackDialog(context),
                    icon: const Icon(Icons.feedback_outlined, size: 18),
                    label: const Text('反馈'),
                    style: TextButton.styleFrom(
                      foregroundColor: Colors.grey[600],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  void _navigateToFeature(BuildContext context) {
    if (featureId == 'english_word') {
      // 点击卡片直接跳转到设置页面
      Navigator.push(
        context,
        MaterialPageRoute(builder: (context) => const WordSettingsScreen()),
      );
    }
  }

  void _showFeedbackDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => FeedbackDialog(
        featureName: name,
        featureId: featureId,
      ),
    );
  }
}

/// 反馈类型枚举
enum FeedbackType {
  suggestion('建议', Icons.lightbulb_outline),
  issue('问题', Icons.bug_report_outlined),
  praise('表扬', Icons.thumb_up_outlined);

  final String label;
  final IconData icon;
  const FeedbackType(this.label, this.icon);
}

/// 反馈对话框组件
class FeedbackDialog extends StatefulWidget {
  final String featureName;
  final String? featureId;

  const FeedbackDialog({
    super.key,
    required this.featureName,
    this.featureId,
  });

  @override
  State<FeedbackDialog> createState() => _FeedbackDialogState();
}

class _FeedbackDialogState extends State<FeedbackDialog> {
  final ApiService _apiService = ApiService();
  final _formKey = GlobalKey<FormState>();
  final _contentController = TextEditingController();
  
  FeedbackType _selectedType = FeedbackType.suggestion;
  int _rating = 0;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _contentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          const Icon(Icons.feedback, color: Colors.teal),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '反馈-${widget.featureName}',
              style: const TextStyle(fontSize: 18),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '反馈类型',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 8),
              Row(
                children: FeedbackType.values.map((type) {
                  final isSelected = _selectedType == type;
                  return Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => _selectedType = type),
                      child: Container(
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        decoration: BoxDecoration(
                          color: isSelected 
                              ? Theme.of(context).primaryColor.withValues(alpha: 0.1)
                              : Colors.grey[100],
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: isSelected 
                                ? Theme.of(context).primaryColor 
                                : Colors.grey[300]!,
                            width: isSelected ? 2 : 1,
                          ),
                        ),
                        child: Column(
                          children: [
                            Icon(
                              type.icon,
                              color: isSelected 
                                  ? Theme.of(context).primaryColor 
                                  : Colors.grey[600],
                              size: 24,
                            ),
                            const SizedBox(height: 4),
                            Text(
                              type.label,
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                color: isSelected 
                                    ? Theme.of(context).primaryColor 
                                    : Colors.grey[600],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),
              const Text(
                '评分（可选）',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: List.generate(5, (index) {
                  final starIndex = index + 1;
                  return GestureDetector(
                    onTap: () => setState(() => _rating = starIndex),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: Icon(
                        starIndex <= _rating ? Icons.star : Icons.star_border,
                        color: Colors.amber,
                        size: 32,
                      ),
                    ),
                  );
                }),
              ),
              const SizedBox(height: 20),
              const Text(
                '反馈内容',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
              ),
              const SizedBox(height: 8),
              TextFormField(
                controller: _contentController,
                maxLines: 4,
                decoration: InputDecoration(
                  hintText: '请填写您的反馈内容...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                  contentPadding: const EdgeInsets.all(12),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return '请填写反馈内容';
                  }
                  if (value.trim().length < 5) {
                    return '反馈内容至少5个字';
                  }
                  return null;
                },
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isSubmitting ? null : () => Navigator.pop(context),
          child: const Text('取消'),
        ),
        ElevatedButton(
          onPressed: _isSubmitting ? null : _submitFeedback,
          style: ElevatedButton.styleFrom(
            backgroundColor: Theme.of(context).primaryColor,
            foregroundColor: Colors.white,
          ),
          child: _isSubmitting
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : const Text('提交'),
        ),
      ],
    );
  }

  Future<void> _submitFeedback() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSubmitting = true);

    try {
      final success = await _apiService.submitFeedback(
        type: _selectedType.name,
        content: _contentController.text.trim(),
        rating: _rating > 0 ? _rating : null,
        featureId: widget.featureId,
      );

      if (!mounted) return;

      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('感谢您的反馈！'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('提交失败，请稍后重试'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('提交失败: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isSubmitting = false);
      }
    }
  }
}
