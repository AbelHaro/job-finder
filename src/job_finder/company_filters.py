"""Exclude companies whose listings are promotional rather than job openings."""

EXCLUDED_COMPANIES = frozenset({"evolve", "bending spoons", "joinrs", "alignerr"})


def is_excluded_company(company: str) -> bool:
    return " ".join(company.casefold().split()) in EXCLUDED_COMPANIES
