"""
Flutter Widget 测试示例
"""
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:plan_ai_flutter/main.dart';
import 'package:plan_ai_flutter/providers/auth_provider.dart';
import 'package:plan_ai_flutter/models/user.dart';


void main() {
  group('App Widget Tests', () {
    testWidgets('App 启动显示加载状态', (WidgetTester tester) async {
      // 构建应用
      await tester.pumpWidget(const MyApp());
      
      // 验证加载指示器显示
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });
  });
  
  group('Auth Provider Tests', () {
    test('初始状态为 unknown', () {
      final provider = AuthProvider();
      expect(provider.status, AuthStatus.unknown);
    });
    
    test('未认证时 isAuthenticated 返回 false', () {
      final provider = AuthProvider();
      expect(provider.isAuthenticated, false);
    });
  });
  
  group('User Model Tests', () {
    test('User.fromJson 正确解析 JSON', () {
      final json = {
        'id': 1,
        'username': 'testuser',
        'created_at': '2026-02-25T10:00:00Z',
      };
      
      final user = User.fromJson(json);
      
      expect(user.id, 1);
      expect(user.username, 'testuser');
      expect(user.createdAt, isNotNull);
    });
    
    test('User.toJson 正确序列化为 JSON', () {
      final user = User(
        id: 1,
        username: 'testuser',
        createdAt: DateTime.parse('2026-02-25T10:00:00Z'),
      );
      
      final json = user.toJson();
      
      expect(json['id'], 1);
      expect(json['username'], 'testuser');
    });
  });
}
