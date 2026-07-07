/* Narrow Highway — sovereign connection-graph renderer.
   Vanilla canvas 2D. No library, no CDN, no dependency. Reads FOUND edges from /graph
   (each edge carries the id of its sealed connection card). A window, not a wall — the
   map points to the records; it is not the records.

   window.NHGraph.local(sectionId, canvasId, cardId) — the per-card local graph.
   window.NHGraph.map(cfg)                            — the full /map.html experience.
*/
(function () {
  "use strict";

  // Shelf hues — legible on both the light card pages and the dark map.
  var SHELF = {
    codex: "#c9a24a", classics: "#9b7bc0", dictionary: "#4f93c0", patristics: "#ce7f4f",
    hymns: "#5fb089", recipes: "#b89152", maker: "#c56aa0", animation: "#8fae52", atlas: "#4fb0a8"
  };
  var REL = { references: "#c9a24a", cites: "#c9a24a", proof_text: "#5fb089", see_also: "#8592a4", parallels: "#9b7bc0", illuminates: "#cf9f5a" };
  function shelfColor(s) { return SHELF[s] || "#8a93a3"; }
  function relColor(k) { return REL[k] || "#8592a4"; }

  function api(path) {
    return fetch(path, { headers: { accept: "application/json" } }).then(function (r) {
      if (!r.ok) throw r.status; return r.json();
    });
  }
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }

  // ── the view ────────────────────────────────────────────────────────────
  function View(canvas, theme) {
    this.cv = canvas; this.ctx = canvas.getContext("2d");
    this.theme = theme === "dark" ? "dark" : "light";
    this.nodes = []; this.links = []; this.byId = {};
    this.tx = 0; this.ty = 0; this.scale = 1;
    this.alpha = 0; this.centerId = null; this.fitted = false;
    this.hover = null; this.drag = null; this.panning = false; this.last = null; this.moved = false;
    this.onpick = null;             // fn(node) on background pick change (map uses it)
    this.relFilter = null;          // Set of visible relationship kinds, or null = all
    this._raf = null;
    var self = this;
    this._resize = function () {
      var dpr = window.devicePixelRatio || 1;
      var w = canvas.clientWidth || 600, h = canvas.clientHeight || 400;
      canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
      self.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      self.w = w; self.h = h; self.draw();
    };
    window.addEventListener("resize", this._resize);
    this._bind();
    this._resize();
  }

  View.prototype.radius = function (n) {
    var r = 3 + Math.sqrt(n.degree || 0) * 1.7;
    if (n.id === this.centerId) r = Math.max(r, 9);
    return Math.min(r, 30);
  };

  View.prototype.setData = function (nodes, links, centerId) {
    this.centerId = centerId || null;
    this.byId = {};
    var i, cx, cy, R = Math.max(60, Math.sqrt(nodes.length) * 26);
    for (i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      var ang = (i / Math.max(1, nodes.length)) * Math.PI * 2;
      // deterministic-ish spread; center pinned near origin
      if (n.id === centerId) { n.x = 0; n.y = 0; } else {
        var rr = R * (0.35 + 0.65 * ((i * 2654435761 % 1000) / 1000));
        n.x = Math.cos(ang) * rr; n.y = Math.sin(ang) * rr;
      }
      n.vx = 0; n.vy = 0; this.byId[n.id] = n;
    }
    this.nodes = nodes; this.links = links || [];
    this.alpha = 1; this.fitted = false;
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      // Respect prefers-reduced-motion: settle the layout silently, then paint once (no animation).
      for (var s = 0; s < 400 && this.alpha > 0; s++) this.step();
      this.alpha = 0; this.fit(); this.draw();
    } else {
      this._loop();
    }
  };

  View.prototype.step = function () {
    var n = this.nodes, L = this.links, N = n.length, i, j, a, b, dx, dy, d2, d, f, ux, uy;
    var k = Math.sqrt((this.w * this.h) / Math.max(1, N)) * 0.9;
    var repK = k * k;
    for (i = 0; i < N; i++) { n[i].fx = 0; n[i].fy = 0; }
    // repulsion (O(n^2) — fine at our capped sizes, and it cools to a stop)
    for (i = 0; i < N; i++) {
      a = n[i];
      for (j = i + 1; j < N; j++) {
        b = n[j]; dx = a.x - b.x; dy = a.y - b.y; d2 = dx * dx + dy * dy;
        if (d2 < 0.01) { dx = (i - j) * 0.01 + 0.1; dy = 0.1; d2 = dx * dx + dy * dy; }
        f = repK / d2; d = Math.sqrt(d2); ux = dx / d; uy = dy / d;
        a.fx += ux * f; a.fy += uy * f; b.fx -= ux * f; b.fy -= uy * f;
      }
    }
    // link springs
    for (i = 0; i < L.length; i++) {
      a = this.byId[L[i].source]; b = this.byId[L[i].target]; if (!a || !b) continue;
      dx = b.x - a.x; dy = b.y - a.y; d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      f = (d - k) * 0.045; ux = dx / d; uy = dy / d;
      a.fx += ux * f; a.fy += uy * f; b.fx -= ux * f; b.fy -= uy * f;
    }
    // gravity + integrate
    for (i = 0; i < N; i++) {
      a = n[i]; if (a === this.drag) continue;
      a.fx += -a.x * 0.012; a.fy += -a.y * 0.012;
      a.vx = (a.vx + a.fx) * 0.88; a.vy = (a.vy + a.fy) * 0.88;
      a.x += clamp(a.vx * this.alpha, -40, 40); a.y += clamp(a.vy * this.alpha, -40, 40);
    }
    this.alpha *= 0.985;
    if (this.alpha < 0.02) { this.alpha = 0; if (!this.fitted) this.fit(); }
  };

  View.prototype.fit = function () {
    if (!this.nodes.length) return;
    var minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9, i, n;
    for (i = 0; i < this.nodes.length; i++) {
      n = this.nodes[i]; if (n.x < minx) minx = n.x; if (n.y < miny) miny = n.y;
      if (n.x > maxx) maxx = n.x; if (n.y > maxy) maxy = n.y;
    }
    var gw = Math.max(1, maxx - minx), gh = Math.max(1, maxy - miny);
    var pad = 60;
    this.scale = clamp(Math.min((this.w - pad) / gw, (this.h - pad) / gh), 0.05, 2.2);
    this.tx = -((minx + maxx) / 2) * this.scale;
    this.ty = -((miny + maxy) / 2) * this.scale;
    this.fitted = true; this.draw();
  };

  View.prototype._sx = function (x) { return this.w / 2 + this.tx + x * this.scale; };
  View.prototype._sy = function (y) { return this.h / 2 + this.ty + y * this.scale; };
  View.prototype._wx = function (sx) { return (sx - this.w / 2 - this.tx) / this.scale; };
  View.prototype._wy = function (sy) { return (sy - this.h / 2 - this.ty) / this.scale; };

  View.prototype.draw = function () {
    var c = this.ctx, dark = this.theme === "dark";
    c.clearRect(0, 0, this.w, this.h);
    var i, a, b, l;
    // edges
    for (i = 0; i < this.links.length; i++) {
      l = this.links[i];
      if (this.relFilter && !this.relFilter[l.kind]) continue;
      a = this.byId[l.source]; b = this.byId[l.target]; if (!a || !b) continue;
      c.beginPath(); c.moveTo(this._sx(a.x), this._sy(a.y)); c.lineTo(this._sx(b.x), this._sy(b.y));
      c.strokeStyle = relColor(l.kind);
      c.globalAlpha = (this.hover && (this.hover === a || this.hover === b)) ? 0.85 : (dark ? 0.22 : 0.28);
      c.lineWidth = (this.hover && (this.hover === a || this.hover === b)) ? 1.6 : 0.8;
      c.stroke();
    }
    c.globalAlpha = 1;
    // nodes
    for (i = 0; i < this.nodes.length; i++) {
      a = this.nodes[i]; var r = this.radius(a), sx = this._sx(a.x), sy = this._sy(a.y);
      c.beginPath(); c.arc(sx, sy, r, 0, Math.PI * 2);
      c.fillStyle = shelfColor(a.shelf);
      if (dark && r > 8) { c.shadowColor = shelfColor(a.shelf); c.shadowBlur = 12; } else { c.shadowBlur = 0; }
      c.fill(); c.shadowBlur = 0;
      c.lineWidth = a.id === this.centerId ? 2.5 : 1;
      c.strokeStyle = a === this.hover ? (dark ? "#fff" : "#1a2230") : (a.id === this.centerId ? (dark ? "#fff" : "#1a3a52") : (dark ? "rgba(10,11,16,.6)" : "rgba(255,255,255,.85)"));
      c.stroke();
    }
    // labels — hubs, the center, and whatever is hovered
    c.font = "600 12px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "bottom";
    var labelColor = dark ? "#e9e3d4" : "#1a2230";
    for (i = 0; i < this.nodes.length; i++) {
      a = this.nodes[i]; var rad = this.radius(a);
      var big = rad >= 12 || a.id === this.centerId || a === this.hover;
      if (!big) continue;
      var t = a.title || a.id; if (t.length > 34) t = t.slice(0, 33) + "…";
      var lx = this._sx(a.x), ly = this._sy(a.y) - rad - 3;
      c.lineWidth = 3; c.strokeStyle = dark ? "rgba(10,11,16,.85)" : "rgba(247,248,250,.9)";
      c.strokeText(t, lx, ly); c.fillStyle = labelColor; c.fillText(t, lx, ly);
    }
  };

  View.prototype.pick = function (sx, sy) {
    var wx = this._wx(sx), wy = this._wy(sy), i, a, r, dx, dy, best = null, bd = 1e9;
    for (i = 0; i < this.nodes.length; i++) {
      a = this.nodes[i]; r = this.radius(a) + 4; dx = a.x - wx; dy = a.y - wy;
      var dd = dx * dx + dy * dy; if (dd <= (r / this.scale) * (r / this.scale) && dd < bd) { bd = dd; best = a; }
    }
    return best;
  };

  View.prototype._bind = function () {
    var self = this, cv = this.cv;
    cv.style.touchAction = "none"; cv.style.cursor = "grab";
    function xy(e) { var rc = cv.getBoundingClientRect(); return [e.clientX - rc.left, e.clientY - rc.top]; }
    cv.addEventListener("wheel", function (e) {
      e.preventDefault();
      var p = xy(e), wx = self._wx(p[0]), wy = self._wy(p[1]);
      var f = e.deltaY < 0 ? 1.12 : 1 / 1.12; self.scale = clamp(self.scale * f, 0.05, 4);
      self.tx = p[0] - self.w / 2 - wx * self.scale; self.ty = p[1] - self.h / 2 - wy * self.scale;
      self.draw();
    }, { passive: false });
    cv.addEventListener("mousedown", function (e) {
      var p = xy(e); self.last = p; self.moved = false; var hit = self.pick(p[0], p[1]);
      if (hit) { self.drag = hit; cv.style.cursor = "grabbing"; } else { self.panning = true; cv.style.cursor = "grabbing"; }
    });
    window.addEventListener("mousemove", function (e) {
      var p = xy(e);
      if (self.drag) {
        self.drag.x = self._wx(p[0]); self.drag.y = self._wy(p[1]); self.drag.vx = 0; self.drag.vy = 0;
        self.alpha = Math.max(self.alpha, 0.25); self.fitted = true; self.moved = true; self._loop();
      } else if (self.panning) {
        self.tx += p[0] - self.last[0]; self.ty += p[1] - self.last[1]; self.last = p; self.moved = true; self.draw();
      } else {
        var h = self.pick(p[0], p[1]);
        if (h !== self.hover) { self.hover = h; cv.style.cursor = h ? "pointer" : "grab"; self.draw(); }
      }
    });
    window.addEventListener("mouseup", function (e) {
      if ((self.drag || self.panning) && !self.moved) {
        var p = xy(e), hit = self.pick(p[0], p[1]);
        if (hit) { if (self.onpick) self.onpick(hit); else location.href = "/card/" + encodeURIComponent(hit.id); }
      }
      self.drag = null; self.panning = false; cv.style.cursor = "grab";
    });
  };

  View.prototype._loop = function () {
    if (this._raf) return;
    var self = this;
    (function tick() {
      if (self.alpha > 0) { self.step(); self.draw(); self._raf = requestAnimationFrame(tick); }
      else { self._raf = null; self.draw(); }
    })();
  };

  // ── driver: per-card local graph ─────────────────────────────────────────
  function local(sectionId, canvasId, cardId) {
    var section = document.getElementById(sectionId), cv = document.getElementById(canvasId);
    if (!section || !cv) return;
    api("/graph?scope=card&id=" + encodeURIComponent(cardId)).then(function (d) {
      if (!d || !d.nodes || d.nodes.length < 2) { section.style.display = "none"; return; }
      section.style.display = "";
      var v = new View(cv, "dark"); v.setData(d.nodes, d.links, d.center);
      var cap = document.getElementById(canvasId + "-cap");
      if (cap) {
        var more = d.total > d.shown ? (" (showing the " + d.shown + " most-connected of " + d.total + ")") : "";
        cap.innerHTML = d.shown + " connection" + (d.shown === 1 ? "" : "s") + more +
          " — found, not generated. Each line is a sealed record. <a href=\"/map.html\">Open the full map →</a>";
      }
    }).catch(function () { section.style.display = "none"; });
  }

  // ── driver: the full map ─────────────────────────────────────────────────
  function map(cfg) {
    var cv = document.getElementById(cfg.canvas);
    var status = document.getElementById(cfg.status);
    var back = document.getElementById(cfg.back);
    var search = document.getElementById(cfg.search);
    var legend = document.getElementById(cfg.legend);
    var v = new View(cv, "dark");
    var state = { level: "overview", label: "" };

    function setStatus(html) { if (status) status.innerHTML = html; }
    function showBack(on) { if (back) back.style.display = on ? "" : "none"; }

    // overview clusters become clickable super-nodes (one per shelf)
    function loadOverview() {
      state.level = "overview"; showBack(false);
      api("/graph?scope=overview").then(function (d) {
        var nodes = d.clusters.map(function (c) {
          return { id: "shelf:" + c.shelf, title: c.shelf + " · " + c.count, shelf: c.shelf, degree: Math.sqrt(c.count) * 3 };
        });
        var links = d.links.filter(function (l) { return l.source !== l.target; }).map(function (l) {
          return { source: "shelf:" + l.source, target: "shelf:" + l.target, kind: "see_also", weight: l.weight };
        });
        v.onpick = function (n) { loadShelf(n.shelf); };
        v.setData(nodes, links, null);
        setStatus("The keeping — <strong>" + d.total_nodes.toLocaleString() + "</strong> ideas, <strong>" +
          d.total_edges.toLocaleString() + "</strong> found connections. Click a shelf to open it, or search below.");
      }).catch(function () { setStatus("The map is resting. Try again in a moment."); });
    }

    function loadShelf(shelf) {
      setStatus("Opening <strong>" + esc(shelf) + "</strong>…");
      api("/graph?scope=shelf&shelf=" + encodeURIComponent(shelf)).then(function (d) {
        state.level = "shelf"; showBack(true);
        v.onpick = null; // clicking a real card navigates to it
        v.setData(d.nodes, d.links, null);
        var note = d.total_in_shelf > d.shown_from_shelf
          ? (" — showing its " + d.shown_from_shelf + " most-connected of " + d.total_in_shelf + ", with their neighbors")
          : "";
        setStatus("<strong>" + esc(shelf) + "</strong>" + note + ". Click any node to open its card. Drag to explore.");
      }).catch(function () { setStatus("Could not open that shelf."); });
    }

    function focusCard(id) {
      api("/graph?scope=card&id=" + encodeURIComponent(id)).then(function (d) {
        if (!d || !d.nodes) { setStatus("No connections found for that card."); return; }
        state.level = "card"; showBack(true); v.onpick = null; v.setData(d.nodes, d.links, d.center);
        var center = d.nodes.filter(function (n) { return n.id === d.center; })[0];
        setStatus("<strong>" + esc(center ? center.title : id) + "</strong> — " + d.shown +
          " of " + d.total + " connections. Click a neighbor to travel.");
      }).catch(function () { setStatus("No card matched that search."); });
    }

    if (back) back.addEventListener("click", function (e) { e.preventDefault(); loadOverview(); });
    if (search) search.addEventListener("keydown", function (e) {
      if (e.key !== "Enter") return;
      var q = search.value.trim(); if (!q) return;
      setStatus("Searching…");
      api("/locate?q=" + encodeURIComponent(q)).then(function (r) {
        var m = (r && r.matches) || [];
        if (!m.length) { setStatus("Nothing matched “" + esc(q) + "”."); return; }
        focusCard(m[0].id);
      }).catch(function () { setStatus("Search is resting."); });
    });

    if (legend) {
      var keys = ["codex", "classics", "dictionary", "patristics", "hymns", "recipes", "maker", "animation", "atlas"];
      legend.innerHTML = keys.map(function (k) {
        return "<span class=leg><i style=\"background:" + shelfColor(k) + "\"></i>" + k + "</span>";
      }).join("");
    }
    loadOverview();
  }

  window.NHGraph = { local: local, map: map, View: View, shelfColor: shelfColor };
})();
