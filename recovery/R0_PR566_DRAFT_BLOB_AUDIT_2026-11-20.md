# R0 — PR #566: full Git blob audit (20.11.2026)

Source HEAD: `01d04ac2bd5c567940defe1d57be3f67b84469f2`. Accepted MAIN: `e6b8480b493365e0a4ff2bb56041891fde0a6f22`. Git blob SHA-1 is not SHA256 or a verified independent backup.

| File path | Draft Git SHA-1 | Bytes | Comparison to main | Main Git SHA-1 |
|---|---|---:|---|---|
| `V20_TradingSystem_M15/V20-04/README_RU.md` | `c60321304894095e1f9d82e78fc93ceae0b92a02` | 5542 | different | `0f8e091ab49813e7dea52de161b45a3ac8b5f30f` |
| `V20_TradingSystem_M15/V20-04/SOURCE_INVENTORY.json` | `10573c55fd8333c98b0c26103e746b974a4ed32f` | 3593 | absent | — |
| `V20_TradingSystem_M15/V20-04/robot_profiles.py` | `f38e3ce307e7440221ac38f9abc07185b9f2e6a1` | 3619 | absent | — |
| `V20_TradingSystem_M15/V20-04/test_robot_profiles.py` | `fdfe2e0577f912cb09d9ff6cc34569646ef96406` | 3117 | absent | — |

**Caution:** same-path absence does not prove all content is globally unique. No merge, installation or historical closure follows automatically. Before archival closure independently preserve Git objects/history, PR metadata, and content with verified hashes.
