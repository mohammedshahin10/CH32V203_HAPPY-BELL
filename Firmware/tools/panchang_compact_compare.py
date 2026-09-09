"""Compare the compact CH32 astronomy model with the high-precision reference."""
import importlib.util
import math
import re
from datetime import date, timedelta
from pathlib import Path

REFERENCE = Path(r"C:\OfficeWorks\esp_bell_idf\test\panchang_reference.py")
GOLDEN_C = Path(r"C:\OfficeWorks\esp_bell_idf\main\driver\astro\tamil_panchangam.c")
spec = importlib.util.spec_from_file_location("panchang_reference", REFERENCE)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)

PI = math.pi
RAD = PI / 180.0
DEG = 180.0 / PI
GOLDEN_SOURCE = GOLDEN_C.read_text(encoding="utf-8")


def c_array(name):
    body = re.search(rf"\b{name}(?:\[\d*\])?\s*=\s*\{{(.*?)\}};",
                     GOLDEN_SOURCE, re.S).group(1)
    return [int(value) for value in re.findall(r"[-+]?\d+", body)]


def c_vp_array(name):
    body = re.search(rf"\b{name}\[\]\s*=\s*\{{(.*?)\}};",
                     GOLDEN_SOURCE, re.S).group(1)
    return [tuple(float(value) for value in row.split(','))
            for row in re.findall(r"\{([^{}]+)\}", body)]


MEL_D, MEL_M = c_array("mel_D"), c_array("mel_M")
MEL_MP, MEL_F, MEL_SL = c_array("mel_Mp"), c_array("mel_F"), c_array("mel_sl")
MLA_D, MLA_M = c_array("mla_D"), c_array("mla_M")
MLA_MP, MLA_F, MLA_SB = c_array("mla_Mp"), c_array("mla_F"), c_array("mla_sb")
VSOP_L = [c_vp_array(f"vsop_L{i}") for i in range(6)]
VSOP_R = [c_vp_array(f"vsop_R{i}") for i in range(3)]


def norm360(v):
    return v % 360.0


def norm180(v):
    v = norm360(v)
    return v - 360.0 if v > 180.0 else v


def golden_jde(jd):
    t = (jd - 2451545.0) / 36525.0
    year = 2000.0 + 100.0 * t
    if year <= 2050.0:
        y = year - 2000.0
        delta = 62.92 + 0.32217 * y + 0.005589 * y * y
    else:
        u = (year - 1820.0) / 100.0
        delta = -20.0 + 32.0 * u * u
    return jd + delta / 86400.0


def golden_sun_longitude(jd):
    jde = golden_jde(jd)
    tau = (jde - 2451545.0) / 365250.0
    powers = [1.0]
    for _ in range(5):
        powers.append(powers[-1] * tau)
    lon = sum(sum(a * math.cos(b + c * tau) for a, b, c in terms) * powers[i]
              for i, terms in enumerate(VSOP_L)) / 1.0e8
    radius = sum(sum(a * math.cos(b + c * tau) for a, b, c in terms) * powers[i]
                 for i, terms in enumerate(VSOP_R)) / 1.0e8
    lon = norm360(lon * DEG + 180.0)
    century = tau * 10.0
    lp = (lon - 1.397 * century - 0.00031 * century * century) * RAD
    lon += (-0.09033 + 0.03916 * (math.cos(lp) - math.sin(lp))) / 3600.0
    omega = norm360(125.04452 - 1934.136261 * century)
    lon += -17.20 * math.sin(omega * RAD) / 3600.0
    return norm360(lon - 20.4898 / (radius * 3600.0))


def golden_moon_position(jd):
    jde = golden_jde(jd)
    t = (jde - 2451545.0) / 36525.0
    t2, t3, t4 = t * t, t * t * t, t * t * t * t
    lp = norm360(218.3164477 + 481267.88123421 * t - 0.0015786 * t2 +
                 t3 / 538841.0 - t4 / 65194000.0)
    elong = norm360(297.8501921 + 445267.1114034 * t - 0.0018819 * t2 +
                    t3 / 545868.0 - t4 / 113065000.0)
    sun_m = norm360(357.5291092 + 35999.0502909 * t - 0.0001536 * t2 +
                    t3 / 24490000.0)
    moon_m = norm360(134.9633964 + 477198.8675055 * t + 0.0087414 * t2 +
                     t3 / 69699.0 - t4 / 14712000.0)
    arg_lat = norm360(93.2720950 + 483202.0175233 * t - 0.0036539 * t2 -
                      t3 / 3526000.0 + t4 / 863310000.0)
    a1, a2, a3 = norm360(119.75 + 131.849 * t), norm360(53.09 + 479264.290 * t), norm360(313.45 + 481266.484 * t)
    eccentricity = 1.0 - 0.002516 * t - 0.0000074 * t2
    sl = sb = 0.0
    for i in range(60):
        multiplier = eccentricity ** abs(MEL_M[i])
        angle = (MEL_D[i] * elong + MEL_M[i] * sun_m + MEL_MP[i] * moon_m + MEL_F[i] * arg_lat) * RAD
        sl += MEL_SL[i] * multiplier * math.sin(angle)
        multiplier = eccentricity ** abs(MLA_M[i])
        angle = (MLA_D[i] * elong + MLA_M[i] * sun_m + MLA_MP[i] * moon_m + MLA_F[i] * arg_lat) * RAD
        sb += MLA_SB[i] * multiplier * math.sin(angle)
    sl += 3958.0 * math.sin(a1 * RAD) + 1962.0 * math.sin((lp - arg_lat) * RAD) + 318.0 * math.sin(a2 * RAD)
    sb += (-2235.0 * math.sin(lp * RAD) + 382.0 * math.sin(a3 * RAD) +
           175.0 * math.sin((a1 - arg_lat) * RAD) + 175.0 * math.sin((a1 + arg_lat) * RAD) +
           127.0 * math.sin((lp - moon_m) * RAD) - 115.0 * math.sin((lp + moon_m) * RAD))
    omega = norm360(125.04452 - 1934.136261 * t)
    lon = lp + sl / 1.0e6 - 17.20 * math.sin(omega * RAD) / 3600.0
    return norm360(lon), sb / 1.0e6


def sin_small(degrees):
    degrees = norm180(degrees)
    if degrees > 90.0:
        degrees = 180.0 - degrees
    elif degrees < -90.0:
        degrees = -180.0 - degrees
    x = degrees * RAD
    x2 = x * x
    return x * (1.0 + x2 * (-0.16666667 + x2 * (0.008333331 - x2 * 0.000198409)))


def cos_small(degrees):
    return sin_small(degrees + 90.0)


def atan_unit(z):
    z2 = z * z
    return z * (0.9998660 + z2 * (-0.3302995 + z2 * (0.1801410 + z2 * (-0.0851330 + z2 * 0.0208351))))


def atan2_small(y, x):
    ax, ay = abs(x), abs(y)
    if not ax and not ay:
        return 0.0
    a = atan_unit(ay / ax) if ax >= ay else PI / 2.0 - atan_unit(ax / ay)
    if x < 0:
        a = PI - a
    return -a if y < 0 else a


def asin_small(x):
    x = max(-1.0, min(1.0, x))
    return atan2_small(x, math.sqrt(max(0.0, 1.0 - x * x)))


def acos_small(x):
    x = max(-1.0, min(1.0, x))
    return atan2_small(math.sqrt(max(0.0, 1.0 - x * x)), x)


def day_number(y, m, d):
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    return d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - yy // 100 + yy // 400 - 32045 - 2451545


def astro_day(y, m, d, utc_hour=0.0):
    return day_number(y, m, d) - 0.5 + utc_hour / 24.0


def ayanamsa(day):
    t = day / 36525.0
    return 23.855563 + 1.3965636 * t + 0.0000139 * t * t


def sun_longitude(day):
    g = norm360(357.5291 + 0.98560028 * day)
    q = norm360(280.459 + 0.98564736 * day)
    return norm360(q + 1.915 * sin_small(g) + 0.020 * sin_small(2 * g))


def moon_position(day):
    year_offset = day / 365.25
    day += (62.92 + 0.32217 * year_offset + 0.005589 * year_offset * year_offset) / 86400.0
    t = day / 36525.0
    t2 = t * t
    lp = norm360(218.3164477 + 13.1763964744 * day - 0.0015786 * t2)
    elong = norm360(297.8501921 + 12.1907491199 * day - 0.0018819 * t2)
    sun_m = norm360(357.5291092 + 0.98560028175 * day - 0.0001536 * t2)
    moon_m = norm360(134.9633964 + 13.0649929502 * day + 0.0087414 * t2)
    arg_lat = norm360(93.2720950 + 13.2293502401 * day - 0.0036539 * t2)
    eccentricity = 1.0 - 0.002516 * t - 0.0000074 * t2

    def term_sum(ds, ms, mps, fs, coeffs, count):
        total = 0.0
        for i in range(count):
            scale = eccentricity ** abs(ms[i])
            angle = ds[i] * elong + ms[i] * sun_m + mps[i] * moon_m + fs[i] * arg_lat
            total += round(coeffs[i] / 1000.0) * scale * sin_small(angle)
        return total * 0.001

    lon = (lp + term_sum(MEL_D, MEL_M, MEL_MP, MEL_F, MEL_SL, 30) +
           0.003958 * sin_small(119.75 + 131.849 * t))
    lat = term_sum(MLA_D, MLA_M, MLA_MP, MLA_F, MLA_SB, 20)
    return norm360(lon), lat


def sidereal(day):
    moon, _ = moon_position(day)
    return norm360(sun_longitude(day) - ayanamsa(day)), norm360(moon - ayanamsa(day))


def sun_event(y, m, d, lat, lon, tz, rising):
    base = astro_day(y, m, d, 0.0)
    adjustment = 0.0
    for _ in range(2):
        t = (base + adjustment) / 36525.0
        mean_lon = norm360(280.46646 + t * (36000.76983 + 0.0003032 * t))
        anomaly = 357.52911 + t * (35999.05029 - 0.0001537 * t)
        eccentricity = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
        omega = 125.04 - 1934.136 * t
        seconds = 21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))
        obliquity = 23.0 + (26.0 + seconds / 60.0) / 60.0 + 0.00256 * cos_small(omega)
        tan_half = sin_small(obliquity * 0.5) / cos_small(obliquity * 0.5)
        yy = tan_half * tan_half
        eq = 4.0 * DEG * (yy * sin_small(2.0 * mean_lon) -
                           2.0 * eccentricity * sin_small(anomaly) +
                           4.0 * eccentricity * yy * sin_small(anomaly) * cos_small(2.0 * mean_lon) -
                           0.5 * yy * yy * sin_small(4.0 * mean_lon) -
                           1.25 * eccentricity * eccentricity * sin_small(2.0 * anomaly))
        center = (sin_small(anomaly) * (1.914602 - t * (0.004817 + 0.000014 * t)) +
                  sin_small(2.0 * anomaly) * (0.019993 - 0.000101 * t) +
                  sin_small(3.0 * anomaly) * 0.000289)
        apparent_lon = mean_lon + center - 0.00569 - 0.00478 * sin_small(omega)
        decl = asin_small(sin_small(obliquity) * sin_small(apparent_lon)) * DEG
        h = ((sin_small(-0.7891071) - sin_small(lat) * sin_small(decl)) /
             (cos_small(lat) * cos_small(decl)))
        hour_angle = acos_small(h) * DEG
        delta = -lon + (-hour_angle if rising else hour_angle)
        utc_minutes = 720.0 + delta * 4.0 - eq
        if utc_minutes < 0.0:
            utc_minutes += 1440.0
        adjustment = utc_minutes / 1440.0
    return (utc_minutes / 60.0 + tz) % 24.0


def circular_minutes(a, b):
    d = abs(a - b) * 60.0
    return min(d, 1440.0 - d)


def moon_altitude(day, lat, lon, golden):
    if golden:
        moon_lon, moon_lat = golden_moon_position(day + 2451545.0)
        t = day / 36525.0
        seconds = 21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))
        eps = 23.0 + (26.0 + seconds / 60.0) / 60.0 + 0.00256 * math.cos((125.04 - 1934.136 * t) * RAD)
        lam, beta = moon_lon * RAD, moon_lat * RAD
        ra = math.atan2(math.sin(lam) * math.cos(eps * RAD) - math.tan(beta) * math.sin(eps * RAD), math.cos(lam)) * DEG
        dec = math.asin(math.sin(beta) * math.cos(eps * RAD) + math.cos(beta) * math.sin(eps * RAD) * math.sin(lam)) * DEG
        ha = norm180(norm360(280.46061837 + 360.98564736629 * day + lon) - norm360(ra))
        altitude = math.asin(math.sin(lat * RAD) * math.sin(dec * RAD) +
                             math.cos(lat * RAD) * math.cos(dec * RAD) * math.cos(ha * RAD)) * DEG
    else:
        moon_lon, moon_lat = moon_position(day)
        eps = 23.4393 - 0.00000036 * day
        ra = atan2_small(sin_small(moon_lon) * cos_small(eps) -
                         (sin_small(moon_lat) / cos_small(moon_lat)) * sin_small(eps),
                         cos_small(moon_lon)) * DEG
        dec = asin_small(sin_small(moon_lat) * cos_small(eps) +
                         cos_small(moon_lat) * sin_small(eps) * sin_small(moon_lon)) * DEG
        ha = norm180(norm360(280.460618 + 360.985647 * day + lon) - ra)
        altitude = asin_small(sin_small(lat) * sin_small(dec) +
                              cos_small(lat) * cos_small(dec) * cos_small(ha)) * DEG
    return altitude


def moon_events_for_date(y, m, d, lat, lon, tz, golden):
    steps, refinements = (360, 30) if golden else (144, 8)
    previous_t = 0.0
    previous = moon_altitude(astro_day(y, m, d, -tz), lat, lon, golden)
    rise = set_ = 0.0
    for i in range(1, steps + 1):
        hour = 24.0 * i / steps
        altitude = moon_altitude(astro_day(y, m, d, hour - tz), lat, lon, golden)
        rising = previous < -0.8333 <= altitude
        setting = previous > -0.8333 >= altitude
        if (rising and not rise) or (setting and not set_):
            lo, hi = previous_t, hour
            for _ in range(refinements):
                mid = (lo + hi) * 0.5
                mid_alt = moon_altitude(astro_day(y, m, d, mid - tz), lat, lon, golden)
                if (rising and mid_alt >= -0.8333) or (setting and mid_alt <= -0.8333):
                    hi = mid
                else:
                    lo = mid
            if rising:
                rise = (lo + hi) * 0.5
            else:
                set_ = (lo + hi) * 0.5
        if rise and set_:
            break
        previous, previous_t = altitude, hour
    return rise, set_


def category_at(day, kind, golden):
    if golden:
        jd = day + 2451545.0
        sun = ref.sidereal(golden_sun_longitude(jd), jd)
        moon = ref.sidereal(golden_moon_position(jd)[0], jd)
    else:
        sun, moon = sidereal(day)
    if kind == "tithi":
        return ref.calc_tithi(sun, moon)
    if kind == "nakshatra":
        return ref.calc_nakshatra(moon)
    return ref.calc_yoga(sun, moon)


def category_change_hour(y, m, d, tz, start_day, kind, golden):
    initial = category_at(start_day, kind, golden)
    step = (5.0 if golden else 10.0) / 1440.0
    previous = start_day
    point = start_day + step
    while point <= start_day + 1.5:
        if category_at(point, kind, golden) != initial:
            lo, hi = previous, point
            for _ in range(20 if golden else 8):
                mid = (lo + hi) * 0.5
                if category_at(mid, kind, golden) == initial:
                    lo = mid
                else:
                    hi = mid
            return ((hi - astro_day(y, m, d, 0.0)) * 24.0 + tz) % 24.0
        previous, point = point, point + step
    return 0.0


event_dates = [(y, m, d) for y in (2000, 2010, 2020, 2026, 2035, 2050)
               for m, d in ((1, 1), (3, 20), (6, 21), (9, 22), (12, 21))]
classification_dates = []
cursor = date(2000, 1, 1)
while cursor <= date(2050, 12, 31):
    classification_dates.append((cursor.year, cursor.month, cursor.day))
    cursor += timedelta(days=7)
locations = [(12.9165, 79.1325, 5.5), (0.0, 0.0, 0.0),
             (51.5074, -0.1278, 0.0), (-33.8688, 151.2093, 10.0)]
counts = {"tithi": 0, "nakshatra": 0, "yoga": 0}
max_error = {"sun_lon_deg": 0.0, "moon_lon_deg": 0.0,
             "sunrise_min": 0.0, "sunset_min": 0.0}
cases = 0
classification_location = (12.9165, 79.1325, 5.5)
for y, m, d in classification_dates:
    lat, lon, tz = classification_location
    reference_day = astro_day(y, m, d, ref.sun_time(y, m, d, lat, lon, tz, True) - tz)
    compact_day = astro_day(y, m, d, sun_event(y, m, d, lat, lon, tz, True) - tz)
    rsun = golden_sun_longitude(reference_day + 2451545.0)
    rmoon = golden_moon_position(reference_day + 2451545.0)[0]
    csun, cmoon = sun_longitude(compact_day), moon_position(compact_day)[0]
    max_error["sun_lon_deg"] = max(max_error["sun_lon_deg"], abs(norm180(csun - rsun)))
    max_error["moon_lon_deg"] = max(max_error["moon_lon_deg"], abs(norm180(cmoon - rmoon)))
    rs = ref.sidereal(rsun, reference_day + 2451545.0)
    rm = ref.sidereal(rmoon, reference_day + 2451545.0)
    cs, cm = sidereal(compact_day)
    counts["tithi"] += ref.calc_tithi(rs, rm) != ref.calc_tithi(cs, cm)
    counts["nakshatra"] += ref.calc_nakshatra(rm) != ref.calc_nakshatra(cm)
    counts["yoga"] += ref.calc_yoga(rs, rm) != ref.calc_yoga(cs, cm)
for y, m, d in event_dates:
    for lat, lon, tz in locations:
        for rising, key in ((True, "sunrise_min"), (False, "sunset_min")):
            expected = ref.sun_time(y, m, d, lat, lon, tz, rising)
            actual = sun_event(y, m, d, lat, lon, tz, rising)
            max_error[key] = max(max_error[key], circular_minutes(expected, actual))
        cases += 1

moon_cases = 0
moon_missing = 0
max_moon_error = {"moonrise_min": 0.0, "moonset_min": 0.0}
for y, m, d in event_dates:
    for lat, lon, tz in locations:
        expected = moon_events_for_date(y, m, d, lat, lon, tz, True)
        actual = moon_events_for_date(y, m, d, lat, lon, tz, False)
        for index, key in enumerate(("moonrise_min", "moonset_min")):
            if bool(expected[index]) != bool(actual[index]):
                moon_missing += 1
            elif expected[index]:
                max_moon_error[key] = max(max_moon_error[key], circular_minutes(expected[index], actual[index]))
        moon_cases += 1

transition_cases = 0
transition_rounded_mismatch = {"tithi_end": 0, "nak_end": 0}
max_transition_error = {"tithi_end_min": 0.0, "nak_end_min": 0.0}
for y in range(2000, 2051):
    for m in range(1, 13):
        d = 15
        lat, lon, tz = classification_location
        reference_start = astro_day(y, m, d, ref.sun_time(y, m, d, lat, lon, tz, True) - tz)
        compact_start = astro_day(y, m, d, sun_event(y, m, d, lat, lon, tz, True) - tz)
        for kind, output_name in (("tithi", "tithi_end"), ("nakshatra", "nak_end")):
            expected = category_change_hour(y, m, d, tz, reference_start, kind, True)
            actual = category_change_hour(y, m, d, tz, compact_start, kind, False)
            max_transition_error[output_name + "_min"] = max(
                max_transition_error[output_name + "_min"], circular_minutes(expected, actual))
            transition_rounded_mismatch[output_name] += ref.round5(expected) != ref.round5(actual)
        transition_cases += 1

print(f"classification cases: {len(classification_dates)}")
print(f"rise/set cases: {cases}")
for key, value in counts.items():
    print(f"{key} mismatches: {value}")
for key, value in max_error.items():
    print(f"max {key}: {value:.3f}")
print(f"moon event cases: {moon_cases}")
print(f"moon event presence mismatches: {moon_missing}")
for key, value in max_moon_error.items():
    print(f"max {key}: {value:.3f}")
print(f"transition cases: {transition_cases}")
for key, value in transition_rounded_mismatch.items():
    print(f"rounded {key} mismatches: {value}")
for key, value in max_transition_error.items():
    print(f"max {key}: {value:.3f}")
