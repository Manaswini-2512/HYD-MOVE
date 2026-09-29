# Development Rules

- Use clear, descriptive Python names and follow PEP 8 conventions.
- Add type hints to public functions and docstrings that explain their purpose, inputs, and return values.
- Keep modules focused and reusable; separate ingestion, cleaning, analysis, modelling, and presentation concerns.
- Add or update pytest tests for behavior changes, especially data-quality edge cases.
- Never fabricate or imply real-world Hyderabad data. Clearly label synthetic fixtures and never present them as findings.
- Do not commit secrets, credentials, private data, or API keys. Use environment-based configuration if credentials are ever needed.
- Treat raw data as immutable. Write transformations to separate processed outputs; never overwrite raw inputs.
- Make analyses reproducible by documenting inputs, transformations, assumptions, and relevant random seeds.
- Keep changes focused, reviewable, and Git-friendly. Do not commit generated environments, caches, or large derived files.
- Do not connect external APIs or add real datasets without an explicit project decision and documented provenance/permissions.