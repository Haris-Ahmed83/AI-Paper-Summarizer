import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/api_service.dart';
import 'summary_screen.dart';

class HomeScreen extends StatefulWidget {
  final VoidCallback onToggleTheme;
  final bool isDark;
  final VoidCallback? onHistoryRefresh;

  const HomeScreen({
    super.key,
    required this.onToggleTheme,
    required this.isDark,
    this.onHistoryRefresh,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  PlatformFile? _file;
  String _language = 'english';
  String _summaryType = 'detailed';
  bool _loading = false;
  String _statusMessage = '';
  int _inputMode = 0;
  final _urlController = TextEditingController();

  static const _langLabels = {
    'english': '🇬🇧 English',
    'urdu': '🇵🇰 Urdu',
    'both': '🌐 Both',
  };
  static const _typeLabels = {
    'detailed': '🔍 Detailed',
    'brief': '📝 Brief',
    'bullet': '• Bullet',
  };

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'txt'],
      withData: true,
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() => _file = result.files.first);
    }
  }

  Future<void> _summarize() async {
    if (_inputMode == 0 && _file == null) {
      _showError('Please select a file first');
      return;
    }
    if (_inputMode == 1 && _urlController.text.trim().isEmpty) {
      _showError('Please enter a URL');
      return;
    }
    setState(() {
      _loading = true;
      _statusMessage = _inputMode == 0 ? 'Uploading file...' : 'Fetching URL...';
    });

    try {
      // Simulate steps for better UX
      await Future.delayed(const Duration(milliseconds: 500));
      if (mounted) setState(() => _statusMessage = 'AI is analyzing the paper...');

      final summary = _inputMode == 0
          ? await ApiService.summarize(
              file: _file!,
              language: _language,
              summaryType: _summaryType,
            )
          : await ApiService.summarizeUrl(
              url: _urlController.text.trim(),
              language: _language,
              summaryType: _summaryType,
            );

      if (mounted) {
        widget.onHistoryRefresh?.call();
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => SummaryScreen(summary: summary),
          ),
        );
      }
    } catch (e) {
      _showError(e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() { _loading = false; _statusMessage = ''; });
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: Theme.of(context).colorScheme.error,
        action: SnackBarAction(
          label: 'Retry',
          textColor: Colors.white,
          onPressed: _summarize,
        ),
        duration: const Duration(seconds: 5),
      ),
    );
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
      appBar: AppBar(
        title: const Text('AI Paper Summarizer'),
        actions: [
          IconButton(
            icon: Icon(widget.isDark ? Icons.light_mode : Icons.dark_mode),
            onPressed: widget.onToggleTheme,
            tooltip: widget.isDark ? 'Light mode' : 'Dark mode',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _buildHeader(context),
            const SizedBox(height: 24),
            _buildLanguageCard(context),
            const SizedBox(height: 12),
            _buildTypeCard(context),
            const SizedBox(height: 12),
            _buildInputModeCard(context),
            const SizedBox(height: 12),
            _buildInputArea(context),
            const SizedBox(height: 24),
            _buildSubmitButton(context),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final t = Theme.of(context);
    final cs = t.colorScheme;
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [cs.primary, cs.tertiary],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('📄 AI Paper Summarizer Pro',
              style: t.textTheme.headlineSmall?.copyWith(
                color: cs.onPrimary,
                fontWeight: FontWeight.bold,
              )),
          const SizedBox(height: 8),
          Text(
            'Upload files or paste URLs — AI summaries in English & Urdu',
            style: t.textTheme.bodyMedium?.copyWith(
              color: cs.onPrimary.withValues(alpha: 0.85),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageCard(BuildContext context) {
    final t = Theme.of(context);
    final cs = t.colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('🌐 Language / زبان',
                style: t.textTheme.titleSmall?.copyWith(
                  color: cs.primary,
                  fontWeight: FontWeight.bold,
                )),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: _langLabels.entries.map((e) {
                return ButtonSegment(value: e.key, label: Text(e.value));
              }).toList(),
              selected: {_language},
              onSelectionChanged: (s) => setState(() => _language = s.first),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTypeCard(BuildContext context) {
    final t = Theme.of(context);
    final cs = t.colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('📋 Summary Type',
                style: t.textTheme.titleSmall?.copyWith(
                  color: cs.primary,
                  fontWeight: FontWeight.bold,
                )),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: _typeLabels.entries.map((e) {
                return ButtonSegment(value: e.key, label: Text(e.value));
              }).toList(),
              selected: {_summaryType},
              onSelectionChanged: (s) => setState(() => _summaryType = s.first),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputModeCard(BuildContext context) {
    final t = Theme.of(context);
    final cs = t.colorScheme;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('📤 Input Mode',
                style: t.textTheme.titleSmall?.copyWith(
                  color: cs.primary,
                  fontWeight: FontWeight.bold,
                )),
            const SizedBox(height: 12),
            SegmentedButton<int>(
              segments: const [
                ButtonSegment(value: 0, label: Text('📄 File')),
                ButtonSegment(value: 1, label: Text('🔗 URL')),
              ],
              selected: {_inputMode},
              onSelectionChanged: (s) => setState(() => _inputMode = s.first),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputArea(BuildContext context) {
    final t = Theme.of(context);
    final cs = t.colorScheme;

    if (_inputMode == 0) {
      return Card(
        child: InkWell(
          onTap: _pickFile,
          borderRadius: BorderRadius.circular(16),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: _file == null
                ? Column(
                    children: [
                      Icon(Icons.upload_file, size: 48, color: cs.primary),
                      const SizedBox(height: 12),
                      Text('Tap to select PDF or TXT file',
                          style: t.textTheme.bodyLarge),
                      const SizedBox(height: 4),
                      Text('Up to 50MB', style: t.textTheme.bodySmall?.copyWith(color: cs.outline)),
                    ],
                  )
                : Row(
                    children: [
                      Text(_file!.name.endsWith('.pdf') ? '📄' : '📃',
                          style: const TextStyle(fontSize: 32)),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(_file!.name, style: t.textTheme.bodyLarge?.copyWith(fontWeight: FontWeight.w600)),
                            Text(
                              _fmtSize(_file!.size),
                              style: t.textTheme.bodySmall?.copyWith(color: cs.outline),
                            ),
                          ],
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close),
                        onPressed: () => setState(() => _file = null),
                      ),
                    ],
                  ),
          ),
        ),
      );
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: TextField(
          controller: _urlController,
          decoration: const InputDecoration(
            hintText: 'https://example.com/paper',
            labelText: 'Paste URL',
            prefixIcon: Icon(Icons.link),
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.url,
        ),
      ),
    );
  }

  Widget _buildSubmitButton(BuildContext context) {
    final canSubmit = !_loading &&
        ((_inputMode == 0 && _file != null) ||
            (_inputMode == 1 && _urlController.text.trim().isNotEmpty));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (_loading && _statusMessage.isNotEmpty)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                    const SizedBox(width: 12),
                    Text(_statusMessage, style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
            ),
          ),
        FilledButton.icon(
          onPressed: canSubmit ? _summarize : null,
          icon: _loading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Icon(Icons.auto_awesome),
          label: Text(_loading ? 'Analyzing...' : '🚀 Generate Summary'),
        ),
      ],
    );
  }

  String _fmtSize(int bytes) {
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
