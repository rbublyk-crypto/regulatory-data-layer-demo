# Controlled demo scenario

The fixtures use invented holders, identifiers, and URLs. They do not represent real holdings or market data.

## Run 1: establish a baseline

| Source | ISIN | Holder | Published short percent | Effective date |
|---|---|---|---:|---|
| demo_fr | FR0000000001 | Northstar Capital | 0.58 | 2026-09-20 |
| demo_fr | FR0000000001 | Northstar Capital | 0.72 | 2026-09-22 |
| demo_no | NO0000000002 | Orion Partners | 0.61 | 2026-09-22 |

The lifecycle-style `demo_fr` source contains two rows for Northstar Capital. The snapshot keeps 0.72% because it is the latest dated record. The first run emits two `BASELINE_POSITION` events, not a spurious increase.

## Run 2: compare a later snapshot

| Observation | Correct result |
|---|---|
| Northstar changes from 0.72% to 0.80% | `POSITION_INCREASED` |
| A new holder appears | `NEW_POSITION` |
| A record is absent from a successfully retrieved source | `POSITION_CLOSED` with public-register semantics |
| `demo_fr` retrieval fails | Source-health failure; preserve the old `demo_fr` state; emit no closure |

## Output contract excerpt

```json
{
  "eventType": "POSITION_INCREASED",
  "positionIdentity": "demo_fr|FR0000000001|Northstar Capital",
  "source": "demo_fr",
  "isin": "FR0000000001",
  "holder": "Northstar Capital",
  "shortPercent": 0.8,
  "previousShortPercent": 0.72,
  "effectiveDate": "2026-09-23",
  "sourceUrl": "https://example.invalid/fr/3"
}
```

Consumers can add notification, dashboard, or workflow layers without being coupled to the original source format.
