class Summary {
  final String id;
  final String filename;
  final int filesize;
  final String filetype;
  final String title;
  final String summary;
  final List<String> keyPoints;
  final List<String> citations;
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
    required this.keyPoints,
    required this.citations,
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
      keyPoints: List<String>.from(json['key_points'] as List? ?? []),
      citations: List<String>.from(json['citations'] as List? ?? []),
      language: json['language'] as String? ?? 'english',
      summaryType: json['summary_type'] as String? ?? 'detailed',
      wordCount: json['word_count'] as int? ?? 0,
      processingTime: (json['processing_time'] as num?)?.toDouble() ?? 0.0,
      createdAt: json['created_at'] as String? ?? '',
      sourceUrl: json['source_url'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'filename': filename,
        'filesize': filesize,
        'filetype': filetype,
        'title': title,
        'summary': summary,
        'key_points': keyPoints,
        'citations': citations,
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
