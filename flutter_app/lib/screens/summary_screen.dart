import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/summary.dart';

class SummaryScreen extends StatelessWidget {
  final Summary summary;

  const SummaryScreen({super.key, required this.summary});

  String _langLabel() {
    switch (summary.language) {
      case 'urdu':
        return '🇵🇰 Urdu';
      case 'both':
        return '🌐 Both';
      default:
        return '🇬🇧 English';
    }
  }

  String _typeLabel() {
    switch (summary.summaryType) {
      case 'brief':
        return '📝 Brief';
      case 'bullet':
        return '• Bullet';
      default:
        return '🔍 Detailed';
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Summary'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.download),
            onSelected: (fmt) => _export(context, fmt),
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'txt', child: ListTile(leading: Icon(Icons.description), title: Text('TXT'))),
              PopupMenuItem(value: 'json', child: ListTile(leading: Icon(Icons.code), title: Text('JSON'))),
              PopupMenuItem(value: 'md', child: ListTile(leading: Icon(Icons.article), title: Text('Markdown'))),
            ],
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Title & metadata
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(summary.title, style: t.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                    if (summary.sourceUrl.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      SelectableText(
                        '🔗 ${summary.sourceUrl}',
                        style: TextStyle(fontSize: 13, color: t.colorScheme.primary),
                      ),
                    ],
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: [
                        _Badge(_langLabel()),
                        _Badge(_typeLabel()),
                        _Badge(summary.filetype),
                        _Badge(summary.filesizeFormatted),
                        _Badge('📝 ${summary.wordCount} words'),
                        _Badge('⚡ ${summary.processingTime.toStringAsFixed(1)}s'),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Summary text
            Text('📝 Summary', style: t.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: SelectableText(
                  summary.summary,
                  style: TextStyle(
                    fontSize: summary.language == 'urdu' ? 20 : 15,
                    height: summary.language == 'urdu' ? 2.0 : 1.6,
                  ),
                  textDirection: summary.language == 'urdu' ? TextDirection.rtl : TextDirection.ltr,
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Key findings
            if (summary.keyPoints.isNotEmpty) ...[
              Text('🔑 Key Findings', style: t.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: summary.keyPoints.map((p) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('✦ ', style: TextStyle(color: t.colorScheme.primary)),
                          Expanded(child: Text(p)),
                        ],
                      ),
                    )).toList(),
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Citations
            if (summary.citations.isNotEmpty) ...[
              Text('📚 Citations', style: t.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: summary.citations.take(10).toList().asMap().entries.map((e) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: SelectableText('[${e.key + 1}] ${e.value}'),
                    )).toList(),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  void _export(BuildContext context, String fmt) {
    String content;
    switch (fmt) {
      case 'json':
        content = const JsonEncoder.withIndent('  ').convert(summary.toJson());
        break;
      case 'md':
        content = '# ${summary.title}\n\n## Summary\n${summary.summary}\n\n## Key Findings\n${summary.keyPoints.map((p) => '- $p').join('\n')}';
        break;
      default:
        content = 'Title: ${summary.title}\n\n${summary.summary}\n\nKey Findings:\n${summary.keyPoints.map((p) => '- $p').join('\n')}';
    }
    Clipboard.setData(ClipboardData(text: content));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Copied as $fmt')),
    );
  }
}

class _Badge extends StatelessWidget {
  final String text;
  const _Badge(this.text);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.secondaryContainer,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(text, style: const TextStyle(fontSize: 12)),
    );
  }
}
