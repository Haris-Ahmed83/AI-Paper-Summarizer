import 'package:flutter/material.dart';
import 'theme/app_theme.dart';
import 'screens/home_screen.dart';
import 'screens/history_screen.dart';

void main() {
  runApp(const PaperSummarizerApp());
}

class PaperSummarizerApp extends StatefulWidget {
  const PaperSummarizerApp({super.key});

  @override
  State<PaperSummarizerApp> createState() => _PaperSummarizerAppState();
}

class _PaperSummarizerAppState extends State<PaperSummarizerApp> {
  bool _darkMode = false;
  int _currentIndex = 0;

  void _toggleTheme() {
    setState(() => _darkMode = !_darkMode);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI Paper Summarizer Pro',
      debugShowCheckedModeBanner: false,
      themeMode: _darkMode ? ThemeMode.dark : ThemeMode.light,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      home: Scaffold(
        body: IndexedStack(
          index: _currentIndex,
          children: [
            HomeScreen(onToggleTheme: _toggleTheme, isDark: _darkMode),
            HistoryScreen(onToggleTheme: _toggleTheme, isDark: _darkMode),
          ],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _currentIndex,
          onDestinationSelected: (i) => setState(() => _currentIndex = i),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Summarize'),
            NavigationDestination(icon: Icon(Icons.history_outlined), selectedIcon: Icon(Icons.history), label: 'History'),
          ],
        ),
      ),
    );
  }
}
