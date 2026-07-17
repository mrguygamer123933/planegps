"use strict";

const COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
function compass(bearing) {
  if (bearing == null) return "?";
  return COMPASS[Math.round(((bearing % 360) / 45)) % 8];
}
function fmtMeters(m) {
  if (m == null) return "?";
  if (m >= 1000) return (m / 1000).toFixed(1) + " km";
  return Math.round(m) + " m";
}
function fmtAlt(m) {
  if (m == null) return "?";
  return Math.round(m).toLocaleString() + " m";
}
function fmtSpeed(ms) {
  if (ms == null) return "?";
  return Math.round(ms * 3.6) + " km/h";
}

// The plane that is highest in the sky (closest to straight overhead).
function mostOverhead(state) {
  const list = state.overhead || [];
  let best = null;
  for (const f of list) {
    if (f.elevation_deg == null) continue;
    if (!best || f.elevation_deg > best.elevation_deg) best = f;
  }
  return best || list[0] || null;
}

let latest = null;

function renderList(state) {
  const list = document.getElementById("list");
  const count = document.getElementById("count");
  count.textContent = state.overhead.length;
  if (state.error) {
    list.innerHTML = `<div class="empty err">Data source error: ${state.error}</div>`;
    return;
  }
  if (!state.overhead.length) {
    list.innerHTML = `<div class="empty">No aircraft overhead right now. Watching ${state.nearby.length} in the wider area&hellip;</div>`;
    return;
  }
  list.innerHTML = state.overhead
    .map((f, i) => {
      const dir = f.bearing_deg != null ? `${compass(f.bearing_deg)} (${Math.round(f.bearing_deg)}\u00b0)` : "?";
      const sub = f.airline || f.origin_country || "";
      return `
      <div class="flight ${i === 0 ? "top" : ""}">
        <div class="row1">
          <span class="cs">\u2708 ${f.callsign || f.registration || f.icao24}</span>
          <span class="type">${f.aircraft_type || "?"}</span>
        </div>
        <div class="route">${f.origin || "?"}<span class="arrow">\u2192</span>${f.destination || "?"}
          ${sub ? `&nbsp;<span style="color:var(--muted);font-size:13px">&middot; ${sub}</span>` : ""}
        </div>
        <div class="stats">
          <span>Dist <b>${fmtMeters(f.distance_m)}</b></span>
          <span>Alt <b>${fmtAlt(f.altitude_m)}</b></span>
          <span>Dir <b>${dir}</b></span>
          <span>Up <b>${f.elevation_deg != null ? Math.round(f.elevation_deg) + "\u00b0" : "?"}</b></span>
          <span>Speed <b>${fmtSpeed(f.ground_speed_ms)}</b></span>
        </div>
      </div>`;
    })
    .join("");
}

function renderLookup(state) {
  const el = document.getElementById("lookup");
  if (state.error) {
    el.className = "lookup-hint idle";
    el.innerHTML = `<div class="big err">Data source error</div>`;
    return;
  }
  const f = mostOverhead(state);
  if (!f) {
    el.className = "lookup-hint idle";
    el.innerHTML = `<div class="big">No plane overhead right now</div>
      <div class="sub">Nothing to look up at &mdash; watching ${state.nearby.length} aircraft nearby.</div>`;
    return;
  }
  const elev = f.elevation_deg;
  const name = f.callsign || f.registration || f.icao24;
  const detail = `<b>${name}</b> ${f.aircraft_type ? "(" + f.aircraft_type + ")" : ""} &middot; ${f.route} &middot; ${fmtAlt(f.altitude_m)} up &middot; ${fmtMeters(f.distance_m)} away`;
  el.className = "lookup-hint";
  if (elev != null && elev >= 80) {
    el.innerHTML = `<div class="big">&#8593; Straight up!</div><div class="sub">${detail}</div>`;
  } else if (elev != null) {
    el.innerHTML =
      `<div class="big">Look ${compass(f.bearing_deg)} &#8599; ${Math.round(elev)}&deg; up</div>` +
      `<div class="sub">${detail}</div>`;
  } else {
    el.innerHTML = `<div class="big">Look ${compass(f.bearing_deg)}</div><div class="sub">${detail}</div>`;
  }
}

// Sky dome: center = straight up (zenith), edge = horizon. Shows which way and
// how high in the sky to look to physically see the plane above you.
function drawSky(state) {
  const canvas = document.getElementById("sky");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R = Math.min(W, H) / 2 - 18;
  ctx.clearRect(0, 0, W, H);

  // Elevation rings (0 deg at edge -> 90 deg at center).
  ctx.strokeStyle = "#1e2c45";
  ctx.fillStyle = "#7c8aa5";
  ctx.font = "11px system-ui";
  ctx.textAlign = "left";
  for (const elev of [0, 30, 60]) {
    const r = ((90 - elev) / 90) * R;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillText(elev + "\u00b0", cx + 3, cy - r + 12);
  }
  // Compass labels around the horizon.
  ctx.fillStyle = "#7c8aa5";
  ctx.textAlign = "center";
  ctx.fillText("N", cx, cy - R - 5);
  ctx.fillText("S", cx, cy + R + 13);
  ctx.fillText("E", cx + R + 9, cy + 4);
  ctx.fillText("W", cx - R - 9, cy + 4);

  // Zenith marker (straight up).
  ctx.fillStyle = "#38bdf8";
  ctx.beginPath();
  ctx.arc(cx, cy, 3, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#7c8aa5";
  ctx.fillText("UP", cx, cy - 8);
  ctx.textAlign = "left";

  const top = mostOverhead(state);
  const plot = (f, isTop) => {
    if (f.bearing_deg == null || f.elevation_deg == null) return;
    const rr = ((90 - Math.max(0, Math.min(90, f.elevation_deg))) / 90) * R;
    const a = (f.bearing_deg - 90) * (Math.PI / 180);
    const x = cx + Math.cos(a) * rr;
    const y = cy + Math.sin(a) * rr;
    if (isTop) {
      // guide line from zenith toward the plane's azimuth
      ctx.strokeStyle = "rgba(52,211,153,.5)";
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.stroke();
    }
    ctx.fillStyle = isTop ? "#34d399" : "#9fb3d1";
    ctx.beginPath();
    ctx.arc(x, y, isTop ? 6 : 3, 0, Math.PI * 2);
    ctx.fill();
    if (isTop) {
      ctx.fillStyle = "#e6edf7";
      ctx.font = "12px system-ui";
      ctx.fillText(f.callsign || f.icao24, x + 9, y - 7);
    }
  };
  (state.overhead || []).forEach((f) => plot(f, top && f.icao24 === top.icao24));
}

function drawRadar(state) {
  const canvas = document.getElementById("radar");
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R = Math.min(W, H) / 2 - 16;
  ctx.clearRect(0, 0, W, H);

  // Rings
  ctx.strokeStyle = "#1e2c45";
  ctx.fillStyle = "#7c8aa5";
  ctx.font = "11px system-ui";
  for (let i = 1; i <= 4; i++) {
    const r = (R * i) / 4;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    const label = fmtMeters((state.radius_m * i) / 4);
    ctx.fillText(label, cx + 4, cy - r + 12);
  }
  // Cross-hairs + compass
  ctx.beginPath();
  ctx.moveTo(cx - R, cy); ctx.lineTo(cx + R, cy);
  ctx.moveTo(cx, cy - R); ctx.lineTo(cx, cy + R);
  ctx.stroke();
  ctx.fillStyle = "#7c8aa5";
  ctx.textAlign = "center";
  ctx.fillText("N", cx, cy - R - 4);
  ctx.fillText("S", cx, cy + R + 12);
  ctx.fillText("E", cx + R + 8, cy + 4);
  ctx.fillText("W", cx - R - 8, cy + 4);
  ctx.textAlign = "left";

  // Sweep
  const t = (Date.now() / 3000) % 1;
  const ang = t * Math.PI * 2 - Math.PI / 2;
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
  grad.addColorStop(0, "rgba(52,211,153,0.28)");
  grad.addColorStop(1, "rgba(52,211,153,0)");
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, R, ang - 0.5, ang);
  ctx.closePath();
  ctx.fill();

  // Center (home)
  ctx.fillStyle = "#38bdf8";
  ctx.beginPath();
  ctx.arc(cx, cy, 4, 0, Math.PI * 2);
  ctx.fill();

  if (!state) return;
  const plot = (f, isTop) => {
    if (f.bearing_deg == null || f.distance_m == null) return;
    const rr = Math.min(1, f.distance_m / state.radius_m) * R;
    const a = (f.bearing_deg - 90) * (Math.PI / 180);
    const x = cx + Math.cos(a) * rr;
    const y = cy + Math.sin(a) * rr;
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate((f.heading || 0) * (Math.PI / 180));
    ctx.fillStyle = isTop ? "#34d399" : "#9fb3d1";
    ctx.beginPath();
    ctx.moveTo(0, -7);
    ctx.lineTo(5, 6);
    ctx.lineTo(0, 3);
    ctx.lineTo(-5, 6);
    ctx.closePath();
    ctx.fill();
    ctx.restore();
    if (isTop) {
      ctx.fillStyle = "#e6edf7";
      ctx.font = "12px system-ui";
      ctx.fillText(f.callsign || f.icao24, x + 8, y - 6);
    }
  };
  // nearby (dim) first, then overhead (bright) on top
  (state.nearby || []).forEach((f) => {
    if (f.distance_m != null && f.distance_m > state.radius_m) {
      // draw clamped to edge as faint marker
      ctx.save();
      const a = (f.bearing_deg - 90) * (Math.PI / 180);
      const x = cx + Math.cos(a) * R;
      const y = cy + Math.sin(a) * R;
      ctx.fillStyle = "rgba(159,179,209,0.25)";
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  });
  (state.overhead || []).forEach((f, i) => plot(f, i === 0));
}

function applyState(state) {
  latest = state;
  document.getElementById("loc").textContent =
    `${state.location_name} (${state.latitude.toFixed(3)}, ${state.longitude.toFixed(3)})`;
  document.getElementById("radius").textContent = fmtMeters(state.radius_m);
  document.getElementById("source").textContent = state.source;
  const age = Date.now() / 1000 - state.updated_at;
  const dot = document.getElementById("statusdot");
  const status = document.getElementById("status");
  if (age > 15) {
    dot.classList.add("stale");
    status.textContent = `stale (${Math.round(age)}s)`;
  } else {
    dot.classList.remove("stale");
    status.textContent = "live";
  }
  renderList(state);
  renderLookup(state);
}

async function poll() {
  try {
    const r = await fetch("/api/state", { cache: "no-store" });
    const s = await r.json();
    applyState(s);
  } catch (e) {
    document.getElementById("status").textContent = "offline";
    document.getElementById("statusdot").classList.add("stale");
  }
}

function loop() {
  if (latest) {
    drawSky(latest);
    drawRadar(latest);
  }
  requestAnimationFrame(loop);
}

poll();
setInterval(poll, 1000);
loop();
