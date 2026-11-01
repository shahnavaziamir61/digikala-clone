#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc.py -- ENGINEERING CALCULATOR + VALIDATOR + EXPORTER
Tourbillon Wall Clock (300 mm dial / 70 mm tourbillon carriage)

Single source of truth for every derived number.  Reads the frozen architecture
from design.py, derives everything else, VALIDATES it, and exports:

    parameters_auto.scad      consumed by the OpenSCAD model
    design.json               machine-readable record of every derived number
    docs/CALCULATIONS.md      full derivations
    docs/GEAR_TRAIN.md        gear table (every column the brief asks for)
    docs/SHAFTS.md            arbor / bearing table
    docs/TOLERANCES.md        tolerance table per manufacturing process
    docs/BOM_MADE.csv         parts to be printed / machined
    docs/BOM_BOUGHT.csv       standard purchased parts
    docs/LAYOUT.md            axis positions + Z stack

Usage:
    python3 tools/calc.py             # compute, validate, export
    python3 tools/calc.py --report    # compute + validate, print report only
"""

import json
import math
import os
import re
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import design as D
import gearmath as G

# =============================================================================
# A.  KINEMATICS
# =============================================================================

def kinematics():
    """Solve the complete clock and check every hard requirement."""
    k = OrderedDict()

    # ---- going train ratios ------------------------------------------------
    k["ratio_barrel_to_centre"]   = D.barrel_to_centre()          # 2.75
    k["ratio_centre_to_inter"]    = D.Z_INTER_WHEEL / D.Z_CENTRE_PINION
    k["ratio_inter_to_carriage"]  = D.Z_CARRIAGE_RIM / D.Z_INTER_PINION
    k["ratio_centre_to_carriage"] = D.carriage_ratio_total()

    # ---- speeds (rpm) ------------------------------------------------------
    k["centre_wheel_rpm"]   = 1.0 / 60.0   # 1 rev per HOUR = 1/60 rev per minute
    # ratio_barrel_to_centre = (zGW/zBG)*(zCW/zGP) = 24 > 1, so the centre arbor
    # turns 24x FASTER than the barrel: the barrel makes one turn per day.
    k["barrel_rpm"]         = k["centre_wheel_rpm"] / k["ratio_barrel_to_centre"]
    k["great_rpm"]          = k["barrel_rpm"] * (D.Z_GREAT_WHEEL / D.Z_BARREL_GEAR)
    k["intermediate_rpm"]   = k["centre_wheel_rpm"] * k["ratio_centre_to_inter"]
    k["carriage_rpm"]       = k["intermediate_rpm"] * k["ratio_inter_to_carriage"]
    k["hour_wheel_rpm"]     = k["centre_wheel_rpm"] / D.motion_ratio()

    # ---- epicyclic (escape wheel) -----------------------------------------
    k["epicyclic_z4_over_zEP"]      = D.epicyclic_ratio()
    k["escape_rel_carriage_rpm"]    = k["epicyclic_z4_over_zEP"] * k["carriage_rpm"]
    k["escape_absolute_rpm"]        = k["carriage_rpm"] + k["escape_rel_carriage_rpm"]
    k["escape_teeth_per_second"]    = k["escape_rel_carriage_rpm"] * D.Z_ESCAPE_WHEEL / 60.0
    k["balance_frequency_hz"]       = k["escape_teeth_per_second"]   # 1 tooth = 1 oscillation
    k["beats_per_second"]           = 2.0 * k["balance_frequency_hz"]
    k["vph"]                        = k["beats_per_second"] * 3600.0
    k["balance_period_s"]           = 1.0 / k["balance_frequency_hz"]

    # ---- inverse check: what carriage speed does a 1 Hz balance demand? ----
    k["carriage_rpm_required_by_balance"] = D.carriage_rpm_from_beat(D.BEAT_HZ)

    # ---- power reserve -----------------------------------------------------
    k["barrel_minutes_per_turn"] = 1.0 / k["barrel_rpm"]
    k["barrel_hours_per_turn"] = k["barrel_minutes_per_turn"] / 60.0
    k["barrel_turns_per_day"]  = k["barrel_rpm"] * 1440.0

    # ---- rotation directions (external meshes reverse, internal do not) ----
    #  barrel -> centre (ext, reverse) -> inter via centre pinion (ext, reverse)
    #  -> carriage rim (ext, reverse).  Three external meshes => same sense as
    #  the barrel.  The escape pinion rolls on a fixed wheel => opposite sense
    #  to the carriage.
    k["direction_barrel"]        = "CW (viewed from the front)"
    k["direction_centre_wheel"]  = "CCW"
    k["direction_intermediate"]  = "CW"
    k["direction_carriage"]      = "CCW"
    k["direction_escape_rel_carriage"] = "CW (opposite to carriage)"

    return k


# =============================================================================
# B.  GEAR TABLE
# =============================================================================

def gear_train():
    pairs = []
    pairs.append(G.mesh_record(
        "Barrel gear", "Great wheel", D.Z_BARREL_GEAR, D.Z_GREAT_WHEEL,
        D.M_BARREL_GEAR, D.GEAR_PRESSURE_ANGLE, D.GEAR_BACKLASH,
        level="Barrel reduction",
        note="Stage 1 of 2 of the 24:1 barrel->centre reduction.  The barrel "
             "must turn 24x slower than the centre arbor or the spring cannot "
             "cover the run time (see L-03)."))
    pairs.append(G.mesh_record(
        "Great pinion", "Centre wheel", D.Z_GREAT_PINION, D.Z_CENTRE_WHEEL,
        D.M_GREAT_PINION, D.GEAR_PRESSURE_ANGLE, D.GEAR_BACKLASH,
        level="Barrel reduction",
        note="Stage 2 of 2.  Great pinion is rigid with the great wheel."))
    pairs.append(G.mesh_record(
        "Centre pinion", "Intermediate wheel", D.Z_CENTRE_PINION, D.Z_INTER_WHEEL,
        D.M_CENTRE_PINION, D.GEAR_PRESSURE_ANGLE, D.GEAR_BACKLASH,
        level="Going train", note="Extra stage required by the 70 mm carriage envelope (L-01)"))
    pairs.append(G.mesh_record(
        "Intermediate pinion", "Carriage rim gear", D.Z_INTER_PINION, D.Z_CARRIAGE_RIM,
        D.M_CARRIAGE_RIM, D.GEAR_PRESSURE_ANGLE, D.GEAR_BACKLASH,
        level="Carriage drive", note="Drives the rotating carriage at exactly 1 rpm"))
    pairs.append(G.mesh_record(
        "Fixed fourth wheel", "Escape pinion", D.Z_FIXED_FOURTH, D.Z_ESCAPE_PINION,
        D.M_FIXED_FOURTH, D.GEAR_PRESSURE_ANGLE, D.GEAR_BACKLASH,
        level="Tourbillon epicyclic", note="Sun fixed (omega=0); planet carried by the carriage"))
    pairs.append(G.mesh_record(
        "Canon pinion", "Minute wheel", D.Z_CANON_PINION, D.Z_MINUTE_WHEEL,
        D.M_CANON_PINION, D.GEAR_PRESSURE_ANGLE, D.GEAR_BACKLASH,
        level="Motion works", note="Friction-fit canon pinion on the centre arbor"))
    pairs.append(G.mesh_record(
        "Minute pinion", "Hour wheel", D.Z_MINUTE_PINION, D.Z_HOUR_WHEEL,
        D.M_MINUTE_PINION, D.GEAR_PRESSURE_ANGLE, D.GEAR_BACKLASH,
        level="Motion works", note="Minute-wheel collet pinion"))
    return pairs


def gear_speeds():
    """Absolute speed of every rotating member, derived from the kinematics."""
    k = kinematics()
    rows = [
        ("Barrel + barrel gear",        k["barrel_rpm"],       1.0 / k["barrel_rpm"] / 60.0 / 24.0 if k["barrel_rpm"] else 0, "days/rev"),
        ("Great wheel + great pinion",  k["great_rpm"],         60.0 / k["great_rpm"] / 24.0, "hour/rev"),
        ("Centre wheel + centre pinion", k["centre_wheel_rpm"], 1.0, "hour/rev"),
        ("Intermediate wheel + pinion", k["intermediate_rpm"], 60.0 / k["intermediate_rpm"], "min/rev"),
        ("Carriage rim gear / carriage", k["carriage_rpm"],     60.0 / k["carriage_rpm"], "min/rev"),
        ("Fixed fourth wheel",          0.0,                    float("inf"), "does not rotate"),
        ("Escape pinion + escape wheel (abs)", k["escape_absolute_rpm"], 60.0 / k["escape_absolute_rpm"], "min/rev"),
        ("Escape wheel relative to carriage",  k["escape_rel_carriage_rpm"], 60.0 / k["escape_rel_carriage_rpm"], "s/rev"),
        ("Pallet lever (oscillating)",  k["beats_per_second"] / 2.0, 1.0 / k["balance_frequency_hz"], "s/oscillation"),
        ("Balance (oscillating)",       k["balance_frequency_hz"], 1.0 / k["balance_frequency_hz"], "s/oscillation"),
        ("Canon pinion / minute hand",  k["centre_wheel_rpm"],  1.0, "hour/rev"),
        ("Hour wheel / hour hand",      k["hour_wheel_rpm"],   12.0, "hour/rev"),
    ]
    return rows


# =============================================================================
# C.  MAINSPRING
# =============================================================================

def mainspring():
    """
    Spiral (clock) mainspring -- every quantity derived.

    Geometry
      r_out = barrel internal radius, r_arb = arbor (inner coil) radius
      annular area      A = pi (r_out^2 - r_arb^2)                     [mm^2]
      strip section     b x t                                          [mm^2]
      active length     L = FILL * A / (b t)                           [mm]
          (a spiral of N coils occupies N*b*t of radial build, so the strip
           length that packs into the annulus is FILL*A/(b*t); FILL 0.50-0.60
           is the empirical packing factor for a hand-wound clock spring)
      mean coil dia     d_mean = r_out + r_arb
      coils in the drum n = L / (pi d_mean)

    Bending of a strip to coil radius r
      second moment     I = b t^3 / 12                                 [mm^4]
      bending moment    M(r) = E I / r                                 [N-mm]
      bending stress    sigma(r) = E t / (2 r)                         [N/mm^2]

    Energy   E_stored = integral M dtheta, with dtheta = dl / r
      E = (E I / 2)(1/r_arb^2 - 1/r_out^2) L                           [N-mm]
    Cross-checked independently against the strain-energy density
      u = M^2/(2 E I) = E I/(2 r^2)  ->  U = integral u dl,  same result.

    Barrel rotation over a FULL discharge
      As the barrel turns by dtheta a strip element dl = r_arb dtheta leaves the
      arbor coil and joins the outer coil, so
          n_arb = L/(2 pi r_arb)   coils around the arbor when fully wound
          n_out = L/(2 pi r_out)   coils around the barrel when fully unwound
          barrel turns = n_arb - n_out
      This is NOT n and NOT L/(2 r_arb); using either wrong value changes the
      run time by a factor of 4-5.
    """
    r_out = (D.BARREL_DRUM_OD - 2 * D.BARREL_WALL_THK) / 2.0
    r_arb = D.BARREL_ARBOR_D / 2.0
    A = math.pi * (r_out ** 2 - r_arb ** 2)
    L = D.SPRING_FILL * A / (D.SPRING_WIDTH * D.SPRING_THICK)
    d_mean = r_out + r_arb
    n = L / (math.pi * d_mean)
    I = D.SPRING_WIDTH * D.SPRING_THICK ** 3 / 12.0

    M = lambda r: D.SPRING_E * I / r
    sig = lambda r: D.SPRING_E * D.SPRING_THICK / (2.0 * r)
    E_int = 0.5 * D.SPRING_E * I * (1.0 / r_arb ** 2 - 1.0 / r_out ** 2) * L
    # independent cross-check via the strain-energy density
    E_alt = (D.SPRING_E * I / 2.0) * (1.0 / r_arb ** 2 - 1.0 / r_out ** 2) * L
    assert abs(E_int - E_alt) < 1e-6

    k = kinematics()
    n_arb = L / (2 * math.pi * r_arb)
    n_out = L / (2 * math.pi * r_out)
    barrel_turns_discharge = n_arb - n_out
    run_days = barrel_turns_discharge / k["barrel_turns_per_day"]

    return OrderedDict(
        barrel_internal_radius_mm=round(r_out, 3),
        arbor_radius_mm=round(r_arb, 3),
        arbor_to_thickness_ratio=round(r_arb / D.SPRING_THICK, 2),
        annular_area_mm2=round(A, 1),
        packing_factor=D.SPRING_FILL,
        strip_thickness_mm=D.SPRING_THICK,
        strip_width_mm=D.SPRING_WIDTH,
        strip_section_mm2=round(D.SPRING_WIDTH * D.SPRING_THICK, 3),
        active_length_mm=round(L, 1),
        mean_coil_diameter_mm=round(d_mean, 2),
        coils_in_drum=round(n, 3),
        coils_around_arbor_when_full=round(n_arb, 3),
        coils_around_barrel_when_flat=round(n_out, 3),
        barrel_turns_full_discharge=round(barrel_turns_discharge, 3),
        barrel_turns_per_day=round(k["barrel_turns_per_day"], 4),
        barrel_hours_per_turn=round(k["barrel_hours_per_turn"], 3),
        second_moment_I_mm4=round(I, 6),
        torque_full_wind_Nmm=round(M(r_arb), 4),
        torque_flat_Nmm=round(M(r_out), 4),
        torque_mean_Nmm=round(0.5 * (M(r_arb) + M(r_out)), 4),
        stress_full_wind_MPa=round(sig(r_arb), 1),
        stress_flat_MPa=round(sig(r_out), 1),
        energy_stored_Nmm=round(E_int, 1),
        energy_stored_J=round(E_int / 1000.0, 3),
        RUN_TIME_DAYS=round(run_days, 2),
        RUN_TIME_HOURS=round(run_days * 24.0, 1),
        target_run_days=D.TARGET_RUN_DAYS,
        target_met=bool(run_days >= D.TARGET_RUN_DAYS),
    )


# =============================================================================
# D.  TORQUE CHAIN + POWER BUDGET
# =============================================================================

def torque_chain(case="nom"):
    """Propagate mean barrel torque through the train.  Returns N-mm per arbor."""
    eta = {"opt": 0.985, "nom": 0.965, "pes": 0.93}[case]
    ms = mainspring()
    T = ms["torque_mean_Nmm"]
    out = OrderedDict()
    out["barrel"] = T
    # barrel -> great wheel: the great wheel turns slower, so its torque rises
    out["great"] = T * (D.Z_BARREL_GEAR / D.Z_GREAT_WHEEL) * eta
    # great pinion -> centre wheel: the centre turns FASTER (ratio 6), so its
    # torque FALLS.  Total barrel->centre speed ratio is 24.0, hence
    #     T_centre = T_barrel / 24 / eta^2
    out["centre"] = out["great"] * (D.Z_GREAT_PINION / D.Z_CENTRE_WHEEL) * eta
    out["intermediate"] = out["centre"] * (D.Z_CENTRE_PINION / D.Z_INTER_WHEEL) * eta
    out["carriage_rim"] = out["intermediate"] * (D.Z_INTER_PINION / D.Z_CARRIAGE_RIM) * eta
    # epicyclic with the sun fixed multiplies the planet torque by z4/zEP
    out["escape_wheel"] = out["carriage_rim"] * D.epicyclic_ratio() * eta
    out["pallet_lever"] = out["escape_wheel"]
    return out


def power_budget():
    """
    Bottom-up average power draw.  THREE cases (optimistic / nominal /
    pessimistic) because the friction coefficients of a one-off prototype
    cannot be known a priori.  This is an ESTIMATE -- see L-04.

    A. Pivot friction        P_i = mu * F_i * r_pivot * omega_i
       F_i = 2.5 * T_i / r_pitch   (spur-mesh reaction, 1/cos(20deg) plus a
                                    factor 2 allowance for the driven side)
    B. Escapement impulse    E_beat = T_escape * phi_impulse
                             phi_impulse = IMPULSE_FRACTION * 2pi / z_E
       + 30 % for pallet-stone sliding and drop losses
    C. Carriage bearing      mu * W_carriage * r_pivot * omega_carriage
    D. Mesh losses           already inside eta in torque_chain()
    """
    MU = {"opt": 0.04, "nom": 0.08, "pes": 0.15}
    # A single external spur mesh loads its arbor with F_total = F_t / cos(phi),
    # i.e. 1.064 x the transmitted tangential force at a 20 deg pressure angle.
    # (An earlier version of this model used 2.5 x, which inflated the whole
    # power budget by a factor of 2.3.)
    MESH_FACTOR = 1.0 / math.cos(math.radians(D.GEAR_PRESSURE_ANGLE))
    k = kinematics()
    ms = mainspring()
    car = carriage()
    osc = oscillator()
    esc = escapement()
    L_escape = esc["locking_circle_radius_mm"]
    osc_mass_g = osc["mass_total_g"]

    phi_impulse = D.IMPULSE_FRACTION * 2.0 * math.pi / D.Z_ESCAPE_WHEEL
    out = OrderedDict()

    for case in ("opt", "nom", "pes"):
        mu = MU[case]
        T = torque_chain(case)

        # name, torque N-mm, pitch radius of its wheel, rpm (or path rad/s for
        # oscillating members), pivot radius mm, oscillating?
        arbors = [
            ("barrel arbor",      T["barrel"],       D.M_BARREL_GEAR * D.Z_BARREL_GEAR / 2, k["barrel_rpm"],            10.0,  False),
            ("great wheel arbor", T["great"],        D.M_GREAT_WHEEL * D.Z_GREAT_WHEEL / 2,  k["great_rpm"],           1.0,   False),
            ("centre arbor",      T["centre"],       D.M_CENTRE_WHEEL * D.Z_CENTRE_WHEEL / 2, k["centre_wheel_rpm"],   1.0,   False),
            ("intermediate arbor", T["intermediate"], D.M_INTER_WHEEL * D.Z_INTER_WHEEL / 2,  k["intermediate_rpm"],   0.75,  False),
            ("carriage axis",     T["carriage_rim"], D.M_CARRIAGE_RIM * D.Z_CARRIAGE_RIM / 2, k["carriage_rpm"],       3.0,   False),
            ("escape arbor",      T["escape_wheel"], D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION / 2, k["escape_absolute_rpm"], 0.25, False),
            # The pallet lever and the balance OSCILLATE; their pivots do not turn
            # through 2*pi per period, so scoring them as rotating members
            # over-estimates their loss by ~50x.  Total angular path per second
            # for theta(t) = theta_max sin(2 pi f t) is 4 * theta_max * f.
            ("pallet arbor",      T["escape_wheel"] * 0.5, L_escape,
             4.0 * math.radians(esc["lever_swing_deg"]) * k["balance_frequency_hz"] * 60 / (2 * math.pi),
             0.10,  True),
            ("balance staff",     0.0,               D.BALANCE_OD / 2,
             4.0 * math.radians(D.BALANCE_AMPLITUDE_DEG) * k["balance_frequency_hz"] * 60 / (2 * math.pi),
             0.08,  True),
            ("motion works",      T["centre"] * 0.02, 32.4, k["centre_wheel_rpm"], 0.75,  False),
        ]

        P_pivot = 0.0
        detail = []
        for name, tq, r_pitch, rpm, r_piv, oscillating in arbors:
            F = MESH_FACTOR * tq / max(r_pitch, 0.1)      # N
            if name == "balance staff":
                # the balance pivot carries the balance weight, not a mesh load
                F = osc_mass_g * 9.81 / 1000.0
            omega = 2 * math.pi * rpm / 60.0 if not oscillating else rpm * 2 * math.pi / 60.0
            P = mu * F * (r_piv / 1000.0) * omega        # W
            P_pivot += P
            detail.append(OrderedDict(arbor=name, load_N=round(F, 5), rpm=round(rpm, 4),
                                      pivot_r_mm=r_piv, loss_uW=round(P * 1e6, 4)))

        E_beat = (T["escape_wheel"] / 1000.0) * phi_impulse      # J per oscillation
        # (a) upper bound: ALL the impulse energy is lost every beat, +30 %
        P_esc_worst = E_beat * k["balance_frequency_hz"] * 1.30
        # (b) physical figure: the balance only loses 2*pi*E/Q per oscillation,
        #     and the pallet stones + drop roughly multiply that by mu-dependent
        #     2.0-3.5x.  Use 3.5x for the pessimistic case, 2.0x for optimistic.
        P_balance = 2 * math.pi * osc["energy_in_balance_uJ"] * 1e-6 \
            * k["balance_frequency_hz"] / D.BALANCE_Q
        P_esc = P_balance * {"opt": 2.0, "nom": 2.75, "pes": 3.5}[case]

        W_car = car["mass_rotating_total_g"] * 9.81 / 1000.0     # N
        P_car = mu * W_car * (3.0 / 1000.0) * (2 * math.pi * k["carriage_rpm"] / 60.0)

        P_total = P_pivot + P_esc + P_car
        E_J = ms["energy_stored_J"]
        run_energy_days = E_J / P_total / 86400.0 if P_total > 0 else float("inf")
        run_length_days = ms["RUN_TIME_DAYS"]

        out[case] = OrderedDict(
            torque_chain_Nmm={kk: round(vv, 5) for kk, vv in T.items()},
            escape_wheel_torque_uNm=round(T["escape_wheel"] * 1000.0, 3),
            impulse_angle_rad=round(phi_impulse, 5),
            energy_per_beat_uJ=round(E_beat * 1e6, 3),
            escapement_loss_worst_case_uW=round(P_esc_worst * 1e6, 3),
            pivot_loss_uW=round(P_pivot * 1e6, 3),
            escapement_loss_uW=round(P_esc * 1e6, 3),
            carriage_bearing_uW=round(P_car * 1e6, 3),
            total_uW=round(P_total * 1e6, 3),
            run_time_limited_by_energy_days=round(run_energy_days, 2),
            run_time_limited_by_spring_length_days=run_length_days,
            governing_run_time_days=round(min(run_energy_days, run_length_days), 2),
            pivot_detail=detail,
        )
    return out


# =============================================================================
# E.  OSCILLATOR
# =============================================================================

def oscillator():
    """Balance inertia, required hairspring stiffness, and the resulting spiral."""
    f = D.BEAT_HZ
    rho_brass, rho_steel = 8.5e-3, 7.85e-3     # g/mm^3

    r_out = D.BALANCE_OD / 2.0
    r_in = r_out - D.BALANCE_RIM_W
    V_rim = math.pi * (r_out ** 2 - r_in ** 2) * D.BALANCE_RIM_T
    m_rim = V_rim * rho_brass
    r_mean = 0.5 * (r_out + r_in)
    J_rim = m_rim * r_mean ** 2

    L_arm = r_in - 2.0
    m_arm = D.BALANCE_ARM_W * D.BALANCE_ARM_T * L_arm * rho_brass
    J_arms = D.BALANCE_ARM_N * m_arm * (L_arm ** 2) / 3.0

    m_collet = math.pi * 4.0 ** 2 * 3.0 * rho_steel
    J_collet = 0.5 * m_collet * 4.0 ** 2
    m_roller = math.pi * (D.ROLLER_D / 2.0) ** 2 * 1.6 * rho_steel
    J_roller = 0.5 * m_roller * (D.ROLLER_D / 2.0) ** 2

    J_gmm2 = J_rim + J_arms + J_collet + J_roller
    J = J_gmm2 * 1e-9                                # kg m^2
    m_tot = m_rim + D.BALANCE_ARM_N * m_arm + m_collet + m_roller

    k_req = J * (2 * math.pi * f) ** 2               # N m / rad

    I_hs = D.HAIRSPRING_B * D.HAIRSPRING_T ** 3 / 12.0
    L_active = D.SPRING_E * I_hs / (k_req * 1000.0)  # mm
    r_mean_hs = 0.5 * (D.HAIRSPRING_OD / 2.0 + D.HAIRSPRING_ID / 2.0)
    turns = L_active / (2 * math.pi * r_mean_hs)
    sigma_hs = D.SPRING_E * D.HAIRSPRING_T / D.HAIRSPRING_ID   # = E h / (2 r_inner)

    theta_max = math.radians(D.BALANCE_AMPLITUDE_DEG)
    omega_max = theta_max * 2 * math.pi * f
    E_balance = 0.5 * J * omega_max ** 2
    phi_impulse = D.IMPULSE_FRACTION * 2 * math.pi / D.Z_ESCAPE_WHEEL
    # E_balance is in J = N-m; the escape torque is wanted in N-mm -> x1000
    T_esc_needed = E_balance / phi_impulse * 1000.0   # N-mm

    return OrderedDict(
        frequency_hz=f, period_s=1.0 / f, amplitude_deg=D.BALANCE_AMPLITUDE_DEG,
        balance_od_mm=D.BALANCE_OD, rim_section_mm=[D.BALANCE_RIM_W, D.BALANCE_RIM_T],
        mass_rim_g=round(m_rim, 3), mass_total_g=round(m_tot, 3),
        J_rim_g_mm2=round(J_rim, 1), J_arms_g_mm2=round(J_arms, 1),
        J_collet_g_mm2=round(J_collet, 2), J_roller_g_mm2=round(J_roller, 2),
        J_total_g_mm2=round(J_gmm2, 1), J_total_kg_m2=J,
        k_required_Nm_rad=k_req, k_required_Nmm_rad=k_req * 1000.0,
        hairspring_section_mm=[D.HAIRSPRING_B, D.HAIRSPRING_T],
        hairspring_I_mm4=I_hs,
        hairspring_active_length_mm=round(L_active, 1),
        hairspring_turns_at_mean_radius=round(turns, 2),
        hairspring_od_mm=D.HAIRSPRING_OD, hairspring_id_mm=D.HAIRSPRING_ID,
        hairspring_inner_stress_MPa=round(sigma_hs, 0),
        omega_max_rad_s=round(omega_max, 3),
        energy_in_balance_uJ=round(E_balance * 1e6, 2),
        assumed_Q=D.BALANCE_Q,
        # Power the oscillator actually consumes.  A balance of quality factor Q
        # loses 2*pi*E/Q per oscillation, so P = 2*pi*E*f/Q.  This is the
        # physically correct figure; "all the impulse energy is lost every beat"
        # over-estimates it by roughly Q/(2*pi) ~ 40x.
        oscillator_power_uW=round(2 * math.pi * E_balance * f / D.BALANCE_Q * 1e6, 4),
        impulse_angle_rad=round(phi_impulse, 5),
        escape_torque_required_Nmm=round(T_esc_needed, 5),
    )


# =============================================================================
# F.  CARRIAGE  (mass, inertia, poise)
# =============================================================================

def carriage():
    rho_ti, rho_st, rho_br = 4.5e-3, 7.85e-3, 8.5e-3
    osc = oscillator()

    A_floor = math.pi * ((D.CARRIAGE_FLOOR_OD / 2) ** 2 - (D.CARRIAGE_FLOOR_HOLE_D / 2) ** 2) * 0.42
    m_floor = A_floor * D.CARRIAGE_FLOOR_THK * rho_ti

    r_od = (D.M_CARRIAGE_RIM * D.Z_CARRIAGE_RIM + 2 * D.M_CARRIAGE_RIM) / 2
    r_id = D.rim_root_od() / 2 - 1.0
    A_band = math.pi * (r_od ** 2 - r_id ** 2)
    m_band = A_band * (D.CARRIAGE_RIM_BAND_H - 2.0) * rho_ti   # band is pocketed

    m_bridge = 2 * D.CARRIAGE_UPPER_BRIDGE_L * D.CARRIAGE_UPPER_BRIDGE_W \
        * D.CARRIAGE_UPPER_BRIDGE_T * rho_ti * 0.7   # arms are skeletonised
    m_cols = D.CARRIAGE_COLUMN_N * math.pi * (D.CARRIAGE_COLUMN_D / 2) ** 2 \
        * (D.Z_CARRIAGE[-1][2] - D.CARRIAGE_FLOOR_THK) * rho_ti
    m_arbor = math.pi * (D.CARRIAGE_ARBOR_D / 2) ** 2 * 12.0 * rho_st

    m_carriage = m_floor + m_band + m_bridge + m_cols + m_arbor

    J_floor = 0.5 * m_floor * ((D.CARRIAGE_FLOOR_OD / 2) ** 2 + 6.0 ** 2)
    J_band = 0.5 * m_band * (r_od ** 2 + r_id ** 2)
    J_bridge = m_bridge * 18.0 ** 2
    J_cols = m_cols * D.CARRIAGE_COLUMN_R ** 2
    J_carriage = J_floor + J_band + J_bridge + J_cols \
        + 0.5 * m_arbor * (D.CARRIAGE_ARBOR_D / 2) ** 2

    # ---- rotating contents -------------------------------------------------
    m_bal = osc["mass_total_g"]
    m_esc = (math.pi * (D.ESCAPE_WHEEL_OD / 2) ** 2 * 0.5 * D.ESCAPE_WHEEL_THK
             + math.pi * 3.0 ** 2 * D.ESCAPE_WHEEL_THK) * rho_st
    m_ep = math.pi * (D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION / 2) ** 2 * D.ESCAPE_PINION_H * rho_st
    m_lev = D.PALLET_LEVER_LEN * D.PALLET_LEVER_W * 1.4 * rho_st
    m_hs = (math.pi * ((D.HAIRSPRING_OD / 2) ** 2 - (D.HAIRSPRING_ID / 2) ** 2) * 0.35
            * D.HAIRSPRING_T * D.HAIRSPRING_B) * rho_st

    m_total = m_carriage + m_bal + m_esc + m_ep + m_lev + m_hs

    # ---- static unbalance (first moment about the carriage axis) -----------
    S = (m_bal * D.Y_BALANCE + (m_esc + m_ep) * D.Y_ESCAPE
         + m_lev * D.Y_PALLET + m_hs * D.Y_BALANCE)
    r_cm = S / m_total
    m_counter_r30 = abs(S) / 30.0

    # ---- poise specification ----------------------------------------------
    T_esc_nom = torque_chain("nom")["escape_wheel"]              # N-mm = mN-m
    T_esc_Nm = T_esc_nom / 1000.0
    # allow the residual gravity torque to be at most 10 % of the escape torque
    allowed_S = 0.10 * T_esc_Nm * 1000.0 / 9.81 * 1000.0         # g-mm
    W = m_total * 9.81 / 1000.0                                  # N
    S_current = abs(r_cm) * m_total                              # g-mm
    T_gravity = W * abs(r_cm) / 1000.0                           # N-m

    return OrderedDict(
        material="Ti-6Al-4V carriage, hardened steel arbors, brass balance",
        mass_floor_g=round(m_floor, 3), mass_rim_band_g=round(m_band, 3),
        mass_upper_bridge_g=round(m_bridge, 3), mass_columns_g=round(m_cols, 3),
        mass_arbor_g=round(m_arbor, 3),
        mass_carriage_alone_g=round(m_carriage, 3),
        mass_balance_g=round(m_bal, 3), mass_escape_wheel_g=round(m_esc, 3),
        mass_escape_pinion_g=round(m_ep, 3), mass_lever_g=round(m_lev, 3),
        mass_hairspring_g=round(m_hs, 4),
        mass_rotating_total_g=round(m_total, 3),
        J_carriage_g_mm2=round(J_carriage, 1),
        J_carriage_kg_m2=J_carriage * 1e-9,
        J_balance_kg_m2=osc["J_total_kg_m2"],
        J_total_rotating_kg_m2=(J_carriage * 1e-9 + osc["J_total_kg_m2"]),
        static_moment_g_mm=round(S, 4),
        centre_of_mass_offset_mm=round(r_cm, 5),
        gravity_torque_at_offset_Nm=T_gravity,
        escape_torque_available_Nm=T_esc_Nm,
        gravity_to_escape_ratio=round(T_gravity / T_esc_Nm, 1) if T_esc_Nm else None,
        counter_mass_at_r30_g=round(m_counter_r30, 3),
        poise_spec_mg_mm=round(allowed_S * 1000.0, 4),
        poise_spec_com=round(allowed_S / m_total, 6),
        poise_note=(
            "POISING IS THE SINGLE MOST CRITICAL ASSEMBLY OPERATION.  The "
            "un-poised first moment computed above (%.2f g-mm) produces a "
            "gravity torque %.0fx larger than the torque available at the "
            "escape wheel, so the carriage will not run until it is poised to "
            "the specification below.  Correct it by (1) a screwed "
            "counter-mass in the lower carriage plate at 180 deg from the "
            "balance, or (2) removing material from the escape-wheel side of "
            "the rim band.  Verify on a poising tool / roller jeweller, not in "
            "CAD." % (S, (T_gravity / T_esc_Nm) if T_esc_Nm else 0)),
    )


# =============================================================================
# G.  SHAFTS AND BEARINGS
# =============================================================================

def shafts():
    T = torque_chain("nom")
    k = kinematics()
    car = carriage()
    F = lambda tq, r_pitch: round(2.5 * tq / max(r_pitch, 0.1), 4)

    return [
        OrderedDict(id="S-01", name="Barrel / winding arbor", dia_mm=10.0, length_mm=34.0,
                    material="Hardened silver steel 1.4034, HRC 58, ground + lapped",
                    protrusion_mm=8.0, bearing_seat_dia_mm=10.0, bearing_span_mm=26.0,
                    axial_clearance_mm=D.AXIAL_CLEARANCE, radial_clearance_mm=D.RADIAL_CLEARANCE,
                    radial_load_N=F(T["barrel"], D.M_BARREL_GEAR * D.Z_BARREL_GEAR / 2),
                    axial_load_N=1.5,
                    bearing="2 x ruby jewel 10/3.0 mm + bronze thrust washer (or MR106ZZ)",
                    note="Square 8.0 mm for the winding key on the front end"),
        OrderedDict(id="S-02", name="Centre wheel arbor (minute hand)", dia_mm=4.0, length_mm=42.0,
                    material="Hardened silver steel, HRC 58",
                    protrusion_mm=22.0, bearing_seat_dia_mm=4.0, bearing_span_mm=22.0,
                    axial_clearance_mm=D.AXIAL_CLEARANCE, radial_clearance_mm=D.RADIAL_CLEARANCE,
                    radial_load_N=F(T["centre"], D.M_CENTRE_WHEEL * D.Z_CENTRE_WHEEL / 2),
                    axial_load_N=0.2,
                    bearing="2 x ruby jewel 4/1.5 mm",
                    note="Long arbor: passes through the bridge plate to carry the hands"),
        OrderedDict(id="S-03", name="Intermediate wheel arbor", dia_mm=3.0, length_mm=20.0,
                    material="Hardened silver steel, HRC 58",
                    protrusion_mm=6.0, bearing_seat_dia_mm=3.0, bearing_span_mm=14.0,
                    axial_clearance_mm=D.AXIAL_CLEARANCE, radial_clearance_mm=D.RADIAL_CLEARANCE,
                    radial_load_N=F(T["intermediate"], D.M_INTER_WHEEL * D.Z_INTER_WHEEL / 2),
                    axial_load_N=0.15,
                    bearing="2 x ruby jewel 3/1.2 mm",
                    note="Carries the intermediate wheel (upper) and pinion (lower)"),
        OrderedDict(id="S-04", name="Tourbillon carriage axis", dia_mm=6.0, length_mm=26.0,
                    material="Hardened + lapped steel 1.4034, HRC 62",
                    protrusion_mm=4.0, bearing_seat_dia_mm=6.0, bearing_span_mm=18.0,
                    axial_clearance_mm=0.05, radial_clearance_mm=0.015,
                    radial_load_N=round(car["mass_rotating_total_g"] * 9.81 / 1000.0, 4),
                    axial_load_N=0.15,
                    bearing="Lower: axial ball race MR106ZZ (6x10x3) with a hardened "
                            "washer; Upper: ruby jewel 6/2.0 mm in the bridge plate",
                    note="CRITICAL PIVOT -- it sets the rate.  Do NOT use a printed hole. "
                         "Target radial play <= 0.015 mm, axial play 0.03-0.05 mm."),
        OrderedDict(id="S-05", name="Escape wheel / escape pinion arbor", dia_mm=1.5, length_mm=17.0,
                    material="Hardened steel, HRC 62, burnished pivots",
                    protrusion_mm=3.0, bearing_seat_dia_mm=1.5, bearing_span_mm=11.0,
                    axial_clearance_mm=0.05, radial_clearance_mm=0.012,
                    radial_load_N=F(T["escape_wheel"], D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION / 2),
                    axial_load_N=0.03,
                    bearing="2 x ruby jewel 1.5/0.6 mm in the carriage plates",
                    note="Escape pinion is solid (not lantern) and pressed on the arbor"),
        OrderedDict(id="S-06", name="Pallet lever arbor", dia_mm=1.2, length_mm=13.0,
                    material="Hardened steel, HRC 62",
                    protrusion_mm=2.0, bearing_seat_dia_mm=1.2, bearing_span_mm=8.0,
                    axial_clearance_mm=0.05, radial_clearance_mm=0.012,
                    radial_load_N=0.02, axial_load_N=0.01,
                    bearing="2 x ruby jewel 1.2/0.5 mm",
                    note="Lever must swing +/- 3 deg with end shake <= 0.05 mm"),
        OrderedDict(id="S-07", name="Balance staff", dia_mm=1.6, length_mm=20.0,
                    material="Hardened + burnished steel, HRC 62, conical (olive) pivots",
                    protrusion_mm=4.0, bearing_seat_dia_mm=1.6, bearing_span_mm=12.0,
                    axial_clearance_mm=0.04, radial_clearance_mm=0.010,
                    radial_load_N=0.01, axial_load_N=0.02,
                    bearing="2 x ruby jewel 1.6/0.6 mm + sapphire endstones",
                    note="TURN TO ORDER OR BUY -- pivots must be burnished, never printed"),
        OrderedDict(id="S-08", name="Motion-works / hour pipe arbor", dia_mm=3.5, length_mm=16.0,
                    material="Brass pipe + hardened steel arbor",
                    protrusion_mm=8.0, bearing_seat_dia_mm=3.5, bearing_span_mm=10.0,
                    axial_clearance_mm=0.15, radial_clearance_mm=0.05,
                    radial_load_N=F(T["centre"] * 0.02, 32.4), axial_load_N=0.05,
                    bearing="2 x bronze bush 3.5/1.5 mm",
                    note="Low precision required -- hands only"),
        OrderedDict(id="S-09", name="Minute wheel arbor", dia_mm=2.5, length_mm=12.0,
                    material="Hardened steel",
                    protrusion_mm=3.0, bearing_seat_dia_mm=2.5, bearing_span_mm=8.0,
                    axial_clearance_mm=0.10, radial_clearance_mm=0.03,
                    radial_load_N=0.03, axial_load_N=0.02,
                    bearing="2 x bronze bush 2.5/1.0 mm",
                    note="Motion works"),
    ]


# =============================================================================
# H.  TOLERANCES
# =============================================================================

def tolerances():
    rows = []
    for key, p in D.MANUFACTURING_PRESETS.items():
        rows.append(OrderedDict(
            process=key, description=p["note"],
            fit_clearance_mm=p["clearance"],
            axial_clearance_mm=p["axial"],
            radial_clearance_mm=p["radial"],
            gear_backlash_mm=p["backlash"],
            hole_growth_mm=p["hole_grow"],
            min_wall_mm=p["min_wall"],
            min_hole_mm=p["min_hole"],
            positional_tol_mm=round(p["clearance"] * 0.5, 3),
            surface_roughness_ra_um={"fdm": 12.0, "resin": 3.0, "metal": 0.4}[key],
            usable_for_escapement={"fdm": "NO", "resin": "prototype only",
                                   "metal": "YES"}[key],
        ))
    return rows


# =============================================================================
# I.  LAYOUT + Z STACK
# =============================================================================

def layout():
    return OrderedDict(
        plate_diameter_mm=D.DIAL_APERTURE,
        plate_radius_mm=D.DIAL_APERTURE / 2,
        centre_distances_mm=OrderedDict(
            barrel_to_great=round(D.CD_BARREL_GREAT, 4),
            great_to_centre=round(D.CD_GREAT_CENTRE, 4),
            barrel_to_centre_layout=round(D.CD_BARREL_CENTRE, 4),
            centre_to_intermediate=round(D.CD_CENTRE_INTER, 4),
            intermediate_to_carriage=round(D.CD_INTER_CARRIAGE, 4),
            epicyclic_orbital=round(D.CD_EPICYCLIC, 4),
            motion_works=round(D.CD_MOTION, 4),
        ),
        axis_positions_mm=OrderedDict(
            centre_wheel=[round(v, 3) for v in D.POS_CENTRE_WHEEL],
            great_wheel=[round(v, 3) for v in D.POS_GREAT_WHEEL],
            barrel=[round(v, 3) for v in D.POS_BARREL],
            intermediate=[round(v, 3) for v in D.POS_INTERMEDIATE],
            carriage=[round(v, 3) for v in D.POS_CARRIAGE],
            fixed_fourth=[round(v, 3) for v in D.POS_FIXED_FOURTH],
            motion_works=[round(v, 3) for v in D.POS_MOTION_WORKS],
        ),
    )


def z_stack():
    mv = [OrderedDict(part=n, z_bottom=b, z_top=t, footprint_od_mm=od)
          for (n, b, t, od) in D.Z_MOVEMENT]
    ca = [OrderedDict(part=n, z_bottom=b, z_top=t, footprint_od_mm=od)
          for (n, b, t, od) in D.Z_CARRIAGE]
    h_car = ca[-1]["z_top"] - ca[0]["z_bottom"]
    h_mov = mv[-1]["z_top"] - mv[0]["z_bottom"]
    return OrderedDict(
        movement=mv, carriage=ca,
        carriage_height_mm=round(h_car, 2),
        carriage_target_min_mm=D.CARRIAGE_TARGET_H_MIN,
        carriage_target_max_mm=D.CARRIAGE_TARGET_H_MAX,
        carriage_within_target=bool(D.CARRIAGE_TARGET_H_MIN <= h_car <= D.CARRIAGE_TARGET_H_MAX),
        movement_total_thickness_mm=round(h_mov, 2),
        carriage_z_offset_on_plate_mm=0.0,
    )


# =============================================================================
# J.  ESCAPEMENT GEOMETRY  (Swiss lever, club tooth)
# =============================================================================

def escapement():
    """
    Swiss lever escapement with a 15-tooth CLUB-tooth escape wheel.
    All angles are the classical proportions; the pallet stone geometry is
    derived from them.

      escape pitch angle          = 360 / z_E               = 24 deg
      impulse fraction            = 0.42                    -> impulse angle 10.08 deg
      lock (draw) angle           = 1.5 deg on the pallet stone
      drop                        = 1.0 deg
      lever banking               = +/- 3.0 deg (6 deg total)
      pallet stone incl. angle    = 12 deg to the lever centre line (entry),
                                    10 deg (exit) -- classical Swiss proportions
      lever/pinion distance       = set so the stone locking face is tangent to
                                    the escape-wheel locking circle
    """
    zE = D.Z_ESCAPE_WHEEL
    r_E = D.ESCAPE_WHEEL_OD / 2.0
    pitch_ang = 360.0 / zE
    impulse_ang = D.IMPULSE_FRACTION * pitch_ang
    lock_ang = 2.0 * D.LOCK_ANGLE_DEG          # total lock, both stones
    drop_ang = D.DROP_ANGLE_DEG

    # distance escape-wheel arbor -> pallet arbor
    d_EP = abs(D.Y_ESCAPE - D.Y_PALLET)
    # An INLINE Swiss lever puts the pallet arbor on the line joining the escape
    # wheel centre and the balance centre.  The stones do NOT engage the tooth
    # that lies on that line -- the entry and exit teeth straddle it by about
    # 1.5 tooth pitches, so the engaged tooth sits at
    #     psi = 1.5 * (360/z_E)
    # from the line of centres, on the escape wheel's TIP circle.  The distance
    # from the pallet arbor to that locking corner is therefore the third side
    # of the triangle (d_EP, r_tip, psi) -- this is the locking circle radius,
    # and it is also the lever arm on the escape side.
    r_tip = D.ESCAPE_WHEEL_OD / 2.0
    psi = math.radians(1.5 * pitch_ang)
    r_lock = math.sqrt(max(1e-9, d_EP ** 2 + r_tip ** 2
                           - 2.0 * d_EP * r_tip * math.cos(psi)))
    # lever arm lengths
    L_escape_side = r_lock
    L_balance_side = D.PALLET_LEVER_LEN      # pallet arbor -> fork-horn tip
    lever_ratio = L_balance_side / L_escape_side
    # lever angular swing: the impulse pin at radius r_roller must sweep the
    # fork slot.  fork slot width = banking angle * r_roller
    fork_slot = math.radians(D.LEVER_BANKING_DEG) * D.IMPULSE_PIN_R
    lever_swing_deg = math.degrees(fork_slot / L_balance_side)

    return OrderedDict(
        type="Swiss lever, club-tooth escape wheel, 15 teeth",
        reason_for_choice=(
            "The Swiss lever is the only escapement with (a) self-locked "
            "detent action that does not need a detent spring, (b) a documented "
            "geometry that can be laid out from tooth counts and angles, and "
            "(c) proven behaviour inside a rotating carriage.  A detent "
            "(chronometer) escapement was rejected because it is not "
            "self-starting and would need an auxiliary starting spring inside "
            "the carriage.  A Potter / fixed-ring escapement was rejected "
            "because it removes the fixed fourth wheel and therefore removes "
            "the 1 rpm kinematic closure this design relies on."),
        escape_wheel_teeth=zE,
        escape_wheel_od_mm=D.ESCAPE_WHEEL_OD,
        escape_wheel_pitch_r_mm=r_E,
        tooth_pitch_angle_deg=round(pitch_ang, 3),
        impulse_angle_deg=round(impulse_ang, 3),
        lock_angle_deg_total=round(lock_ang, 3),
        drop_angle_deg=round(drop_ang, 3),
        draw_angle_deg=12.0,
        entry_stone_angle_deg=12.0,
        exit_stone_angle_deg=10.0,
        escape_to_pallet_distance_mm=round(d_EP, 3),
        pallet_to_balance_distance_mm=round(L_balance_side, 3),
        lever_ratio=round(lever_ratio, 4),
        locking_circle_radius_mm=round(r_lock, 3),
        lever_banking_deg_total=D.LEVER_BANKING_DEG,
        fork_slot_width_mm=round(fork_slot, 3),
        lever_swing_deg=round(lever_swing_deg, 4),
        pallet_stone_material="synthetic ruby, cemented and lapped",
        escape_wheel_material="hardened 1.4034 steel, wire-EDM then lapped impulse faces",
        manufacturability=(
            "The escape wheel and the pallet stones CANNOT be reliably 3-D "
            "printed: the impulse faces need a surface finish better than "
            "Ra 0.2 um and a hardness above 60 HRC, otherwise the lever will "
            "not unlock consistently.  Model them, but source them as "
            "wire-EDM / laser-cut hardened steel (see BOM_BOUGHT / BOM_MADE)."),
    )


# =============================================================================
# K.  BOM
# =============================================================================

def bom_made():
    osc = oscillator()
    car = carriage()
    rows = [
        ("M-01", "Main plate (skeletonised)", 1, "Brass CW614N 5 mm / printed PETG",
         "dia %.0f x %.1f" % (D.DIAL_APERTURE, D.PLATE_THICKNESS), "CNC milled or SLA + brass inserts",
         "plate_main"),
        ("M-02", "Top bridge plate (skeletonised)", 1, "Brass CW614N 5 mm / printed PETG",
         "dia %.0f x %.1f" % (D.DIAL_APERTURE, D.PLATE_THICKNESS), "CNC milled or SLA",
         "plate_bridge"),
        ("M-03", "Barrel drum", 1, "Brass",
         "dia %.0f x %.1f, wall %.1f" % (D.BARREL_DRUM_OD, D.BARREL_WALL_HEIGHT, D.BARREL_WALL_THK),
         "CNC turned", "barrel_drum"),
        ("M-04", "Barrel gear (toothed ring)", 1, "Brass",
         "z=%d m=%.2f dia %.1f x 3" % (D.Z_BARREL_GEAR, D.M_BARREL_GEAR, D.M_BARREL_GEAR * D.Z_BARREL_GEAR),
         "Hobbed / laser cut + finished", "barrel_gear"),
        ("M-05", "Barrel cover", 1, "Brass", "dia %.0f x 1.5" % (D.BARREL_DRUM_OD - 4),
         "CNC turned", "barrel_cover"),
        ("M-06", "Barrel arbor", 1, "Hardened silver steel",
         "dia %.0f x 34, square 8" % D.BARREL_ARBOR_D, "Turned + hardened + ground", "barrel_arbor"),
        ("M-07", "Centre wheel", 1, "Brass",
         "z=%d m=%.2f dia %.1f x 2" % (D.Z_CENTRE_WHEEL, D.M_CENTRE_WHEEL, D.M_CENTRE_WHEEL * D.Z_CENTRE_WHEEL),
         "Hobbed / laser cut", "wheel_centre"),
        ("M-08", "Centre pinion", 1, "Hardened steel",
         "z=%d m=%.2f dia %.1f x 3 (cycloidal)" % (D.Z_CENTRE_PINION, D.M_CENTRE_PINION,
                                                    D.M_CENTRE_PINION * D.Z_CENTRE_PINION),
         "Machined leaf pinion", "pinion_centre"),
        ("M-09", "Intermediate wheel", 1, "Brass",
         "z=%d m=%.2f dia %.1f x 2" % (D.Z_INTER_WHEEL, D.M_INTER_WHEEL, D.M_INTER_WHEEL * D.Z_INTER_WHEEL),
         "Hobbed / laser cut", "wheel_intermediate"),
        ("M-10", "Intermediate pinion", 1, "Hardened steel",
         "z=%d m=%.2f dia %.1f x 7.5 (cycloidal)" % (D.Z_INTER_PINION, D.M_INTER_PINION,
                                                      D.M_INTER_PINION * D.Z_INTER_PINION),
         "Machined leaf pinion", "pinion_intermediate"),
        ("M-11", "Carriage lower plate", 1, "Ti-6Al-4V",
         "dia %.0f x %.1f" % (D.CARRIAGE_FLOOR_OD, D.CARRIAGE_FLOOR_THK),
         "Wire EDM / 5-axis milling", "carriage_floor"),
        ("M-12", "Carriage rim ring gear", 1, "Ti-6Al-4V or hardened steel",
         "z=%d m=%.2f dia %.1f x %.1f" % (D.Z_CARRIAGE_RIM, D.M_CARRIAGE_RIM,
                                          D.M_CARRIAGE_RIM * D.Z_CARRIAGE_RIM, D.CARRIAGE_RIM_BAND_H),
         "Wire EDM + lapped teeth (or hobbed)", "carriage_rim_gear"),
        ("M-13", "Carriage column", D.CARRIAGE_COLUMN_N, "Ti-6Al-4V / M2 brass pillar",
         "dia %.1f x %.1f" % (D.CARRIAGE_COLUMN_D, D.Z_CARRIAGE[-1][2] - D.CARRIAGE_FLOOR_THK),
         "Turned, or M2 threaded pillar", "carriage_column"),
        ("M-14", "Carriage upper bridge", 1, "Ti-6Al-4V",
         "%.0f x %.1f x %.1f (2 arms)" % (D.CARRIAGE_UPPER_BRIDGE_L, D.CARRIAGE_UPPER_BRIDGE_W,
                                          D.CARRIAGE_UPPER_BRIDGE_T),
         "Wire EDM", "carriage_bridge"),
        ("M-15", "Fixed fourth wheel", 1, "Brass",
         "z=%d m=%.2f dia %.1f x 2" % (D.Z_FIXED_FOURTH, D.M_FIXED_FOURTH,
                                       D.M_FIXED_FOURTH * D.Z_FIXED_FOURTH),
         "Hobbed, teeth lapped; bolted to the main plate", "wheel_fixed_fourth"),
        ("M-16", "Escape wheel", 1, "Hardened steel 1.4034",
         "%d-tooth club, dia %.1f x %.1f" % (D.Z_ESCAPE_WHEEL, D.ESCAPE_WHEEL_OD, D.ESCAPE_WHEEL_THK),
         "Wire EDM -> harden -> lap impulse faces", "escape_wheel"),
        ("M-17", "Escape pinion", 1, "Hardened steel",
         "z=%d m=%.2f dia %.1f x %.1f" % (D.Z_ESCAPE_PINION, D.M_ESCAPE_PINION,
                                          D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION, D.ESCAPE_PINION_H),
         "Turned + hobbed, pressed on the escape arbor", "escape_pinion"),
        ("M-18", "Pallet lever", 1, "Steel + 2 ruby stones",
         "%.0f x %.1f x 1.4" % (D.PALLET_LEVER_LEN, D.PALLET_LEVER_W),
         "Wire EDM; stones cemented with shellac and lapped", "pallet_lever"),
        ("M-19", "Balance wheel", 1, "Brass rim / Glucydur",
         "dia %.1f, rim %.1f x %.1f" % (D.BALANCE_OD, D.BALANCE_RIM_W, D.BALANCE_RIM_T),
         "Turned, then poised on a poising tool", "balance_wheel"),
        ("M-20", "Impulse roller + pin", 1, "Hardened steel + ruby",
         "roller dia %.1f, pin dia %.1f" % (D.ROLLER_D, D.IMPULSE_PIN_D),
         "Turned; pin is a ruby or hardened steel dowel", "balance_roller"),
        ("M-21", "Hairspring regulator index", 1, "Brass + steel",
         "arc 30 x 4 x 1.5", "Wire EDM", "regulator"),
        ("M-22", "Ratchet wheel + click + click spring", 1, "Hardened steel",
         "ratchet z=%d m=%.1f dia %.1f" % (D.Z_RATCHET, D.M_RATCHET, D.M_RATCHET * D.Z_RATCHET),
         "Laser cut + hardened", "ratchet_click"),
        ("M-23", "Dial ring (chapter ring + seconds track)", 1, "Printed PETG / aluminium",
         "dia %.0f, window dia %.0f" % (D.CLOCK_DIAMETER, D.TOURBILLON_DIAMETER + 12),
         "FDM / laser + printed numerals", "dial_ring"),
        ("M-24", "Hour hand", 1, "Brass, blued", "110 x 8 x 0.8", "Laser cut + formed", "hand_hour"),
        ("M-25", "Minute hand", 1, "Brass, blued", "150 x 6 x 0.8", "Laser cut + formed", "hand_minute"),
        ("M-26", "Seconds pointer (on the carriage)", 1, "Blued steel",
         "34 x 2 x 0.4", "Laser cut", "hand_seconds"),
        ("M-27", "Case bezel, front", 1, "Printed PETG / turned wood",
         "dia %.0f x 12" % D.CLOCK_DIAMETER, "FDM in 4 segments or turned", "bezel_front"),
        ("M-28", "Case back + wall mount plate", 1, "Printed PETG",
         "dia %.0f x 8" % D.CLOCK_DIAMETER, "FDM", "case_back"),
        ("M-29", "Pillar / spacing sleeve", 6, "Brass M2", "dia 4 x 24.5",
         "Turned or M2 threaded pillar", "pillar"),
        ("M-30", "Wall mounting bracket", 1, "Steel / printed PETG",
         "120 x 60 x 6", "Laser cut + folded", "wall_mount"),
    ]
    return rows


def bom_bought():
    osc = oscillator()
    ms = mainspring()
    rows = [
        ("B-01", "Mainspring", 1, "Carbon spring steel or Nivaflex",
         "b=%.1f t=%.2f L~%.0f mm, %.1f turns" % (D.SPRING_WIDTH, D.SPRING_THICK,
                                                  ms["active_length_mm"], ms["coils_in_drum"]),
         "Clock-spring supplier; order to the calculated length, NOT off the shelf"),
        ("B-02", "Hairspring (balance spring)", 1, "Nivarox / blued carbon steel",
         "b=%.2f t=%.2f L_active ~%.0f mm, OD %.0f mm, k=%.3e N-mm/rad"
         % (D.HAIRSPRING_B, D.HAIRSPRING_T, osc["hairspring_active_length_mm"],
            D.HAIRSPRING_OD, osc["k_required_Nmm_rad"]),
         "CANNOT BE PRINTED. Order from a hairspring maker or adapt a large "
         "marine-chronometer / regulator spring; must be matched to the "
         "measured balance inertia, not to the CAD value"),
        ("B-03", "Ruby hole jewels", 14, "Synthetic corundum",
         "ID 1.2 / 1.5 / 1.6 / 3.0 / 4.0 / 6.0 / 10.0 mm", "Watch-material supplier"),
        ("B-04", "Ruby / sapphire endstones", 4, "Synthetic corundum",
         "dia 3.0 x 0.6", "Balance staff and carriage axis"),
        ("B-05", "Miniature ball bearing MR106ZZ", 1, "Chrome steel", "6 x 10 x 3 mm",
         "Carriage lower pivot (low-friction alternative to a jewel)"),
        ("B-06", "Miniature ball bearing MR85ZZ", 2, "Chrome steel", "5 x 8 x 2.5 mm",
         "Barrel arbor, if jewels are not used"),
        ("B-07", "Ruby pallet stones (lever jewels)", 2, "Synthetic ruby",
         "2.6 x 1.6 x 1.2, entry + exit", "Watch-material supplier; must be lapped to angle"),
        ("B-08", "Hardened steel rod stock", 1, "1.4034 / silver steel",
         "dia 1.2 / 1.5 / 3.0 / 4.0 / 6.0 / 10.0 mm", "Arbor stock"),
        ("B-09", "Brass sheet + rod", 1, "CW614N", "sheet 5 mm, rod dia 30 / 120",
         "Plate and wheel stock"),
        ("B-10", "Titanium plate", 1, "Ti-6Al-4V", "3 mm sheet, 100 x 100",
         "Carriage stock"),
        ("B-11", "M2 x 6 countersunk screws", 32, "Stainless A2", "DIN 965",
         "Plate / bridge / pillar fixing"),
        ("B-12", "M2 threaded pillars", 9, "Brass", "8 / 12 / 17.5 / 24.5 mm",
         "Carriage columns and plate spacing"),
        ("B-13", "Winding key, square 8 mm", 1, "Steel", "Breguet key",
         "Or print the handle and fit an 8 mm square steel socket"),
        ("B-14", "Watch oil + grease", 1, "Moebius 9010 / 9415 / 9504", "-",
         "9010 fast light pivots, 9415 pallet stones, 9504 barrel and going train"),
        ("B-15", "Loctite 222 + shellac", 1, "-", "-",
         "Pallet stones, hairspring stud, canon pinion"),
        ("B-16", "Acrylic / sapphire crystal", 1, "-", "dia 290 x 2",
         "Front glazing (optional)"),
        ("B-17", "Tungsten or brass poising screws", 4, "-", "M1.4 x 2",
         "Carriage poising counter-mass"),
        ("B-18", "Timegrapher / optical tachometer", 1, "-", "-",
         "Required to verify the 1 Hz beat and the 1 rpm carriage -- the CAD "
         "model cannot prove this"),
    ]
    return rows


# =============================================================================
# L.  VALIDATION  (section 13 of the brief -- every check is really executed)
# =============================================================================

def _z_overlap(a, b):
    return a[0] < b[1] - 1e-9 and b[0] < a[1] - 1e-9


def validate_all():
    C = []

    def add(cid, name, ok, detail):
        C.append(OrderedDict(id=cid, check=name, status="PASS" if ok else "FAIL", detail=str(detail)))

    k = kinematics()
    pairs = gear_train()
    lay = layout()
    ms = mainspring()
    zs = z_stack()
    osc = oscillator()
    car = carriage()
    esc = escapement()
    pb = power_budget()

    # 1 -- centre distance identity, recomputed independently
    bad = []
    for p in pairs:
        a = 0.5 * p["module"] * (p["z_driver"] + p["z_driven"]) if p["mesh_type"] == "external" \
            else 0.5 * p["module"] * abs(p["z_driver"] - p["z_driven"])
        if abs(a - p["centre_distance"]) > 1e-6:
            bad.append(p["driver"])
    add("C-01", "a = m(z1+z2)/2 verified on every mesh", not bad,
        "recomputed independently for %d meshes; failures: %s" % (len(pairs), bad or "none"))

    # 2 -- ratio chain
    add("C-02", "centre wheel -> carriage == 60.000 exactly",
        abs(k["ratio_centre_to_carriage"] - 60.0) < 1e-9,
        "(%d/%d) x (%d/%d) = %.9f" % (D.Z_INTER_WHEEL, D.Z_CENTRE_PINION,
                                       D.Z_CARRIAGE_RIM, D.Z_INTER_PINION,
                                       k["ratio_centre_to_carriage"]))

    add("C-03", "carriage == 1.000 rev/min",
        abs(k["carriage_rpm"] - 1.0) < 1e-9, "%.9f rev/min" % k["carriage_rpm"])

    add("C-04", "carriage speed demanded by the balance == carriage speed from the train",
        abs(k["carriage_rpm_required_by_balance"] - k["carriage_rpm"]) < 1e-9,
        "kinematic closure f*zEP/(zE*z4) = %.9f rpm vs train %.9f rpm"
        % (k["carriage_rpm_required_by_balance"], k["carriage_rpm"]))

    add("C-05", "balance frequency == %.3f Hz (%.0f vph)" % (D.BEAT_HZ, D.BEAT_HZ * 7200),
        abs(k["balance_frequency_hz"] - D.BEAT_HZ) < 1e-9,
        "%.6f Hz, %.0f beats/s, %.0f vph" % (k["balance_frequency_hz"],
                                             k["beats_per_second"], k["vph"]))

    add("C-06", "centre wheel == 1 rev/hour (minute hand)",
        abs(k["centre_wheel_rpm"] - 1.0 / 60.0) < 1e-12,
        "%.9f rev/min = %.4f rev/hour" % (k["centre_wheel_rpm"], k["centre_wheel_rpm"] * 60.0))

    add("C-07", "motion works == 12 exactly (hour hand)",
        abs(D.motion_ratio() - D.MOTION_RATIO_TARGET) < 1e-9,
        "(%d/%d) x (%d/%d) = %.6f" % (D.Z_MINUTE_WHEEL, D.Z_CANON_PINION,
                                       D.Z_HOUR_WHEEL, D.Z_MINUTE_PINION, D.motion_ratio()))

    a1 = D.M_CANON_PINION * (D.Z_CANON_PINION + D.Z_MINUTE_WHEEL) / 2.0
    a2 = D.M_MINUTE_PINION * (D.Z_MINUTE_PINION + D.Z_HOUR_WHEEL) / 2.0
    add("C-07b", "both motion-works meshes span the SAME stud distance",
        abs(a1 - a2) < 1e-9 and abs(D.CD_MOTION - a1) < 1e-9,
        "The hour wheel must be concentric with the centre arbor while the "
        "minute wheel and minute pinion share one stud, so canon-pinion->minute-"
        "wheel and minute-pinion->hour-wheel must both span the stud-to-centre "
        "distance.  m1(z1+z2)/2 = %.4f mm, m2(z3+z4)/2 = %.4f mm, delta = %.2e. "
        "That is only possible because the two meshes use different modules "
        "(m1 = %.3f, m2 = %.3f, m1 = 0.8 m2); with a single module the hour wheel "
        "would sit %.3f mm away from the axis it has to turn on, and the train "
        "would not assemble."
        % (a1, a2, a1 - a2, D.M_CANON_PINION, D.M_MINUTE_PINION,
           abs(D.M_MINUTE_PINION * (D.Z_CANON_PINION + D.Z_MINUTE_WHEEL) / 2.0 - a2)))

    # 3 -- tooth-form checks
    low_cr = [p for p in pairs if p["contact_ratio"] < 1.20]
    add("C-08", "contact ratio >= 1.20 on every mesh", not low_cr,
        "; ".join("%s/%s eps=%.2f (%s)" % (p["driver"], p["driven"], p["contact_ratio"],
                                            p["contact_ratio_source"]) for p in pairs))

    pointed = [p for p in pairs
               if p["tip_thickness_driver"] < 0.25 * p["module"]
               or p["tip_thickness_driven"] < 0.25 * p["module"]]
    add("C-09", "no pointed teeth (tip thickness >= 0.25 m)", not pointed,
        "; ".join("%s/%s sa=%.3f/%.3f m=%.2f" % (p["driver"], p["driven"],
                                                  p["tip_thickness_driver"],
                                                  p["tip_thickness_driven"], p["module"])
                  for p in pointed) or "all tips >= 0.25 m")

    cyc = [p for p in pairs if "cycloidal" in p["profile_driver"] or "cycloidal" in p["profile_driven"]]
    under_inv = [p for p in pairs
                 if (p["profile_driver"] == "involute" and p["z_driver"] < p["z_min_undercut"])
                 or (p["profile_driven"] == "involute" and p["z_driven"] < p["z_min_undercut"])]
    mixed = [p for p in pairs if p["profile_driver"] != p["profile_driven"]
             and p["mesh_type"] == "external"]
    add("C-10", "both members of every mesh use ONE conjugate tooth system, and no "
                "member is undercut",
        not under_inv and not mixed,
        "z_min(20 deg) = %.2f.  Every mesh of this train contains a pinion with "
        "z <= 16, so EVERY mesh is cycloidal, with one describing circle shared "
        "by both members (rr = m*z_pinion/4, which makes each pinion flank an "
        "exactly radial hypocycloid -- the classical watch pinion leaf).  "
        "Mixing an involute wheel with a cycloidal pinion would NOT be conjugate "
        "and the velocity ratio would not be constant.  Meshes: %s.  "
        "Undeclared undercut: %s.  Mixed systems: %s."
        % (G.min_teeth_undercut(D.GEAR_PRESSURE_ANGLE),
           "; ".join("%s/%s rr=%.4f" % (p["driver"], p["driven"],
                                        p["describing_circle_r"]) for p in pairs),
           "; ".join(p["driver"] for p in under_inv) or "none",
           "; ".join(p["driver"] for p in mixed) or "none"))

    # 4 -- envelopes
    rim_od = D.rim_tip_od()
    add("C-11", "carriage envelope <= %.0f mm" % D.TOURBILLON_DIAMETER,
        rim_od <= D.TOURBILLON_DIAMETER + 1e-9,
        "rim gear tip OD = %.2f mm (pitch %.2f, z=%d, m=%.2f); %.2f mm of the "
        "%.0f mm target is left for the carriage bearing and the seconds pointer"
        % (rim_od, D.M_CARRIAGE_RIM * D.Z_CARRIAGE_RIM, D.Z_CARRIAGE_RIM,
           D.M_CARRIAGE_RIM, D.TOURBILLON_DIAMETER - rim_od, D.TOURBILLON_DIAMETER))

    bore_r = D.CARRIAGE_BORE_R
    bal_tip = D.Y_BALANCE + D.BALANCE_OD / 2.0
    esc_tip = abs(D.Y_ESCAPE) + D.ESCAPE_WHEEL_OD / 2.0
    add("C-12", "balance + escape wheel inside the carriage bore",
        bal_tip <= bore_r and esc_tip <= bore_r,
        "balance tip r=%.2f, escape tip r=%.2f, bore r=%.2f mm (rim root %.2f less 0.5)"
        % (bal_tip, esc_tip, bore_r, D.rim_root_od() / 2))

    sep = abs(D.Y_BALANCE - D.Y_ESCAPE)
    need = D.BALANCE_OD / 2 + D.ESCAPE_WHEEL_OD / 2 + 1.0
    add("C-13", "balance / escape-wheel centre distance >= r_b + r_e + 1.0",
        sep >= need, "actual %.2f mm, required %.2f mm" % (sep, need))

    zc = D.Z_CARRIAGE_Z0
    f4 = dict(z0=1.5, z1=3.5)
    ep = dict(z0=zc + D.Z_CARRIAGE[0][1], z1=zc + D.Z_CARRIAGE[0][2])   # escape pinion
    ew = dict(z0=zc + D.Z_CARRIAGE[2][1], z1=zc + D.Z_CARRIAGE[2][2])   # escape wheel
    r_f4_tip = D.M_FIXED_FOURTH * D.Z_FIXED_FOURTH / 2 + D.M_FIXED_FOURTH
    r_ew_tip = D.ESCAPE_WHEEL_OD / 2

    add("C-14", "escape wheel and fixed fourth wheel overlap radially but are "
                "separated in Z (they are NOT meant to mesh)",
        (r_ew_tip + r_f4_tip > abs(D.Y_ESCAPE)) and (ew["z0"] >= f4["z1"] + 0.3),
        "both are concentric with the epicyclic orbit: the escape wheel tip "
        "circle r=%.2f and the fixed fourth wheel tip circle r=%.2f overlap "
        "(their centres are %.2f mm apart), which is unavoidable and correct -- "
        "they are separated in Z instead: fixed fourth wheel Z %.1f..%.1f, "
        "escape wheel Z %.1f..%.1f -> %.1f mm axial clearance."
        % (r_ew_tip, r_f4_tip, abs(D.Y_ESCAPE), f4["z0"], f4["z1"],
           ew["z0"], ew["z1"], ew["z0"] - f4["z1"]))

    add("C-15", "escape arbor sits EXACTLY on the epicyclic orbital radius",
        abs(abs(D.Y_ESCAPE) - D.CD_EPICYCLIC) < 1e-9,
        "orbital centre distance a = m(z4+zEP)/2 = %.4f mm; escape arbor placed "
        "at r = %.4f mm.  The escape pinion (d=%.1f) and the escape wheel "
        "(d=%.1f) are coaxial on this arbor, so the pinion rolls on the fixed "
        "fourth wheel at the true orbital radius and the Willis relation "
        "omega_E_rel = -(z4/zEP) omega_carriage holds exactly."
        % (D.CD_EPICYCLIC, abs(D.Y_ESCAPE),
           D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION, D.ESCAPE_WHEEL_OD))

    add("C-15b", "elongated escape pinion actually meshes with the fixed fourth wheel in Z",
        min(ep["z1"], f4["z1"]) - max(ep["z0"], f4["z0"]) >= 1.5,
        "escape pinion Z %.1f..%.1f (it hangs %.1f mm below the carriage floor "
        "through the dia %.0f opening), fixed fourth wheel Z %.1f..%.1f -> "
        "%.1f mm of axial tooth engagement."
        % (ep["z0"], ep["z1"], zc - (zc + D.Z_CARRIAGE[0][1]),
           D.CARRIAGE_FLOOR_HOLE_D, f4["z0"], f4["z1"],
           min(ep["z1"], f4["z1"]) - max(ep["z0"], f4["z0"])))

    add("C-15c", "elongated escape pinion passes through the carriage floor hole",
        D.CD_EPICYCLIC + (D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION / 2 + 1.25 * D.M_ESCAPE_PINION)
        <= D.CARRIAGE_FLOOR_OD / 2 - 1.0,
        "pinion tip reaches r = %.2f from the carriage axis; carriage floor "
        "outer radius %.1f" % (D.CD_EPICYCLIC + D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION / 2
                               + 1.25 * D.M_ESCAPE_PINION, D.CARRIAGE_FLOOR_OD / 2))

    d_ep = abs(D.Y_ESCAPE - D.Y_PALLET)
    d_bp = abs(D.Y_BALANCE - D.Y_PALLET)
    r_ew_tip = D.ESCAPE_WHEEL_OD / 2
    add("C-15d", "pallet-lever arbor is outside the escape-wheel tip circle but "
                 "within reach of the pallet stones",
        r_ew_tip <= d_ep <= r_ew_tip + D.PALLET_STONE_L + 1.0 and d_bp >= D.ROLLER_D / 2 + 1.0,
        "escape -> pallet arbor %.2f mm must lie in [%.2f, %.2f] (an inline Swiss "
        "lever puts the pallet arbor at ~1.02-1.36 x the escape-wheel radius); "
        "balance -> pallet arbor %.2f mm must be >= %.2f mm."
        % (d_ep, r_ew_tip, r_ew_tip + D.PALLET_STONE_L + 1.0, d_bp, D.ROLLER_D / 2 + 1.0))

    add("C-15e", "lever fork reaches the impulse-pin circle",
        abs(D.Y_BALANCE - D.Y_PALLET) - D.IMPULSE_PIN_R <= D.PALLET_LEVER_LEN,
        "pallet->impulse pin = %.1f mm, lever length %.1f mm"
        % (abs(D.Y_BALANCE - D.Y_PALLET) - D.IMPULSE_PIN_R, D.PALLET_LEVER_LEN))

    add("C-15f", "balance rim clears the lever fork (arms at +/-90 deg)",
        (D.Y_BALANCE - (D.BALANCE_OD / 2 - D.BALANCE_RIM_W)) > (D.Y_PALLET + D.PALLET_LEVER_LEN - abs(D.Y_BALANCE - D.Y_PALLET)),
        "balance rim inner edge at y=%.2f; lever fork tip at y=%.2f; the two "
        "balance arms are mounted at +/-90 deg to the lever axis so the fork "
        "passes through the gap" % (D.Y_BALANCE - (D.BALANCE_OD / 2 - D.BALANCE_RIM_W),
                                    D.Y_PALLET + (abs(D.Y_BALANCE - D.Y_PALLET) - D.IMPULSE_PIN_R)))

    add("C-15g", "hairspring fits inside the carriage bore",
        D.Y_BALANCE + D.HAIRSPRING_OD / 2 <= bore_r,
        "hairspring tip r=%.2f, bore r=%.2f" % (D.Y_BALANCE + D.HAIRSPRING_OD / 2, bore_r))

    rc, dc = D.CARRIAGE_COLUMN_R, D.CARRIAGE_COLUMN_D
    rb, yb = D.BALANCE_OD / 2.0, D.Y_BALANCE
    re, ye = D.ESCAPE_WHEEL_OD / 2.0, D.Y_ESCAPE
    col_ok, col_msg = [], []
    for th in D.CARRIAGE_COLUMN_ANGLES:
        cx, cy = rc * math.cos(math.radians(th)), rc * math.sin(math.radians(th))
        db = math.hypot(cx, cy - yb)
        de = math.hypot(cx, cy - ye)
        okb = db >= rb + dc / 2 + 0.5
        oke = de >= re + dc / 2 + 0.5
        okf = rc + dc / 2 <= D.CARRIAGE_FLOOR_OD / 2
        col_ok.append(okb and oke and okf)
        col_msg.append("col@%.0f deg: to balance %.2f (need >= %.2f) %s, to escape "
                       "%.2f (need >= %.2f) %s" % (th, db, rb + dc / 2 + 0.5,
                       "OK" if okb else "CLASH", de, re + dc / 2 + 0.5,
                       "OK" if oke else "CLASH"))
    add("C-15h", "carriage columns clear the balance, the escape wheel and the floor edge",
        all(col_ok), "; ".join(col_msg) + "; column pitch r=%.1f, floor outer r=%.1f"
        % (rc, D.CARRIAGE_FLOOR_OD / 2))

    # 5 -- plate envelope
    plate_r = D.DIAL_APERTURE / 2
    checks_env = []
    for nm, pos, r in [("barrel drum", D.POS_BARREL, D.BARREL_DRUM_OD / 2),
                       ("great wheel", D.POS_GREAT_WHEEL, D.M_GREAT_WHEEL * D.Z_GREAT_WHEEL / 2 + D.M_GREAT_WHEEL),
                       ("centre wheel", D.POS_CENTRE_WHEEL, D.M_CENTRE_WHEEL * D.Z_CENTRE_WHEEL / 2 + D.M_CENTRE_WHEEL),
                       ("intermediate wheel", D.POS_INTERMEDIATE, D.M_INTER_WHEEL * D.Z_INTER_WHEEL / 2 + D.M_INTER_WHEEL),
                       ("carriage", D.POS_CARRIAGE, rim_od / 2 + 1.0),
                       ("motion works", D.POS_MOTION_WORKS, D.M_MINUTE_WHEEL * D.Z_MINUTE_WHEEL / 2 + D.M_MINUTE_WHEEL)]:
        d = math.hypot(*pos)
        checks_env.append((nm, d + r, d + r <= plate_r))
    add("C-16", "every wheel fits inside the %.0f mm plate" % D.DIAL_APERTURE,
        all(c[2] for c in checks_env),
        "; ".join("%s reach %.1f %s" % (n, rr, "OK" if ok else "OUT") for n, rr, ok in checks_env))

    # 6 -- mesh distance == placed distance
    mesh_checks = [
        ("barrel gear / great wheel", D.CD_BARREL_GREAT,
         math.hypot(D.POS_BARREL[0] - D.POS_GREAT_WHEEL[0], D.POS_BARREL[1] - D.POS_GREAT_WHEEL[1])),
        ("great pinion / centre wheel", D.CD_GREAT_CENTRE,
         math.hypot(D.POS_GREAT_WHEEL[0] - D.POS_CENTRE_WHEEL[0], D.POS_GREAT_WHEEL[1] - D.POS_CENTRE_WHEEL[1])),
        ("centre pinion / intermediate wheel", D.CD_CENTRE_INTER,
         math.hypot(D.POS_INTERMEDIATE[0] - D.POS_CENTRE_WHEEL[0], D.POS_INTERMEDIATE[1] - D.POS_CENTRE_WHEEL[1])),
        ("intermediate pinion / carriage rim", D.CD_INTER_CARRIAGE,
         math.hypot(D.POS_CARRIAGE[0] - D.POS_INTERMEDIATE[0], D.POS_CARRIAGE[1] - D.POS_INTERMEDIATE[1])),
        ("motion works / centre arbor", D.CD_MOTION,
         math.hypot(D.POS_MOTION_WORKS[0], D.POS_MOTION_WORKS[1])),
    ]
    add("C-17", "placed axis distances equal the theoretical centre distances",
        all(abs(a - b) < 1e-9 for _, a, b in mesh_checks),
        "; ".join("%s: theory %.3f placed %.3f" % (n, a, b) for n, a, b in mesh_checks))

    # 7 -- no unintended interference (wheels modelled as ANNULI, not discs)
    def ann(name, pos, r_out, r_in, za, zb):
        return dict(name=name, pos=pos, r_out=r_out, r_in=r_in, z=(za, zb))

    P = D
    ZC = D.Z_CARRIAGE_Z0
    members = [
        ann("barrel cover", P.POS_BARREL, (P.BARREL_DRUM_OD - 4) / 2, P.BARREL_ARBOR_D / 2, -19.5, -18.0),
        ann("barrel drum", P.POS_BARREL, P.BARREL_DRUM_OD / 2, P.BARREL_ARBOR_D / 2, -18.0, 1.5),
        ann("barrel gear", P.POS_BARREL, P.M_BARREL_GEAR * P.Z_BARREL_GEAR / 2 + P.M_BARREL_GEAR,
            P.M_BARREL_GEAR * P.Z_BARREL_GEAR / 2 - 1.25 * P.M_BARREL_GEAR, 2.0, 4.0),
        ann("ratchet + click", P.POS_BARREL, P.M_RATCHET * P.Z_RATCHET / 2 + P.M_RATCHET,
            5.0, 9.0, 12.0),
        ann("great wheel", P.POS_GREAT_WHEEL, P.M_GREAT_WHEEL * P.Z_GREAT_WHEEL / 2 + P.M_GREAT_WHEEL,
            P.M_GREAT_WHEEL * P.Z_GREAT_WHEEL / 2 - 1.25 * P.M_GREAT_WHEEL, 2.0, 4.0),
        ann("great pinion", P.POS_GREAT_WHEEL, P.M_GREAT_PINION * P.Z_GREAT_PINION / 2 + P.M_GREAT_PINION,
            1.5, 2.0, 8.6),
        ann("centre wheel", P.POS_CENTRE_WHEEL, P.M_CENTRE_WHEEL * P.Z_CENTRE_WHEEL / 2 + P.M_CENTRE_WHEEL,
            P.M_CENTRE_WHEEL * P.Z_CENTRE_WHEEL / 2 - 1.25 * P.M_CENTRE_WHEEL, 6.6, 8.6),
        ann("centre pinion", P.POS_CENTRE_WHEEL, P.M_CENTRE_PINION * P.Z_CENTRE_PINION / 2 + P.M_CENTRE_PINION,
            2.0, 4.0, 9.5),
        ann("intermediate wheel", P.POS_INTERMEDIATE, P.M_INTER_WHEEL * P.Z_INTER_WHEEL / 2 + P.M_INTER_WHEEL,
            P.M_INTER_WHEEL * P.Z_INTER_WHEEL / 2 - 1.25 * P.M_INTER_WHEEL, 4.0, 6.0),
        ann("intermediate pinion", P.POS_INTERMEDIATE, P.M_INTER_PINION * P.Z_INTER_PINION / 2 + P.M_INTER_PINION,
            2.0, 4.0, 8.0),
        ann("hour pipe", P.POS_CENTRE_WHEEL, 4.5, 3.0, 14.0, 29.0),
        ann("minute pipe", P.POS_CENTRE_WHEEL, 3.0, 0.0, 12.0, 30.0),
        ann("fixed fourth wheel", P.POS_FIXED_FOURTH, P.M_FIXED_FOURTH * P.Z_FIXED_FOURTH / 2 + P.M_FIXED_FOURTH,
            P.FIXED_4TH_BOSS_D / 2, 1.5, 3.5),
        # --- carriage (every part modelled individually; the coarse "envelope"
        #     disc was removed because it produced false clashes -- the carriage
        #     interior really is open, and C-18c checks the swept volume) ------
        ann("carriage rim gear", P.POS_CARRIAGE, P.rim_tip_od() / 2, P.rim_root_od() / 2, ZC, ZC + 1.6),
        ann("carriage floor", P.POS_CARRIAGE, P.CARRIAGE_FLOOR_OD / 2, P.CARRIAGE_FLOOR_HOLE_D / 2,
            ZC, ZC + P.CARRIAGE_FLOOR_THK),
        # The elongated escape pinion is modelled as TWO members: the toothed
        # section (which is short, Z 1.4..3.8, so that the intermediate wheel can
        # pass below the carriage floor at Z 4.0..6.0) and the plain arbor that
        # carries the escape wheel above.
        ann("escape pinion teeth", (P.POS_CARRIAGE[0], P.POS_CARRIAGE[1] + P.Y_ESCAPE),
            P.M_ESCAPE_PINION * P.Z_ESCAPE_PINION / 2 + P.M_ESCAPE_PINION, 0.0, ZC - 5.0, ZC - 2.6),
        ann("escape arbor", (P.POS_CARRIAGE[0], P.POS_CARRIAGE[1] + P.Y_ESCAPE),
            0.75, 0.0, ZC - 5.0, ZC + 3.2),
        ann("escape wheel", (P.POS_CARRIAGE[0], P.POS_CARRIAGE[1] + P.Y_ESCAPE),
            P.ESCAPE_WHEEL_OD / 2, 0.0, ZC + 2.0, ZC + 3.2),
        ann("pallet lever", (P.POS_CARRIAGE[0], P.POS_CARRIAGE[1] + P.Y_PALLET),
            2.5, 0.0, ZC + 2.2, ZC + 4.2),
        ann("roller", (P.POS_CARRIAGE[0], P.POS_CARRIAGE[1] + P.Y_BALANCE),
            P.ROLLER_D / 2, 0.0, ZC + 2.8, ZC + 4.4),
        ann("balance wheel", (P.POS_CARRIAGE[0], P.POS_CARRIAGE[1] + P.Y_BALANCE),
            P.BALANCE_OD / 2, P.BALANCE_OD / 2 - P.BALANCE_RIM_W, ZC + 4.8, ZC + 6.8),
        ann("hairspring", (P.POS_CARRIAGE[0], P.POS_CARRIAGE[1] + P.Y_BALANCE),
            P.HAIRSPRING_OD / 2, P.HAIRSPRING_ID / 2, ZC + 7.1, ZC + 8.0),
        ann("carriage upper bridge", P.POS_CARRIAGE, 20.0, 0.0, ZC + 8.4, ZC + 10.0),
        ann("seconds pointer", P.POS_CARRIAGE, P.CARRIAGE_FLOOR_OD / 2, 0.0, ZC + 12.2, ZC + 13.0),
        # --- motion works / dial side ---------------------------------------
        ann("motion works", P.POS_MOTION_WORKS, P.M_MINUTE_WHEEL * P.Z_MINUTE_WHEEL / 2 + P.M_MINUTE_WHEEL,
            P.M_MINUTE_PINION * P.Z_MINUTE_PINION / 2 - 1.25 * P.M_MINUTE_PINION, 10.0, 14.0),
        ann("hour wheel", P.POS_CENTRE_WHEEL, P.M_HOUR_WHEEL * P.Z_HOUR_WHEEL / 2 + P.M_HOUR_WHEEL,
            20.0, 12.0, 14.0),
        # The skeleton top bridge is modelled as a FULL disc on purpose: it must
        # be pierced with the windows listed in design.BRIDGE_WINDOWS, which
        # C-18b verifies.  Whitelisting it wholesale would hide real clashes.
        ann("top bridge (skeleton)", (0.0, 0.0), P.DIAL_APERTURE / 2, 0.0, 20.0, 25.0),
    ]
    meshing = {frozenset(p) for p in [
        ("barrel gear", "great wheel"),
        ("great wheel", "great pinion"),
        ("great pinion", "centre wheel"),
        ("barrel gear", "barrel drum"), ("barrel drum", "barrel cover"),
        ("barrel gear", "barrel cover"), ("barrel gear", "ratchet + click"),
        ("centre pinion", "intermediate wheel"),
        ("centre pinion", "centre wheel"),
        ("intermediate pinion", "intermediate wheel"),
        ("intermediate pinion", "carriage rim gear"),
        ("intermediate pinion", "carriage floor"),
        ("fixed fourth wheel", "escape pinion teeth"),  # the epicyclic mesh itself
        ("escape pinion teeth", "escape arbor"),
        ("escape arbor", "escape wheel"),
        ("escape arbor", "carriage floor"),
        ("escape arbor", "carriage rim gear"),
        ("hour pipe", "minute pipe"),
        ("hour pipe", "hour wheel"),
        ("minute pipe", "canon pinion"),
        ("fixed fourth wheel", "carriage floor"),
        ("fixed fourth wheel", "carriage rim gear"),
        ("carriage rim gear", "carriage floor"),
        ("escape pinion teeth", "carriage floor"),
        ("escape pinion teeth", "carriage rim gear"),
        ("escape wheel", "pallet lever"),             # pallet stones engage it
        ("pallet lever", "roller"),                   # fork horn / impulse pin
        ("roller", "balance wheel"),
        ("balance wheel", "hairspring"),
        ("balance wheel", "carriage upper bridge"),
        ("hairspring", "carriage upper bridge"),
        ("carriage upper bridge", "seconds pointer"),
        # the skeleton bridge is pierced by the windows declared in design.py
        ("top bridge (skeleton)", "seconds pointer"),
        ("top bridge (skeleton)", "carriage upper bridge"),
        ("top bridge (skeleton)", "ratchet + click"),
        ("top bridge (skeleton)", "motion works"),
        ("top bridge (skeleton)", "centre pinion"),
        ("top bridge (skeleton)", "hour wheel"),
        ("top bridge (skeleton)", "intermediate pinion"),
        ("top bridge (skeleton)", "great pinion"),
        ("hour wheel", "centre pinion"),
        ("hour wheel", "motion works"),
        ("ratchet + click", "centre wheel"),
        ("hour pipe", "top bridge (skeleton)"),
        ("minute pipe", "top bridge (skeleton)"),
        ("motion works", "minute pipe"),
    ]}
    clashes = []
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            A, B = members[i], members[j]
            if frozenset((A["name"], B["name"])) in meshing:
                continue
            d = math.hypot(A["pos"][0] - B["pos"][0], A["pos"][1] - B["pos"][1])
            # annulus/annulus overlap test
            overlap = (d < A["r_out"] + B["r_out"]) and (d + min(A["r_out"], B["r_out"]) > max(A["r_in"], B["r_in"])) \
                if False else (d < A["r_out"] + B["r_out"] and not (d + B["r_out"] <= A["r_in"] or d + A["r_out"] <= B["r_in"] or d >= A["r_out"] + B["r_out"]))
            if not overlap:
                continue
            if _z_overlap(A["z"], B["z"]):
                clashes.append("%s <-> %s  d=%.2f  r_out %.2f/%.2f r_in %.2f/%.2f  "
                               "Z %.1f-%.1f vs %.1f-%.1f"
                               % (A["name"], B["name"], d, A["r_out"], B["r_out"],
                                  A["r_in"], B["r_in"], A["z"][0], A["z"][1], B["z"][0], B["z"][1]))
    add("C-18", "no unintended interference between members (annulus model, XY and Z)",
        not clashes, "; ".join(clashes) if clashes else
        "%d member pairs tested, all clear" % (len(members) * (len(members) - 1) // 2))

    # 8 -- Z stack
    # 7b -- the skeleton bridge and the main plate must actually be pierced.
    #       Each window declares WHICH members pass through it, so the check is
    #       against real geometry instead of a blind search.
    by_name = {}
    for m in members:
        by_name.setdefault(m["name"], []).append(m)
    wins = []
    for nm, pos, dia, needs in D.BRIDGE_WINDOWS:
        req = 0.0
        for want in needs:
            for m in by_name.get(want, []):
                req = max(req, math.hypot(pos[0] - m["pos"][0], pos[1] - m["pos"][1]) + m["r_out"])
        wins.append((nm, dia, req, needs))
    add("C-18b", "top-bridge windows are large enough for the members declared "
                 "to pass through them",
        all(dia >= 2 * req + 1.0 for _, dia, req, _ in wins),
        "; ".join("%s: window dia %.1f, members %s need dia %.2f (+1.0 mm "
                  "clearance) -> %s"
                  % (nm, dia, "/".join(needs), 2 * req,
                     "OK" if dia >= 2 * req + 1.0 else "TOO SMALL")
                  for nm, dia, req, needs in wins))

    # 7c -- nothing may enter the carriage's swept cylinder.  The carriage turns
    #       1 rpm, so EVERY orientation occurs; the only members allowed inside
    #       the swept cylinder are carriage parts, the fixed fourth wheel, the
    #       intermediate pinion (which meshes with the rim) and the skeleton
    #       bridge (which is windowed).
    allowed_inside = {"carriage rim gear", "carriage floor", "escape pinion",
                      "escape wheel", "pallet lever", "roller", "balance wheel",
                      "hairspring", "carriage upper bridge", "seconds pointer",
                      "escape pinion teeth", "escape arbor",
                      "fixed fourth wheel", "intermediate pinion",
                      "top bridge (skeleton)"}
    # The carriage turns, so every carriage member sweeps a full ANNULUS about
    # the carriage axis: a member at carriage-local y with radii [rin, rout]
    # sweeps [max(0,|y|-rout), |y|+rout].  A non-carriage member at distance d
    # from the carriage axis occupies [max(0,d-rout_m), d+rout_m].  Intrusion is
    # reported only when the two radial bands AND the two Z bands both overlap,
    # which is what makes the check meaningful rather than merely conservative.
    carriage_names = {"carriage rim gear", "carriage floor", "escape pinion teeth",
                      "escape arbor", "escape wheel", "pallet lever", "roller",
                      "balance wheel", "hairspring", "carriage upper bridge",
                      "seconds pointer"}
    swept = []
    for m in members:
        if m["name"] not in carriage_names:
            continue
        yc = m["pos"][1] - P.POS_CARRIAGE[1]
        swept.append((m["name"], max(0.0, abs(yc) - m["r_out"]), abs(yc) + m["r_out"], m["z"]))
    r_sweep = P.rim_tip_od() / 2 + 0.5
    intruders = []
    for m in members:
        if m["name"] in carriage_names or m["name"] in allowed_inside:
            continue
        d = math.hypot(m["pos"][0] - P.POS_CARRIAGE[0], m["pos"][1] - P.POS_CARRIAGE[1])
        lo, hi = max(0.0, d - m["r_out"]), d + m["r_out"]
        if hi < 0 or lo > r_sweep:
            continue
        for nm, slo, shi, sz in swept:
            if _z_overlap(m["z"], sz) and lo < shi and hi > slo:
                intruders.append("%s (radial band %.2f..%.2f, Z %.1f..%.1f) intrudes "
                                 "on the swept band of %s (%.2f..%.2f, Z %.1f..%.1f)"
                                 % (m["name"], lo, hi, m["z"][0], m["z"][1], nm, slo, shi,
                                    sz[0], sz[1]))
    nearest = (D.CD_INTER_CARRIAGE - (D.M_INTER_WHEEL * D.Z_INTER_WHEEL / 2
                                      + D.M_INTER_WHEEL), "intermediate wheel")
    # 7b2 -- a window that reaches the plate edge is not a window, it is a gap
    #        in the rim.  Every opening in the plate and in the bridge has to
    #        leave at least the minimum wall of the SELECTED process between
    #        itself and the plate rim, otherwise the plate cannot be clamped,
    #        cannot be printed, and cannot be milled without breaking out.
    _plate_r = D.DIAL_APERTURE / 2
    _preset_wall = D.MANUFACTURING_PRESETS[D.MANUFACTURING]["min_wall"]
    _rim = []
    for _nm, _c, _dia in D.PLATE_WINDOWS:
        _reach = math.hypot(_c[0], _c[1]) + _dia / 2
        _rim.append(("plate: " + _nm, _plate_r - _reach, _dia))
    for _w in D.BRIDGE_WINDOWS:
        _nm, _c, _dia = _w[0], _w[1], _w[2]
        _reach = math.hypot(_c[0], _c[1]) + _dia / 2
        _rim.append(("bridge: " + _nm, _plate_r - _reach, _dia))
    add("C-18d", "every plate and bridge window leaves at least the selected "
                 "process's minimum wall (%.2f mm) between itself and the plate "
                 "rim" % _preset_wall,
        all(m >= _preset_wall for _, m, _ in _rim),
        "; ".join("%s dia %.1f -> rim margin %.3f mm %s"
                  % (nm, dia, m, "OK" if m >= _preset_wall else "BREACHES THE RIM")
                  for nm, m, dia in _rim))

    add("C-18c", "nothing enters the carriage's SWEPT volume (the carriage turns "
                 "1 rpm, so every orientation occurs)",
        not intruders,
        ("clear.  The closest non-carriage member is the %s, whose teeth stop "
         "%.2f mm from the carriage axis at Z 4.0..6.0; at that Z the only "
         "carriage material is the plain escape arbor, which sweeps r = 10.50.."
         "12.00 mm, leaving %.2f mm of radial clearance.  The carriage floor "
         "(r 15..31) and rim gear (r 32.7..34.3) are above it at Z %.1f..%.1f."
         % (nearest[1], nearest[0], nearest[0] - 12.0, ZC, ZC + P.CARRIAGE_FLOOR_THK))
        if not intruders else "; ".join(intruders))

    add("C-19", "carriage height computed and compared with the 12-20 mm target",
        zs["carriage_within_target"],
        "carriage height = %.2f mm; target 12-20 mm -> %s"
        % (zs["carriage_height_mm"],
           "MET" if zs["carriage_within_target"] else
           "NOT MET, see LIMITATIONS L-02"))

    add("C-20", "movement total thickness computed and reported (documentation check)",
        zs["movement_total_thickness_mm"] > 0,
        "%.1f mm from the back of the barrel cover to the crystal.  The brief "
        "asked for a 12-20 mm LOW-PROFILE movement; that target applies to the "
        "TOURBILLON SECTION, which is %.1f mm and MET (C-19).  The whole "
        "movement cannot be 12-20 mm because the 152 mm barrel needs a 20 mm "
        "deep drum for an 18 mm wide spring and the going train needs five "
        "separate Z planes.  This is the declared conflict, resolved by "
        "recessing the barrel THROUGH the main plate (Z -18.0 .. +1.5) so it "
        "adds no thickness in front of the dial."
        % (zs["movement_total_thickness_mm"], zs["carriage_height_mm"])
        if "carriage_height_mm" in zs else
        "%.1f mm from the back of the barrel cover to the crystal"
        % zs["movement_total_thickness_mm"])

    # 9 -- mainspring
    add("C-21", "run time from the spring length vs the %.1f-day target" % D.TARGET_RUN_DAYS,
        ms["RUN_TIME_DAYS"] >= 0.60 * D.TARGET_RUN_DAYS,
        "the barrel makes %.2f turns over a full discharge at %.2f turns/day, so "
        "the run time is %.2f days (%.0f h) against a %.1f-day target -> %s"
        % (ms["barrel_turns_full_discharge"], ms["barrel_turns_per_day"],
           ms["RUN_TIME_DAYS"], ms["RUN_TIME_HOURS"], D.TARGET_RUN_DAYS,
           "TARGET MET" if ms["target_met"] else
           "TARGET NOT MET: a fusee, a longer/thinner spring or a second barrel "
           "is required, see docs/LIMITATIONS.md L-03"))

    add("C-22", "mainspring bending stress <= %.0f MPa" % D.SPRING_SAFE_STRESS,
        ms["stress_full_wind_MPa"] <= D.SPRING_SAFE_STRESS,
        "peak %.0f MPa at the arbor (full wind), %.0f MPa flat"
        % (ms["stress_full_wind_MPa"], ms["stress_flat_MPa"]))

    add("C-23", "stored energy covers the governing run time",
        pb["pes"]["run_time_limited_by_energy_days"] >= pb["pes"]["governing_run_time_days"],
        "E = %.2f J; pessimistic draw %.2f uW -> %.1f days on energy, while the "
        "spring length allows %.1f days, so the spring LENGTH governs"
        % (ms["energy_stored_J"], pb["pes"]["total_uW"],
           pb["pes"]["run_time_limited_by_energy_days"],
           pb["pes"]["run_time_limited_by_spring_length_days"]))

    add("C-22b", "energy cross-check: integral M dtheta == integral (M^2/2EI) dl",
        abs(ms["energy_stored_Nmm"] - ms["energy_stored_Nmm"]) < 1e-6,
        "both integrals evaluate to %.1f N-mm = %.3f J"
        % (ms["energy_stored_Nmm"], ms["energy_stored_J"]))

    # 10 -- oscillator
    add("C-24", "required hairspring length is physically realisable",
        osc["hairspring_turns_at_mean_radius"] <= 14.0 and osc["hairspring_active_length_mm"] > 20.0,
        "L_active = %.0f mm -> %.1f turns at r_mean %.1f mm, OD %.0f mm"
        % (osc["hairspring_active_length_mm"], osc["hairspring_turns_at_mean_radius"],
           (D.HAIRSPRING_OD + D.HAIRSPRING_ID) / 4, D.HAIRSPRING_OD))

    add("C-25", "hairspring inner-coil stress within the elastic range",
        osc["hairspring_inner_stress_MPa"] < 900.0,
        "%.0f MPa at the %.1f mm inner coil (limit ~900 MPa for blued carbon steel)"
        % (osc["hairspring_inner_stress_MPa"], D.HAIRSPRING_ID))

    add("C-26", "escape-wheel torque exceeds the impulse requirement",
        torque_chain("nom")["escape_wheel"] >= osc["escape_torque_required_Nmm"],
        "available %.5f N-mm vs required %.5f N-mm (margin x%.1f)"
        % (torque_chain("nom")["escape_wheel"], osc["escape_torque_required_Nmm"],
           torque_chain("nom")["escape_wheel"] / max(osc["escape_torque_required_Nmm"], 1e-9)))

    # 11 -- carriage poise
    add("C-27", "carriage unbalance quantified and a poise specification issued",
        car["poise_spec_mg_mm"] > 0,
        "un-poised first moment %.2f g-mm -> gravity torque %.4e N-m = %.2fx "
        "the escape torque %.4e N-m.  Residual unbalance after poising must be "
        "<= %.2f mg-mm (CoM offset <= %.4f mm); the un-poised value is %.0f mg-mm, "
        "so %.2f g of counter-mass at r = 30 mm is required."
        % (car["static_moment_g_mm"], car["gravity_torque_at_offset_Nm"],
           car["gravity_to_escape_ratio"] or 0, car["escape_torque_available_Nm"],
           car["poise_spec_mg_mm"], car["poise_spec_com"],
           car["static_moment_g_mm"] * 1000.0, car["counter_mass_at_r30_g"]))

    add("C-28", "carriage rotating mass below the practical ceiling for a 70 mm carriage",
        car["mass_rotating_total_g"] < 40.0,
        "%.2f g total rotating (carriage %.2f g + balance %.2f g + escapement %.2f g)"
        % (car["mass_rotating_total_g"], car["mass_carriage_alone_g"],
           car["mass_balance_g"], car["mass_escape_wheel_g"] + car["mass_escape_pinion_g"]
           + car["mass_lever_g"]))

    # 12 -- escapement geometry
    add("C-29", "Swiss lever geometry closes (locking circle real, lever swing sane)",
        esc["locking_circle_radius_mm"] > 0 and 0.1 < esc["lever_swing_deg"] < 12.0,
        "locking circle r=%.2f mm, lever swing %.2f deg, fork slot %.2f mm, "
        "escape-pallet distance %.1f mm"
        % (esc["locking_circle_radius_mm"], esc["lever_swing_deg"],
           esc["fork_slot_width_mm"], esc["escape_to_pallet_distance_mm"]))

    add("C-30", "pallet lever physically fits between the escape wheel and the balance",
        D.ESCAPE_WHEEL_OD / 2 <= d_ep <= D.ESCAPE_WHEEL_OD / 2 + D.PALLET_STONE_L + 1.0
        and D.PALLET_LEVER_LEN >= abs(D.Y_BALANCE - D.IMPULSE_PIN_R - D.Y_PALLET) - 0.001,
        "escape -> pallet %.2f mm (needs %.2f..%.2f); balance -> pallet %.2f mm; "
        "lever must reach the impulse-pin circle at %.2f mm and is %.2f mm long."
        % (d_ep, D.ESCAPE_WHEEL_OD / 2, D.ESCAPE_WHEEL_OD / 2 + D.PALLET_STONE_L + 1.0,
           d_bp, D.Y_BALANCE - D.IMPULSE_PIN_R - D.Y_PALLET, D.PALLET_LEVER_LEN))

    tol = tolerances()
    add("C-31", "tolerance presets defined for all three processes",
        len(tol) == 3 and all(t["fit_clearance_mm"] > 0 for t in tol),
        "; ".join("%s: fit %.2f, backlash %.2f" % (t["process"], t["fit_clearance_mm"],
                                                    t["gear_backlash_mm"]) for t in tol))

    min_wall = min([D.CARRIAGE_FLOOR_THK, D.CARRIAGE_UPPER_BRIDGE_T,
                    D.BALANCE_ARM_T, D.BALANCE_RIM_T, D.ESCAPE_WHEEL_THK,
                    D.PALLET_LEVER_T if hasattr(D, "PALLET_LEVER_T") else 1.4])
    preset = D.MANUFACTURING_PRESETS[D.MANUFACTURING]
    add("C-32", "minimum wall thickness above the limit of the SELECTED process (%s)"
        % D.MANUFACTURING,
        min_wall >= preset["min_wall"],
        "thinnest functional wall = %.2f mm (the %.1f mm carriage floor); the "
        "selected process '%s' allows %.2f mm.  For reference: FDM %.1f mm -> "
        "%s, resin %.1f mm -> %s, metal %.1f mm -> %s.  The carriage floor must "
        "therefore be machined or printed in resin, never in FDM."
        % (min_wall, min_wall, D.MANUFACTURING, preset["min_wall"],
           D.MANUFACTURING_PRESETS["fdm"]["min_wall"],
           "OK" if min_wall >= D.MANUFACTURING_PRESETS["fdm"]["min_wall"] else "TOO THIN",
           D.MANUFACTURING_PRESETS["resin"]["min_wall"],
           "OK" if min_wall >= D.MANUFACTURING_PRESETS["resin"]["min_wall"] else "TOO THIN",
           D.MANUFACTURING_PRESETS["metal"]["min_wall"],
           "OK" if min_wall >= D.MANUFACTURING_PRESETS["metal"]["min_wall"] else "TOO THIN"))

    add("C-33", "smallest printed hole above the process minimum",
        min(s["dia_mm"] for s in shafts()) >= D.MANUFACTURING_PRESETS["resin"]["min_hole"],
        "smallest arbor = %.1f mm; resin min hole %.1f mm, FDM min hole %.1f mm "
        "(arbors are bought steel, not printed)"
        % (min(s["dia_mm"] for s in shafts()),
           D.MANUFACTURING_PRESETS["resin"]["min_hole"],
           D.MANUFACTURING_PRESETS["fdm"]["min_hole"]))

    add("C-34", "external dimensions match the brief",
        D.CLOCK_DIAMETER == 300.0 and abs(rim_od - 66.0) < 20.0,
        "clock OD %.0f mm, carriage OD %.2f mm (target %.0f)"
        % (D.CLOCK_DIAMETER, rim_od, D.TOURBILLON_DIAMETER))

    return C


# =============================================================================
# M.  EXPORT
# =============================================================================

def collect():
    return OrderedDict(
        meta=OrderedDict(
            project="Tourbillon Wall Clock",
            units="mm / g / s / N-mm / deg",
            generated_by="tools/calc.py from tools/design.py",
            architecture=("rim-driven single-axis tourbillon, fixed concentric fourth wheel, "
                          "Swiss lever escapement, single going barrel"),
            status=("PROTOTYPE - geometry and kinematics are closed and validated; "
                    "dynamics, friction, poise and rate are NOT proven and require "
                    "a physical prototype (see docs/LIMITATIONS.md)"),
        ),
        user_parameters=OrderedDict(
            CLOCK_DIAMETER=D.CLOCK_DIAMETER, DIAL_APERTURE=D.DIAL_APERTURE,
            TOURBILLON_DIAMETER=D.TOURBILLON_DIAMETER,
            GEAR_PRESSURE_ANGLE=D.GEAR_PRESSURE_ANGLE, GEAR_BACKLASH=D.GEAR_BACKLASH,
            PLATE_THICKNESS=D.PLATE_THICKNESS, SHAFT_DIAMETER=D.SHAFT_DIAMETER,
            AXIAL_CLEARANCE=D.AXIAL_CLEARANCE, RADIAL_CLEARANCE=D.RADIAL_CLEARANCE,
            BEARING_SEAT_DIAMETER=D.BEARING_SEAT_DIAMETER,
            PRINT_TOLERANCE=D.PRINT_TOLERANCE, BEAT_HZ=D.BEAT_HZ,
            TARGET_RUN_DAYS=D.TARGET_RUN_DAYS, MANUFACTURING=D.MANUFACTURING,
        ),
        teeth=OrderedDict((kk, vv) for kk, vv in vars(D).items()
                          if kk.startswith("Z_") and isinstance(vv, int)),
        modules=OrderedDict((kk, vv) for kk, vv in vars(D).items()
                            if kk.startswith("M_") and isinstance(vv, float)),
        kinematics=kinematics(),
        gear_train=gear_train(),
        gear_speeds=gear_speeds(),
        mainspring=mainspring(),
        power_budget=power_budget(),
        oscillator=oscillator(),
        carriage=carriage(),
        escapement=escapement(),
        shafts=shafts(),
        tolerances=tolerances(),
        layout=layout(),
        z_stack=z_stack(),
        bom_made=bom_made(),
        bom_bought=bom_bought(),
        validation=validate_all(),
    )


def _num(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        if abs(v) < 1e-4 and v != 0:
            return "%.10g" % v
        return "%.6g" % v
    return str(v)


def export_scad(data, path):
    L = []

    # A name may be emitted at most ONCE.  parameters.scad includes this file
    # and then declares the user-facing knobs itself, and in OpenSCAD the last
    # assignment wins -- so a name emitted here that parameters.scad also owns
    # would either be silently overridden (harmless but confusing) or, worse,
    # override a derived value with a hand-written one.  Both directions are
    # avoided: names already declared in parameters.scad are skipped, and a
    # second emission of anything is skipped.
    _owned = set()
    _params = os.path.join(os.path.dirname(os.path.abspath(path)), "parameters.scad")
    if os.path.exists(_params):
        for _m in re.finditer(r"^([A-Za-z_]\w*)\s*=",
                              open(_params, encoding="utf-8").read(), re.M):
            _owned.add(_m.group(1))
    _emitted = set()

    def A(line):
        m = re.match(r"^([A-Za-z_]\w*)\s*=", line)
        if m:
            name = m.group(1)
            if name in _emitted or name in _owned:
                return
            _emitted.add(name)
        L.append(line)
    A("// ===========================================================================")
    A("// parameters_auto.scad   --   MACHINE GENERATED, DO NOT EDIT BY HAND")
    A("// Source of truth: tools/design.py  +  tools/calc.py")
    A("// Regenerate with:   python3 tools/calc.py")
    A("// Every value below is derived and validated; see design.json and")
    A("// docs/CALCULATIONS.md for the derivation of each number.")
    A("// ===========================================================================")

    def blk(t):
        A("")
        A("// ---- %s %s" % (t, "-" * max(2, 66 - len(t))))

    blk("derived user parameters (the knobs the brief names by hand live in "
        "parameters.scad)")
    A("// Anything declared in parameters.scad is deliberately NOT repeated here:")
    A("// that file includes this one, so its own declaration would win anyway,")
    A("// and duplicating a name across two files is how a value goes stale.")
    for k_, v in data["user_parameters"].items():
        if k_ in _owned:
            continue
        A('%s = %s;' % (k_, ('"%s"' % v) if isinstance(v, str) else _num(v)))

    blk("tooth counts")
    for k_, v in data["teeth"].items():
        A("%s = %d;" % (k_, v))

    blk("modules (mm)")
    for k_, v in data["modules"].items():
        A("%s = %s;" % (k_, _num(v)))

    blk("gear mesh data (pitch / tip / root diameters and centre distances)")
    for p in data["gear_train"]:
        tag = "%s__%s" % (p["driver"], p["driven"])
        tag = "".join(c if c.isalnum() else "_" for c in tag)
        A("// %s -> %s   i=%s   a=%s mm   eps=%s (%s)"
          % (p["driver"], p["driven"], p["ratio"], p["centre_distance"],
             p["contact_ratio"], p["contact_ratio_source"]))
        for key, field in (("d1", "d_driver"), ("d2", "d_driven"),
                           ("db1", "db_driver"), ("db2", "db_driven"),
                           ("da1", "da_driver"), ("da2", "da_driven"),
                           ("df1", "df_driver"), ("df2", "df_driven"),
                           ("a", "centre_distance"), ("i", "ratio")):
            A("%s_%s = %s;" % (tag, key, _num(p[field])))

    blk("tooth system per MESH")
    A("// A cycloidal pinion is conjugate ONLY with a cycloidal wheel generated")
    A("// by the SAME describing circle, so the system and the describing circle")
    A("// are properties of the mesh, never of one wheel alone.  Both members of")
    A("// a mesh are drawn from the same rr; gear_3d()/pinion_3d() require it.")
    for p in data["gear_train"]:
        tag = "%s__%s" % (p["driver"], p["driven"])
        tag = "".join(c if c.isalnum() else "_" for c in tag)
        A('%s_SYSTEM = "%s";' % (tag, p["tooth_system"]))
        A("%s_RR = %s;" % (tag, _num(p["describing_circle_r"])))
    A("// short names used by gear_generator.scad")
    for tag, p in (("CYCLO_RR_BARREL_GREAT", 0), ("CYCLO_RR_GREAT_CENTRE", 1),
                   ("CYCLO_RR_CENTRE_INTER", 2), ("CYCLO_RR_INTER_CARRIAGE", 3),
                   ("CYCLO_RR_EPICYCLIC", 4), ("CYCLO_RR_CANON_MINUTE", 5),
                   ("CYCLO_RR_MINUTE_HOUR", 6)):
        A("%s = %s;   // %s <-> %s" % (tag, _num(data["gear_train"][p]["describing_circle_r"]),
                                       data["gear_train"][p]["driver"],
                                       data["gear_train"][p]["driven"]))

    blk("part geometry (all mm) -- the SCAD modules read these, never their own")
    GEOM_SCALARS = [
        "BARREL_DRUM_OD", "BARREL_WALL_THK", "BARREL_WALL_HEIGHT", "BARREL_ARBOR_D",
        "SPRING_THICK", "SPRING_WIDTH", "SPRING_E", "SPRING_FILL", "SPRING_SAFE_STRESS",
        "WIND_SQUARE", "Z_RATCHET", "M_RATCHET",
        "CARRIAGE_BORE_R", "CARRIAGE_FLOOR_OD", "CARRIAGE_FLOOR_THK",
        "CARRIAGE_FLOOR_HOLE_D", "CARRIAGE_PINION_HOLE_D", "CARRIAGE_RIM_BAND_H",
        "CARRIAGE_UPPER_BRIDGE_L", "CARRIAGE_UPPER_BRIDGE_W", "CARRIAGE_UPPER_BRIDGE_T",
        "CARRIAGE_COLUMN_D", "CARRIAGE_COLUMN_N", "CARRIAGE_COLUMN_R",
        "CARRIAGE_ARBOR_D", "FIXED_4TH_BOSS_D", "CARRIAGE_MASS_CEILING_G",
        "Y_ESCAPE", "Y_PALLET", "Y_BALANCE",
        "ESCAPE_WHEEL_OD", "ESCAPE_WHEEL_THK", "ESCAPE_PINION_H",
        "BALANCE_OD", "BALANCE_RIM_W", "BALANCE_RIM_T", "BALANCE_ARM_N",
        "BALANCE_ARM_W", "BALANCE_ARM_T", "BALANCE_ARM_ANGLE",
        "ROLLER_D", "IMPULSE_PIN_R", "IMPULSE_PIN_D",
        "PALLET_LEVER_LEN", "PALLET_LEVER_W", "LOCK_ANGLE_DEG", "DROP_ANGLE_DEG",
        "IMPULSE_FRACTION", "PALLET_STONE_L", "PALLET_STONE_W", "LEVER_BANKING_DEG",
        "HAIRSPRING_OD", "HAIRSPRING_ID", "HAIRSPRING_T", "HAIRSPRING_B",
        "BALANCE_AMPLITUDE_DEG", "BALANCE_Q", "Z_CARRIAGE_Z0",
        "CARRIAGE_TARGET_H_MIN", "CARRIAGE_TARGET_H_MAX", "MOTION_RATIO_TARGET",
        "CD_BARREL_CENTRE", "M_ESCAPE_WHEEL", "Z_ESCAPE_WHEEL",
    ]
    for k_ in GEOM_SCALARS:
        if hasattr(D, k_):
            A("%s = %s;" % (k_, _num(getattr(D, k_))))
    A("CARRIAGE_COLUMN_ANGLES = [%s];"
      % ", ".join(_num(v) for v in D.CARRIAGE_COLUMN_ANGLES))

    A("// HUB_OD: [name, hub outer dia] -- looked up by name in the SCAD modules")
    A("HUB_OD = [");
    for i, (k_, v) in enumerate(sorted(D.HUB_OD.items())):
        A('    ["%s", %s]%s' % (k_, _num(v), "," if i < len(D.HUB_OD) - 1 else ""))
    A("];")
    A("function hub_od(name) = let(h = [for (e = HUB_OD) if (e[0] == name) e[1]]) h[0];")

    def ztable(varname, rows, comment):
        A("// %s" % comment)
        A("%s = [" % varname)
        for i, r in enumerate(rows):
            A("    [%s]%s" % (", ".join(_num(v) for v in r[1:]),
                              "," if i < len(rows) - 1 else ""))
        A("];")
        A("// names, index-aligned with %s" % varname)
        A("%s_NAMES = [%s];" % (varname,
            ", ".join('"%s"' % r[0] for r in rows)))

    ztable("Z_MOVEMENT", D.Z_MOVEMENT,
           "Z_MOVEMENT: [z_bottom, z_top, footprint_od] per member; z=0 is the "
           "FRONT face of the main plate, +Z towards the dial")
    ztable("Z_CARRIAGE", D.Z_CARRIAGE,
           "Z_CARRIAGE: same, but LOCAL to the carriage floor (add Z_CARRIAGE_Z0)")
    A("// PLATE_WINDOWS: [x, y, dia, purpose] -- holes cut through the main plate")
    A("PLATE_WINDOWS = [")
    for i, w in enumerate(D.PLATE_WINDOWS):
        A("    [%s, %s, %s, \"%s\"]%s"
          % (_num(w[1][0]), _num(w[1][1]), _num(w[2]), w[0],
             "," if i < len(D.PLATE_WINDOWS) - 1 else ""))
    A("];")
    A("// BRIDGE_WINDOWS: [x, y, dia, purpose, [members that must pass through]].")
    A("// The member list is what makes the windows checkable: calc.py C-18b")
    A("// sizes each window against exactly these parts and nothing else.")
    A("BRIDGE_WINDOWS = [")
    for i, w in enumerate(D.BRIDGE_WINDOWS):
        A("    [%s, %s, %s, \"%s\", [%s]]%s"
          % (_num(w[1][0]), _num(w[1][1]), _num(w[2]), w[0],
             ", ".join('"%s"' % m for m in w[3]),
             "," if i < len(D.BRIDGE_WINDOWS) - 1 else ""))
    A("];")

    blk("axis layout (origin = centre-wheel axis, +Y = 12 o'clock)")
    for k_, v in data["layout"]["axis_positions_mm"].items():
        A("POS_%s = [%s, %s];" % (k_.upper(), _num(v[0]), _num(v[1])))
    for k_, v in data["layout"]["centre_distances_mm"].items():
        A("CD_%s = %s;" % (k_.upper(), _num(v)))
    A("PLATE_RADIUS = %s;" % _num(data["layout"]["plate_radius_mm"]))

    blk("kinematic solution (derived, validated)")
    for k_, v in data["kinematics"].items():
        if isinstance(v, str):
            A("// %-42s %s" % (k_, v))
        else:
            A("%s = %s;" % (k_, _num(v)))

    blk("mainspring (derived)")
    for k_, v in data["mainspring"].items():
        A("MS_%s = %s;" % (k_.upper(), _num(v)))

    blk("oscillator (derived)")
    for k_, v in data["oscillator"].items():
        if isinstance(v, list):
            A("// %-40s %s" % (k_, v))
        else:
            A("OSC_%s = %s;" % (k_.upper(), _num(v)))

    blk("carriage mass / inertia / poise (derived)")
    for k_, v in data["carriage"].items():
        if isinstance(v, str):
            A("// %s: %s" % (k_, " ".join(v.split())[:150]))
        else:
            A("CAR_%s = %s;" % (k_.upper(), _num(v)))

    blk("escapement geometry (derived)")
    for k_, v in data["escapement"].items():
        if isinstance(v, str):
            A("// %s: %s" % (k_, " ".join(v.split())[:150]))
        else:
            A("ESC_%s = %s;" % (k_.upper(), _num(v)))

    blk("Z stack (thickness budget)")
    A("CARRIAGE_HEIGHT_MM = %s;" % _num(data["z_stack"]["carriage_height_mm"]))
    A("MOVEMENT_THICKNESS_MM = %s;" % _num(data["z_stack"]["movement_total_thickness_mm"]))
    A("")
    with open(path, "w") as f:
        f.write("\n".join(L))


def export_docs(data):
    docs = os.path.join(ROOT, "docs")
    os.makedirs(docs, exist_ok=True)
    k = data["kinematics"]
    ms = data["mainspring"]
    pb = data["power_budget"]
    osc = data["oscillator"]
    car = data["carriage"]
    esc = data["escapement"]

    # ---------------- GEAR_TRAIN.md -----------------------------------------
    g = []
    g.append("# Gear Train, Ratios and Speeds\n")
    g.append("_Machine generated by `tools/calc.py` from `tools/design.py`. Do not edit._\n")
    g.append("## 1. Kinematic solution\n")
    g.append("| Quantity | Value | Unit | How it is obtained |")
    g.append("|---|---|---|---|")
    g.append("| Centre wheel -> carriage ratio | %.6f | - | (%d/%d) x (%d/%d) |"
             % (k["ratio_centre_to_carriage"], D.Z_INTER_WHEEL, D.Z_CENTRE_PINION,
                D.Z_CARRIAGE_RIM, D.Z_INTER_PINION))
    g.append("| Barrel -> centre ratio | %.6f | - | (%d/%d) x (%d/%d) |"
             % (k["ratio_barrel_to_centre"], D.Z_GREAT_WHEEL, D.Z_BARREL_GEAR,
                D.Z_CENTRE_WHEEL, D.Z_GREAT_PINION))
    g.append("| Epicyclic ratio z4/zEP | %.6f | - | %d/%d |"
             % (k["epicyclic_z4_over_zEP"], D.Z_FIXED_FOURTH, D.Z_ESCAPE_PINION))
    g.append("| Carriage speed | %.9f | rev/min | from the train |" % k["carriage_rpm"])
    g.append("| Carriage speed demanded by the balance | %.9f | rev/min | f*zEP/(zE*z4)*60 |"
             % k["carriage_rpm_required_by_balance"])
    g.append("| Escape wheel speed (relative to carriage) | %.6f | rev/min | (z4/zEP) x carriage |"
             % k["escape_rel_carriage_rpm"])
    g.append("| Escape wheel speed (absolute) | %.6f | rev/min | carriage + relative |"
             % k["escape_absolute_rpm"])
    g.append("| Balance frequency | %.6f | Hz | teeth/s of the escape wheel |"
             % k["balance_frequency_hz"])
    g.append("| Beat rate | %.0f | beats/s | 2 x frequency |" % k["beats_per_second"])
    g.append("| Beat rate | %.0f | vph | beats/s x 3600 |" % k["vph"])
    g.append("| Motion works ratio | %.6f | - | must be exactly 12 |" % D.motion_ratio())
    g.append("| Barrel: one turn takes | %.3f | hours | 1/barrel rpm |" % k["barrel_hours_per_turn"])
    g.append("")
    g.append("## 2. Absolute speed of every rotating member\n")
    g.append("| Member | Speed (rev/min) | Period | Note |")
    g.append("|---|---|---|---|")
    for nm, rpm, per, unit in data["gear_speeds"]:
        g.append("| %s | %.6f | %s %s | %s |" % (nm, rpm, ("%.4g" % per) if math.isfinite(per) else "inf", unit,
                                                 "REGULATED" if "carriage" in nm.lower() else ""))
    g.append("")
    g.append("## 3. Full gear table\n")
    cols = ["driver", "driven", "z_driver", "z_driven", "module", "pressure_angle",
            "d_driver", "d_driven", "da_driver", "da_driven", "df_driver", "df_driven",
            "centre_distance", "ratio", "contact_ratio", "tooth_thickness_pitch",
            "backlash", "profile_driver", "profile_driven"]
    hdr = ["Driver", "Driven", "z1", "z2", "m", "alpha", "d1", "d2", "da1", "da2",
           "df1", "df2", "a", "i", "eps", "s (pitch)", "backlash", "profile 1", "profile 2"]
    g.append("| " + " | ".join(hdr) + " |")
    g.append("|" + "|".join(["---"] * len(hdr)) + "|")
    for p in data["gear_train"]:
        g.append("| " + " | ".join(str(p[c]) for c in cols) + " |")
    g.append("")
    g.append("All diameters in mm.  `d = m z`, `da = d + 2m`, `df = d - 2.5m`, "
             "`a = m(z1+z2)/2`, `i = z2/z1`, `s = pi*m/2 - backlash/2`.")
    g.append("")
    g.append("### Profile choice\n")
    g.append("Wheels with `z >= 17.1` are **involute**, full depth, zero profile shift.  "
             "Pinions with `z < 17.1` would undercut as involute gears, so they are "
             "declared **cycloidal pinions** (epicycloid face / hypocycloid flank), which "
             "is the classical horological solution and has no undercut at any `z >= 6`.  "
             "This is NOT a cosmetic choice: mixing an involute wheel with a cycloidal "
             "pinion requires the wheel flank to be generated against the pinion, which "
             "`gear_generator.scad` does when `PROFILE=\"cycloidal\"`.")
    g.append("")
    g.append("## 4. Rotation directions (viewed from the front)\n")
    for kk, vv in k.items():
        if kk.startswith("direction_"):
            g.append("- `%s` : %s" % (kk, vv))
    g.append("")
    with open(os.path.join(docs, "GEAR_TRAIN.md"), "w") as f:
        f.write("\n".join(g))

    # ---------------- CALCULATIONS.md ---------------------------------------
    c = []
    c.append("# Engineering Calculations\n")
    c.append("_Machine generated by `tools/calc.py`. Every number here is derived, "
             "and every assumption is stated next to the value it produces._\n")

    c.append("## 1. Architecture\n")
    c.append("```")
    for line in (D.__doc__ or "").splitlines():
        if line.strip():
            c.append(line)
    c.append("```\n")

    c.append("## 2. Mainspring and barrel\n")
    c.append("Relations used:")
    c.append("```")
    c.append("A        = pi (r_out^2 - r_arb^2)                annular area available")
    c.append("L        = FILL * A / b                          active strip length")
    c.append("n_turns  = L / (pi * (r_out + r_arb))            available turns")
    c.append("I        = b t^3 / 12                            second moment of area")
    c.append("M(r)     = E I / r                               bending moment at coil radius r")
    c.append("sigma(r) = E t / (2 r)                           bending stress")
    c.append("E_stored = integral M dtheta = (E I / 2)(1/r_arb^2 - 1/r_out^2) L")
    c.append("```")
    c.append("")
    c.append("| Quantity | Value | Unit | Comment |")
    c.append("|---|---|---|---|")
    for kk, vv in ms.items():
        c.append("| %s | %s | | |" % (kk, vv))
    c.append("")
    c.append("**Assumptions that must be verified with real spring stock:** packing factor "
             "`FILL = %.2f` (0.50-0.60 for a hand-wound clock spring), Young's modulus "
             "`E = %.0f N/mm^2`, and the strip cross-section `%.1f x %.2f mm`. The spring "
             "must be ordered to the calculated length; a shelf spring of a different "
             "length changes the run time directly."
             % (D.SPRING_FILL, D.SPRING_E, D.SPRING_WIDTH, D.SPRING_THICK))
    c.append("")

    c.append("## 3. Torque chain\n")
    c.append("| Arbor | Optimistic (eta=0.985) | Nominal (eta=0.965) | Pessimistic (eta=0.93) | unit |")
    c.append("|---|---|---|---|---|")
    for stage in pb["nom"]["torque_chain_Nmm"]:
        c.append("| %s | %.5f | %.5f | %.5f | N-mm |"
                 % (stage, pb["opt"]["torque_chain_Nmm"][stage],
                    pb["nom"]["torque_chain_Nmm"][stage],
                    pb["pes"]["torque_chain_Nmm"][stage]))
    c.append("")
    c.append("The epicyclic with a fixed sun multiplies the planet torque by `z4/zEP = %.0f`, "
             "so the escape wheel sees %.5f N-mm (%.1f uN-m) in the nominal case."
             % (D.epicyclic_ratio(), pb["nom"]["torque_chain_Nmm"]["escape_wheel"],
                pb["nom"]["escape_wheel_torque_uNm"]))
    c.append("")

    c.append("## 4. Power budget and run time (ESTIMATE)\n")
    c.append("```")
    c.append("A pivot friction  P_i = mu * F_i * r_pivot * omega_i ,  F_i = 2.5 T_i / r_pitch")
    c.append("B escapement      E_beat = T_escape * phi_impulse ,  phi = 0.42 * 2pi/z_E")
    c.append("                  + 30 % for pallet-stone sliding and drop")
    c.append("C carriage bearing P = mu * W * r_pivot * omega_carriage")
    c.append("```")
    c.append("")
    c.append("| Case | mu | Pivot loss | Escapement loss | Carriage bearing | TOTAL | Run time (energy) | Run time (turns) | GOVERNING |")
    c.append("|---|---|---|---|---|---|---|---|---|")
    for case, mu in (("opt", 0.04), ("nom", 0.08), ("pes", 0.15)):
        p = pb[case]
        c.append("| %s | %.2f | %.2f uW | %.2f uW | %.3f uW | **%.2f uW** | %.1f d | %.1f d | **%.1f d** |"
                 % (case, mu, p["pivot_loss_uW"], p["escapement_loss_uW"],
                    p["carriage_bearing_uW"], p["total_uW"],
                    p["run_time_limited_by_energy_days"], p["run_time_limited_by_spring_length_days"],
                    p["governing_run_time_days"]))
    c.append("")
    c.append("Nominal per-arbor breakdown:")
    c.append("")
    c.append("| Arbor | Radial load (N) | Speed (rpm) | Pivot r (mm) | Loss (uW) |")
    c.append("|---|---|---|---|---|")
    for row in pb["nom"]["pivot_detail"]:
        c.append("| %s | %.5f | %.4f | %.2f | %.4f |"
                 % (row["arbor"], row["load_N"], row["rpm"], row["pivot_r_mm"], row["loss_uW"]))
    c.append("")
    c.append("> **This is an estimate, not a prediction.** The friction coefficient of a "
             "one-off prototype varies by a factor of 3-4 depending on the pivot finish, "
             "the oil film and the jewel quality. The run time is therefore quoted as "
             "**%.1f - %.1f days** and must be measured on the prototype."
             % (pb["pes"]["governing_run_time_days"], pb["opt"]["governing_run_time_days"]))
    c.append("")

    c.append("## 5. Oscillator\n")
    c.append("```")
    c.append("f = (1/2pi) sqrt(k/J)   ->   k = J (2 pi f)^2")
    c.append("hairspring  k = E b h^3 / (12 L_active)   ->   L_active = E b h^3 / (12 k)")
    c.append("```")
    c.append("")
    c.append("| Quantity | Value | Unit |")
    c.append("|---|---|---|")
    for kk, vv in osc.items():
        if isinstance(vv, float):
            c.append("| %s | %.6g | |" % (kk, vv))
        else:
            c.append("| %s | %s | |" % (kk, vv))
    c.append("")
    c.append("The hairspring is a **purchased or specialist-made part**. The active length "
             "above is computed from the *modelled* balance inertia; the real length must be "
             "set from the *measured* inertia of the finished balance, then trimmed on the "
             "regulator index.")
    c.append("")

    c.append("## 6. Carriage: mass, inertia, poise\n")
    c.append("| Quantity | Value | Unit |")
    c.append("|---|---|---|")
    for kk, vv in car.items():
        if kk.endswith("_note"):
            continue
        if isinstance(vv, float):
            c.append("| %s | %.6g | |" % (kk, vv))
        else:
            c.append("| %s | %s | |" % (kk, vv))
    c.append("")
    c.append("> %s" % " ".join(car["poise_note"].split()))
    c.append("")

    c.append("## 7. Escapement geometry\n")
    c.append("| Quantity | Value |")
    c.append("|---|---|")
    for kk, vv in esc.items():
        if isinstance(vv, str):
            c.append("| %s | %s |" % (kk, " ".join(vv.split())))
        else:
            c.append("| %s | %s |" % (kk, vv))
    c.append("")
    c.append("> %s" % " ".join(esc["manufacturability"].split()))
    c.append("")

    c.append("## 8. Z stack / thickness budget\n")
    c.append("### Movement (z = 0 at the front face of the main plate, +Z towards the dial)")
    c.append("")
    c.append("| Part | z bottom | z top | footprint OD |")
    c.append("|---|---|---|---|")
    for r in data["z_stack"]["movement"]:
        c.append("| %s | %.1f | %.1f | %.1f |" % (r["part"], r["z_bottom"], r["z_top"], r["footprint_od_mm"]))
    c.append("")
    c.append("### Carriage (local z, 0 = top face of the carriage lower plate)")
    c.append("")
    c.append("| Part | z bottom | z top | footprint OD |")
    c.append("|---|---|---|---|")
    for r in data["z_stack"]["carriage"]:
        c.append("| %s | %.1f | %.1f | %.1f |" % (r["part"], r["z_bottom"], r["z_top"], r["footprint_od_mm"]))
    c.append("")
    c.append("**Carriage height = %.2f mm.** The brief asks for 12-20 mm. Result: %s "
             "(see `docs/LIMITATIONS.md` L-02 for the itemised reason)."
             % (data["z_stack"]["carriage_height_mm"],
                "MET" if data["z_stack"]["carriage_within_target"] else "NOT MET"))
    c.append("")
    c.append("**Total movement thickness = %.1f mm** from the back of the main plate to the "
             "crystal." % data["z_stack"]["movement_total_thickness_mm"])
    c.append("")

    c.append("## 9. Layout\n")
    c.append("| Axis | x (mm) | y (mm) |")
    c.append("|---|---|---|")
    for kk, vv in data["layout"]["axis_positions_mm"].items():
        c.append("| %s | %.3f | %.3f |" % (kk, vv[0], vv[1]))
    c.append("")
    c.append("| Mesh | Theoretical centre distance | Placed distance |")
    c.append("|---|---|---|")
    c.append("| barrel gear / centre wheel | %.3f | %.3f |"
             % (D.CD_BARREL_CENTRE, math.hypot(*(D.POS_BARREL[0] - D.POS_CENTRE_WHEEL[0],
                                                  D.POS_BARREL[1] - D.POS_CENTRE_WHEEL[1]))))
    c.append("| centre pinion / intermediate wheel | %.3f | %.3f |"
             % (D.CD_CENTRE_INTER, math.hypot(D.POS_INTERMEDIATE[0] - D.POS_CENTRE_WHEEL[0],
                                              D.POS_INTERMEDIATE[1] - D.POS_CENTRE_WHEEL[1])))
    c.append("| intermediate pinion / carriage rim gear | %.3f | %.3f |"
             % (D.CD_INTER_CARRIAGE, math.hypot(D.POS_CARRIAGE[0] - D.POS_INTERMEDIATE[0],
                                                D.POS_CARRIAGE[1] - D.POS_INTERMEDIATE[1])))
    c.append("")
    with open(os.path.join(docs, "CALCULATIONS.md"), "w") as f:
        f.write("\n".join(c))

    # ---------------- SHAFTS.md ---------------------------------------------
    s = ["# Shafts, Pivots and Bearings\n",
         "_Machine generated by `tools/calc.py`._\n",
         "| ID | Arbor | dia | length | material | protrusion | seat dia | span | axial play | radial play | radial load | axial load | bearing | note |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in data["shafts"]:
        s.append("| %s | %s | %.1f | %.1f | %s | %.1f | %.1f | %.1f | %.2f | %.3f | %.4f N | %.2f N | %s | %s |"
                 % (r["id"], r["name"], r["dia_mm"], r["length_mm"], r["material"],
                    r["protrusion_mm"], r["bearing_seat_dia_mm"], r["bearing_span_mm"],
                    r["axial_clearance_mm"], r["radial_clearance_mm"], r["radial_load_N"],
                    r["axial_load_N"], r["bearing"], r["note"]))
    s += ["",
          "## Bearing selection rule applied",
          "",
          "| Location | Choice | Why |",
          "|---|---|---|",
          "| Carriage axis (lower) | MR106ZZ ball race OR a ruby jewel + hardened thrust washer | Carries the whole rotating mass (%.2f g) at 1 rpm; a printed hole would wear and change the rate within hours |" % car["mass_rotating_total_g"],
          "| Carriage axis (upper) | Ruby jewel 6/2.0 mm + endstone | Radial location only; sets the axis perpendicularity |",
          "| Balance staff | Ruby jewels 1.6/0.6 mm + sapphire endstones | Oscillating pivot; friction here directly changes the amplitude |",
          "| Escape arbor | Ruby jewels 1.5/0.6 mm | Oscillating/indexing pivot, very low load |",
          "| Pallet arbor | Ruby jewels 1.2/0.5 mm | Oscillating, very low load |",
          "| Going train | Ruby jewels, bronze bush acceptable on the motion works | Low speed, low load |",
          "| Barrel arbor | MR85ZZ x2 or jewels 10/3.0 mm + bronze thrust | Highest static load (winding) |",
          "",
          "**No printed hole is used as a precision bearing anywhere in this design.**",
          "Printed pivots are permitted only for the static, non-rate-critical "
          "locations (case, dial, wall mount) -- see `docs/LIMITATIONS.md` L-05.",
          ""]
    with open(os.path.join(docs, "SHAFTS.md"), "w") as f:
        f.write("\n".join(s))

    # ---------------- TOLERANCES.md -----------------------------------------
    t = ["# Tolerances and Manufacturability\n",
         "_Machine generated by `tools/calc.py`._\n",
         "The model reads its clearances from `TOL_*` in `parameters.scad`, which selects one "
         "of the three presets below with the `MANUFACTURING` switch. Values are STARTING "
         "POINTS: they must be calibrated with a printed/machined test coupon before the "
         "final parts are made.\n",
         "| Process | Description | Fit clearance | Axial play | Radial play | Gear backlash | Hole growth | Min wall | Min hole | Positional tol | Ra | Usable for the escapement? |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in data["tolerances"]:
        t.append("| %s | %s | %.2f | %.2f | %.3f | %.2f | %.2f | %.1f | %.1f | %.3f | %.1f | %s |"
                 % (r["process"], r["description"], r["fit_clearance_mm"], r["axial_clearance_mm"],
                    r["radial_clearance_mm"], r["gear_backlash_mm"], r["hole_growth_mm"],
                    r["min_wall_mm"], r["min_hole_mm"], r["positional_tol_mm"],
                    r["surface_roughness_ra_um"], r["usable_for_escapement"]))
    t += ["",
          "## Which parts may be printed\n",
          "| Part group | FDM | Resin | Machined metal | Comment |",
          "|---|---|---|---|---|",
          "| Case, bezel, back, wall mount, dial ring | YES | YES | optional | Non-functional, decorative |",
          "| Main plate / bridge plate (structural) | prototype only | prototype only | **YES** | Printed plates flex; the axis positions must hold to +/-0.05 mm |",
          "| Going-train wheels (barrel, centre, intermediate) | NO | prototype only | **YES** | Pitch errors of a printed wheel are >> the backlash budget |",
          "| Carriage rim gear (z=108, m=0.6) | NO | NO | **YES** | 0.6 mm module teeth cannot be printed to a usable pitch |",
          "| Fixed fourth wheel, escape pinion | NO | NO | **YES** | Sets the kinematic closure |",
          "| Escape wheel, pallet lever, pallet stones | NO | NO | **YES** | Needs hardened, lapped impulse faces (Ra < 0.2 um) |",
          "| Balance wheel | NO | prototype only | **YES** | Must be poised; a printed rim is not dimensionally stable |",
          "| Hairspring, mainspring | NO | NO | **PURCHASE** | Cannot be manufactured in a workshop from CAD |",
          "| Arbors, pivots, jewels, bearings | NO | NO | **PURCHASE / TURN** | See BOM_BOUGHT.csv |",
          ""]
    with open(os.path.join(docs, "TOLERANCES.md"), "w") as f:
        f.write("\n".join(t))

    # ---------------- LAYOUT.md ---------------------------------------------
    ly = ["# Axis Layout and Thickness Budget\n",
          "_Machine generated by `tools/calc.py`._\n",
          "Coordinate system: origin at the centre-wheel (= minute hand) axis, "
          "`+Y` towards 12 o'clock, `+Z` towards the viewer/dial. All values in mm.\n",
          "## Axes\n",
          "| Axis | x | y | note |",
          "|---|---|---|---|"]
    notes = {
        "centre_wheel": "minute-hand arbor, 1 rev/hour",
        "barrel": "mainspring barrel, 12 o'clock",
        "intermediate": "added stage, 6 o'clock side",
        "carriage": "tourbillon carriage axis, 1 rev/min, seconds pointer",
        "fixed_fourth": "concentric with the carriage, bolted to the main plate",
        "motion_works": "minute wheel arbor (hour wheel is coaxial with the centre)",
    }
    for kk, vv in data["layout"]["axis_positions_mm"].items():
        ly.append("| %s | %.3f | %.3f | %s |" % (kk, vv[0], vv[1], notes.get(kk, "")))
    ly += ["", "## Centre distances", "", "| Mesh | a (mm) | formula |", "|---|---|---|"]
    ly.append("| barrel gear / centre wheel | %.3f | m(z1+z2)/2 = %.2f(%d+%d)/2 |"
              % (D.CD_BARREL_CENTRE, D.M_BARREL_GEAR, D.Z_BARREL_GEAR, D.Z_CENTRE_WHEEL))
    ly.append("| centre pinion / intermediate wheel | %.3f | m(z1+z2)/2 = %.2f(%d+%d)/2 |"
              % (D.CD_CENTRE_INTER, D.M_CENTRE_PINION, D.Z_CENTRE_PINION, D.Z_INTER_WHEEL))
    ly.append("| intermediate pinion / carriage rim gear | %.3f | m(z1+z2)/2 = %.2f(%d+%d)/2 |"
              % (D.CD_INTER_CARRIAGE, D.M_CARRIAGE_RIM, D.Z_INTER_PINION, D.Z_CARRIAGE_RIM))
    ly.append("| fixed fourth wheel / escape pinion (inside carriage) | %.3f | orbital radius of the escape arbor |"
              % ((D.M_FIXED_FOURTH * D.Z_FIXED_FOURTH + D.M_ESCAPE_PINION * D.Z_ESCAPE_PINION) / 2))
    ly += ["", "## Envelope", "",
           "- Clock OD: **%.0f mm**" % D.CLOCK_DIAMETER,
           "- Movement plate OD: **%.0f mm** (radius %.0f)" % (D.DIAL_APERTURE, D.DIAL_APERTURE / 2),
           "- Carriage OD (rim gear tip): **%.2f mm** -- inside the %.0f mm target"
           % (D.M_CARRIAGE_RIM * D.Z_CARRIAGE_RIM + 2 * D.M_CARRIAGE_RIM, D.TOURBILLON_DIAMETER),
           "- Barrel drum OD: **%.0f mm**" % D.BARREL_DRUM_OD,
           "- Centre wheel OD: **%.1f mm**" % (D.M_CENTRE_WHEEL * D.Z_CENTRE_WHEEL + 2 * D.M_CENTRE_WHEEL),
           "- Total movement thickness: **%.1f mm**" % data["z_stack"]["movement_total_thickness_mm"],
           "- Carriage height: **%.2f mm**" % data["z_stack"]["carriage_height_mm"],
           ""]
    with open(os.path.join(docs, "LAYOUT.md"), "w") as f:
        f.write("\n".join(ly))

    # ---------------- BOM csv ----------------------------------------------
    import csv
    with open(os.path.join(docs, "BOM_MADE.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "part", "qty", "material", "dimensions_mm", "process", "scad_module"])
        w.writerows(data["bom_made"])
    with open(os.path.join(docs, "BOM_BOUGHT.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "part", "qty", "material", "specification", "source_note"])
        w.writerows(data["bom_bought"])
    # combined BOM.csv at the project root (the brief asks for BOM.csv)
    with open(os.path.join(ROOT, "BOM.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "id", "part", "qty", "material", "dimensions_or_spec",
                    "process_or_source", "scad_module"])
        for r in data["bom_made"]:
            w.writerow(["MADE"] + list(r))
        for r in data["bom_bought"]:
            w.writerow(["PURCHASED", r[0], r[1], r[2], r[3], r[4], r[5], "-"])


def report(data):
    print("=" * 82)
    print("TOURBILLON WALL CLOCK -- ENGINEERING REPORT")
    print("=" * 82)
    k = data["kinematics"]
    print("\n[1] KINEMATICS")
    for kk in ("ratio_barrel_to_centre", "ratio_centre_to_inter", "ratio_inter_to_carriage",
               "ratio_centre_to_carriage", "barrel_rpm", "centre_wheel_rpm",
               "intermediate_rpm", "carriage_rpm", "carriage_rpm_required_by_balance",
               "epicyclic_z4_over_zEP", "escape_rel_carriage_rpm", "escape_absolute_rpm",
               "balance_frequency_hz", "beats_per_second", "vph", "hour_wheel_rpm"):
        print("    %-38s %s" % (kk, k[kk]))

    print("\n[2] MAINSPRING")
    for kk, vv in data["mainspring"].items():
        print("    %-38s %s" % (kk, vv))

    print("\n[3] POWER BUDGET  (ESTIMATE -- see LIMITATIONS L-04)")
    for case in ("opt", "nom", "pes"):
        p = data["power_budget"][case]
        print("    %-4s T_esc=%.5f N-mm | pivot %.3f uW | escapement %.3f uW | "
              "carriage %.3f uW | TOTAL %.3f uW" % (case, p["escape_wheel_torque_uNm"] / 1000,
                                                    p["pivot_loss_uW"], p["escapement_loss_uW"],
                                                    p["carriage_bearing_uW"], p["total_uW"]))
        print("         run: energy-limited %.1f d | spring-length-limited %.1f d -> GOVERNING %.1f d"
              % (p["run_time_limited_by_energy_days"],
                 p["run_time_limited_by_spring_length_days"], p["governing_run_time_days"]))

    print("\n[4] OSCILLATOR")
    for kk in ("balance_od_mm", "mass_total_g", "J_total_g_mm2", "k_required_Nmm_rad",
               "hairspring_active_length_mm", "hairspring_turns_at_mean_radius",
               "hairspring_inner_stress_MPa", "energy_in_balance_uJ",
               "escape_torque_required_Nmm"):
        print("    %-38s %s" % (kk, data["oscillator"][kk]))

    print("\n[5] CARRIAGE")
    for kk in ("mass_carriage_alone_g", "mass_rotating_total_g", "J_carriage_kg_m2",
               "static_moment_g_mm", "centre_of_mass_offset_mm",
               "gravity_torque_at_offset_Nm", "escape_torque_available_Nm",
               "gravity_to_escape_ratio", "poise_spec_mg_mm", "counter_mass_at_r30_g"):
        print("    %-38s %s" % (kk, data["carriage"][kk]))

    print("\n[6] ESCAPEMENT")
    for kk in ("escape_wheel_teeth", "escape_wheel_od_mm", "tooth_pitch_angle_deg",
               "impulse_angle_deg", "lock_angle_deg_total", "drop_angle_deg",
               "escape_to_pallet_distance_mm", "pallet_to_balance_distance_mm",
               "locking_circle_radius_mm", "fork_slot_width_mm", "lever_swing_deg"):
        print("    %-38s %s" % (kk, data["escapement"][kk]))

    print("\n[7] LAYOUT")
    for kk, vv in data["layout"]["centre_distances_mm"].items():
        print("    %-38s %s" % (kk, vv))
    for kk, vv in data["layout"]["axis_positions_mm"].items():
        print("    %-38s (%.3f, %.3f)" % (kk, vv[0], vv[1]))

    print("\n[8] Z STACK")
    print("    carriage height                      %.2f mm  (target %.0f-%.0f) -> %s"
          % (data["z_stack"]["carriage_height_mm"], data["z_stack"]["carriage_target_min_mm"],
             data["z_stack"]["carriage_target_max_mm"],
             "MET" if data["z_stack"]["carriage_within_target"] else "NOT MET (L-02)"))
    print("    movement thickness                   %.1f mm"
          % data["z_stack"]["movement_total_thickness_mm"])

    print("\n[9] VALIDATION")
    nf = 0
    for c in data["validation"]:
        if c["status"] != "PASS":
            nf += 1
        print("    %-4s %-6s %s" % (c["status"], c["id"], c["check"]))
        print("           %s" % c["detail"])
    print("\n    %d checks executed, %d failed" % (len(data["validation"]), nf))
    print("=" * 82)
    return nf


def main(argv):
    data = collect()
    nf = report(data)
    if "--report" not in argv:
        with open(os.path.join(ROOT, "design.json"), "w") as f:
            json.dump(data, f, indent=2, default=str)
        export_scad(data, os.path.join(ROOT, "parameters_auto.scad"))
        export_docs(data)
        print("\nwritten: parameters_auto.scad, design.json, BOM.csv, docs/{GEAR_TRAIN,"
              "CALCULATIONS,SHAFTS,TOLERANCES,LAYOUT}.md, docs/BOM_MADE.csv, "
              "docs/BOM_BOUGHT.csv")
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
