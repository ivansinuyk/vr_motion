import math
import cv2

import config
from analysis import (
    linear_speed, angle, angular_velocity, wrap_angle, find_impact_idx,
    segment_angle, joint_angle_3pt, midpoint, RunningMedian,
)
from drawing import draw_skeleton, draw_stick, draw_ball
from utils_filter import (
    MedianFilter2D,
    smooth_trajectory_poly,
    despike_trajectory,
    is_physical,
)
from kalman import Kalman2D
from rts_smoother import rts_smooth


class SwingAnalyzer:
    def __init__(self, data, fps, screen_size):
        self.data = data
        self.dt = 1.0 / fps if fps and fps > 0 else 1.0 / 30.0
        self.screen_w, self.screen_h = screen_size

        # ---- time / core kinematics ----
        self.times = []
        self.speeds = []
        self.ang_vels = []
        self.accels = []
        self.ang_accels = []
        self.energies = []
        self.jerks = []
        self.tip_ball_distances = []

        # ---- trajectory buffers ----
        self.tip_positions_raw = []
        self.tip_positions = []
        self.tip_positions_m = []
        self.base_positions = []

        # ---- biomechanics buffers ----
        self.hip_angles = []
        self.shoulder_angles = []
        self.x_factors = []
        self.wrist_angles = []
        self.arc_radii = []
        self.stick_lengths_px = []

        # ---- previous-frame state ----
        self.prev_tip = None
        self.prev_speed = None
        self.prev_ang = None
        self.prev_ang_vel = None
        self.prev_acc = None

        # ---- filters ----
        self.kalman = Kalman2D(q_pos=8.0, q_vel=8.0, r_meas=6.0)
        self.median = MedianFilter2D(win=config.MEDIAN_WIN)
        self.missing_tip_frames = 0
        self.prev_meas = None
        self.prev_meas_speed = None
        self.rejected_tip_frames = 0

        # ---- dynamic calibration ----
        self.stick_len_median = RunningMedian(win=config.STICK_CAL_WIN)
        self.scale_m = None
        self.scale_m_series = []

        # ---- impact ----
        self.impact_idx = None

        # ---- rolling summary state (for O(1) summary) ----
        self.max_speed = 0.0
        self.max_ang_vel = 0.0
        self.max_accel = 0.0
        self.peak_speed_idx = 0
        self.jerk_sq_sum = 0.0
        self.jerk_nonzero_count = 0
        self.max_x_factor_abs = 0.0
        self.max_x_factor_val = 0.0

        # ---- trajectory smoothing cache ----
        self._kalman_states = []
        self._kalman_covs = []
        self._kalman_dts = []
        self._rts_tip_px_cache = []
        self._smoothed_tip_px_cache = []
        self._despiked_tip_px_cache = []
        self._trajectory_dirty = True
        self._export_cache = None

    # ------------------------------------------------------------------ #
    #  Calibration (updated every frame with running median)
    # ------------------------------------------------------------------ #
    def _update_calibration(self, stick_len_px):
        med = self.stick_len_median.update(stick_len_px)
        if med and med > 0:
            raw_scale = config.STICK_REAL_LENGTH_M / med
            if self.scale_m is None:
                self.scale_m = raw_scale
                return

            # Clamp sudden scale jumps (depth/perspective spikes) and smooth.
            max_rel_step = 0.03
            lo = self.scale_m * (1.0 - max_rel_step)
            hi = self.scale_m * (1.0 + max_rel_step)
            bounded = min(max(raw_scale, lo), hi)
            alpha = 0.20
            self.scale_m = (1.0 - alpha) * self.scale_m + alpha * bounded

    # ------------------------------------------------------------------ #
    #  Landmark helper
    # ------------------------------------------------------------------ #
    @staticmethod
    def _lm_px(pts, i, w, h):
        if i >= len(pts):
            return None
        p = pts[i]
        x = p.get("x")
        y = p.get("y")
        if x is None or y is None:
            return None
        return (float(x) * w, float(y) * h)

    @staticmethod
    def _dist(a, b):
        if a is None or b is None:
            return 0.0
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _adaptive_r_from_residual(self, residual_px):
        base = self.kalman.base_r
        scale = max(float(config.KF_ADAPTIVE_RESIDUAL_PX), 1e-6)
        u = max(0.0, float(residual_px)) / scale
        mult = min(1.0 + u * u, float(config.KF_ADAPTIVE_R_MULT_MAX))
        return base * mult

    def _measurement_is_valid(self, meas, dt):
        if meas is None:
            return False
        if not self.kalman.initialized or self.prev_meas is None:
            return True
        return is_physical(
            self.prev_meas,
            meas,
            dt,
            self.prev_meas_speed,
            max_v=float(config.KF_MAX_MEAS_SPEED_PX_S),
            max_a=float(config.KF_MAX_MEAS_ACCEL_PX_S2),
        )

    def _append_kalman_snapshot(self, dt):
        if self.kalman.initialized:
            self._kalman_states.append(self.kalman.x.copy())
            self._kalman_covs.append(self.kalman.P.copy())
            self._kalman_dts.append(float(dt))
        else:
            self._kalman_states.append(None)
            self._kalman_covs.append(None)
            self._kalman_dts.append(None)

    def _rts_smoothed_points(self):
        n = len(self._kalman_states)
        out = [None] * n
        i = 0
        while i < n:
            if self._kalman_states[i] is None:
                i += 1
                continue
            j = i
            while j < n and self._kalman_states[j] is not None:
                j += 1

            seg_states = [s.copy() for s in self._kalman_states[i:j]]
            seg_covs = [p.copy() for p in self._kalman_covs[i:j]]
            seg_fs = []
            for k in range(i, j - 1):
                dt_next = self._kalman_dts[k + 1]
                if dt_next is None:
                    seg_fs = []
                    break
                seg_fs.append(self.kalman.transition(dt_next))

            if len(seg_states) >= 3 and len(seg_fs) == len(seg_states) - 1:
                # Pass the same process-noise matrix used by Kalman2D.predict so
                # RTS predicted covariance matches the forward filter.
                xs_s, _ = rts_smooth(
                    seg_states, seg_covs, seg_fs, Q=self.kalman.Q_diag
                )
            else:
                xs_s = seg_states

            for k, x in enumerate(xs_s):
                out[i + k] = (float(x[0, 0]), float(x[1, 0]))
            i = j
        return out

    def _smooth_tip_positions(self):
        if self._trajectory_dirty:
            self._rts_tip_px_cache = self._rts_smoothed_points()
            self._despiked_tip_px_cache = despike_trajectory(
                self._rts_tip_px_cache,
                thresh_px=config.TRAJ_DESPIKE_THRESH_PX,
                max_neighbor_px=config.TRAJ_DESPIKE_MAX_NEIGHBOR_PX,
                passes=config.TRAJ_DESPIKE_PASSES,
            )
            self._smoothed_tip_px_cache = smooth_trajectory_poly(
                self._despiked_tip_px_cache,
                window=config.TRAJ_POLY_WIN,
                degree=config.TRAJ_POLY_DEG,
                raw_ref=self.tip_positions_raw,
                raw_blend=config.TRAJ_BLEND_RAW,
                max_dev_px=config.TRAJ_MAX_DEV_PX,
                laplace_passes=config.TRAJ_LAPLACE_PASSES,
                laplace_alpha=config.TRAJ_LAPLACE_ALPHA,
                closed_dist_px=config.TRAJ_CLOSED_DIST_PX,
                closed_min_cos=config.TRAJ_CLOSED_MIN_COS,
                post_despike_thresh_px=config.TRAJ_POST_DESPIKE_THRESH_PX,
                post_despike_max_neighbor_px=config.TRAJ_POST_DESPIKE_MAX_NEIGHBOR_PX,
                post_despike_passes=config.TRAJ_POST_DESPIKE_PASSES,
            )
            self._trajectory_dirty = False
        return self._smoothed_tip_px_cache

    def _update_tip_filter(self, tip, dt):
        med = self.median.update(tip)
        meas = med if med is not None else tip
        accepted = self._measurement_is_valid(meas, dt) if meas is not None else False

        if meas is not None and accepted:
            residual_px = 0.0
            if self.kalman.initialized:
                z_pred, _ = self.kalman.predict_measurement(dt)
                residual_px = math.hypot(
                    float(meas[0]) - float(z_pred[0, 0]),
                    float(meas[1]) - float(z_pred[1, 0]),
                )
            adaptive_r = self._adaptive_r_from_residual(residual_px)
            x = self.kalman.update(meas, dt, r_meas=adaptive_r)
            self.missing_tip_frames = 0
            if self.prev_meas is not None and dt > 0:
                self.prev_meas_speed = self._dist(self.prev_meas, meas) / dt
            self.prev_meas = meas
        else:
            if meas is not None:
                self.rejected_tip_frames += 1
            self.missing_tip_frames += 1
            if self.kalman.initialized and self.missing_tip_frames <= config.MAX_KF_PREDICT_GAP:
                x = self.kalman.predict(dt)
            else:
                x = None

        tip_f = (float(x[0, 0]), float(x[1, 0])) if x is not None else None
        self.tip_positions.append(tip_f)
        self._append_kalman_snapshot(dt)
        self._trajectory_dirty = True
        return tip_f

    def _record_scale_state(self, tip_f):
        """Append current scale estimate and compute metric-space tip position."""
        scale_i = self.scale_m
        if scale_i is None and self.scale_m_series:
            scale_i = self.scale_m_series[-1]
        self.scale_m_series.append(scale_i)

        if tip_f is not None and scale_i:
            self.tip_positions_m.append((tip_f[0] * scale_i, tip_f[1] * scale_i))
        else:
            self.tip_positions_m.append((0.0, 0.0))

    def _append_time(self, dt, t):
        if t is None:
            t = (self.times[-1] + dt) if self.times else 0.0
        self.times.append(float(t))

    @staticmethod
    def _step_kinematics(prev_tip, tip, prev_speed, prev_ang, prev_ang_vel, prev_acc, base, scale, dt):
        """Compute one-step kinematics. Returns (v, acc, ang, w_ang, ang_acc, jerk)."""
        v = linear_speed(prev_tip, tip, dt) * scale
        acc = (v - prev_speed) / dt if prev_speed is not None else 0.0
        ang = angle(base, tip)
        w_ang = angular_velocity(prev_ang, ang, dt) if (prev_ang is not None and ang is not None) else 0.0
        ang_acc = (w_ang - prev_ang_vel) / dt if prev_ang_vel is not None else 0.0
        jerk = (acc - prev_acc) / dt if prev_acc is not None else 0.0
        return v, acc, ang, w_ang, ang_acc, jerk

    def _append_kinematics(self, idx, base, tip_f, dt):
        scale_i = self.scale_m_series[-1] if self.scale_m_series and self.scale_m_series[-1] else (self.scale_m or 1.0)
        v, acc, ang, w_ang, ang_acc, jerk = self._step_kinematics(
            self.prev_tip, tip_f, self.prev_speed, self.prev_ang,
            self.prev_ang_vel, self.prev_acc, base, scale_i, dt,
        )

        self.speeds.append(v)
        if v >= self.max_speed:
            self.max_speed = v
            self.peak_speed_idx = idx

        self.accels.append(acc)
        if acc >= self.max_accel:
            self.max_accel = acc

        self.ang_vels.append(w_ang)
        if w_ang >= self.max_ang_vel:
            self.max_ang_vel = w_ang

        self.ang_accels.append(ang_acc)
        self.energies.append(v * v)
        self.jerks.append(jerk)
        if jerk != 0:
            self.jerk_sq_sum += jerk * jerk
            self.jerk_nonzero_count += 1

        self.prev_tip = tip_f
        self.prev_speed = v
        self.prev_ang = ang
        self.prev_ang_vel = w_ang
        self.prev_acc = acc

    def _append_biomechanics(
        self,
        base,
        tip_f,
        l_shoulder,
        r_shoulder,
        l_hip,
        r_hip,
        r_elbow,
        r_wrist,
    ):
        hip_a = segment_angle(l_hip, r_hip)
        self.hip_angles.append(math.degrees(hip_a) if hip_a is not None else None)

        sh_a = segment_angle(l_shoulder, r_shoulder)
        self.shoulder_angles.append(math.degrees(sh_a) if sh_a is not None else None)

        if hip_a is not None and sh_a is not None:
            xf = wrap_angle(sh_a - hip_a)
            xf = math.degrees(xf)
            self.x_factors.append(xf)
            if abs(xf) >= self.max_x_factor_abs:
                self.max_x_factor_abs = abs(xf)
                self.max_x_factor_val = xf
        else:
            self.x_factors.append(None)

        self.wrist_angles.append(joint_angle_3pt(r_elbow, r_wrist, base))

        sh_mid = midpoint(l_shoulder, r_shoulder)
        if sh_mid and tip_f is not None:
            self.arc_radii.append(math.hypot(tip_f[0] - sh_mid[0], tip_f[1] - sh_mid[1]))
        else:
            self.arc_radii.append(None)

    def _append_impact(self, idx, tip_f, ball):
        if tip_f is not None and ball:
            dist = math.hypot(tip_f[0] - ball[0], tip_f[1] - ball[1])
        else:
            dist = None
        self.tip_ball_distances.append(dist)

        if self.impact_idx is None and dist is not None and dist < config.IMPACT_DIST_PX:
            self.impact_idx = idx

    @staticmethod
    def _curvature_3pt(p0, p1, p2):
        if p0 is None or p1 is None or p2 is None:
            return None
        a = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        b = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        c = math.hypot(p2[0] - p0[0], p2[1] - p0[1])
        if a <= 1e-9 or b <= 1e-9 or c <= 1e-9:
            return None
        area2 = abs(
            (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
        )
        return (2.0 * area2) / (a * b * c)

    @staticmethod
    def _estimate_transition_idx(speeds, ang_vels, impact_idx):
        if impact_idx <= 1:
            return 0
        peak_idx = max(range(impact_idx + 1), key=lambda i: speeds[i] if i < len(speeds) else 0.0)
        lo = max(1, int(0.05 * impact_idx))
        hi = max(lo + 1, min(peak_idx, impact_idx))
        if hi <= lo:
            return max(0, min(peak_idx, impact_idx - 1))
        return min(range(lo, hi + 1), key=lambda i: abs(ang_vels[i]) if i < len(ang_vels) else 1e9)

    def _compute_export_metrics(self):
        if self.impact_idx is None:
            self.impact_idx = find_impact_idx(self.speeds, self.tip_ball_distances)

        impact = min(self.impact_idx, len(self.times) - 1)
        smoothed_tip_px = self._smooth_tip_positions()
        speeds_out = []
        ang_vels_out = []
        accels_out = []
        ang_accels_out = []
        energies_out = []
        jerks_out = []
        tip_sm_m = []

        prev_tip = None
        prev_speed = None
        prev_ang = None
        prev_ang_vel = None
        prev_acc = None

        for i in range(impact + 1):
            dt_i = self.dt if i == 0 else max(self.times[i] - self.times[i - 1], 1e-6)
            tip_i = smoothed_tip_px[i]
            base_i = self.base_positions[i] if i < len(self.base_positions) else None
            scale_i = self.scale_m_series[i] if i < len(self.scale_m_series) and self.scale_m_series[i] else (self.scale_m or 1.0)

            v, acc, ang, w_ang, ang_acc, jerk = self._step_kinematics(
                prev_tip, tip_i, prev_speed, prev_ang, prev_ang_vel, prev_acc, base_i, scale_i, dt_i,
            )

            speeds_out.append(v)
            ang_vels_out.append(w_ang)
            accels_out.append(acc)
            ang_accels_out.append(ang_acc)
            energies_out.append(v * v)
            jerks_out.append(jerk)
            tip_sm_m.append((tip_i[0] * scale_i, tip_i[1] * scale_i) if tip_i is not None else None)

            prev_tip = tip_i
            prev_speed = v
            prev_ang = ang
            prev_ang_vel = w_ang
            prev_acc = acc

        curvature = []
        path_eff = []
        first_valid = None
        path_len = 0.0
        prev_valid = None
        for i in range(impact + 1):
            cur = tip_sm_m[i]
            if cur is not None:
                if first_valid is None:
                    first_valid = cur
                if prev_valid is not None:
                    path_len += math.hypot(cur[0] - prev_valid[0], cur[1] - prev_valid[1])
                prev_valid = cur

            disp = (
                math.hypot(cur[0] - first_valid[0], cur[1] - first_valid[1])
                if (cur is not None and first_valid is not None)
                else 0.0
            )
            path_eff.append(disp / path_len if path_len > 1e-9 else 0.0)

            if 0 < i < impact:
                curvature.append(self._curvature_3pt(tip_sm_m[i - 1], tip_sm_m[i], tip_sm_m[i + 1]))
            else:
                curvature.append(None)

        transition_idx = self._estimate_transition_idx(speeds_out, ang_vels_out, impact)
        phase = [
            ("backswing" if i <= transition_idx else "downswing")
            for i in range(impact + 1)
        ]

        return {
            "impact_idx": impact,
            "transition_idx": transition_idx,
            "smoothed_tip_px": smoothed_tip_px,
            "tip_sm_m": tip_sm_m,
            "speeds": speeds_out,
            "ang_vels": ang_vels_out,
            "accels": accels_out,
            "ang_accels": ang_accels_out,
            "energies": energies_out,
            "jerks": jerks_out,
            "curvature": curvature,
            "path_efficiency": path_eff,
            "phase": phase,
        }

    def _get_export_metrics(self):
        if self._export_cache is None:
            self._export_cache = self._compute_export_metrics()
        return self._export_cache

    # ------------------------------------------------------------------ #
    #  Process one frame
    # ------------------------------------------------------------------ #
    def process_frame(self, idx, frame_img, frame, dt=None, t=None):
        dt = self.dt if dt is None else max(float(dt), 1e-6)
        pts = frame["landmarks"][0]
        w, h = frame_img.shape[1], frame_img.shape[0]
        lm = lambda i: self._lm_px(pts, i, w, h)

        # ---- draw visuals ----
        draw_skeleton(frame_img, pts, w, h)
        draw_stick(frame_img, pts, w, h)
        ball = draw_ball(frame_img, frame, w, h)

        # ---- key landmarks (float, subpixel) ----
        base = lm(17)
        tip = lm(19)
        l_shoulder = lm(5)
        r_shoulder = lm(6)
        l_hip = lm(11)
        r_hip = lm(12)
        r_elbow = lm(8)
        r_wrist = lm(10)

        # ---- dynamic stick-length calibration ----
        if base and tip:
            slen = math.hypot(tip[0] - base[0], tip[1] - base[1])
            self.stick_lengths_px.append(slen)
            self._update_calibration(slen)
        else:
            self.stick_lengths_px.append(None)

        # ---- raw tip / filtered tip ----
        self.tip_positions_raw.append(tip)
        self.base_positions.append(base)
        tip_f = self._update_tip_filter(tip, dt)
        self._record_scale_state(tip_f)
        self._append_time(dt, t)
        self._append_kinematics(idx, base, tip_f, dt)
        self._append_biomechanics(
            base,
            tip_f,
            l_shoulder,
            r_shoulder,
            l_hip,
            r_hip,
            r_elbow,
            r_wrist,
        )
        self._append_impact(idx, tip_f, ball)
        self._export_cache = None

    # ------------------------------------------------------------------ #
    #  Draw trajectories
    # ------------------------------------------------------------------ #
    def draw_trajectory(
        self,
        frame_img,
        raw_color=(0, 0, 255),
        raw_thickness=1,
        smooth_color=(0, 255, 0),
        smooth_thickness=2,
    ):
        raw = self.tip_positions_raw
        for i in range(1, len(raw)):
            if raw[i - 1] is None or raw[i] is None:
                continue
            cv2.line(
                frame_img,
                (int(raw[i - 1][0]), int(raw[i - 1][1])),
                (int(raw[i][0]), int(raw[i][1])),
                raw_color, raw_thickness,
            )

        filt_smooth = self._smooth_tip_positions()
        for i in range(1, len(filt_smooth)):
            if filt_smooth[i - 1] is None or filt_smooth[i] is None:
                continue
            cv2.line(
                frame_img,
                (int(filt_smooth[i - 1][0]), int(filt_smooth[i - 1][1])),
                (int(filt_smooth[i][0]), int(filt_smooth[i][1])),
                smooth_color, smooth_thickness,
            )

    # ------------------------------------------------------------------ #
    #  Summary metrics
    # ------------------------------------------------------------------ #
    def summary(self):
        """Return a dict of scalar summary metrics for the swing.

        Uses a cheap approximation while streaming (impact not yet known),
        and switches to full export-metric computation once finalized.
        """
        n = len(self.times)
        if n < 2:
            return {}

        # --- cheap streaming path: impact not known yet ---
        if self.impact_idx is None and n < len(self.data):
            impact = n - 1
            transition = max(0, min(self.peak_speed_idx, impact - 1))
            t_back = self.times[transition] - self.times[0] if transition > 0 else 0.0
            t_down = self.times[impact] - self.times[transition] if impact > transition else 0.0
            tempo = t_back / t_down if t_down > 0 else 0.0

            valid = [p for p in self.tip_positions_m[:n] if p != (0.0, 0.0)]
            path_len = 0.0
            if len(valid) > 1:
                for i in range(1, len(valid)):
                    path_len += math.hypot(valid[i][0] - valid[i - 1][0], valid[i][1] - valid[i - 1][1])
            disp = math.hypot(valid[-1][0] - valid[0][0], valid[-1][1] - valid[0][1]) if len(valid) > 1 else 0.0
            path_eff = disp / path_len if path_len > 1e-9 else 0.0

            bs_speeds = self.speeds[:transition + 1] if transition >= 0 else []
            ds_speeds = self.speeds[transition:impact + 1] if impact >= transition else []

            smoothness = 0.0
            if self.jerk_nonzero_count > 0:
                mean_sq_jerk = self.jerk_sq_sum / self.jerk_nonzero_count
                smoothness = -math.log10(mean_sq_jerk + 1e-9)

            return {
                "max_speed": self.max_speed if self.speeds else 0.0,
                "max_ang_vel": self.max_ang_vel if self.ang_vels else 0.0,
                "max_accel": self.max_accel if self.accels else 0.0,
                "swing_duration": self.times[-1] - self.times[0],
                "swing_tempo": tempo,
                "smoothness_index": smoothness,
                "max_x_factor": self.max_x_factor_val,
                "transition_time": self.times[transition],
                "impact_time": self.times[impact],
                "backswing_duration": t_back,
                "downswing_duration": t_down,
                "backswing_peak_speed": max(bs_speeds) if bs_speeds else 0.0,
                "downswing_peak_speed": max(ds_speeds) if ds_speeds else 0.0,
                "path_efficiency": path_eff,
                "curvature_rms": 0.0,
                "backswing_curvature_mean": 0.0,
                "downswing_curvature_mean": 0.0,
            }

        # --- final path: use fully smoothed export metrics ---
        exp = self._get_export_metrics()
        impact = exp["impact_idx"]
        transition = exp["transition_idx"]
        speeds = exp["speeds"]
        ang_vels = exp["ang_vels"]
        accels = exp["accels"]
        jerks = exp["jerks"]
        path_eff = exp["path_efficiency"]
        curv = [c for c in exp["curvature"] if c is not None]

        t_back = self.times[transition] - self.times[0] if transition > 0 else 0.0
        t_down = self.times[impact] - self.times[transition] if impact > transition else 0.0
        tempo = t_back / t_down if t_down > 0 else 0.0

        jerk_nz = [j for j in jerks if abs(j) > 0.0]
        smoothness = 0.0
        if jerk_nz:
            mean_sq_jerk = sum(j * j for j in jerk_nz) / len(jerk_nz)
            smoothness = -math.log10(mean_sq_jerk + 1e-9)

        bs_speeds = speeds[:transition + 1] if transition >= 0 else []
        ds_speeds = speeds[transition:impact + 1] if impact >= transition else []
        bs_curv = [exp["curvature"][i] for i in range(0, transition + 1) if exp["curvature"][i] is not None]
        ds_curv = [exp["curvature"][i] for i in range(transition, impact + 1) if exp["curvature"][i] is not None]

        return {
            "max_speed": max(speeds) if speeds else 0.0,
            "max_ang_vel": max(ang_vels) if ang_vels else 0.0,
            "max_accel": max(accels) if accels else 0.0,
            "swing_duration": self.times[-1] - self.times[0],
            "swing_tempo": tempo,
            "smoothness_index": smoothness,
            "max_x_factor": self.max_x_factor_val,
            "transition_time": self.times[transition],
            "impact_time": self.times[impact],
            "backswing_duration": t_back,
            "downswing_duration": t_down,
            "backswing_peak_speed": max(bs_speeds) if bs_speeds else 0.0,
            "downswing_peak_speed": max(ds_speeds) if ds_speeds else 0.0,
            "path_efficiency": path_eff[impact] if path_eff else 0.0,
            "curvature_rms": math.sqrt(sum(c * c for c in curv) / len(curv)) if curv else 0.0,
            "backswing_curvature_mean": (sum(bs_curv) / len(bs_curv)) if bs_curv else 0.0,
            "downswing_curvature_mean": (sum(ds_curv) / len(ds_curv)) if ds_curv else 0.0,
        }

    # ------------------------------------------------------------------ #
    #  Finalize & export rows
    # ------------------------------------------------------------------ #
    def finalize(self):
        exp = self._get_export_metrics()
        self.impact_idx = exp["impact_idx"]

        t0 = self.times[0]
        t1 = self.times[self.impact_idx]
        if abs(t1 - t0) < 1e-9:
            t1 = t0 + self.dt

        smoothed_tip_px = exp["smoothed_tip_px"]
        speeds_out = exp["speeds"]
        ang_vels_out = exp["ang_vels"]
        accels_out = exp["accels"]
        ang_accels_out = exp["ang_accels"]
        energies_out = exp["energies"]
        jerks_out = exp["jerks"]
        curv_out = exp["curvature"]
        path_eff_out = exp["path_efficiency"]
        phase_out = exp["phase"]

        rows = []
        for i in range(self.impact_idx + 1):
            tn = (self.times[i] - t0) / (t1 - t0) if (t1 - t0) != 0 else 0.0

            tip_sm_px = smoothed_tip_px[i]
            scale_i = self.scale_m_series[i] if i < len(self.scale_m_series) and self.scale_m_series[i] else self.scale_m
            if tip_sm_px and scale_i:
                tip_fm = (tip_sm_px[0] * scale_i, tip_sm_px[1] * scale_i)
            else:
                tip_fm = self.tip_positions_m[i]
            tip_raw_px = self.tip_positions_raw[i]
            if tip_raw_px and scale_i:
                tip_raw_m = (tip_raw_px[0] * scale_i, tip_raw_px[1] * scale_i)
            else:
                tip_raw_m = (0.0, 0.0)

            rows.append([
                self.times[i],
                speeds_out[i],
                ang_vels_out[i],
                accels_out[i],
                ang_accels_out[i],
                energies_out[i],
                jerks_out[i],
                tn,
                tip_fm[0],
                tip_fm[1],
                tip_raw_m[0],
                tip_raw_m[1],
                scale_i if scale_i else "",
                self.hip_angles[i] if self.hip_angles[i] is not None else "",
                self.shoulder_angles[i] if self.shoulder_angles[i] is not None else "",
                self.x_factors[i] if self.x_factors[i] is not None else "",
                self.wrist_angles[i] if self.wrist_angles[i] is not None else "",
                self.arc_radii[i] if self.arc_radii[i] is not None else "",
                curv_out[i] if curv_out[i] is not None else "",
                path_eff_out[i],
                phase_out[i],
            ])

        return rows
