# Telemetry Chart
st.subheader("📈 Ground Truth Moisture vs. Spaceborne NDVI Correlation")

field_history = df_truth[df_truth["field_id"] == selected_field_id]

if not field_history.empty:
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=field_history["date"],
        y=field_history["soil_moisture_pct"],
        name="Soil Moisture (%)",
        mode="lines+markers",
        line=dict(color="#3182ce", width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=field_history["date"],
        y=field_history["scout_vigour"],
        name="Canopy Health (0-1)",
        mode="lines+markers",
        line=dict(color="#38a169", width=3, dash="dot"),
        yaxis="y2"
    ))
    
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(title="Date"),
        yaxis=dict(title="Soil Moisture (%)", titlefont=dict(color="#3182ce")),
        yaxis2=dict(
            title="Crop Vigour Index",
            titlefont=dict(color="#38a169"),
            overlaying="y",
            side="right",
            range=[0, 1.1]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No historical telemetry time-series logs recorded for this parcel yet.")