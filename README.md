# gmail-insights

gmail-insights ist ein Analyse-Framework zur lokalen Auswertung von Gmail-Postfächern über die Gmail-API.  
Es extrahiert strukturierte Metadaten (IDs, Thread-Struktur, Absender, Datum, Betreff, Labels, Attachments) und ermöglicht sowohl deterministische Regeln als auch probabilistische Mustererkennung, um die Leitfrage zu beantworten:

"Was kann ich getrost löschen?"

## Features

* Gmail-API-Extraktion
* Thread-Rekonstruktion über RFC822-IDs
* Attachment-Analyse
* Feature-Engineering
* Deterministische Regeln
* Probabilistische Clusteranalyse
* CLI-Tools für reproduzierbare Pipelines

## Projektstruktur

\`\`\`
gmail-insights/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
│
├── config/
│   ├── oauth_client.json
│   └── settings.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── models/
│
├── src/
│   ├── gmail_api/
│   │   ├── auth.py
│   │   ├── fetch.py
│   │   └── parse.py
│   │
│   ├── features/
│   │   ├── ids.py
│   │   ├── threads.py
│   │   ├── attachments.py
│   │   └── transform.py
│   │
│   ├── analysis/
│   │   ├── deterministic.py
│   │   ├── clustering.py
│   │   └── segments.py
│   │
│   ├── utils/
│   │   ├── logging.py
│   │   ├── storage.py
│   │   └── helpers.py
│   │
│   └── cli/
│       ├── extract.py
│       ├── build_features.py
│       └── analyze.py
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_clustering.ipynb
│
├── tests/
│   ├── test_api.py
│   ├── test_parsing.py
│   ├── test_features.py
│   └── test_clustering.py
│
└── docs/
    ├── architecture.md
    ├── data_model.md
    ├── api_usage.md
    └── clustering_methods.md
\`\`\`

## Datenmodell

Die zentrale Tabelle enthält:

* gmail_id  
* rfc822_msgid  
* in_reply_to  
* references  
* thread_id  
* thread_depth  
* from, to, date, subject  
* labels  
* has_attachment  
* attachment_total_size  
* size_estimate

## Installation

Wird ergänzt, sobald pyproject.toml definiert ist.

## CLI-Tools

* extract.py  
* build_features.py  
* analyze.py  

## Notebooks

* 01_exploration.ipynb  
* 02_feature_engineering.ipynb  
* 03_clustering.ipynb  

## Tests

Unit-Tests für API-Parsing, Feature-Engineering, Clustering und Thread-Rekonstruktion.

## Dokumentation

* docs/architecture.md  
* docs/data_model.md  
* docs/api_usage.md  
* docs/clustering_methods.md

## Agent-Integration

Die Struktur ist so aufgebaut, dass der zoo/Gemini-Agent das gesamte Projekt kontextsensitiv erweitern, refactoren und analysieren kann.
