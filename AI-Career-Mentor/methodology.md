# Methodology

This dataset was generated using a strict 'No Fabrication' policy. All 97 records point to real, highly canonical, authoritative sources.

## Sourcing
Records were curated from established educational providers and official documentation (e.g., Harvard/edX, Stanford, Kaggle, freeCodeCamp, Meta, AWS, Google, official language docs). 

## Derivation of Fields
Certain fields are required by the recommendation engine but are not explicitly stated by the source. These were derived systematically:
- **`department_relevance`**: Mapped based on the technical domain (e.g., Computer Science fundamentals map to CSE/IT).
- **`recommended_year_min` / `max`**: Estimated based on typical undergraduate progression (e.g., CS50 is year 1, Advanced Machine Learning is year 3-4).
- **`difficulty`**: Where not provided by the source, derived from prerequisites (e.g., if it requires prior programming, it is marked 'Intermediate').
- **`estimated_hours`**: When missing, calculated using an assumption of typical course workloads (e.g., small tutorial = 3-5 hours, full course = 30-100 hours). Marked as "Mixed" in `data_origin`.
- **`skills_to_learn` / `technologies`**: Normalized from the course syllabus to standard industry terms (e.g., 'Python', 'React', 'Docker').

All fields that involve derivation are explicitly flagged via the `data_origin` column and the `notes` column.
