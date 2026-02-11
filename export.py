"""Export animated Plotly figures as MP4 video files.

Uses *kaleido* to render each animation frame to PNG and *imageio-ffmpeg*
to stitch the resulting images into an H.264 MP4.
"""

from __future__ import annotations

import copy
import io
import os
import tempfile

import imageio
import plotly.graph_objects as go


def plotly_fig_to_mp4(
    fig: go.Figure,
    frame_duration_ms: int = 150,
    width: int = 1280,
    height: int = 720,
    progress_cb=None,
) -> bytes | None:
    """Render every animation frame of *fig* to PNG and stitch into an MP4.

    Parameters
    ----------
    fig : go.Figure
        A Plotly figure whose ``fig.frames`` list is non-empty.
    frame_duration_ms : int
        Milliseconds per frame – converted to video FPS.
    width, height : int
        Resolution of the exported video.
    progress_cb : callable or None
        Called with a float in ``[0, 1]`` after each frame is rendered.

    Returns
    -------
    bytes or None
        Raw MP4 file contents, or ``None`` when the figure has no frames.
    """
    if not fig.frames:
        return None

    fps = max(1, round(1000 / frame_duration_ms))

    # Preserve the base layout but strip animation-only UI widgets
    base_layout = copy.deepcopy(fig.layout)
    base_layout.updatemenus = None
    base_layout.sliders = None

    total = len(fig.frames)
    png_images: list[bytes] = []

    for idx, frame in enumerate(fig.frames):
        frame_fig = go.Figure(data=frame.data, layout=base_layout)
        if frame.layout:
            frame_fig.update_layout(frame.layout)
        png_images.append(
            frame_fig.to_image(
                format="png", width=width, height=height, engine="kaleido",
            )
        )
        if progress_cb is not None:
            progress_cb((idx + 1) / total)

    # Stitch PNGs into MP4 via ffmpeg (temp file for broad compatibility)
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        writer = imageio.get_writer(
            tmp_path,
            fps=fps,
            codec="libx264",
            output_params=["-pix_fmt", "yuv420p"],
        )
        for png in png_images:
            img = imageio.imread(io.BytesIO(png))
            # Drop alpha channel if present (MP4 doesn't support it)
            if img.ndim == 3 and img.shape[2] == 4:
                img = img[:, :, :3]
            writer.append_data(img)
        writer.close()

        with open(tmp_path, "rb") as fh:
            return fh.read()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
