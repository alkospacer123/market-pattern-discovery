"""Pure Plotly rendering from display contracts, no strategy calculations."""
import plotly.graph_objects as go
from .models import RobotSnapshot, SourceKind
from .freshness import MSK


def candle_chart(snapshot: RobotSnapshot, symbol: str, count: int) -> go.Figure:
    rows = [row for row in snapshot.candles if row.instrument == symbol][-count:]
    fig = go.Figure()
    if not rows:
        fig.add_annotation(text="UNKNOWN — источник не содержит свечей", showarrow=False)
        return fig
    demo = snapshot.status.provenance.source_kind == SourceKind.SYNTHETIC
    label = "SYNTHETIC / DEMO" if demo else "OFFLINE_FIXTURE"
    x = [row.close_at.astimezone(MSK) for row in rows]
    fig.add_trace(go.Candlestick(x=x, open=[r.open for r in rows], high=[r.high for r in rows],
                                low=[r.low for r in rows], close=[r.close for r in rows], name="SYNTHETIC OHLC" if demo else "OFFLINE_FIXTURE OHLC",
                                increasing_line_color="#45d6bb", decreasing_line_color="#fb7185"))
    if any(row.demo_indicator is not None for row in rows):
        fig.add_trace(go.Scatter(x=x, y=[r.demo_indicator for r in rows], name="DEMO-линия (не T3)",
                                 line=dict(color="#8b9dff", width=1.5)))
    for direction, color, marker in (("LONG", "#45d6bb", "triangle-up"), ("EXIT", "#ffbf69", "triangle-down")):
        points = [s for s in snapshot.signals if s.instrument == symbol and s.direction == direction and s.price is not None
                  and rows[0].close_at <= s.occurred_at <= rows[-1].close_at]
        fig.add_trace(go.Scatter(x=[s.occurred_at.astimezone(MSK) for s in points], y=[s.price for s in points],
                                 mode="markers", name=f"DEMO {direction}" if demo else f"OFFLINE_FIXTURE {direction}", marker=dict(color=color, symbol=marker, size=12)))
    for instrument in snapshot.instruments:
        if instrument.instrument == symbol and instrument.stop_price is not None:
            fig.add_hline(y=instrument.stop_price, line_dash="dash", line_color="#fb7185",
                          annotation_text="SYNTHETIC стоп")
    fig.update_layout(template="plotly_dark", paper_bgcolor="#0b101a", plot_bgcolor="#0b101a",
                      height=420, margin=dict(l=8, r=8, t=80, b=8),
                      title=dict(text=f"{symbol} · {label}", y=0.98, x=0.01), xaxis_title="Завершение демонстрационной свечи · MSK (UTC+3)" if demo else "Закрытие H1 · MSK (UTC+3) · актуальность UNKNOWN",
                      xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=1.12),
                      yaxis_title="DEMO-цена" if demo else "OFFLINE_FIXTURE-цена")
    return fig
