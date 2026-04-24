# LaTeX Compile Notes

The report source is ready at `report/main.tex`, but this local environment does not currently have `latexmk` or `pdflatex` available on `PATH`.

Verified missing commands:

```bash
which latexmk
which pdflatex
```

Both returned no executable.

## Preferred Compile Command

From the repository root:

```bash
latexmk -pdf report/main.tex
```

## Fallback Compile Command

```bash
cd report
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The report includes `report/neurips_2026.sty`, copied from `KRR_Class_Report_Template/neurips_2026.sty`, so it does not require the style file to be referenced from outside the `report/` folder.
