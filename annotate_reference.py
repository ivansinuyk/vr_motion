"""Article 2 - annotation helper: build the manual reference subset.

Interactive OpenCV tool to step through a session video and record:
  - swing-event frames (address / top_backswing / downswing_transition / impact);
  - stick-tip control points (mouse click at the current frame).

By default annotations are appended to ``second_article_outputs/reference_annotations.csv``.
With ``--output`` they go to a separate raw rater file (required for annotator 2).

Clicks are always stored in ORIGINAL video pixel coordinates even when the
on-screen frame is downscaled to fit the display.

Controls:
    d / RIGHT : next frame            a / LEFT  : previous frame
    w / s     : jump +/-10 frames     SPACE     : play / pause
    [ / ]     : jump to prev/next annotated or planned frame
    m         : jump to next missing planned point frame (point-plan mode)
    t         : toggle showing ALL placed points (as a faint trajectory)
    1 2 3 4   : mark address / top_backswing / downswing_transition / impact
    left-click: add a stick-tip control point at the current frame
    u         : undo last point on this frame
    e         : write rows for this session (de-duplicated)
    n / p     : next / previous session in the subset
    r         : reset markings for current session (in-memory)
    q / ESC   : quit (auto-saves when complete rules allow)

Run:
    python annotate_reference.py --annotator alice
    python annotate_reference.py --session <session_id> --annotator bob --round 2
    python annotate_reference.py --restart
    python annotate_reference.py --point-plan second_article_outputs/second_annotator_frame_plan.csv \\
        --output second_article_outputs/reference_annotations_annotator2_round1.csv \\
        --annotator "FRIEND FULL NAME" --round 1 --require-complete --restart
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import pandas as pd

import second_article_common as common

EVENT_KEYS = {
    ord("1"): "address",
    ord("2"): "top_backswing",
    ord("3"): "downswing_transition",
    ord("4"): "impact",
}
REQUIRED_EVENTS = ("address", "top_backswing", "downswing_transition", "impact")


def _is_filled(series: pd.Series) -> pd.Series:
    return series.notna() & (series.astype(str).str.strip() != "") & (series.astype(str) != "nan")


def load_point_plan(path: Path | None) -> dict[str, list[int]]:
    if path is None:
        return {}
    df = pd.read_csv(path)
    required = {"session_id", "reference_frame"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Point plan missing columns: {sorted(missing)}")
    forbidden = {"x_px", "y_px"}
    if forbidden.intersection(df.columns):
        raise RuntimeError("Point plan must not contain x_px/y_px (blinding).")
    df["session_id"] = df["session_id"].astype(str)
    df["reference_frame"] = pd.to_numeric(df["reference_frame"], errors="coerce")
    df = df.dropna(subset=["reference_frame"])
    out: dict[str, list[int]] = {}
    for sid, g in df.groupby("session_id"):
        frames = sorted({int(f) for f in g["reference_frame"].tolist()})
        out[str(sid)] = frames
    return out


def load_session_plan(path: Path | None) -> set[str] | None:
    if path is None:
        return None
    df = pd.read_csv(path)
    if "session_id" not in df.columns:
        raise RuntimeError("Session plan must contain session_id.")
    return set(df["session_id"].astype(str).tolist())


def load_subset_sessions(dataset_root: str, session_plan: set[str] | None = None):
    subset_path = common.OUTPUT_DIR / "reference_subset.csv"
    point_ids = set()
    if subset_path.exists():
        df = pd.read_csv(subset_path)
        ids = df["session_id"].astype(str).tolist()
        if "selected_for_points" in df.columns:
            point_ids = set(
                df[df["selected_for_points"] == True]["session_id"].astype(str)  # noqa: E712
            )
    else:
        ids = [p.name for p in Path(dataset_root).iterdir() if p.is_dir()]
    if session_plan is not None:
        ids = [sid for sid in ids if sid in session_plan]
    sessions = []
    for sid in ids:
        video = Path(dataset_root) / sid / "video_processed.mp4"
        if video.exists():
            sessions.append((sid, video, sid in point_ids))
    return sessions


def load_annotations_df(path: Path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame(columns=common.REFERENCE_ANNOTATION_COLUMNS)


class SessionState:
    def __init__(self, session_id, video_path, planned_frames: list[int] | None = None):
        self.session_id = session_id
        self.video_path = str(video_path)
        self.events = {}  # event_name -> (frame, time_s)
        self.points = {}  # frame -> list[(x_px, y_px)]  (original coords)
        self.planned_frames = list(planned_frames or [])

    def add_point(self, frame, x, y, replace_planned: bool = False):
        if replace_planned and frame in self.planned_frames:
            self.points[frame] = [(int(round(x)), int(round(y)))]
            return
        self.points.setdefault(frame, []).append((int(round(x)), int(round(y))))

    def undo_point(self, frame):
        if self.points.get(frame):
            self.points[frame].pop()
            if not self.points[frame]:
                del self.points[frame]

    def total_points(self):
        return sum(len(v) for v in self.points.values())

    def missing_events(self):
        return [name for name in REQUIRED_EVENTS if name not in self.events]

    def missing_planned_frames(self):
        missing = []
        for f in self.planned_frames:
            if not self.points.get(f):
                missing.append(f)
        return missing

    def is_complete(self, require_points: bool) -> bool:
        if self.missing_events():
            return False
        if require_points and self.missing_planned_frames():
            return False
        return True

    def completeness_message(self, require_points: bool) -> str:
        parts = []
        miss_e = self.missing_events()
        if miss_e:
            parts.append("missing events: " + ",".join(miss_e))
        if require_points:
            miss_p = self.missing_planned_frames()
            if miss_p:
                parts.append(
                    f"missing planned clicks: {len(miss_p)} "
                    f"(next={miss_p[0]})"
                )
            else:
                parts.append(f"planned clicks: {len(self.planned_frames)}/{len(self.planned_frames)}")
        return "; ".join(parts) if parts else "complete"

    def load_existing(self, df, annotator, ann_round):
        """Populate marks from previously saved rows for this session/annotator/round."""
        if df.empty:
            return
        sub = df[
            (df["session_id"].astype(str) == str(self.session_id))
            & (df["annotator_id"].astype(str) == str(annotator))
            & (pd.to_numeric(df["annotation_round"], errors="coerce") == ann_round)
        ]

        def _s(v):
            return "" if pd.isna(v) else str(v).strip()

        for _, r in sub.iterrows():
            event_name = _s(r.get("event_name"))
            point_name = _s(r.get("point_name"))
            frame = pd.to_numeric(r.get("reference_frame"), errors="coerce")
            if pd.isna(frame):
                continue
            frame = int(frame)
            if event_name:
                t = pd.to_numeric(r.get("reference_time_s"), errors="coerce")
                self.events[event_name] = (frame, float(t) if pd.notna(t) else 0.0)
            elif point_name:
                x = pd.to_numeric(r.get("x_px"), errors="coerce")
                y = pd.to_numeric(r.get("y_px"), errors="coerce")
                if pd.notna(x) and pd.notna(y):
                    self.points.setdefault(frame, []).append((int(x), int(y)))

    def to_rows(self, fps, width, height, annotator, ann_round, quality_note):
        rows = []
        for event_name, (frame, t) in self.events.items():
            rows.append(
                self._row(
                    fps,
                    width,
                    height,
                    annotator,
                    ann_round,
                    quality_note,
                    event_name=event_name,
                    frame=frame,
                    t=t,
                )
            )
        # In planned mode export only planned frames (one click each).
        frames = self.planned_frames if self.planned_frames else sorted(self.points.keys())
        for frame in frames:
            pts = self.points.get(frame, [])
            if not pts:
                continue
            t = frame / fps if fps else 0.0
            for i, (x, y) in enumerate(pts, start=1):
                rows.append(
                    self._row(
                        fps,
                        width,
                        height,
                        annotator,
                        ann_round,
                        quality_note,
                        point_name=f"stick_tip_{i}",
                        frame=frame,
                        t=t,
                        x=x,
                        y=y,
                    )
                )
        # Free-mode extra frames not in plan (only when no plan).
        if not self.planned_frames:
            pass
        else:
            # Drop accidental non-planned clicks from export.
            pass
        return rows

    def _row(
        self,
        fps,
        width,
        height,
        annotator,
        ann_round,
        quality_note,
        event_name="",
        point_name="",
        frame="",
        t="",
        x="",
        y="",
    ):
        return {
            "session_id": self.session_id,
            "video_path": self.video_path,
            "fps": fps,
            "frame_width": width,
            "frame_height": height,
            "event_name": event_name,
            "reference_frame": frame,
            "reference_time_s": round(t, 5) if t != "" else "",
            "point_name": point_name,
            "x_px": x,
            "y_px": y,
            "annotator_id": annotator,
            "annotation_round": ann_round,
            "quality_note": quality_note,
        }


def save_session_rows(rows, session_id, annotator, ann_round, output_path: Path):
    """Write rows for one session, replacing any prior rows for the same
    (session_id, annotator_id, annotation_round) so re-saving never duplicates."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_annotations_df(output_path)
    if not existing.empty:
        mask = (
            (existing["session_id"].astype(str) == str(session_id))
            & (existing["annotator_id"].astype(str) == str(annotator))
            & (pd.to_numeric(existing["annotation_round"], errors="coerce") == ann_round)
        )
        existing = existing[~mask]
    new_df = pd.DataFrame(rows, columns=common.REFERENCE_ANNOTATION_COLUMNS)
    out = pd.concat([existing, new_df], ignore_index=True) if not existing.empty else new_df
    out.to_csv(output_path, index=False)
    return len(rows)


def session_done_for_rater(df: pd.DataFrame, session_id, annotator, ann_round) -> bool:
    if df.empty:
        return False
    sub = df[
        (df["session_id"].astype(str) == str(session_id))
        & (df["annotator_id"].astype(str) == str(annotator))
        & (pd.to_numeric(df["annotation_round"], errors="coerce") == ann_round)
    ]
    if sub.empty:
        return False
    events = set(sub.loc[_is_filled(sub["event_name"]), "event_name"].astype(str))
    return all(name in events for name in REQUIRED_EVENTS)


def _draw_timeline(img, state, frame_idx, total):
    """Bottom strip showing events, planned frames, and current point frames."""
    h, w = img.shape[:2]
    y = h - 14
    denom = max(1, total - 1)
    cv2.line(img, (6, y), (w - 6, y), (90, 90, 90), 2)

    def fx(f):
        return int(6 + (w - 12) * (f / denom))

    for f in state.planned_frames:
        cv2.line(img, (fx(f), y - 7), (fx(f), y + 7), (255, 180, 0), 2)
    for f in state.points:
        cv2.line(img, (fx(f), y - 6), (fx(f), y + 6), (0, 255, 0), 2)
    for name, (f, _t) in state.events.items():
        cv2.line(img, (fx(f), y - 8), (fx(f), y + 8), (0, 200, 255), 2)
        cv2.putText(
            img,
            name[0].upper(),
            (fx(f) - 4, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 200, 255),
            1,
            cv2.LINE_AA,
        )
    cv2.line(img, (fx(frame_idx), y - 10), (fx(frame_idx), y + 10), (255, 255, 255), 1)


def annotated_or_planned_frames(state):
    frames = set(state.points.keys())
    frames.update(f for f, _t in state.events.values())
    frames.update(state.planned_frames)
    return sorted(frames)


def draw_overlay(
    disp_img,
    state,
    frame_idx,
    fps,
    total,
    scale,
    already_done,
    is_point_session,
    status,
    show_all=False,
):
    img = disp_img.copy()

    if show_all:
        for f, pts in state.points.items():
            if f == frame_idx:
                continue
            for (x, y) in pts:
                cv2.circle(img, (int(x * scale), int(y * scale)), 3, (120, 120, 120), -1)

    for i, (x, y) in enumerate(state.points.get(frame_idx, []), start=1):
        dx, dy = int(x * scale), int(y * scale)
        cv2.circle(img, (dx, dy), 5, (0, 255, 0), -1)
        cv2.circle(img, (dx, dy), 7, (0, 0, 0), 1)
        cv2.putText(
            img,
            str(i),
            (dx + 8, dy - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    _draw_timeline(img, state, frame_idx, total)

    header = f"{state.session_id}"
    if already_done:
        header += "  [ALREADY ANNOTATED]"
    planned_here = frame_idx in state.planned_frames
    if state.planned_frames:
        point_hint = (
            f"   PLANNED FRAME ({state.planned_frames.index(frame_idx) + 1}/"
            f"{len(state.planned_frames)}) — click clubhead"
            if planned_here
            else "   (not a planned point frame; press m)"
        )
    else:
        point_hint = (
            "   POINT SESSION (click ~5-10 tips)" if is_point_session else "   (events only)"
        )
    lines = [
        header,
        f"frame {frame_idx}/{total - 1}  t={frame_idx / fps:.3f}s" + point_hint,
    ]
    for name in REQUIRED_EVENTS:
        if name in state.events:
            f = state.events[name][0]
            marker = " <--" if f == frame_idx else ""
            lines.append(f"{name}: frame {f}{marker}")
        else:
            lines.append(f"{name}: --")
    if state.planned_frames:
        done_n = len(state.planned_frames) - len(state.missing_planned_frames())
        lines.append(
            f"planned clicks: {done_n}/{len(state.planned_frames)}   "
            f"points here: {len(state.points.get(frame_idx, []))}   (m=next missing)"
        )
        preview = ",".join(str(f) for f in state.planned_frames)
        lines.append(f"plan frames: {preview}")
    else:
        pt_frames = sorted(state.points.keys())
        lines.append(
            f"points here: {len(state.points.get(frame_idx, []))}   total points: {state.total_points()}"
            + (f"   ([/] jump; t=show all)" if pt_frames else "")
        )
        if pt_frames:
            preview = ",".join(str(f) for f in pt_frames[:12]) + (
                " ..." if len(pt_frames) > 12 else ""
            )
            lines.append(f"point frames: {preview}")
    if status:
        lines.append(status)

    y0 = 22
    for i, line in enumerate(lines):
        cv2.putText(
            img, line, (10, y0 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 3, cv2.LINE_AA
        )
        cv2.putText(
            img,
            line,
            (10, y0 + i * 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
    return img


def annotate_session(
    state,
    annotator,
    ann_round,
    quality_note,
    max_w,
    max_h,
    already_done,
    is_point_session,
    output_path: Path,
    require_complete: bool,
):
    cap = cv2.VideoCapture(state.video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

    scale = min(max_w / width, max_h / height, 1.0)
    disp_size = (max(1, int(width * scale)), max(1, int(height * scale)))

    frame_idx = state.planned_frames[0] if state.planned_frames else 0
    playing = False
    show_all = False
    status = state.completeness_message(bool(state.planned_frames))
    win = "annotate_reference"
    cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
    require_points = bool(state.planned_frames)

    def on_mouse(event, x, y, flags, _param):
        nonlocal status, frame_idx
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if state.planned_frames and frame_idx not in state.planned_frames:
            status = f"Ignored click @ {frame_idx}: not a planned frame (press m)"
            return
        state.add_point(
            frame_idx, x / scale, y / scale, replace_planned=bool(state.planned_frames)
        )
        status = state.completeness_message(require_points)

    cv2.setMouseCallback(win, on_mouse)

    def read_frame(i):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, img = cap.read()
        return img if ok else None

    def try_save(force_message: str | None = None) -> bool:
        nonlocal already_done, status
        if require_complete and not state.is_complete(require_points):
            status = "SAVE BLOCKED: " + state.completeness_message(require_points)
            return False
        if not (state.events or state.points):
            status = "nothing to save"
            return False
        n = save_session_rows(
            state.to_rows(fps, width, height, annotator, ann_round, quality_note),
            state.session_id,
            annotator,
            ann_round,
            output_path,
        )
        already_done = True
        status = force_message or f"SAVED {n} rows -> {output_path.name}"
        return True

    loaded_idx = -1
    disp_base = None
    action = "stay"
    while True:
        if loaded_idx != frame_idx:
            raw = read_frame(frame_idx)
            if raw is None:
                frame_idx = max(0, min(frame_idx, total - 1))
                raw = read_frame(frame_idx)
                if raw is None:
                    break
            disp_base = (
                cv2.resize(raw, disp_size, interpolation=cv2.INTER_AREA) if scale < 1.0 else raw
            )
            loaded_idx = frame_idx

        frame_show = draw_overlay(
            disp_base,
            state,
            frame_idx,
            fps,
            total,
            scale,
            already_done,
            is_point_session,
            status,
            show_all,
        )
        cv2.imshow(win, frame_show)
        key = cv2.waitKey(20) & 0xFF

        if playing:
            if frame_idx < total - 1:
                frame_idx += 1
            else:
                playing = False
            if key == 255:
                continue

        if key == 255:
            continue

        if key in (ord("d"), 83):
            frame_idx = min(total - 1, frame_idx + 1)
        elif key in (ord("a"), 81):
            frame_idx = max(0, frame_idx - 1)
        elif key == ord("w"):
            frame_idx = min(total - 1, frame_idx + 10)
        elif key == ord("s"):
            frame_idx = max(0, frame_idx - 10)
        elif key == ord("]"):
            nxt = [f for f in annotated_or_planned_frames(state) if f > frame_idx]
            if nxt:
                frame_idx = nxt[0]
        elif key == ord("["):
            prv = [f for f in annotated_or_planned_frames(state) if f < frame_idx]
            if prv:
                frame_idx = prv[-1]
        elif key == ord("m"):
            missing = state.missing_planned_frames()
            if missing:
                # Prefer the next missing after current frame, else wrap.
                after = [f for f in missing if f > frame_idx]
                frame_idx = after[0] if after else missing[0]
                status = f"jumped to missing planned frame {frame_idx}"
            else:
                status = "all planned frames clicked"
        elif key == ord("t"):
            show_all = not show_all
            status = f"show-all points: {'ON' if show_all else 'OFF'}"
        elif key == ord(" "):
            playing = not playing
        elif key in EVENT_KEYS:
            state.events[EVENT_KEYS[key]] = (frame_idx, frame_idx / fps)
            status = (
                f"marked {EVENT_KEYS[key]} @ frame {frame_idx}; "
                + state.completeness_message(require_points)
            )
        elif key == ord("u"):
            state.undo_point(frame_idx)
            status = "undo point; " + state.completeness_message(require_points)
        elif key == ord("e"):
            try_save()
        elif key == ord("r"):
            state.events.clear()
            state.points.clear()
            status = "reset (in-memory)"
        elif key == ord("n"):
            if require_complete and not state.is_complete(require_points):
                status = "NEXT BLOCKED: " + state.completeness_message(require_points)
                continue
            if state.events or state.points:
                if not try_save():
                    continue
            action = "next"
            break
        elif key == ord("p"):
            action = "prev"
            break
        elif key in (ord("q"), 27):
            if state.events or state.points:
                if require_complete and not state.is_complete(require_points):
                    status = "QUIT without save (incomplete): " + state.completeness_message(
                        require_points
                    )
                    # Still allow quit, but do not write incomplete rows.
                    action = "quit"
                    break
                try_save()
            action = "quit"
            break

    # Auto-save on leaving when markings exist and completeness allows.
    if action != "quit" and (state.events or state.points):
        if not require_complete or state.is_complete(require_points):
            save_session_rows(
                state.to_rows(fps, width, height, annotator, ann_round, quality_note),
                state.session_id,
                annotator,
                ann_round,
                output_path,
            )
    cap.release()
    cv2.destroyWindow(win)
    return action


def main():
    parser = argparse.ArgumentParser(description="Manual reference annotation tool.")
    parser.add_argument("--dataset-root", default=common.DEFAULT_DATASET_ROOT)
    parser.add_argument("--annotator", default="annotator1")
    parser.add_argument("--round", dest="ann_round", type=int, default=1)
    parser.add_argument("--session", default=None, help="Annotate only this session id.")
    parser.add_argument("--quality-note", default="")
    parser.add_argument("--max-width", type=int, default=1280, help="Max display width, px.")
    parser.add_argument("--max-height", type=int, default=720, help="Max display height, px.")
    parser.add_argument("--restart", action="store_true", help="Ignore resume; start at first session.")
    parser.add_argument(
        "--point-plan",
        default=None,
        help="CSV of required control frames (session_id, reference_frame).",
    )
    parser.add_argument(
        "--session-plan",
        default=None,
        help="CSV limiting sessions (session_id column).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Raw rater CSV path. Defaults to reference_annotations.csv.",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Block save/next unless all 4 events and all planned point frames are set.",
    )
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else common.REFERENCE_ANNOTATIONS_CSV
    point_plan = load_point_plan(Path(args.point_plan) if args.point_plan else None)
    session_plan = load_session_plan(Path(args.session_plan) if args.session_plan else None)

    if args.require_complete and not point_plan:
        print(
            "Warning: --require-complete without --point-plan only enforces the four events.",
            file=sys.stderr,
        )

    sessions = load_subset_sessions(args.dataset_root, session_plan)
    if args.session:
        sessions = [s for s in sessions if s[0] == args.session]
    if point_plan:
        # Keep subset order, but only sessions present in the point plan.
        sessions = [s for s in sessions if s[0] in point_plan]
        missing_plan = sorted(set(point_plan) - {s[0] for s in sessions})
        if missing_plan:
            raise RuntimeError(
                "Point-plan sessions missing from subset/videos: "
                + ", ".join(missing_plan[:5])
                + (" ..." if len(missing_plan) > 5 else "")
            )
    if not sessions:
        raise RuntimeError("No sessions to annotate (run prepare_reference_subset.py first).")

    ann_df = load_annotations_df(output_path)
    done_ids = {
        sid
        for sid, _v, _p in sessions
        if session_done_for_rater(ann_df, sid, args.annotator, args.ann_round)
    }

    start = 0
    if not args.restart and not args.session:
        for idx, (sid, _v, _p) in enumerate(sessions):
            if sid not in done_ids:
                start = idx
                break
        else:
            start = 0
        print(
            f"Resume: {len(done_ids)} session(s) complete for "
            f"{args.annotator}/round {args.ann_round}. "
            f"Starting at #{start + 1}/{len(sessions)} ({sessions[start][0]})."
        )
        print(f"Output file: {output_path}")

    i = start
    while 0 <= i < len(sessions):
        sid, video, is_point = sessions[i]
        planned = point_plan.get(sid, [])
        if planned:
            is_point = True
        already = session_done_for_rater(
            load_annotations_df(output_path), sid, args.annotator, args.ann_round
        )
        tag = (
            f"PLANNED {len(planned)} pts+events"
            if planned
            else ("POINTS+events" if is_point else "events-only")
        )
        print(
            f"[{i + 1}/{len(sessions)}] {sid}  ({tag})"
            + ("  [already annotated]" if already else "")
        )
        state = SessionState(sid, video, planned_frames=planned)
        state.load_existing(load_annotations_df(output_path), args.annotator, args.ann_round)
        action = annotate_session(
            state,
            args.annotator,
            args.ann_round,
            args.quality_note,
            args.max_width,
            args.max_height,
            already,
            is_point,
            output_path,
            args.require_complete,
        )
        if action == "quit":
            break
        i = i + 1 if action != "prev" else max(0, i - 1)

    # Final completeness gate for planned multi-session runs.
    if args.require_complete and point_plan:
        final_df = load_annotations_df(output_path)
        incomplete = []
        for sid, _v, _p in sessions:
            st = SessionState(sid, "", planned_frames=point_plan.get(sid, []))
            st.load_existing(final_df, args.annotator, args.ann_round)
            if not st.is_complete(True):
                incomplete.append(f"{sid}: {st.completeness_message(True)}")
        if incomplete:
            print("INCOMPLETE --require-complete check failed:")
            for line in incomplete:
                print("  -", line)
            raise SystemExit(1)
        print(
            f"Complete: {len(sessions)} sessions with 4 events and "
            f"{sum(len(v) for v in point_plan.values())} planned clicks "
            f"-> {output_path}"
        )

    print("Done.")


if __name__ == "__main__":
    main()
