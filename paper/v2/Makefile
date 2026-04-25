.PHONY: pdf tectonic clean

pdf:
	pdflatex -halt-on-error main.tex && bibtex main && pdflatex -halt-on-error main.tex && pdflatex -halt-on-error main.tex

tectonic:
	tectonic main.tex

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc
