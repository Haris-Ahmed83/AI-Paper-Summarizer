import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _urlController = TextEditingController();
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _loadUrl();
  }

  Future<void> _loadUrl() async {
    final url = await ApiService.getBaseUrl();
    _urlController.text = url;
    setState(() => _loading = false);
  }

  Future<void> _save() async {
    final url = _urlController.text.trim();
    if (url.isEmpty) return;
    setState(() => _saving = true);
    await ApiService.setBaseUrl(url);
    if (mounted) {
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Server URL saved')),
      );
      Navigator.pop(context);
    }
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);
    final cs = t.colorScheme;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.dns, color: cs.primary),
                              const SizedBox(width: 8),
                              Text('Server Configuration',
                                  style: t.textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: cs.primary,
                                  )),
                            ],
                          ),
                          const SizedBox(height: 16),
                          TextField(
                            controller: _urlController,
                            decoration: const InputDecoration(
                              labelText: 'Server URL',
                              hintText: 'http://localhost:8000',
                              prefixIcon: Icon(Icons.link),
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: TextInputType.url,
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'For Hugging Face: https://haris-83-ai-paper-summarizer.hf.space',
                            style: t.textTheme.bodySmall?.copyWith(color: cs.outline),
                          ),
                          const SizedBox(height: 20),
                          FilledButton.icon(
                            onPressed: _saving ? null : _save,
                            icon: _saving
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2, color: Colors.white),
                                  )
                                : const Icon(Icons.save),
                            label: Text(_saving ? 'Saving...' : 'Save'),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.info_outline, color: cs.primary),
                              const SizedBox(width: 8),
                              Text('About',
                                  style: t.textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.bold,
                                    color: cs.primary,
                                  )),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text('AI Paper Summarizer Pro v3.1',
                              style: t.textTheme.bodyMedium?.copyWith(
                                fontWeight: FontWeight.w600,
                              )),
                          const SizedBox(height: 4),
                          Text(
                            'Multi-provider AI summarization (Groq, Gemini, Grok).\n'
                            'Supports PDF, TXT, and URL input.\n'
                            'English & Urdu languages.',
                            style: t.textTheme.bodySmall?.copyWith(color: cs.outline),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
