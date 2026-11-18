# Security and data-use boundary

Only generated synthetic data belongs in this repository or in the local demo database. Do not submit patient-identifiable data, employer content, credentials, or provider secrets.

Implemented controls are tenant-scoped repository queries, synthetic-only seeded fixtures, non-secret offline model configuration, deterministic result provenance, request IDs, CORS allowlisting, audit events that exclude document text, pinned direct dependencies, and CI secret scanning.

This is not a clinical system, medical device, healthcare deployment, or a statement of compliance with ADHICS, DoH, NABIDH, Riayati, HIPAA, or any other framework. Production use requires qualified legal, security, privacy, and clinical review.
