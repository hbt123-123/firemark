/// 用户响应数据模型
class UserResponse {
  final int id;
  final String username;
  final DateTime? createdAt;

  UserResponse({
    required this.id,
    required this.username,
    this.createdAt,
  });

  factory UserResponse.fromJson(Map<String, dynamic> json) {
    return UserResponse(
      id: json['id'] as int,
      username: json['username'] as String,
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'created_at': createdAt?.toIso8601String(),
    };
  }
}

/// Token响应数据模型
class TokenResponse {
  final String accessToken;
  final String tokenType;

  TokenResponse({
    required this.accessToken,
    required this.tokenType,
  });

  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'access_token': accessToken,
      'token_type': tokenType,
    };
  }
}

/// 登录请求数据模型
class LoginRequest {
  final String username;
  final String password;

  LoginRequest({
    required this.username,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'username': username,
      'password': password,
    };
  }

  Map<String, String> toFormData() {
    return {
      'username': username,
      'password': password,
    };
  }
}

/// 注册请求数据模型
class RegisterRequest {
  final String username;
  final String password;

  RegisterRequest({
    required this.username,
    required this.password,
  });

  Map<String, dynamic> toJson() {
    return {
      'username': username,
      'password': password,
    };
  }
}
