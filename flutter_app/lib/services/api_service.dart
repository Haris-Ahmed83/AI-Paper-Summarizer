import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/summary.dart';

class ApiService {
  static String _baseUrl = 'http://localhost:8000';

  static Future<String> getBaseUrl() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString('server_url') ?? 'http://localhost:8000';
    return _baseUrl;
  }

  static Future<void> setBaseUrl(String url) async {
    _baseUrl = url.endsWith('/') ? url.substring(0, url.length - 1) : url;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', _baseUrl);
  }

  static Future<Summary> summarize({
    required PlatformFile file,
    required String language,
    required String summaryType,
  }) async {
    await getBaseUrl();
    final uri = Uri.parse('$_baseUrl/summarize');
    final request = http.MultipartRequest('POST', uri);

    request.fields['language'] = language;
    request.fields['summary_type'] = summaryType;

    bool hasPath = false;
    try { hasPath = file.path != null; } catch (_) {}
    if (hasPath && file.path != null) {
      request.files.add(await http.MultipartFile.fromPath('file', file.path!));
    } else if (file.bytes != null) {
      request.files.add(http.MultipartFile.fromBytes(
        'file',
        file.bytes!,
        filename: file.name,
      ));
    }

    final streamed = await request.send().timeout(const Duration(seconds: 180));
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return Summary.fromJson(json);
    } else {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      final detail = body['detail'] as String? ?? 'HTTP ${response.statusCode}';
      throw Exception(detail);
    }
  }

  static Future<Summary> summarizeUrl({
    required String url,
    required String language,
    required String summaryType,
  }) async {
    await getBaseUrl();
    final uri = Uri.parse('$_baseUrl/summarize-url');
    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'url': url,
            'language': language,
            'summary_type': summaryType,
          }),
        )
        .timeout(const Duration(seconds: 180));

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return Summary.fromJson(json);
    } else {
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      final detail = body['detail'] as String? ?? 'HTTP ${response.statusCode}';
      throw Exception(detail);
    }
  }

  static Future<List<HistoryItem>> getHistory() async {
    await getBaseUrl();
    try {
      final uri = Uri.parse('$_baseUrl/history');
      final response = await http.get(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode == 200) {
        final list = jsonDecode(response.body) as List;
        return list.map((e) => HistoryItem.fromJson(e as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<Summary?> getSummary(String id) async {
    await getBaseUrl();
    try {
      final uri = Uri.parse('$_baseUrl/summary/$id');
      final response = await http.get(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode == 200) {
        return Summary.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> deleteSummary(String id) async {
    await getBaseUrl();
    try {
      final uri = Uri.parse('$_baseUrl/summary/$id');
      final response = await http.delete(uri).timeout(const Duration(seconds: 10));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<String?> exportSummary(String id, {String fmt = 'txt'}) async {
    await getBaseUrl();
    try {
      final uri = Uri.parse('$_baseUrl/export/$id?fmt=$fmt');
      final response = await http.get(uri).timeout(const Duration(seconds: 15));
      if (response.statusCode == 200) {
        return response.body;
      }
    } catch (_) {}
    return null;
  }
}
