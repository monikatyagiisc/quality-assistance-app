# Quality Assistance project report

This directory contains the IISc M.Tech. (Online) report source, class file, and chapters. The
IISc seal image is kept separately in [`reports/images`](../images).

## Build the PDF on macOS

From the repository root, run:

```bash
./scripts/build-report-macos.sh
```

The IISc class file needs `pdflatex` (not `tectonic`). If those tools are missing, the script
installs a user-local [TinyTeX](https://yihui.org/tinytex/) and the packages this report uses.
A full [MacTeX](https://tug.org/mactex/) install also works if you already have one.

The script then runs `pdflatex`, `bibtex`, and `makeindex`, writes the PDF to
`tmp/reports/quality-assistant-app.pdf`, and copies it to `reports/quality-assistant-app.pdf`.
Open the finished report with:

```bash
open reports/quality-assistant-app.pdf
```

## Build the PDF on Ubuntu

Install the TeX distribution and report dependencies once:

```bash
sudo apt-get update
sudo apt-get install -y \
  texlive-latex-base \
  texlive-latex-extra \
  texlive-science \
  texlive-bibtex-extra \
  texlive-pictures \
  texlive-fonts-recommended
```

From the repository root, run:

```bash
./scripts/build-report.sh
```

The script runs the LaTeX, bibliography, and nomenclature passes. It writes the final PDF and
intermediate compiler files outside this source directory:

```text
tmp/reports/quality-assistant-app.pdf
```

The finished PDF is also copied to `reports/quality-assistant-app.pdf` for convenient access.
Build logs and intermediate files are kept under `tmp/reports`. The source files in this
directory are not modified by compilation.
