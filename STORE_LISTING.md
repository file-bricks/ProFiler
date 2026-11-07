# Store Listing Draft - ProFiler Suite

**Status:** draft only; no Store submission or publication is claimed. The source version remains frozen at `15.0.2`.

## Deutsch

### Kurzbeschreibung

Lokale Dokumentverwaltung mit Suche, OCR, PDF-Werkzeugen und einer regelbasierten Prüfung möglicher sensibler Begriffe.

### Beschreibung

ProFiler Suite ist eine Windows-orientierte Desktopanwendung für lokale Datei- und Dokumentabläufe. Sie kombiniert Dateisuche, OCR, PDF-Werkzeuge, Duplikaterkennung und Hinweise auf möglicherweise sensible Begriffe.

**Funktionen**

- Suche in ausgewählten lokalen Ordnern und Dokumenten
- OCR über Tesseract, sofern das Programm auf dem Host verfügbar ist
- PDF-Werkzeuge für Extraktion, Verschlüsselung, Entschlüsselung und Schwärzung
- Regelbasierte Hinweise auf ausgewählte sensible Begriffe
- Schema-gefilterter Workspace-Austausch; Exporte vor einer Weitergabe prüfen
- Optionale Startmöglichkeiten für separate Desktop-Werkzeuge

**Hinweis zum Store-Kanal**

- Die vorhandenen Store-Dateien sind Entwürfe und Staging-Material.
- Das Manifest deklariert derzeit `runFullTrust`; daraus folgt keine Store-Freigabe.
- Ein signiertes MSIX, ein aktueller WACK-Lauf auf diesem Paket und eine Partner-Center-Einreichung sind nicht belegt.
- Der in `build_exe.bat` verlangte Tesseract-/Poppler-Bundle fehlt im geprüften Quellstand; der native Paketbuild ist blockiert.
- Abhängigkeitshinweise stehen in `THIRD_PARTY_LICENSES.md` und `THIRD_PARTY_LICENSES.txt`; sie sind keine vollständige Lizenz- oder Kompatibilitätsprüfung.

### Datenschutz

Siehe [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

### Support

Siehe [SUPPORT.md](SUPPORT.md).

### Schlüsselwörter

Dokumentverwaltung, OCR, PDF-Werkzeuge, Datenschutzprüfung, Volltextsuche, Offline, Dateimanager

### Screenshot-Referenzen

- `screenshots/store/shot-1-library-overview.png`: Dateibaum und Dokumentübersicht
- `screenshots/store/shot-2-search-ocr.png`: Suche und OCR
- `screenshots/store/shot-3-privacy-traffic-light.png`: Hinweise der regelbasierten Datenschutzampel
- `screenshots/store/shot-4-pdf-tools.png`: PDF-Werkzeuge und Schwärzung

---

## English

### Short description

Local document management with search, OCR, PDF tools, and rule-based sensitive-term review.

### Description

ProFiler Suite is a Windows-oriented desktop application for local file and document workflows. It combines file search, OCR, PDF utilities, duplicate detection, and indicators for selected potentially sensitive terms.

**Features**

- Search selected local folders and documents
- OCR through Tesseract when available on the host
- PDF utilities for extraction, encryption, decryption, and redaction
- Rule-based indicators for selected sensitive terms
- Schema-filtered workspace exchange; inspect exports before sharing
- Optional launchers for separate desktop tools

**Store channel note**

- Existing Store files are drafts and staging material.
- The current manifest declares `runFullTrust`; this does not establish Store approval.
- A signed MSIX, a current WACK run on that package, and a Partner Center submission are not evidenced.
- The Tesseract/Poppler bundle required by `build_exe.bat` is absent from the reviewed source checkout, so the native package build is blocked.
- Dependency notes are in `THIRD_PARTY_LICENSES.md` and `THIRD_PARTY_LICENSES.txt`; they are not a complete license or compatibility review.

### Privacy

See [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

### Support

See [SUPPORT.md](SUPPORT.md).

### Keywords

Document Manager, OCR, PDF Tools, Privacy Review, Full Text Search, Offline, File Organizer

### Screenshot references

- `screenshots/store/shot-1-library-overview.png`: directory tree and document overview
- `screenshots/store/shot-2-search-ocr.png`: search and OCR
- `screenshots/store/shot-3-privacy-traffic-light.png`: rule-based privacy review indicators
- `screenshots/store/shot-4-pdf-tools.png`: PDF utilities and redaction

---

## Español

### Descripción corta

Gestor local de documentos con búsqueda, OCR, utilidades PDF y revisión de privacidad.

### Descripción

ProFiler Suite es una aplicación de escritorio local para Windows diseñada para la gestión segura de documentos personales y profesionales. Combina búsqueda avanzada de archivos, OCR de alta precisión, flujos de trabajo PDF, detección de duplicados e inspección de privacidad en una interfaz unificada, sin dependencia de la nube ni cargas forzadas de datos.

**Funciones principales**

- Búsqueda local de texto completo en archivos PDF, documentos de oficina, imágenes, hojas de cálculo y texto
- OCR con Tesseract para documentos escaneados e imágenes
- Herramientas PDF integradas para descifrado, redacción, extracción de páginas y exportación
- Semáforo de privacidad para inspección de términos confidenciales y cumplimiento de normativas de protección de datos
- Exportación de espacios de trabajo redactados para revisiones seguras y verificación multiplataforma
- Lanzador integrado para utilidades complementarias de escritorio como ProSync y SQLiteViewer

### Privacidad

Véase [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

### Soporte

Véase [SUPPORT.md](SUPPORT.md).

### Palabras clave

Gestor Documental, OCR, Herramientas PDF, Privacidad, Búsqueda, Sin Conexión, Organizador

---

## 简体中文

### 简短描述

本地文档管理与全文搜索工具，支持OCR文字识别、PDF实用工具及隐私安全审查。

### 详细描述

ProFiler Suite 是一款面向 Windows 的本地桌面应用程序，专为个人和专业文档库的高效安全管理而设计。该应用集成了全文文件检索、OCR光学字符识别、PDF工作流、文件查重和隐私数据审查于一体，无需依赖云端账户，杜绝强制数据上传。

**核心功能**

- 本地全文搜索：支持扫描 PDF、Office 文档、图像、电子表格及文本文件
- Tesseract OCR：针对扫描件和图像文档的高精度本地文字识别
- PDF 综合工具：支持文档解密、隐私涂黑遮盖、页面拆分提取及导出
- 隐私审查指示灯：自动识别敏感字段与术语，确保合规与数据安全
- 匿名化工作区导出：生成脱敏配置文件，便于跨平台审查和安全协作
- 桌面扩展联动：支持一键启动 ProSync 与 SQLiteViewer 等本地伙伴工具

### 隐私政策

参阅 [PRIVACY_POLICY.md](PRIVACY_POLICY.md)。

### 技术支持

参阅 [SUPPORT.md](SUPPORT.md)。

### 关键词

文档管理, 文字识别, PDF工具, 隐私保护, 全文搜索, 离线工具, 文件整理

---

## 日本語

### 簡単な説明

全文検索、OCR文字認識、PDFツール、プライバシー保護検査を備えたローカル文書管理ソフト。

### 詳細な説明

ProFiler Suite は、個人および業務用の文書コレクションを安全かつ効率的に整理するためのローカルファースト Windows デスクトップアプリです。クラウド連携や不要な外部アップロードを一切要求せず、ファイル検索、高精度OCR、PDF処理ワークフロー、重複ファイル検出、プライバシー監査機能を単一の直感的なインターフェースに統合しています。

**主な機能**

- ローカル全文検索：PDF、Office 文書、画像、スプレッドシート、テキストファイルを迅速にインデックス・検索
- Tesseract OCR：スキャン資料や画像ファイルからのローカル文字認識処理
- PDF ユーティリティ：パスワード解除、墨消し（黒塗り）、ページ抽出、変換エクスポート
- プライバシー信号灯：機密用語や個人情報（PII）の検出によるコンプライアンス管理
- 秘匿化ワークスペース出力：機密を除去した安全なレビューとクロスプラットフォーム検証
- 連携ツール起動：ProSync や SQLiteViewer などのデスクトップ拡張をシームレスに呼び出し

### プライバシーポリシー

[PRIVACY_POLICY.md](PRIVACY_POLICY.md) を参照。

### サポート

[SUPPORT.md](SUPPORT.md) を参照。

### 検索キーワード

文書管理, OCR文字認識, PDFツール, プライバシー保護, 全文検索, オフライン, ファイル整理

---

## Русский

### Краткое описание

Локальный менеджер документов с полнотекстовым поиском, OCR, PDF и проверкой приватности.

### Описание

ProFiler Suite — это локальное приложение для Windows, созданное для безопасного и структурированного управления личными и рабочими коллекциями документов. Программа объединяет полнотекстовый поиск, оптическое распознавание символов (OCR), инструменты для работы с PDF, поиск дубликатов и аудит конфиденциальности в едином интерфейсе без принудительной облачной синхронизации.

**Основные возможности**

- Локальный полнотекстовый поиск по PDF, документам Office, изображениям, таблицам и текстовым файлам
- Tesseract OCR для распознавания текста со сканов и графических документов
- Инструменты PDF для снятия паролей, цензурирования (закрашивания), извлечения страниц и экспорта
- Светофор конфиденциальности для обнаружения конфиденциальных терминов и персональных данных
- Экспорт отредактированных рабочих областей для безопасного обмена и аудита
- Встроенный запуск сопутствующих локальных инструментов (ProSync, SQLiteViewer)

### Конфиденциальность

См. [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

### Поддержка

См. [SUPPORT.md](SUPPORT.md).

### Ключевые слова

Управление файлами, OCR распознавание, PDF утилиты, Конфиденциальность, Поиск документов, Офлайн, Файловый менеджер
