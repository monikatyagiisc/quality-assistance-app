# Quality Assistance project report

This directory contains the IISc M.Tech. (Online) report source, class file, and chapters. The
IISc seal image is kept separately in [`reports/images`](../images).

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

Build logs and intermediate files are also kept under `tmp/reports`. The source files in this
directory are not modified by compilation.
