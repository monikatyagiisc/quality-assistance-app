# Quality Assistance project report

This directory contains the IISc M.Tech. (Online) LaTeX report and its source chapters. It follows the supplied IISc thesis/report template and is based on the project proposal, mid-term presentation, and implementation snapshot through October 2026. The report distinguishes implemented behavior from planned evaluation and deployment work.

## Requirements

Install a LaTeX distribution that provides `pdflatex`, `bibtex`, and `makeindex` (for example, MiKTeX or TeX Live), and ensure those executables are available on `PATH`.

## Build the PDF (PowerShell)

From the repository root:

```powershell
Set-Location reports\quality-assistance-report
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
makeindex main.nlo -s nomencl.ist -o main.nls
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The last two LaTeX passes resolve the table of contents, lists, citations, and cross-references. The resulting PDF is `main.pdf` in this directory.
