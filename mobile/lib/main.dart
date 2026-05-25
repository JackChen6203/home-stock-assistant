import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

const String _defaultApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://home-stock-api.onrender.com',
);

void main() {
  runApp(const HomeStockApp());
}

class HomeStockApp extends StatelessWidget {
  const HomeStockApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Home Stock Assistant',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.green),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final baseUrlCtl = TextEditingController(text: _defaultApiBaseUrl);
  final emailCtl = TextEditingController();
  final pwdCtl = TextEditingController(text: '1234');
  final nameCtl = TextEditingController();
  final itemCtl = TextEditingController();

  String token = '';
  Map<String, dynamic> items = {'personal': [], 'family': []};
  String status = '';

  String get apiBaseUrl => baseUrlCtl.text.trim().replaceAll(RegExp(r'/+$'), '');

  Dio get dio => Dio(BaseOptions(baseUrl: apiBaseUrl));

  Map<String, String> get authHeaders => token.isEmpty ? {} : {'Authorization': 'Bearer $token'};

  String describeDioError(DioException e) {
    final response = e.response;
    if (response != null) {
      final data = response.data;
      final detail = data is Map && data['detail'] != null ? data['detail'].toString() : data.toString();
      return 'HTTP ${response.statusCode}: $detail';
    }
    return e.message ?? e.type.name;
  }

  @override
  void dispose() {
    baseUrlCtl.dispose();
    emailCtl.dispose();
    pwdCtl.dispose();
    nameCtl.dispose();
    itemCtl.dispose();
    super.dispose();
  }

  Future<void> register() async {
    try {
      final r = await dio.post('/auth/register', data: {'email': emailCtl.text, 'password': pwdCtl.text, 'name': nameCtl.text});
      setState(() => status = '註冊成功 user=${r.data['user_id']}');
    } on DioException catch (e) {
      setState(() => status = '註冊失敗：${describeDioError(e)}');
    }
  }

  Future<void> login() async {
    try {
      final r = await dio.post('/auth/login', data: {'email': emailCtl.text, 'password': pwdCtl.text});
      setState(() {
        token = r.data['token'];
        status = '登入成功';
      });
      await fetchItems();
    } on DioException catch (e) {
      setState(() => status = '登入失敗：${describeDioError(e)}');
    }
  }

  Future<void> addItem(String type) async {
    try {
      await dio.post('/items',
          data: {'name': itemCtl.text, 'qty_needed': 1, 'list_type': type},
          options: Options(headers: authHeaders));
      await fetchItems();
    } on DioException catch (e) {
      setState(() => status = '新增失敗：${describeDioError(e)}');
    }
  }

  Future<void> buy(String type) async {
    try {
      await dio.post('/purchase',
          data: {'item_name': itemCtl.text, 'for_list_type': type},
          options: Options(headers: authHeaders));
      await fetchItems();
    } on DioException catch (e) {
      setState(() => status = '購買失敗：${describeDioError(e)}');
    }
  }

  Future<void> fetchItems() async {
    if (token.isEmpty) {
      setState(() => status = '請先登入再刷新清單');
      return;
    }
    try {
      final r = await dio.get('/items/me', options: Options(headers: authHeaders));
      setState(() => items = Map<String, dynamic>.from(r.data));
    } on DioException catch (e) {
      setState(() => status = '讀取清單失敗：${describeDioError(e)}');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home Stock Assistant MVP')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: ListView(children: [
          TextField(
            controller: baseUrlCtl,
            decoration: const InputDecoration(
              labelText: 'API Base URL',
              helperText: '預設連到 Render；可改成你的實際 API 網址',
            ),
          ),
          TextField(controller: emailCtl, decoration: const InputDecoration(labelText: 'Email')),
          TextField(controller: pwdCtl, decoration: const InputDecoration(labelText: 'Password')),
          TextField(controller: nameCtl, decoration: const InputDecoration(labelText: 'Name (註冊用)')),
          Row(children: [
            ElevatedButton(onPressed: register, child: const Text('註冊')),
            const SizedBox(width: 8),
            ElevatedButton(onPressed: login, child: const Text('登入')),
          ]),
          const Divider(),
          TextField(controller: itemCtl, decoration: const InputDecoration(labelText: '品項（如 阿猴鮮奶 / 蘋果）')),
          Wrap(spacing: 8, children: [
            ElevatedButton(onPressed: token.isEmpty ? null : () => addItem('personal'), child: const Text('加到個人')),
            ElevatedButton(onPressed: token.isEmpty ? null : () => addItem('family'), child: const Text('加到家用')),
            ElevatedButton(onPressed: token.isEmpty ? null : () => buy('personal'), child: const Text('個人購買')),
            ElevatedButton(onPressed: token.isEmpty ? null : () => buy('family'), child: const Text('家用購買')),
            OutlinedButton(onPressed: token.isEmpty ? null : fetchItems, child: const Text('刷新清單')),
          ]),
          Text('API: ${apiBaseUrl.isEmpty ? "未設定" : apiBaseUrl}'),
          Text('狀態: $status'),
          Text(token.isEmpty ? '登入後才可操作清單' : 'Token: ${token.substring(0, token.length > 16 ? 16 : token.length)}...'),
          Text('Personal: ${items['personal']}'),
          Text('Family: ${items['family']}'),
          const SizedBox(height: 20),
          const Text('Siri：請用快捷指令 POST /voice/siri 並帶 Bearer token'),
        ]),
      ),
    );
  }
}
