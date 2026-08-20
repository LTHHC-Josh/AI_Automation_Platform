# Authoritative reference workbook configuration

The production reference source uses the Microsoft Graph drive-item boundary
already present in the platform. Operators must configure both values locally:

- `GRAPH_REFERENCE_DRIVE_ID`: the Graph drive identifier containing the
  authoritative workbook.
- `GRAPH_REFERENCE_ITEM_ID`: the Graph item identifier for the authoritative
  workbook file.

Do not place real identifiers in source control, tests, logs, tracker output, or
project memory. The values belong in the existing ignored local environment
configuration boundary.

The source reads `eTag`, `lastModifiedDateTime`, and `size` metadata. `eTag` is
the preferred refresh version; `lastModifiedDateTime` is the deterministic
fallback. A changed version triggers download and validation. A malformed or
unavailable refresh cannot replace the ignored last-known-good cache in
`data/reference_cache/`.

No site identifier is required by the current architecture because the Graph
endpoint addresses the workbook by drive and item identity.
