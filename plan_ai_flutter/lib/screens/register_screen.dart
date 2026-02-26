import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import 'home_screen.dart';

/// 注册页面
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _usernameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void dispose() {
    _usernameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final username = _usernameController.text.trim();
    final password = _passwordController.text;

    try {
      final authProvider = context.read<AuthProvider>();
      await authProvider.register(username, password);

      if (mounted) {
        // Show success message - AuthWrapper will auto-navigate
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('注册成功！欢迎使用 Plan AI'),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      final authProvider = context.read<AuthProvider>();
      await authProvider.register(username, password);

      if (mounted) {
        // 注册成功，跳转到主页
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const HomeScreen()),
          (route) => false,
        );
        
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('注册成功！欢迎使用 Plan AI'),
            backgroundColor: Colors.green,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString()),
            backgroundColor: Colors.red,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  void _navigateBack() {
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('注册'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: _navigateBack,
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // App Logo/Title
                  Icon(
                    Icons.task_alt,
                    size: 60,
                    color: Theme.of(context).primaryColor,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '创建账号',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '开始使用 Plan AI 智能学习计划',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  const SizedBox(height: 32),

                  // 用户名输入框
                  TextFormField(
                    controller: _usernameController,
                    decoration: const InputDecoration(
                      labelText: '用户名',
                      prefixIcon: Icon(Icons.person_outline),
                      border: OutlineInputBorder(),
                      hintText: '3-80个字符',
                    ),
                    textInputAction: TextInputAction.next,
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return '请输入用户名';
                      }
                      if (value.length < 3) {
                        return '用户名至少3个字符';
                      }
                      if (value.length > 80) {
                        return '用户名不能超过80个字符';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),

                  // 密码输入框
                  TextFormField(
                    controller: _passwordController,
                    decoration: InputDecoration(
                      labelText: '密码',
                      prefixIcon: const Icon(Icons.lock_outline),
                      border: const OutlineInputBorder(),
                      hintText: '至少6个字符',
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePassword
                              ? Icons.visibility_off
                              : Icons.visibility,
                        ),
                        onPressed: () {
                          setState(() {
                            _obscurePassword = !_obscurePassword;
                          });
                        },
                      ),
                    ),
                    obscureText: _obscurePassword,
                    textInputAction: TextInputAction.next,
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return '请输入密码';
                      }
                      if (value.length < 6) {
                        return '密码至少6个字符';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),

                  // 确认密码输入框
                  TextFormField(
                    controller: _confirmPasswordController,
                    decoration: InputDecoration(
                      labelText: '确认密码',
                      prefixIcon: const Icon(Icons.lock_outline),
                      border: const OutlineInputBorder(),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscureConfirmPassword
                              ? Icons.visibility_off
                              : Icons.visibility,
                        ),
                        onPressed: () {
                          setState(() {
                            _obscureConfirmPassword = !_obscureConfirmPassword;
                          });
                        },
                      ),
                    ),
                    obscureText: _obscureConfirmPassword,
                    textInputAction: TextInputAction.done,
                    onFieldSubmitted: (_) => _handleRegister(),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return '请再次输入密码';
                      }
                      if (value != _passwordController.text) {
                        return '两次输入的密码不一致';
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 24),

                  // 注册按钮
                  Consumer<AuthProvider>(
                    builder: (context, auth, _) {
                      return ElevatedButton(
                        onPressed: auth.isLoading ? null : _handleRegister,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: auth.isLoading
                            ? const SizedBox(
                                height: 20,
                                width: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : const Text(
                                '注册',
                                style: TextStyle(fontSize: 16),
                              ),
                      );
                    },
                  ),
                  const SizedBox(height: 16),

                  // 登录链接
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        '已有账号? ',
                        style: TextStyle(color: Colors.grey[600]),
                      ),
                      TextButton(
                        onPressed: _navigateBack,
                        child: const Text('立即登录'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
