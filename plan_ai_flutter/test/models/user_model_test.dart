/**
 * Flutter 模型单元测试
 */
import 'package:flutter_test/flutter_test.dart';

import 'package:plan_ai_flutter/models/user.dart';


void main() {
  group('UserResponse Model Tests', () {
    test('fromJson 正确解析完整数据', () {
      final json = {
        'id': 1,
        'username': 'testuser',
        'created_at': '2026-02-25T10:00:00Z',
      };
      
      final user = UserResponse.fromJson(json);
      
      expect(user.id, 1);
      expect(user.username, 'testuser');
      expect(user.createdAt, isNotNull);
    });
    
    test('fromJson 处理空 createdAt', () {
      final json = {
        'id': 1,
        'username': 'testuser',
      };
      
      final user = UserResponse.fromJson(json);
      
      expect(user.id, 1);
      expect(user.username, 'testuser');
      expect(user.createdAt, isNull);
    });
    
    test('toJson 正确序列化', () {
      final user = UserResponse(
        id: 1,
        username: 'testuser',
        createdAt: DateTime.parse('2026-02-25T10:00:00Z'),
      );
      
      final json = user.toJson();
      
      expect(json['id'], 1);
      expect(json['username'], 'testuser');
      expect(json['created_at'], isNotNull);
    });
  });
  
  group('TokenResponse Model Tests', () {
    test('fromJson 正确解析数据', () {
      final json = {
        'access_token': 'test_token_123',
        'token_type': 'bearer',
      };
      
      final token = TokenResponse.fromJson(json);
      
      expect(token.accessToken, 'test_token_123');
      expect(token.tokenType, 'bearer');
    });
    
    test('fromJson 使用默认 tokenType', () {
      final json = {
        'access_token': 'test_token_123',
      };
      
      final token = TokenResponse.fromJson(json);
      
      expect(token.accessToken, 'test_token_123');
      expect(token.tokenType, 'bearer');
    });
    
    test('toJson 正确序列化', () {
      final token = TokenResponse(
        accessToken: 'test_token',
        tokenType: 'bearer',
      );
      
      final json = token.toJson();
      
      expect(json['access_token'], 'test_token');
      expect(json['token_type'], 'bearer');
    });
  });
  
  group('LoginRequest Model Tests', () {
    test('toJson 正确序列化', () {
      final request = LoginRequest(
        username: 'testuser',
        password: 'password123',
      );
      
      final json = request.toJson();
      
      expect(json['username'], 'testuser');
      expect(json['password'], 'password123');
    });
    
    test('toFormData 正确序列化为表单数据', () {
      final request = LoginRequest(
        username: 'testuser',
        password: 'password123',
      );
      
      final formData = request.toFormData();
      
      expect(formData['username'], 'testuser');
      expect(formData['password'], 'password123');
    });
  });
  
  group('RegisterRequest Model Tests', () {
    test('toJson 正确序列化', () {
      final request = RegisterRequest(
        username: 'newuser',
        password: 'newpass123',
      );
      
      final json = request.toJson();
      
      expect(json['username'], 'newuser');
      expect(json['password'], 'newpass123');
    });
  });
}
