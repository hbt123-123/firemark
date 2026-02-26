/// 评论类型枚举
enum CommentType {
  comment,  // 普通评论
  like,     // 点赞
}

extension CommentTypeExtension on CommentType {
  String get apiValue {
    switch (this) {
      case CommentType.comment:
        return 'comment';
      case CommentType.like:
        return 'like';
    }
  }

  static CommentType fromString(String? value) {
    switch (value?.toLowerCase()) {
      case 'like':
        return CommentType.like;
      default:
        return CommentType.comment;
    }
  }
}

/// 评论数据模型
class Comment {
  final int id;
  final int taskId;
  final int userId;
  final String? username;
  final String content;
  final CommentType type;
  final DateTime? createdAt;

  Comment({
    required this.id,
    required this.taskId,
    required this.userId,
    this.username,
    required this.content,
    this.type = CommentType.comment,
    this.createdAt,
  });

  factory Comment.fromJson(Map<String, dynamic> json) {
    return Comment(
      id: json['id'] as int,
      taskId: json['task_id'] as int,
      userId: json['user_id'] as int,
      username: json['username'] as String?,
      content: json['content'] as String,
      type: CommentTypeExtension.fromString(json['type'] as String?),
      createdAt: json['created_at'] != null
          ? DateTime.parse(json['created_at'] as String)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'task_id': taskId,
      'user_id': userId,
      'content': content,
      'type': type.apiValue,
    };
  }

  /// 创建新评论时的请求数据
  Map<String, dynamic> toCreateJson() {
    return {
      'content': content,
      'type': type.apiValue,
    };
  }

  /// 判断是否是点赞
  bool get isLike => type == CommentType.like;
}
