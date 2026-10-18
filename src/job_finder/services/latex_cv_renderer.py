"""Render trusted LaTeX structure with escaped, untrusted plain-text content."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote, urlsplit

from job_finder.models.cv import CVContent, CVEntry
from job_finder.models.personal_info import PersonalInfo

_ESCAPES = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "%": r"\%",
    "_": r"\_",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(value: str) -> str:
    return "".join(_ESCAPES.get(char, char) for char in " ".join(value.split()))


class LatexCompilationError(RuntimeError):
    """Compilation failed or the required LaTeX installation is unavailable."""


def latex_link(url: str, label: str) -> str:
    if urlsplit(url).scheme not in {"https", "http", "mailto"}:
        raise ValueError("CV links must use https, http or mailto.")
    encoded = quote(url, safe="/:@?=&-._")
    return r"\href{" + escape_latex(encoded) + "}{" + escape_latex(label) + "}"


class LatexCVRenderer:
    def render(self, cv: CVContent, personal_info: PersonalInfo) -> str:
        esc = escape_latex
        header = personal_info.header
        links = [
            latex_link(header.github, "GitHub"),
            latex_link(header.linkedin, "LinkedIn"),
            latex_link(header.portfolio, "abelharo.me"),
        ]
        lines = [
            r"\documentclass[11pt,a4paper]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage{lmodern}",
            r"\usepackage[left=1.5cm,right=1.5cm,top=1.2cm,bottom=1.2cm]{geometry}",
            r"\usepackage{enumitem,titlesec,xcolor}",
            r"\usepackage[hidelinks]{hyperref}\urlstyle{same}",
            r"\input{glyphtounicode}\pdfgentounicode=1",
            r"\pagestyle{empty}\setlength{\parindent}{0pt}",
            r"\definecolor{heading}{HTML}{20384C}",
            r"\titleformat{\section}{\large\bfseries\color{heading}}{}{0pt}{}[\vspace{1pt}\titlerule]",
            r"\titlespacing*{\section}{0pt}{7pt}{4pt}",
            r"\setlist[itemize]{leftmargin=1.3em,itemsep=1.5pt,topsep=3pt,parsep=0pt,partopsep=0pt}",
            r"\raggedright\begin{document}",
            r"\fontsize{10.5pt}{12.4pt}\selectfont",
            r"\begin{center}",
            r"{\LARGE\bfseries\color{heading} " + esc(header.name) + r"}\\[3pt]",
            esc(cv.headline) + r"\\[3pt]",
            r"{\small "
            + latex_link("mailto:" + header.email, header.email)
            + r"\\[2pt]",
            r" \enspace|\enspace ".join(links) + "}",
            r"\end{center}\vspace{-7pt}",
            r"\section{" + esc(cv.headings.profile) + "}",
            esc(cv.profile),
        ]

        def entry_lines(
            entry: CVEntry, url: str = "", technologies: tuple[str, ...] = ()
        ) -> None:
            title = latex_link(url, entry.title) if url else esc(entry.title)
            lines.append(
                r"\textbf{" + title + r"}\hfill {\small " + esc(entry.dates) + r"}\par"
            )
            if entry.subtitle:
                lines.append(r"{\small\textit{" + esc(entry.subtitle) + r"}}\par")
            if technologies:
                lines.append(
                    r"{\small\textbf{"
                    + esc(cv.headings.technologies)
                    + ":} "
                    + esc(", ".join(technologies))
                    + r"}\par"
                )
            lines.append(r"\begin{itemize}")
            lines.extend(r"\item " + esc(bullet) for bullet in entry.bullets)
            lines.extend([r"\end{itemize}", r"\vspace{2pt}"])

        lines.append(r"\section{" + esc(cv.headings.experience) + "}")
        for entry in cv.experience:
            entry_lines(entry)
        lines.append(r"\section{" + esc(cv.headings.projects) + "}")
        catalog = {project.id: project for project in personal_info.projects}
        for project in cv.projects:
            original = catalog[project.project_id]
            entry_lines(project, original.url, original.technologies)
        lines.append(r"\section{" + esc(cv.headings.education) + "}")
        for entry in cv.education:
            entry_lines(entry)
        lines.append(r"\section{" + esc(cv.headings.languages) + "}")
        lines.append(r" \enspace|\enspace ".join(map(esc, cv.languages)) + r"\par")
        lines.append(r"\end{document}")
        return "\n".join(lines) + "\n"

    def compile(self, source: str) -> bytes:
        compiler = shutil.which("pdflatex")
        if compiler is None:
            raise LatexCompilationError(
                "pdflatex is required. Install texlive-latex-extra and lmodern."
            )
        with tempfile.TemporaryDirectory(prefix="job-finder-cv-") as directory:
            work = Path(directory)
            (work / "cv.tex").write_text(source, encoding="utf-8")
            try:
                result = subprocess.run(
                    [
                        compiler,
                        "-no-shell-escape",
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        "cv.tex",
                    ],
                    cwd=work,
                    capture_output=True,
                    check=False,
                    timeout=60,
                )
            except subprocess.TimeoutExpired as exc:
                raise LatexCompilationError(
                    "LaTeX compilation exceeded 60 seconds."
                ) from exc
            pdf = work / "cv.pdf"
            if result.returncode != 0 or not pdf.is_file():
                detail = result.stdout.decode("utf-8", errors="replace")[-4000:]
                raise LatexCompilationError(f"LaTeX compilation failed:\n{detail}")
            return pdf.read_bytes()
