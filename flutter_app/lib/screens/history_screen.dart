import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/summary.dart';
import 'summary_screen.dart';

class HistoryScreen extends StatefulWidget {
  final VoidCallback onToggleTheme;
  final bool isDark;

  const HistoryScreen({
    super.key,
    required this.onToggleTheme,
    required this.isDark,
  });

  @override
  State<HistoryScreen> createState() => HistoryScreenState();
}

class HistoryScreenState extends State<HistoryScreen> {
  List<HistoryItem> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> refresh() => _load();

  Future<void> _load() async {
    setState(() => _loading = true);
    final items = await ApiService.getHistory();
    if (mounted) setState(() { _items = items; _loading = false; });
  }

  Future<void> _delete(String id) async {
    final ok = await ApiService.deleteSummary(id);
    if (!ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to delete summary')),
      );
    }
    _load();
  }

  Future<void> _open(String id) async {
    final summary = await ApiService.getSummary(id);
    if (summary != null && mounted) {
      Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => SummaryScreen(summary: summary)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('History'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
          IconButton(
            icon: Icon(widget.isDark ? Icons.light_mode : Icons.dark_mode),
            onPressed: widget.onToggleTheme,
            tooltip: widget.isDark ? 'Light mode' : 'Dark mode',
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _items.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.history, size: 64, color: t.colorScheme.outline),
                      const SizedBox(height: 16),
                      Text('No summaries yet', style: t.textTheme.titleMedium),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: _items.length,
                    itemBuilder: (_, i) {
                      final item = _items[i];
                      final flag = switch (item.language) {
                        'urdu' => '🇵🇰',
                        'both' => '🌐',
                        _ => '🇬🇧',
                      };
                      return Card(
                        margin: const EdgeInsets.symmetric(vertical: 4),
                        child: ListTile(
                          leading: Text(item.sourceUrl.isNotEmpty ? '🔗' : flag, style: const TextStyle(fontSize: 24)),
                          title: Text(item.title, maxLines: 1, overflow: TextOverflow.ellipsis),
                          subtitle: Text('${item.filetype} · ${item.filesizeFormatted} · ${item.createdAt.length >= 10 ? item.createdAt.substring(0, 10) : item.createdAt}'),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                icon: const Icon(Icons.open_in_new, size: 20),
                                onPressed: () => _open(item.id),
                              ),
                              IconButton(
                                icon: const Icon(Icons.delete_outline, size: 20),
                                onPressed: () => _delete(item.id),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
