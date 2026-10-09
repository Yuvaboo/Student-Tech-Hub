# Data Dictionary

| Column Name | Description | Data Type | Origin |
|---|---|---|---|
| item_id | Unique identifier for the item (LR=Learning Resource, PRJ=Project, SKL=Skill, etc.) | String | Generated |
| item_type | The category of the item (`Learning Resource`, `Project`, `Skill`, `Learning Path`) | String | Source-provided / Normalized |
| title | Title of the resource, project, or skill | String | Source-provided |
| description | A brief summary of the item's content | String | Source-provided |
| source_name | The organization, platform, or creator | String | Source-provided |
| source_url | A verified canonical URL to the item | URL String | Source-provided |
| source_date_or_version | Date or version of the content (usually marked 'Current') | String | Derived |
| domain | The primary tech domain (e.g., Data Science, Web Development) | String | Derived |
| department_relevance | Academic departments for which this item is most relevant (e.g., CSE) | String | Derived |
| recommended_year_min | Minimum recommended college year (1-4) | Integer | Derived |
| recommended_year_max | Maximum recommended college year (1-4) | Integer | Derived |
| difficulty | Skill level required (Beginner, Intermediate, Advanced) | String | Mixed (Source/Derived) |
| current_skills | Skills the student already possesses (used in recommendation logic) | String | Derived |
| required_skills | Hard prerequisites for attempting the item | String | Mixed |
| skills_to_learn | The normalized skills the student will acquire | String | Normalized from source |
| interests | Tags mapping to student interest areas | String | Derived from source |
| technologies | Normalized tools/technologies used | String | Normalized from source |
| estimated_hours | Total hours of work required | Integer | Mixed (Source/Estimated) |
| estimated_duration_weeks | Suggested weeks to complete | Integer | Estimated |
| learning_resource_url | Specific link to learning material | URL String | Source-provided |
| project_reference_url | Specific link to project repository or brief | URL String | Source-provided |
| prerequisites | Human-readable prerequisites | String | Mixed |
| career_roles | Recommended career roles this item prepares for | String | Derived |
| source_confidence | Confidence level in the source data (always High in this curated set) | String | Derived |
| data_origin | Traceability tag for the record's primary metadata origin | String | Derived |
| notes | Additional methodological notes | String | Derived |
