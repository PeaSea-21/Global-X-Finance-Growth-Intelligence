# Pipeline architecture

```text
RSS/X fetch -> immutable Evidence -> source adapter -> finance gate
            -> entity + market-qualified security mapping
            -> stable event assignment -> opportunity ranking
            -> diversity-aware read-only snapshot
TWSE daily OHLCV -> prior-20-session baseline -> StockSignal
StockSignal <-> event IDs <-> Evidence links -> content opportunity
```

The public exporter now reads event Evidence, stock signals, source coverage and snapshot metadata.
No paid API, minute bar, model-generated draft or server write endpoint is introduced.
