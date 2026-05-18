import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';
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
            _buildTitleCard(context),
            const SizedBox(height: 16),
            if (summary.summary.isNotEmpty) _buildSection(context, '📝 Summary', summary.summary, isUrdu: summary.language == 'urdu'),
            if (summary.researchObjective.isNotEmpty) ...[const SizedBox(height: 12), _buildSection(context, '🎯 Research Objective', summary.researchObjective)],
            if (summary.methodology.isNotEmpty) ...[const SizedBox(height: 12), _buildSection(context, '🔬 Methodology', summary.methodology)],
            if (summary.keyFindings.isNotEmpty) ...[const SizedBox(height: 12), _buildListSection(context, '🔑 Key Findings', summary.keyFindings)],
            if (summary.keyTakeaways.isNotEmpty) ...[const SizedBox(height: 12), _buildListSection(context, '💡 Key Takeaways', summary.keyTakeaways)],
            if (summary.strengths.isNotEmpty) ...[const SizedBox(height: 12), _buildListSection(context, '✅ Strengths', summary.strengths)],
            if (summary.weaknesses.isNotEmpty) ...[const SizedBox(height: 12), _buildListSection(context, '⚠️ Weaknesses', summary.weaknesses)],
            if (summary.novelty.isNotEmpty) ...[const SizedBox(height: 12), _buildSection(context, '🌟 Novelty', summary.novelty)],
            if (summary.researchGaps.isNotEmpty) ...[const SizedBox(height: 12), _buildListSection(context, '🔍 Research Gaps', summary.researchGaps)],
            if (summary.futureDirections.isNotEmpty) ...[const SizedBox(height: 12), _buildListSection(context, '🚀 Future Directions', summary.futureDirections)],
            if (summary.practicalImplications.isNotEmpty) ...[const SizedBox(height: 12), _buildSection(context, '💼 Practical Implications', summary.practicalImplications)],
            if (summary.conclusion.isNotEmpty) ...[const SizedBox(height: 12), _buildSection(context, '📌 Conclusion', summary.conclusion)],
            if (summary.citations.isNotEmpty) ...[const SizedBox(height: 16), _buildCitations(context)],
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildTitleCard(BuildContext context) {
    final t = Theme.of(context);
    return Card(
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
                if (summary.difficultyLevel.isNotEmpty) _Badge(summary.difficultyLevel),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(BuildContext context, String title, String content, {bool isUrdu = false}) {
    final t = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: t.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: SelectableText(
              content,
              style: TextStyle(
                fontSize: isUrdu ? 20 : 15,
                height: isUrdu ? 2.0 : 1.6,
              ),
              textDirection: isUrdu ? TextDirection.rtl : TextDirection.ltr,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildListSection(BuildContext context, String title, List<String> items) {
    final t = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title, style: t.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: items.map((p) => Padding(
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
      ],
    );
  }

  Widget _buildCitations(BuildContext context) {
    final t = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
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
    );
  }

  Future<void> _export(BuildContext context, String fmt) async {
    String content;
    switch (fmt) {
      case 'json':
        content = const JsonEncoder.withIndent('  ').convert(summary.toJson());
        break;
      case 'md':
        content = _toMarkdown();
        break;
      default:
        content = _toText();
    }

    try {
      final dir = await getApplicationDocumentsDirectory();
      final ext = fmt == 'md' ? 'md' : fmt;
      final fname = 'summary_${summary.id}.$ext';
      final file = File('${dir.path}/$fname');
      await file.writeAsString(content);

      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Saved to Documents/$fname'),
            action: SnackBarAction(
              label: 'Copy',
              onPressed: () {
                Clipboard.setData(ClipboardData(text: content));
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Copied to clipboard')),
                );
              },
            ),
          ),
        );
      }
    } catch (e) {
      Clipboard.setData(ClipboardData(text: content));
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Copied as $fmt (file save failed)')),
        );
      }
    }
  }

  String _toText() {
    final buf = StringBuffer()
      ..writeln(summary.title)
      ..writeln('=' * 60)
      ..writeln()
      ..writeln('SUMMARY')
      ..writeln(summary.summary)
      ..writeln();
    if (summary.researchObjective.isNotEmpty) {
      buf.writeln('RESEARCH OBJECTIVE');
      buf.writeln(summary.researchObjective);
      buf.writeln();
    }
    if (summary.methodology.isNotEmpty) {
      buf.writeln('METHODOLOGY');
      buf.writeln(summary.methodology);
      buf.writeln();
    }
    if (summary.keyFindings.isNotEmpty) {
      buf.writeln('KEY FINDINGS');
      for (final f in summary.keyFindings) buf.writeln('  * $f');
      buf.writeln();
    }
    if (summary.conclusion.isNotEmpty) {
      buf.writeln('CONCLUSION');
      buf.writeln(summary.conclusion);
    }
    return buf.toString();
  }

  String _toMarkdown() {
    final buf = StringBuffer()
      ..writeln('# ${summary.title}')
      ..writeln()
      ..writeln('## Summary')
      ..writeln(summary.summary)
      ..writeln();
    if (summary.researchObjective.isNotEmpty) {
      buf.writeln('## Research Objective');
      buf.writeln(summary.researchObjective);
      buf.writeln();
    }
    if (summary.methodology.isNotEmpty) {
      buf.writeln('## Methodology');
      buf.writeln(summary.methodology);
      buf.writeln();
    }
    if (summary.keyFindings.isNotEmpty) {
      buf.writeln('## Key Findings');
      for (final f in summary.keyFindings) buf.writeln('- $f');
      buf.writeln();
    }
    if (summary.conclusion.isNotEmpty) {
      buf.writeln('## Conclusion');
      buf.writeln(summary.conclusion);
    }
    return buf.toString();
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
