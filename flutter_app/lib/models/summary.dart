class Summary {
  final String id;
  final String filename;
  final int filesize;
  final String filetype;
  final String title;
  final String summary;
  final String methodology;
  final List<String> keyFindings;
  final List<String> researchGaps;
  final List<String> futureDirections;
  final List<String> strengths;
  final List<String> weaknesses;
  final String conclusion;
  final String difficultyLevel;
  final List<String> keyTerms;
  final List<String> keyPoints;
  final List<String> citations;
  final String researchObjective;
  final String novelty;
  final String practicalImplications;
  final List<String> keyTakeaways;
  final String language;
  final String summaryType;
  final int wordCount;
  final double processingTime;
  final String createdAt;
  final String sourceUrl;

  Summary({
    required this.id,
    required this.filename,
    required this.filesize,
    required this.filetype,
    required this.title,
    required this.summary,
    this.methodology = '',
    this.keyFindings = const [],
    this.researchGaps = const [],
    this.futureDirections = const [],
    this.strengths = const [],
    this.weaknesses = const [],
    this.conclusion = '',
    this.difficultyLevel = 'Intermediate',
    this.keyTerms = const [],
    this.keyPoints = const [],
    this.citations = const [],
    this.researchObjective = '',
    this.novelty = '',
    this.practicalImplications = '',
    this.keyTakeaways = const [],
    required this.language,
    required this.summaryType,
    required this.wordCount,
    required this.processingTime,
    required this.createdAt,
    this.sourceUrl = '',
  });

  factory Summary.fromJson(Map<String, dynamic> json) {
    return Summary(
      id: json['id'] as String? ?? '',
      filename: json['filename'] as String? ?? '',
      filesize: json['filesize'] as int? ?? 0,
      filetype: json['filetype'] as String? ?? '',
      title: json['title'] as String? ?? 'Untitled',
      summary: json['summary'] as String? ?? '',
      methodology: json['methodology'] as String? ?? '',
      keyFindings: _toStrList(json['key_findings']),
      researchGaps: _toStrList(json['research_gaps']),
      futureDirections: _toStrList(json['future_directions']),
      strengths: _toStrList(json['strengths']),
      weaknesses: _toStrList(json['weaknesses']),
      conclusion: json['conclusion'] as String? ?? '',
      difficultyLevel: json['difficulty_level'] as String? ?? 'Intermediate',
      keyTerms: _toStrList(json['key_terms']),
      keyPoints: _toStrList(json['key_points']),
      citations: _toStrList(json['citations']),
      researchObjective: json['research_objective'] as String? ?? '',
      novelty: json['novelty'] as String? ?? '',
      practicalImplications: json['practical_implications'] as String? ?? '',
      keyTakeaways: _toStrList(json['key_takeaways']),
      language: json['language'] as String? ?? 'english',
      summaryType: json['summary_type'] as String? ?? 'detailed',
      wordCount: json['word_count'] as int? ?? 0,
      processingTime: (json['processing_time'] as num?)?.toDouble() ?? 0.0,
      createdAt: json['created_at'] as String? ?? '',
      sourceUrl: json['source_url'] as String? ?? '',
    );
  }

  static List<String> _toStrList(dynamic v) {
    if (v == null) return [];
    if (v is List) return v.map((e) => e.toString()).toList();
    return [];
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'filename': filename,
        'filesize': filesize,
        'filetype': filetype,
        'title': title,
        'summary': summary,
        'methodology': methodology,
        'key_findings': keyFindings,
        'research_gaps': researchGaps,
        'future_directions': futureDirections,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'conclusion': conclusion,
        'difficulty_level': difficultyLevel,
        'key_terms': keyTerms,
        'key_points': keyPoints,
        'citations': citations,
        'research_objective': researchObjective,
        'novelty': novelty,
        'practical_implications': practicalImplications,
        'key_takeaways': keyTakeaways,
        'language': language,
        'summary_type': summaryType,
        'word_count': wordCount,
        'processing_time': processingTime,
        'created_at': createdAt,
        'source_url': sourceUrl,
      };

  String get filesizeFormatted {
    if (filesize < 1024 * 1024) {
      return '${(filesize / 1024).toStringAsFixed(0)} KB';
    }
    return '${(filesize / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

class HistoryItem {
  final String id;
  final String filename;
  final String title;
  final String filetype;
  final String language;
  final int filesize;
  final String createdAt;
  final String sourceUrl;

  HistoryItem({
    required this.id,
    required this.filename,
    required this.title,
    required this.filetype,
    required this.language,
    required this.filesize,
    required this.createdAt,
    this.sourceUrl = '',
  });

  factory HistoryItem.fromJson(Map<String, dynamic> json) {
    return HistoryItem(
      id: json['id'] as String? ?? '',
      filename: json['filename'] as String? ?? '',
      title: json['title'] as String? ?? 'Untitled',
      filetype: json['filetype'] as String? ?? '',
      language: json['language'] as String? ?? 'english',
      filesize: json['filesize'] as int? ?? 0,
      createdAt: json['created_at'] as String? ?? '',
      sourceUrl: json['source_url'] as String? ?? '',
    );
  }

  String get filesizeFormatted {
    if (filesize < 1024 * 1024) {
      return '${(filesize / 1024).toStringAsFixed(0)} KB';
    }
    return '${(filesize / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}
