import 'package:flutter/material.dart';
import '../models/goal.dart';
import '../services/api_service.dart';

/// AI计划对话页面
class AIPlanScreen extends StatefulWidget {
  const AIPlanScreen({super.key});

  @override
  State<AIPlanScreen> createState() => _AIPlanScreenState();
}

class _AIPlanScreenState extends State<AIPlanScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  
  // 对话状态
  bool _isInitializing = true;
  bool _isLoading = false;
  bool _hasStarted = false;
  String? _sessionId;
  String? _error;
  
  // 对话消息列表
  final List<AIMessage> _messages = [];

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  /// 开始AI计划 - 发送初始目标
  Future<void> _startPlan() async {
    final goal = _inputController.text.trim();
    if (goal.isEmpty) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // 添加用户消息
      _messages.add(AIMessage(role: 'user', content: goal));
      
      // 调用API
      final response = await _apiService.startAIPlan(goal);
      
      setState(() {
        _sessionId = response.sessionId;
        _hasStarted = true;
        _isInitializing = false;
        _isLoading = false;
        _messages.add(AIMessage(
          role: 'assistant',
          content: response.message,
          isPlanPreview: response.hasPlanPreview,
          planData: response.planPreview,
        ));
      });
      
      _scrollToBottom();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
        // 移除用户消息
        _messages.removeLast();
      });
    }
  }

  /// 继续AI对话
  Future<void> _continueChat() async {
    final message = _inputController.text.trim();
    if (message.isEmpty || _sessionId == null) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // 添加用户消息
      _messages.add(AIMessage(role: 'user', content: message));
      _inputController.clear();
      
      // 调用API
      final response = await _apiService.continueAIPlan(_sessionId!, message);
      
      setState(() {
        _isLoading = false;
        _messages.add(AIMessage(
          role: 'assistant',
          content: response.message,
          isPlanPreview: response.hasPlanPreview,
          planData: response.planPreview,
        ));
      });
      
      _scrollToBottom();
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
        // 移除用户消息
        _messages.removeLast();
      });
    }
  }

  /// 确认计划
  Future<void> _confirmPlan() async {
    if (_sessionId == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      await _apiService.confirmAIPlan(_sessionId!);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('目标创建成功！')),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// 重新开始
  void _restart() {
    setState(() {
      _isInitializing = true;
      _hasStarted = false;
      _sessionId = null;
      _messages.clear();
      _inputController.clear();
      _error = null;
    });
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI 智能规划'),
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Column(
        children: [
          // 对话内容
          Expanded(
            child: _hasStarted ? _buildChatList() : _buildInitialInput(),
          ),
          // 底部输入框
          if (_hasStarted && !_hasPlanPreview) _buildInputBar(),
          // 计划预览和按钮
          if (_hasPlanPreview) _buildPlanPreviewButtons(),
        ],
      ),
    );
  }

  /// 判断是否有计划预览
  bool get _hasPlanPreview {
    return _messages.isNotEmpty && 
           _messages.last.isAssistant && 
           _messages.last.isPlanPreview;
  }

  /// 构建初始输入界面
  Widget _buildInitialInput() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.auto_awesome,
            size: 80,
            color: Theme.of(context).primaryColor,
          ),
          const SizedBox(height: 24),
          const Text(
            'AI 智能目标规划',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '告诉我你的目标，AI将帮你制定详细计划',
            style: TextStyle(color: Colors.grey[600]),
          ),
          const SizedBox(height: 32),
          TextField(
            controller: _inputController,
            decoration: InputDecoration(
              hintText: '例如：我想在3个月内学会Python',
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            maxLines: 3,
            textInputAction: TextInputAction.send,
            onSubmitted: (_) => _startPlan(),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _startPlan,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: _isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('开始规划'),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(
              _error!,
              style: const TextStyle(color: Colors.red),
              textAlign: TextAlign.center,
            ),
          ],
        ],
      ),
    );
  }

  /// 构建对话列表
  Widget _buildChatList() {
    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(16),
      itemCount: _messages.length,
      itemBuilder: (context, index) {
        return _buildMessageBubble(_messages[index]);
      },
    );
  }

  /// 构建消息气泡
  Widget _buildMessageBubble(AIMessage message) {
    final isUser = message.isUser;
    
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        decoration: BoxDecoration(
          color: isUser 
              ? Theme.of(context).primaryColor 
              : Colors.grey[200],
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(isUser ? 16 : 4),
            bottomRight: Radius.circular(isUser ? 4 : 16),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 计划预览
            if (message.isPlanPreview && message.planData != null)
              _buildPlanPreviewCard(message.planData!),
            // 普通文本消息
            if (!message.isPlanPreview || message.planData == null)
              Text(
                message.content,
                style: TextStyle(
                  color: isUser ? Colors.white : Colors.black87,
                ),
              ),
          ],
        ),
      ),
    );
  }

  /// 构建计划预览卡片
  Widget _buildPlanPreviewCard(Map<String, dynamic> planData) {
    final title = planData['title'] as String? ?? '';
    final outline = planData['outline'] as String? ?? '';
    final tasks = planData['tasks'] as List<dynamic>? ?? [];

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title.isNotEmpty) ...[
            Text(
              title,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 8),
          ],
          if (outline.isNotEmpty) ...[
            Text(outline, style: const TextStyle(fontSize: 14)),
            const SizedBox(height: 8),
          ],
          if (tasks.isNotEmpty) ...[
            const Text(
              '任务列表:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            ...tasks.take(5).map((task) {
              final taskTitle = task is Map ? task['title']?.toString() ?? '' : task.toString();
              return Padding(
                padding: const EdgeInsets.only(left: 8, top: 2),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle_outline, size: 14),
                    const SizedBox(width: 4),
                    Expanded(child: Text(taskTitle, style: const TextStyle(fontSize: 13))),
                  ],
                ),
              );
            }),
            if (tasks.length > 5)
              Padding(
                padding: const EdgeInsets.only(left: 8, top: 4),
                child: Text(
                  '...还有 ${tasks.length - 5} 个任务',
                  style: TextStyle(color: Colors.grey[600], fontSize: 12),
                ),
              ),
          ],
        ],
      ),
    );
  }

  /// 构建底部输入栏
  Widget _buildInputBar() {
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
                controller: _inputController,
                decoration: InputDecoration(
                  hintText: '回复AI的问题...',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                ),
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _continueChat(),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: _isLoading
                  ? const SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(
                      Icons.send,
                      color: Theme.of(context).primaryColor,
                    ),
              onPressed: _isLoading ? null : _continueChat,
            ),
          ],
        ),
      ),
    );
  }

  /// 构建计划预览按钮区域
  Widget _buildPlanPreviewButtons() {
    return Container(
      padding: const EdgeInsets.all(16),
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
              child: OutlinedButton(
                onPressed: _isLoading ? null : _restart,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: const Text('重新开始'),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: ElevatedButton(
                onPressed: _isLoading ? null : _confirmPlan,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                ),
                child: _isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Text('确认创建'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
