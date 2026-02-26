import 'dart:async';
import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import '../services/api_service.dart';
import 'word_settings_screen.dart';

/// 每日单词练习页面
class WordPracticeScreen extends StatefulWidget {
  final String? date;

  const WordPracticeScreen({super.key, this.date});

  @override
  State<WordPracticeScreen> createState() => _WordPracticeScreenState();
}

class _WordPracticeScreenState extends State<WordPracticeScreen> {
  final ApiService _apiService = ApiService();
  final AudioPlayer _audioPlayer = AudioPlayer();

  // 用户设置
  int _englishRepeat = 2;
  int _chineseRepeat = 1;

  // 单词数据
  List<dynamic> _words = [];
  int _currentIndex = 0;
  int _completedCount = 0;
  int _totalCount = 0;
  String _practiceDate = '';

  // 播放状态
  bool _isPlaying = false;
  bool _isPaused = false;
  bool _isLoading = true;
  String? _error;
  bool _isCompleted = false;

  // 播放控制
  int _englishPlayed = 0;
  int _chinesePlayed = 0;
  String _currentPlayPhase = 'idle'; // idle, english, chinese, waiting

  StreamSubscription? _playerSubscription;
  Timer? _autoNextTimer;

  @override
  void initState() {
    super.initState();
    _practiceDate = widget.date ?? _formatDate(DateTime.now());
    _initAudio();
    _loadData();
  }

  void _initAudio() {
    _playerSubscription = _audioPlayer.onPlayerComplete.listen((_) {
      _onAudioComplete();
    });
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
      // 检查用户是否设置了偏好
      final hasSettings = await _apiService.hasWordSettings();
      if (!hasSettings) {
        if (mounted) {
          _showSettingsPrompt();
        }
        return;
      }

      // 获取用户设置
      try {
        final settings = await _apiService.getWordSettings();
        setState(() {
          _englishRepeat = settings['english_repeat'] ?? 2;
          _chineseRepeat = settings['chinese_repeat'] ?? 1;
        });
      } catch (e) {
        // 使用默认值
      }

      // 获取每日单词
      final response = await _apiService.getDailyWords(date: _practiceDate);
      final words = response['words'] as List<dynamic>? ?? [];
      final completed = response['completed_count'] as int? ?? 0;

      setState(() {
        _words = words;
        _totalCount = words.length;
        _completedCount = completed;
        // 从未完成的单词开始
        _currentIndex = completed;
        _isLoading = false;
      });

      if (_words.isEmpty) {
        setState(() {
          _isCompleted = true;
        });
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _showSettingsPrompt() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('请先设置学习偏好'),
        content: const Text('您尚未设置每日单词数量和词库类型，是否前往设置？'),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.pop(context);
            },
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const WordSettingsScreen()),
              ).then((_) => _loadData());
            },
            child: const Text('前往设置'),
          ),
        ],
      ),
    );
    setState(() {
      _isLoading = false;
    });
  }

  @override
  void dispose() {
    _playerSubscription?.cancel();
    _autoNextTimer?.cancel();
    _audioPlayer.dispose();
    super.dispose();
  }

  // 开始播放
  Future<void> _startPlaying() async {
    if (_words.isEmpty || _currentIndex >= _words.length) return;

    setState(() {
      _isPlaying = true;
      _isPaused = false;
      _englishPlayed = 0;
      _chinesePlayed = 0;
      _currentPlayPhase = 'english';
    });

    await _playCurrentWord();
  }

  // 播放当前单词
  Future<void> _playCurrentWord() async {
    if (_currentIndex >= _words.length) return;

    final word = _words[_currentIndex];
    final englishAudio = word['english_audio'] as String?;
    final chineseAudio = word['chinese_audio'] as String?;

    if (_currentPlayPhase == 'english' && englishAudio != null) {
      await _playAudio(englishAudio);
    } else if (_currentPlayPhase == 'chinese' && chineseAudio != null) {
      await _playAudio(chineseAudio);
    } else {
      // 没有音频，直接完成
      _onAudioComplete();
    }
  }

  Future<void> _playAudio(String url) async {
    try {
      await _audioPlayer.play(UrlSource(url));
    } catch (e) {
      debugPrint('播放音频失败: $e');
      _onAudioComplete();
    }
  }

  // 音频播放完成
  void _onAudioComplete() {
    if (!mounted) return;

    final word = _words[_currentIndex];

    if (_currentPlayPhase == 'english') {
      // 英文播放完成
      setState(() {
        _englishPlayed++;
      });

      if (_englishPlayed < _englishRepeat) {
        // 继续播放英文
        _playCurrentWord();
      } else {
        // 切换到中文
        setState(() {
          _currentPlayPhase = 'chinese';
          _chinesePlayed = 0;
        });
        _playCurrentWord();
      }
    } else if (_currentPlayPhase == 'chinese') {
      // 中文播放完成
      setState(() {
        _chinesePlayed++;
      });

      if (_chinesePlayed < _chineseRepeat) {
        // 继续播放中文
        _playCurrentWord();
      } else {
        // 当前单词播放完成
        _markWordComplete(word);
      }
    }
  }

  // 标记单词完成
  Future<void> _markWordComplete(dynamic word) async {
    final wordId = word['id'] as int?;

    if (wordId != null) {
      try {
        await _apiService.completeWord(wordId: wordId, date: _practiceDate);
      } catch (e) {
        debugPrint('标记完成失败: $e');
      }
    }

    // 等待1-2秒后切换到下一个
    setState(() {
      _completedCount++;
      _currentPlayPhase = 'waiting';
    });

    _autoNextTimer?.cancel();
    _autoNextTimer = Timer(const Duration(milliseconds: 1500), () {
      if (!mounted) return;
      _nextWord();
    });
  }

  // 切换到下一个单词
  Future<void> _nextWord() async {
    _autoNextTimer?.cancel();
    await _audioPlayer.stop();

    setState(() {
      _currentIndex++;
      _englishPlayed = 0;
      _chinesePlayed = 0;
      _currentPlayPhase = 'idle';
    });

    if (_currentIndex >= _totalCount) {
      setState(() {
        _isCompleted = true;
        _isPlaying = false;
      });
    } else {
      // 自动开始播放下一个
      await _startPlaying();
    }
  }

  // 暂停
  Future<void> _pause() async {
    await _audioPlayer.pause();
    _autoNextTimer?.cancel();
    setState(() {
      _isPaused = true;
    });
  }

  // 继续
  Future<void> _resume() async {
    setState(() {
      _isPaused = false;
    });

    if (_currentPlayPhase == 'waiting') {
      _nextWord();
    } else {
      await _playCurrentWord();
    }
  }

  // 手动下一个
  Future<void> _skipToNext() async {
    await _audioPlayer.stop();
    _autoNextTimer?.cancel();

    // 标记当前单词为完成（如果还没有完成）
    if (_currentIndex < _words.length) {
      final word = _words[_currentIndex];
      final wordId = word['id'] as int?;
      if (wordId != null && _currentPlayPhase != 'waiting') {
        try {
          await _apiService.completeWord(wordId: wordId, date: _practiceDate);
          setState(() {
            _completedCount++;
          });
        } catch (e) {
          debugPrint('标记完成失败: $e');
        }
      }
    }

    await _nextWord();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('每日单词 - $_practiceDate'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadData,
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
      return _buildErrorView();
    }

    if (_isCompleted) {
      return _buildCompletedView();
    }

    if (_words.isEmpty) {
      return _buildEmptyView();
    }

    return _buildPracticeView();
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

  Widget _buildEmptyView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.inbox, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text('今日暂无单词', style: TextStyle(fontSize: 18, color: Colors.grey[600])),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('返回'),
          ),
        ],
      ),
    );
  }

  Widget _buildCompletedView() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.check_circle, size: 80, color: Colors.green),
          const SizedBox(height: 24),
          const Text(
            '🎉 恭喜完成今日学习！',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          Text(
            '今日学习 $_totalCount 个单词',
            style: TextStyle(fontSize: 16, color: Colors.grey[600]),
          ),
          const SizedBox(height: 32),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
            ),
            child: const Text('返回'),
          ),
        ],
      ),
    );
  }

  Widget _buildPracticeView() {
    final word = _words[_currentIndex];
    final english = word['english'] as String? ?? '';
    final chinese = word['chinese'] as String? ?? '';
    final phonetic = word['phonetic'] as String? ?? '';

    return SafeArea(
      child: Column(
        children: [
          // 进度条
          _buildProgressBar(),

          // 单词显示
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // 英文
                  Text(
                    english,
                    style: const TextStyle(
                      fontSize: 48,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  // 音标
                  if (phonetic.isNotEmpty)
                    Text(
                      '/$phonetic/',
                      style: TextStyle(
                        fontSize: 20,
                        color: Colors.grey[600],
                      ),
                    ),
                  const SizedBox(height: 24),
                  // 中文释义
                  Text(
                    chinese,
                    style: TextStyle(
                      fontSize: 18,
                      color: Colors.grey[700],
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 32),
                  // 播放状态指示
                  _buildPlayStatus(),
                ],
              ),
            ),
          ),

          // 播放控制
          _buildControls(),
        ],
      ),
    );
  }

  Widget _buildProgressBar() {
    final progress = _totalCount > 0 ? _completedCount / _totalCount : 0.0;

    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '当前第 ${_currentIndex + 1} 个',
                style: const TextStyle(fontSize: 14),
              ),
              Text(
                '已完成 $_completedCount / $_totalCount',
                style: TextStyle(fontSize: 14, color: Colors.grey[600]),
              ),
            ],
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 8,
              backgroundColor: Colors.grey[200],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlayStatus() {
    String statusText = '';
    IconData statusIcon = Icons.play_circle_outline;
    Color statusColor = Colors.grey;

    if (_isPlaying && !_isPaused) {
      if (_currentPlayPhase == 'english') {
        statusText = '正在播放英文 ($_englishPlayed/$_englishRepeat)';
        statusIcon = Icons.volume_up;
        statusColor = Colors.blue;
      } else if (_currentPlayPhase == 'chinese') {
        statusText = '正在播放中文 ($_chinesePlayed/$_chineseRepeat)';
        statusIcon = Icons.record_voice_over;
        statusColor = Colors.green;
      } else if (_currentPlayPhase == 'waiting') {
        statusText = '准备切换下一个...';
        statusIcon = Icons.hourglass_empty;
        statusColor = Colors.orange;
      }
    } else if (_isPaused) {
      statusText = '已暂停';
      statusIcon = Icons.pause_circle_outline;
      statusColor = Colors.grey;
    } else {
      statusText = '点击播放开始学习';
      statusIcon = Icons.play_circle_outline;
      statusColor = Colors.grey;
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(statusIcon, color: statusColor, size: 20),
        const SizedBox(width: 8),
        Text(
          statusText,
          style: TextStyle(color: statusColor, fontSize: 14),
        ),
      ],
    );
  }

  Widget _buildControls() {
    return Container(
      padding: const EdgeInsets.all(24),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          // 播放/暂停按钮
          FloatingActionButton.large(
            heroTag: 'playPause',
            onPressed: () {
              if (!_isPlaying) {
                _startPlaying();
              } else if (_isPaused) {
                _resume();
              } else {
                _pause();
              }
            },
            backgroundColor: Theme.of(context).primaryColor,
            child: Icon(
              _isPlaying && !_isPaused ? Icons.pause : Icons.play_arrow,
              size: 36,
              color: Colors.white,
            ),
          ),
          // 下一个按钮
          FloatingActionButton(
            heroTag: 'next',
            onPressed: _isPlaying ? _skipToNext : null,
            backgroundColor: _isPlaying ? Colors.orange : Colors.grey[300],
            child: const Icon(Icons.skip_next, color: Colors.white),
          ),
        ],
      ),
    );
  }
}
