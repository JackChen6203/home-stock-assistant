import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

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
  final baseUrlCtl = TextEditingController(text: 'https://YOUR-RENDER-APP.onrender.com');
  final emailCtl = TextEditingController();
  final pwdCtl = TextEditingController(text: '1234');
  final nameCtl = TextEditingController();
  final itemCtl = TextEditingController();

  String token = '';
  Map<String, dynamic> items = {'personal': [], 'family': []};
  String status = '';

  Dio get dio => Dio(BaseOptions(baseUrl: baseUrlCtl.text.trim()));

  Future<void> register() async {
    final r = await dio.post('/auth/register', data: {'email': emailCtl.text, 'password': pwdCtl.text, 'name': nameCtl.text});
    setState(() => status = '註冊成功 user=${r.data['user_id']}');
  }

  Future<void> login() async {
    final r = await dio.post('/auth/login', data: {'email': emailCtl.text, 'password': pwdCtl.text});
    setState(() {
      token = r.data['token'];
      status = '登入成功';
    });
    await fetchItems();
  }

  Future<void> addItem(String type) async {
    await dio.post('/items',
        data: {'name': itemCtl.text, 'qty_needed': 1, 'list_type': type},
        options: Options(headers: {'Authorization': 'Bearer $token'}));
    await fetchItems();
  }

  Future<void> buy(String type) async {
    await dio.post('/purchase',
        data: {'item_name': itemCtl.text, 'for_list_type': type},
        options: Options(headers: {'Authorization': 'Bearer $token'}));
    await fetchItems();
  }

  Future<void> fetchItems() async {
    final r = await dio.get('/items/me', options: Options(headers: {'Authorization': 'Bearer $token'}));
    setState(() => items = Map<String, dynamic>.from(r.data));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home Stock Assistant MVP')),
      body: Padding(
        padding: const EdgeInsets.all(12),
        child: ListView(children: [
          TextField(controller: baseUrlCtl, decoration: const InputDecoration(labelText: 'API Base URL')),
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
            ElevatedButton(onPressed: () => addItem('personal'), child: const Text('加到個人')),
            ElevatedButton(onPressed: () => addItem('family'), child: const Text('加到家用')),
            ElevatedButton(onPressed: () => buy('personal'), child: const Text('個人購買')),
            ElevatedButton(onPressed: () => buy('family'), child: const Text('家用購買')),
            OutlinedButton(onPressed: fetchItems, child: const Text('刷新清單')),
          ]),
          Text('狀態: $status'),
          Text('Personal: ${items['personal']}'),
          Text('Family: ${items['family']}'),
          const SizedBox(height: 20),
          const Text('Siri：請用快捷指令 POST /voice/siri 並帶 Bearer token'),
        ]),
      ),
    );
  }
}
