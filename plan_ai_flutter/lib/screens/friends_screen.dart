import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'friend_tasks_screen.dart';

/// 好友页面
class FriendsScreen extends StatefulWidget {
  const FriendsScreen({super.key});

  @override
  State<FriendsScreen> createState() => _FriendsScreenState();
}

class _FriendsScreenState extends State<FriendsScreen> {
  final ApiService _apiService = ApiService();
  List<Map<String, dynamic>> _friends = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadFriends();
  }

  Future<void> _loadFriends() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final friends = await _apiService.getFriends();
      setState(() {
        _friends = friends;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _navigateToFriendTasks(Map<String, dynamic> friend) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => FriendTasksScreen(
          friendId: friend['id'] as int,
          friendName: friend['username'] as String? ?? '好友',
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('好友'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadFriends,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('添加好友功能开发中'),
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
        child: const Icon(Icons.person_add),
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
              onPressed: _loadFriends,
              child: const Text('重试'),
            ),
          ],
        ),
      );
    }

    if (_friends.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.people_outline, size: 80, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              '暂无好友',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '点击右下角按钮添加好友',
              style: TextStyle(color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _friends.length,
      itemBuilder: (context, index) {
        return _buildFriendCard(_friends[index]);
      },
    );
  }

  Widget _buildFriendCard(Map<String, dynamic> friend) {
    final username = friend['username'] as String? ?? '未知用户';
    final id = friend['id'] as int;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: Colors.purple[100],
          child: Text(
            username[0].toUpperCase(),
            style: TextStyle(
              color: Colors.purple[700],
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        title: Text(
          username,
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Text('ID: $id'),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => _navigateToFriendTasks(friend),
      ),
    );
  }
}
