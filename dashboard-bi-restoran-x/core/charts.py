"""Grafik Plotly bertema gelap + olive, selaras dengan design token dashboard."""
import plotly.graph_objects as go

# Palet olive/sage untuk seri data.
OLIVE_SEQ = ["#90a857", "#bcc79a", "#6c7d3c", "#d6ddbf",
             "#54632e", "#9fae72", "#eef1e4", "#738a42"]
GRID = "#2d3227"
TEXT = "#a4aa94"
PRIMARY = "#90a857"


def _base(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Inter, sans-serif", size=12),
        colorway=OLIVE_SEQ, height=height,
        margin=dict(l=12, r=12, t=36, b=12),
        legend=dict(font=dict(color=TEXT), bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#1a1d16", font=dict(color="#e9ebe2")),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
                     tickfont=dict(color=TEXT))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
                     tickfont=dict(color=TEXT))
    return fig


def bar_top_items(df, value="net_sales", n=15):
    """Bar horizontal: n item teratas berdasarkan total `value`."""
    agg = (df.groupby("items", as_index=False)[value].sum()
             .sort_values(value, ascending=True).tail(n))
    fig = go.Figure(go.Bar(
        x=agg[value], y=agg["items"], orientation="h",
        marker=dict(color=PRIMARY), hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"))
    fig.update_layout(title=f"{n} Item Teratas — total {value}")
    return _base(fig, height=max(320, 22 * len(agg)))


def donut_category(df, value="net_sales"):
    """Donut: kontribusi tiap kategori terhadap total `value`."""
    agg = df.groupby("category", as_index=False)[value].sum().sort_values(value, ascending=False)
    fig = go.Figure(go.Pie(
        labels=agg["category"], values=agg[value], hole=0.55,
        marker=dict(colors=OLIVE_SEQ, line=dict(color="#0d0e0c", width=1.5)),
        textfont=dict(color="#0d0e0c"),
        hovertemplate="%{label}<br>%{value:,.0f} (%{percent})<extra></extra>"))
    fig.update_layout(title=f"Kontribusi Kategori — {value}")
    return _base(fig, height=360)


def line_quantity_by_month(df):
    """Garis + titik: total kuantitas per bulan."""
    if "bulan" not in df.columns:
        return None
    agg = df.groupby("bulan", as_index=False)["quantity"].sum().sort_values("bulan")
    fig = go.Figure(go.Scatter(
        x=agg["bulan"], y=agg["quantity"], mode="lines+markers",
        line=dict(color=PRIMARY, width=2),
        marker=dict(color="#d6ddbf", size=8, line=dict(color=PRIMARY, width=1.5)),
        hovertemplate="%{x}<br>%{y:,.0f} unit<extra></extra>"))
    fig.update_layout(title="Kuantitas Terjual per Bulan")
    return _base(fig, height=320)


def bar_items_in_category(df, category, value="net_sales", n=20):
    """Bar item-item di dalam satu kategori (mode fokus)."""
    sub = df[df["category"] == category]
    agg = (sub.groupby("items", as_index=False)[value].sum()
              .sort_values(value, ascending=True).tail(n))
    fig = go.Figure(go.Bar(
        x=agg[value], y=agg["items"], orientation="h",
        marker=dict(color="#9fae72"), hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"))
    fig.update_layout(title=f"Item dalam kategori \u201c{category}\u201d — {value}")
    return _base(fig, height=max(300, 22 * len(agg)))


def scatter_clusters(df, x, y, color_col, title, xlab=None, ylab=None):
    """Sebaran menu diwarnai per klaster/profil (visual hasil, bukan metrik)."""
    fig = go.Figure()
    groups = sorted(df[color_col].astype(str).unique())
    for i, cv in enumerate(groups):
        d = df[df[color_col].astype(str) == cv]
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y], mode="markers", name=str(cv),
            marker=dict(size=9, color=OLIVE_SEQ[i % len(OLIVE_SEQ)],
                        line=dict(color="#0d0e0c", width=0.6)),
            text=d["items"],
            hovertemplate="%{text}<br>%{x:,.0f} / %{y:,.0f}<extra></extra>"))
    fig.update_layout(title=title, xaxis_title=xlab or x, yaxis_title=ylab or y)
    return _base(fig, height=420)
