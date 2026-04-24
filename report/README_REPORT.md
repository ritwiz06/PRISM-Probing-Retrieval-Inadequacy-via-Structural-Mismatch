# PRISM Final Report

This folder contains the final LaTeX report for PRISM.

## Files

- `main.tex`: final report source
- `references.bib`: bibliography
- `neurips_2026.sty`: copied from the local course template folder
- `figures/`: report figures copied from real final-release artifacts
- `tables/`: report tables using recorded evaluation numbers

## Source of Truth

The report uses existing artifacts only:

- `data/eval/*`
- `data/human_eval/*`
- `data/final_release/*`
- `README.md`
- latest logs under `logs/work/` and `logs/process/`

No benchmark labels, human annotations, production routing decisions, or metrics were changed for the report.

## Compile

Preferred:

```bash
latexmk -pdf report/main.tex
```

Fallback:

```bash
cd report
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The report uses the provided `neurips_2026.sty` style copied into this folder.
