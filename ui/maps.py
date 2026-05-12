"""Map renderers for CovMo Telecom Intelligence Platform."""
from __future__ import annotations

from typing import List, Dict, Any, Optional
import json

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False


# ── Geographic Constants ─────────────────────────────────────────────────────
TAIPEI_ARENA = (25.0516, 121.5500)
NANJING_FUXING_MRT = (25.0528, 121.5445)
NANGANG_STATION = (25.0550, 121.5433)  # Reference


def _dark_tile() -> folium.TileLayer:
    """Return a dark-themed tile layer for Folium."""
    try:
        return folium.TileLayer(
            tiles="CartoDB dark_matter",
            attr="CartoDB"
        )
    except Exception:
        return folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="CartoDB dark_matter",
            name="Dark Matter"
        )


def _create_base_map(center: tuple[float, float] = TAIPEI_ARENA, zoom: int = 16) -> folium.Map:
    """Create a dark-themed base map centered on Taipei Arena."""
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,
        width="100%",
        height="100%",
        prefer_canvas=True,
    )
    _dark_tile().add_to(m)
    return m


def _add_taipei_arena(m: folium.Map) -> None:
    """Add Taipei Arena marker with custom icon."""
    folium.Marker(
        location=TAIPEI_ARENA,
        popup=folium.Popup(
            "<b>🎤 Taipei Arena</b><br>Power Station Concert<br>May 15, 2026",
            max_width=200
        ),
        tooltip="Taipei Arena",
        icon=folium.Icon(
            color="red", icon="music", prefix="fa",
            icon_color="white"
        )
    ).add_to(m)

    # Arena circle
    folium.Circle(
        location=TAIPEI_ARENA,
        radius=120,
        color="#FF1744",
        fill=True,
        fill_color="#FF1744",
        fill_opacity=0.15,
        weight=2,
        dash_array="5,5",
        popup="Taipei Arena Coverage Zone"
    ).add_to(m)


def _add_mrt_station(m: folium.Map) -> None:
    """Add Nanjing Fuxing MRT station marker."""
    folium.Marker(
        location=NANJING_FUXING_MRT,
        popup=folium.Popup(
            "<b>🚇 Nanjing Fuxing MRT</b><br>Blue Line<br>BL12 Station",
            max_width=200
        ),
        tooltip="Nanjing Fuxing MRT Station",
        icon=folium.Icon(
            color="blue", icon="subway", prefix="fa",
            icon_color="white"
        )
    ).add_to(m)

    # MRT underground zone
    folium.Circle(
        location=NANJING_FUXING_MRT,
        radius=80,
        color="#00E5FF",
        fill=True,
        fill_color="#00E5FF",
        fill_opacity=0.1,
        weight=2,
        popup="MRT Underground Zone"
    ).add_to(m)


def _add_cell_sectors(m: folium.Map, cells_data: List[Dict]) -> None:
    """Add cell sector overlays from mock_cells.json."""
    for cell in cells_data:
        loc = cell.get("location", {})
        lat, lon = loc.get("lat", 0), loc.get("lon", 0)
        cell_type = cell.get("cell_type", "macro")

        if cell_type == "small_cell":
            color = "#00E676"
            radius = 60
        elif cell_type == "distributed_antenna":
            color = "#E040FB"
            radius = 50
        else:
            color = "#FF9100"
            radius = 100

        folium.Circle(
            location=(lat, lon),
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.12,
            weight=1,
            popup=f"<b>{cell.get('name')}</b><br>ID: {cell.get('cell_id')}<br>Type: {cell_type}",
        ).add_to(m)


def _add_egress_path(m: folium.Map, progress: float = 0.5) -> None:
    """Add the egress path from Arena to MRT with animated segments."""
    import numpy as np

    # Full path
    lats = np.linspace(TAIPEI_ARENA[0], NANJING_FUXING_MRT[0], 30)
    lons = np.linspace(TAIPEI_ARENA[1], NANJING_FUXING_MRT[1], 30)

    # Completed segments (crowd has passed)
    n_complete = int(len(lats) * progress)
    if n_complete > 0:
        folium.PolyLine(
            locations=list(zip(lats[:n_complete], lons[:n_complete])),
            color="#00E676",
            weight=4,
            opacity=0.8,
            popup=f"Egress path — {progress*100:.0f}% complete"
        ).add_to(m)

    # Remaining path
    if n_complete < len(lats):
        folium.PolyLine(
            locations=list(zip(lats[n_complete:], lons[n_complete:])),
            color="#546E7A",
            weight=3,
            opacity=0.5,
            dash_array="8,8",
        ).add_to(m)


def _add_subscriber_dots(
    m: folium.Map,
    telemetry: List[Dict],
    max_dots: int = 100,
) -> None:
    """Add subscriber dots on the map colored by RSRP quality."""
    if not telemetry:
        return

    sample = telemetry[:max_dots]

    for t in sample:
        loc = t.get("location", {})
        lat, lon = loc.get("lat", 0), loc.get("lon", 0)
        rsrp = t.get("metrics", {}).get("rsrp", -100)
        is_vip = t.get("qos_class") == "VIP_Premium"

        # Color by RSRP quality
        if rsrp > -90:
            color = "#00E676"  # Good
        elif rsrp > -105:
            color = "#FF9100"  # Fair
        else:
            color = "#FF1744"  # Poor

        icon_color = "#FF1744" if is_vip else color

        folium.CircleMarker(
            location=(lat, lon),
            radius=4 if is_vip else 2,
            color=icon_color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=f"<b>UE: {t.get('ue_id')}</b><br>"
                  f"RSRP: {rsrp:.1f} dBm<br>"
                  f"SINR: {t.get('metrics',{}).get('sinr',0):.1f} dB<br>"
                  f"PRB: {t.get('metrics',{}).get('prb_utilization',0):.1f}%",
        ).add_to(m)


def render_mobility_map(
    telemetry: List[Dict],
    cells_data: List[Dict],
    progress: float = 0.5,
    exit_data: Optional[List[Dict]] = None,
) -> folium.Map:
    """
    Render the full mobility digital twin map.

    Args:
        telemetry: List of UETelemetry dicts
        cells_data: List of cell dicts from mock_cells.json
        progress: Egress completion percentage (0.0-1.0)
        exit_data: Optional MRT exit data
    """
    if not FOLIUM_AVAILABLE:
        return None

    m = _create_base_map()

    # Add base infrastructure
    _add_taipei_arena(m)
    _add_mrt_station(m)

    # Add cell sectors
    if cells_data:
        _add_cell_sectors(m, cells_data)

    # Add egress path
    _add_egress_path(m, progress)

    # Add MRT exits if provided
    if exit_data:
        for exit_info in exit_data:
            loc = exit_info.get("location", {})
            if loc:
                folium.Marker(
                    location=(loc.get("lat", 0), loc.get("lon", 0)),
                    popup=exit_info.get("name", "Exit"),
                    icon=folium.Icon(
                        color="orange", icon="sign-out", prefix="fa",
                        icon_color="white"
                    )
                ).add_to(m)

    # Add subscriber dots
    _add_subscriber_dots(m, telemetry)

    # Add YouBike marker
    folium.Marker(
        location=(25.0518, 121.5492),
        popup="🚲 YouBike Arena Station<br>Available: 12<br>Empty docks: 8",
        tooltip="YouBike Station 500101077",
        icon=folium.Icon(color="green", icon="bicycle", prefix="fa",
                         icon_color="white")
    ).add_to(m)

    return m


def render_map_st(telemetry: List[Dict], cells_data: List[Dict], progress: float = 0.5) -> None:
    """
    Render mobility map directly in Streamlit using streamlit-folium.
    Call this inside a st.container() or st.column().
    """
    if not FOLIUM_AVAILABLE:
        import streamlit as st
        st.warning("streamlit-folium not installed. Map unavailable.")
        return

    m = render_mobility_map(telemetry, cells_data, progress)
    if m is not None:
        st_folium(m, width="100%", height=480, returned_objects=[])