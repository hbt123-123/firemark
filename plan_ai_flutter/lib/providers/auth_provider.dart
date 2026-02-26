import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../utils/constants.dart';

/// 认证状态
enum AuthStatus {
  unknown,
  unauthenticated,
  authenticated,
}

/// 认证Provider - 管理用户认证状态
class AuthProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
  );

  AuthStatus _status = AuthStatus.unknown;
  UserResponse? _user;
  String? _token;
  bool _isLoading = false;

  // Callback for 401 handling
  VoidCallback? onTokenExpired;

  // Getters
  AuthStatus get status => _status;
  UserResponse? get user => _user;
  String? get token => _token;
  bool get isLoading => _isLoading;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  /// 初始化 - 检查本地存储的Token
  Future<void> initialize() async {
    _isLoading = true;
    notifyListeners();

    try {
      _token = await _secureStorage.read(key: StorageKeys.accessToken);

      if (_token != null && _token!.isNotEmpty) {
        // 设置Token到API服务
        _apiService.setToken(_token);
        
        // 验证Token有效性
        try {
          _user = await _apiService.getCurrentUser();
          _status = AuthStatus.authenticated;
        } catch (e) {
          // Token无效，清除并保持未登录状态
          await _clearToken();
        }
      } else {
        _status = AuthStatus.unauthenticated;
      }
    } catch (e) {
      _status = AuthStatus.unauthenticated;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 登录
  Future<bool> login(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      final tokenResponse = await _apiService.login(username, password);
      _token = tokenResponse.accessToken;
      
      // 保存Token到安全存储
      await _saveToken(_token!);
      
      // 设置Token到API服务
      _apiService.setToken(_token);
      
      // 获取用户信息
      _user = await _apiService.getCurrentUser();
      
      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 注册
  Future<bool> register(String username, String password) async {
    _isLoading = true;
    notifyListeners();

    try {
      // 注册用户
      await _apiService.register(username, password);
      
      // 注册成功后自动登录
      await login(username, password);
      return true;
    } catch (e) {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
      rethrow;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 登出
  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      // 清除本地存储的Token
      await _clearToken();
      
      // 清除API服务的Token
      _apiService.setToken(null);
      
      _token = null;
      _user = null;
      _status = AuthStatus.unauthenticated;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// 处理Token过期
  Future<void> handleTokenExpired() async {
    await logout();
    onTokenExpired?.call();
  }

  /// 获取Token
  Future<String?> getToken() async {
    if (_token != null) {
      return _token;
    }
    
    _token = await _secureStorage.read(key: StorageKeys.accessToken);
    return _token;
  }

  /// 保存Token到安全存储
  Future<void> _saveToken(String token) async {
    await _secureStorage.write(key: StorageKeys.accessToken, value: token);
    
    // 保存用户名
    if (_user != null) {
      await _secureStorage.write(key: StorageKeys.userId, value: _user!.id.toString());
      await _secureStorage.write(key: StorageKeys.username, value: _user!.username);
    }
  }

  /// 清除Token
  Future<void> _clearToken() async {
    await _secureStorage.delete(key: StorageKeys.accessToken);
    await _secureStorage.delete(key: StorageKeys.tokenType);
    await _secureStorage.delete(key: StorageKeys.userId);
    await _secureStorage.delete(key: StorageKeys.username);
  }
}
