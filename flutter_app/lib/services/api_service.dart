import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import '../models/summary.dart';

class ApiService {
  static String baseUrl = 'http://localhost:8000';

  static void setBaseUrl(String url) {
    baseUrl = url;
  }

  static Future<Summary> summarize({
    required PlatformFile file,
    required String language,
    required String summaryType,
  }) async {
    final uri = Uri.parse('$baseUrl/summarize');
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

    final streamed = await request.send();
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
    final uri = Uri.parse('$baseUrl/summarize-url');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'url': url,
        'language': language,
        'summary_type': summaryType,
      }),
    );

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
    try {
      final uri = Uri.parse('$baseUrl/history');
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        final list = jsonDecode(response.body) as List;
        return list.map((e) => HistoryItem.fromJson(e as Map<String, dynamic>)).toList();
      }
    } catch (_) {}
    return [];
  }

  static Future<Summary?> getSummary(String id) async {
    try {
      final uri = Uri.parse('$baseUrl/summary/$id');
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        return Summary.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
      }
    } catch (_) {}
    return null;
  }

  static Future<bool> deleteSummary(String id) async {
    try {
      final uri = Uri.parse('$baseUrl/summary/$id');
      final response = await http.delete(uri);
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  static Future<String?> exportSummary(String id, {String fmt = 'txt'}) async {
    try {
      final uri = Uri.parse('$baseUrl/export/$id?fmt=$fmt');
      final response = await http.get(uri);
      if (response.statusCode == 200) {
        return response.body;
      }
    } catch (_) {}
    return null;
  }
}
