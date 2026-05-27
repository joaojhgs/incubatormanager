# Final report

This directory contains the final assignment LaTeX report source and compiled
PDF artifact.

Build from the repository root:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=docs/final-report docs/final-report/final-report.tex
```

Clean generated auxiliary files while keeping the committed PDF:

```bash
latexmk -c -outdir=docs/final-report docs/final-report/final-report.tex
```
