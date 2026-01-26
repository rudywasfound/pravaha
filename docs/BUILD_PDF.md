# Building PDF Documentation

Complete guide to converting Pravaha documentation to PDF.

## Quick Start

The simplest method using Pandoc:

```bash
cd DOCUMENTATION

# Install pandoc if needed
# macOS: brew install pandoc
# Ubuntu: sudo apt-get install pandoc
# Windows: choco install pandoc

# Build PDF
pandoc \
  00_TABLE_OF_CONTENTS.md \
  01_INTRODUCTION.md \
  02_INSTALLATION.md \
  03_QUICKSTART.md \
  04_RUNNING_FRAMEWORK.md \
  05_CONFIGURATION.md \
  06_OUTPUT_INTERPRETATION.md \
  07_ARCHITECTURE.md \
  08_CAUSAL_GRAPH.md \
  09_INFERENCE_ALGORITHM.md \
  10_API_REFERENCE.md \
  11_PYTHON_LIBRARY.md \
  12_RUST_INTEGRATION.md \
  13_SIMULATION.md \
  14_CUSTOM_SCENARIOS.md \
  15_PERFORMANCE.md \
  16_DEPLOYMENT.md \
  17_TROUBLESHOOTING.md \
  18_MONITORING.md \
  19_DEVELOPMENT.md \
  20_CONTRIBUTING.md \
  21_TESTING.md \
  22_GLOSSARY.md \
  23_FAQ.md \
  24_REFERENCES.md \
  -o pravaha_documentation.pdf \
  --toc \
  --toc-depth=2 \
  -V papersize=a4 \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V linestretch=1.15
```

Output: `pravaha_documentation.pdf` (~150 pages)

## Installation Methods

### Method 1: Pandoc (Recommended)

#### macOS
```bash
brew install pandoc
# Or download from https://pandoc.org/installing.html
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install pandoc
```

#### Windows
```bash
# Using Chocolatey
choco install pandoc

# Or download from https://pandoc.org/installing.html
```

#### Verify Installation
```bash
pandoc --version
```

### Method 2: Docker

```bash
docker run --rm \
  -v $(pwd)/DOCUMENTATION:/data \
  pandoc/latex \
  /data/00_TABLE_OF_CONTENTS.md \
  ... \
  /data/24_REFERENCES.md \
  -o /data/pravaha_documentation.pdf \
  --toc \
  --toc-depth=2
```

### Method 3: Python Script

Create `build_pdf.py`:

```python
#!/usr/bin/env python3
"""Build Pravaha documentation PDF"""

import subprocess
import sys
from pathlib import Path

def build_pdf():
    docs_dir = Path("DOCUMENTATION")
    
    # List of documents in order
    documents = [
        "00_TABLE_OF_CONTENTS.md",
        "01_INTRODUCTION.md",
        "02_INSTALLATION.md",
        "03_QUICKSTART.md",
        "04_RUNNING_FRAMEWORK.md",
        "05_CONFIGURATION.md",
        "06_OUTPUT_INTERPRETATION.md",
        "07_ARCHITECTURE.md",
        "08_CAUSAL_GRAPH.md",
        "09_INFERENCE_ALGORITHM.md",
        "10_API_REFERENCE.md",
        "11_PYTHON_LIBRARY.md",
        "12_RUST_INTEGRATION.md",
        "13_SIMULATION.md",
        "14_CUSTOM_SCENARIOS.md",
        "15_PERFORMANCE.md",
        "16_DEPLOYMENT.md",
        "17_TROUBLESHOOTING.md",
        "18_MONITORING.md",
        "19_DEVELOPMENT.md",
        "20_CONTRIBUTING.md",
        "21_TESTING.md",
        "22_GLOSSARY.md",
        "23_FAQ.md",
        "24_REFERENCES.md",
    ]
    
    # Verify all files exist
    doc_paths = []
    for doc in documents:
        path = docs_dir / doc
        if not path.exists():
            print(f"ERROR: {path} not found")
            return False
        doc_paths.append(str(path))
    
    # Build PDF
    cmd = [
        "pandoc",
        *doc_paths,
        "-o", "pravaha_documentation.pdf",
        "--toc",
        "--toc-depth=2",
        "-V", "papersize=a4",
        "-V", "geometry:margin=1in",
        "-V", "fontsize=11pt",
        "-V", "linestretch=1.15",
    ]
    
    print(f"Building PDF with {len(documents)} documents...")
    print(f"Command: {' '.join(cmd[:3])} ... -o pravaha_documentation.pdf")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("[OK] PDF built successfully: pravaha_documentation.pdf")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e.stderr}")
        return False
    except FileNotFoundError:
        print("ERROR: pandoc not found. Install with: brew install pandoc")
        return False

if __name__ == "__main__":
    sys.exit(0 if build_pdf() else 1)
```

Run it:
```bash
python build_pdf.py
```

## Advanced Options

### Custom Cover Page

Create `cover.tex`:

```latex
\documentclass{article}
\usepackage[utf8]{inputenc}

\begin{document}

\begin{titlepage}
    \centering
    \vspace*{2cm}
    
    {\Huge\bfseries Pravaha}
    \vspace{0.5cm}
    
    {\Large Satellite Causal Inference Framework}
    \vspace{1cm}
    
    {\Large Documentation}
    \vspace{2cm}
    
    {\Large Version 1.0}
    \vspace{1cm}
    
    {\large January 2026}
    
    \vfill
    
    {\large A framework for diagnosing root causes in}
    {\large multi-fault satellite systems using causal inference.}
    
\end{titlepage}

\end{document}
```

Build with cover:
```bash
pandoc cover.tex \
  00_TABLE_OF_CONTENTS.md ... 24_REFERENCES.md \
  -o pravaha_documentation.pdf
```

### Different Page Styles

#### With Headers/Footers
```bash
pandoc ... -o output.pdf \
  --include-before-body=before.tex \
  --include-after-body=after.tex
```

#### With CSS Styling (HTML first)
```bash
pandoc ... -o output.html --self-contained-html
# Then convert HTML to PDF with wkhtmltopdf or similar
```

#### Two-Column Layout
```bash
pandoc ... -o output.pdf \
  -V documentclass=article \
  -V classoption=twocolumn
```

### Split into Chapters

Create separate PDFs for each section:

```bash
# Part 1: Getting Started
pandoc 00_TABLE_OF_CONTENTS.md 01_INTRODUCTION.md 02_INSTALLATION.md 03_QUICKSTART.md \
  -o 01_GETTING_STARTED.pdf --toc

# Part 2: User Guide
pandoc 04_RUNNING_FRAMEWORK.md 05_CONFIGURATION.md 06_OUTPUT_INTERPRETATION.md \
  -o 02_USER_GUIDE.pdf --toc

# Part 3: Architecture
pandoc 07_ARCHITECTURE.md 08_CAUSAL_GRAPH.md 09_INFERENCE_ALGORITHM.md \
  -o 03_ARCHITECTURE.pdf --toc

# ... etc
```

## Customization

### Font & Styling

```bash
pandoc ... -o output.pdf \
  -V fontfamily=libertine \      # Change font
  -V fontsize=10pt \             # Font size
  -V linestretch=1.5 \           # Line spacing
  -V papersize=letter            # Page size (a4, letter, etc)
```

### Color Support

```bash
pandoc ... -o output.pdf \
  --highlight-style=tango \      # Syntax highlighting
  --pdf-engine=xelatex           # Better color support
```

### Table of Contents Depth

```bash
pandoc ... -o output.pdf \
  --toc \                        # Include TOC
  --toc-depth=3 \                # How many levels to include
  --number-sections              # Number headings
```

## Quality Check

After building, verify:

```bash
# Check file exists and has reasonable size
ls -lh pravaha_documentation.pdf
# Should be 2-5 MB

# Check page count
pdfinfo pravaha_documentation.pdf
# Should show ~150 pages

# Validate PDF (on macOS with ghostscript)
gs -sDEVICE=nulldevice -dNODISPLAY -dBATCH pravaha_documentation.pdf
```

## Automation

Add to GitHub Actions (`.github/workflows/build-docs.yml`):

```yaml
name: Build Documentation

on:
  push:
    branches: [main]
    paths:
      - 'DOCUMENTATION/**'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install pandoc
        run: sudo apt-get install pandoc
      
      - name: Build PDF
        run: |
          cd DOCUMENTATION
          pandoc 00_TABLE_OF_CONTENTS.md ... 24_REFERENCES.md \
            -o pravaha_documentation.pdf \
            --toc --toc-depth=2
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: documentation
          path: DOCUMENTATION/pravaha_documentation.pdf
```

## Distribution

### Hosting Options

1. **GitHub Releases**
   - Attach PDF to release
   - Automatic versioning
   - Easy download

2. **GitHub Pages**
   - Host HTML version
   - Auto-update on push
   - Free CDN

3. **Documentation Site**
   - MkDocs: https://www.mkdocs.org/
   - Sphinx: https://www.sphinx-doc.org/
   - Read the Docs: https://readthedocs.org/

### Create HTML Version

```bash
# Build HTML for hosting
pandoc DOCUMENTATION/*.md -o index.html --self-contained-html --toc

# Or use MkDocs
mkdocs build
```

## Troubleshooting

### Pandoc not found

```bash
# Check if installed
which pandoc

# Install if missing
brew install pandoc        # macOS
sudo apt-get install pandoc  # Ubuntu
choco install pandoc       # Windows
```

### PDF build fails

```bash
# Check file encoding
file DOCUMENTATION/*.md
# Should show: UTF-8 Unicode text

# Convert if needed
iconv -f ISO-8859-1 -t UTF-8 file.md -o file_fixed.md
```

### Large PDF size

```bash
# Check output size
ls -lh pravaha_documentation.pdf

# Compress
gs -qs -dNOPAUSE -dBATCH -dSAFER \
   -sDEVICE=pdfwrite \
   -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook \
   -dDetectDuplicateImages \
   -dCompressFonts=true \
   -dSubsetFonts=true \
   -dColorImageResolution=150 \
   -dGrayImageResolution=150 \
   -sOutputFile=compressed.pdf \
   pravaha_documentation.pdf
```

### Broken links in PDF

Links won't work in PDF by default. To enable:

```bash
pandoc ... -o output.pdf \
  --pdf-engine=pdflatex  # Better link support
```

## Next Steps

1. **Build your PDF**: Use one of the methods above
2. **Distribute**: Upload to GitHub, your website, or documentation platform
3. **Keep updated**: Rebuild when documentation changes
4. **Version control**: Commit updated PDFs to releases branch

---

**Back to:** [README ->](README.md)
