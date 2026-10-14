import json
import heapq
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from collections import deque
import math


DATA_FILE = "routes_student_project_v2.json"


class RoutePlanner:
    def __init__(self, graph):
        self.graph = graph

    def find_shortest_time(self, start, end):
        return self._dijkstra(start, end, "time")

    def find_cheapest_route(self, start, end):
        return self._dijkstra(start, end, "cost")

    def find_recommended_route(self, start, end):
        return self._dijkstra(start, end, "score")

    def find_min_stops(self, start, end):
        if start not in self.graph or end not in self.graph:
            return None

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            current, path = queue.popleft()
            if current == end:
                return {"route": path, "stops": len(path) - 1}

            for edge in self.graph.get(current, []):
                neighbor = edge["to"]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def _dijkstra(self, start, end, weight_key):
        if start not in self.graph or end not in self.graph:
            return None

        priority_queue = [(0, 0, 0, 0, start, [start], None)]
        visited = {}

        while priority_queue:
            current_value, total_time, total_cost, stops, current_node, path, last_type = heapq.heappop(priority_queue)

            if current_node == end:
                result = {"route": path}
                if weight_key == "time":
                    result["time"] = total_time
                    result["cost"] = total_cost
                elif weight_key == "cost":
                    result["cost"] = total_cost
                    result["time"] = total_time
                elif weight_key == "score":
                    result["score"] = current_value
                    result["time"] = total_time
                    result["cost"] = total_cost
                return result

            state_key = (current_node, last_type) if weight_key == "score" else current_node
            best_so_far = visited.get(state_key)
            current_priority = (current_value, total_time, total_cost, stops)
            if best_so_far is not None and best_so_far <= current_priority:
                continue

            visited[state_key] = current_priority

            for edge in self.graph.get(current_node, []):
                next_node = edge["to"]
                edge_time = edge["time"]
                edge_cost = edge["cost"]
                edge_type = edge.get("type", "transport public")
                next_time = total_time + edge_time
                next_cost = total_cost + edge_cost
                next_stops = stops + 1

                if weight_key == "time":
                    next_value = next_time
                elif weight_key == "cost":
                    next_value = next_cost
                else:
                    next_value = current_value + self._recommended_edge_score(edge, last_type)

                heapq.heappush(
                    priority_queue,
                    (next_value, next_time, next_cost, next_stops, next_node,
                     path + [next_node],
                     edge_type)
                )

        return None

    def _recommended_edge_score(self, edge, last_type):
        """
        Scor pentru ruta recomandata:
        - timpul conteaza direct;
        - costul este ponderat cu 3, deoarece pentru studenti pretul conteaza mult;
        - fiecare oprire adauga o penalizare mica;
        - schimbarea tipului de transport adauga penalizare;
        - mersul pe jos este penalizat usor, deoarece poate fi mai incomod.
        """
        edge_type = edge.get("type", "transport public")

        time_score = edge["time"]
        cost_score = edge["cost"] * 3
        stop_penalty = 1.5
        transfer_penalty = 0

        if edge_type == "mers pe jos":
            time_score *= 1.35

        if last_type and last_type != edge_type:
            transfer_penalty = 4

        return time_score + cost_score + stop_penalty + transfer_penalty

    def get_route_details(self, route):
        details = []
        for i in range(len(route) - 1):
            start = route[i]
            end = route[i + 1]
            for edge in self.graph.get(start, []):
                if edge["to"] == end:
                    details.append(edge)
                    break
        return details

    # ── NOU: compara toate 4 algoritmi ──────────────
    def compare_all(self, start, end):
        return {
            "Minim timp (Dijkstra)"   : self.find_shortest_time(start, end),
            "Minim cost (Dijkstra)"   : self.find_cheapest_route(start, end),
            "Recomandata (scor realist)"  : self.find_recommended_route(start, end),
            "Minim opriri (BFS)"      : self.find_min_stops(start, end),
        }


# ─────────────────────────────────────────────
#  SIMULARE SCENARII
# ─────────────────────────────────────────────

class ScenarioSimulator:
    def __init__(self, graph):
        self.graph = graph

    def simulate_delay(self, start, end, delay):
        for edge in self.graph.get(start, []):
            if edge["to"] == end:
                edge["time"] += delay
                return True
        return False

    def simulate_cost_increase(self, start, end, extra_cost):
        for edge in self.graph.get(start, []):
            if edge["to"] == end:
                edge["cost"] += extra_cost
                return True
        return False

    def simulate_station_closure(self, station):
        changed = False
        if station in self.graph:
            del self.graph[station]
            changed = True
        for node in list(self.graph):
            before = len(self.graph[node])
            self.graph[node] = [e for e in self.graph[node] if e["to"] != station]
            if len(self.graph[node]) < before:
                changed = True
        return changed


# ─────────────────────────────────────────────
#  DATE IMPLICITE (Timisoara)
# ─────────────────────────────────────────────

def create_default_graph():
    # Graf BIDIRECȚIONAL complet – fiecare linie fizică apare în ambele sensuri.
    # Timpii sunt identici în ambele direcții (simplificare realistă pentru
    # transport urban; pot fi ajustați individual dacă e nevoie).
    return {
        # ── UPT ──────────────────────────────────────────────────────────
        "UPT": [
            {"to": "Complex Studentesc", "time": 5,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Biblioteca UPT",     "time": 4,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Piata Victoriei",    "time": 12, "cost": 4.0, "type": "tramvai",     "schedule": ["08:00","08:20","08:40","09:00"]},
            {"to": "Gara de Nord",       "time": 24, "cost": 4.0, "type": "tramvai",     "schedule": ["08:10","08:40","09:10"]},
            {"to": "Shopping City",      "time": 28, "cost": 4.0, "type": "autobuz",     "schedule": ["08:05","08:35","09:05"]},
        ],
        # ── Biblioteca UPT ───────────────────────────────────────────────
        "Biblioteca UPT": [
            {"to": "UPT",                "time": 4,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Complex Studentesc", "time": 6,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Piata Victoriei",    "time": 9,  "cost": 4.0, "type": "tramvai",     "schedule": ["08:15","08:35","08:55"]},
        ],
        # ── Complex Studentesc ───────────────────────────────────────────
        "Complex Studentesc": [
            {"to": "UPT",             "time": 5,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Biblioteca UPT",  "time": 6,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Medicina",        "time": 7,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Piata Victoriei", "time": 10, "cost": 4.0, "type": "autobuz",     "schedule": ["08:10","08:30","08:50","09:10"]},
            {"to": "Iulius Mall",     "time": 18, "cost": 4.0, "type": "autobuz",     "schedule": ["08:05","08:35","09:05"]},
        ],
        # ── Medicina ─────────────────────────────────────────────────────
        "Medicina": [
            {"to": "Complex Studentesc", "time": 7,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Piata Unirii",       "time": 11, "cost": 4.0, "type": "autobuz",     "schedule": ["08:00","08:25","08:50"]},
            {"to": "Piata Victoriei",    "time": 14, "cost": 4.0, "type": "tramvai",     "schedule": ["08:10","08:40","09:10"]},
            {"to": "Iulius Mall",        "time": 14, "cost": 4.0, "type": "autobuz",     "schedule": ["08:05","08:35","09:05"]},
        ],
        # ── Piata Victoriei ──────────────────────────────────────────────
        "Piata Victoriei": [
            {"to": "UPT",                "time": 12, "cost": 4.0, "type": "tramvai",     "schedule": ["08:00","08:20","08:40","09:00"]},
            {"to": "Biblioteca UPT",     "time": 9,  "cost": 4.0, "type": "tramvai",     "schedule": ["08:15","08:35","08:55"]},
            {"to": "Complex Studentesc", "time": 10, "cost": 4.0, "type": "autobuz",     "schedule": ["08:10","08:30","08:50","09:10"]},
            {"to": "Medicina",           "time": 14, "cost": 4.0, "type": "tramvai",     "schedule": ["08:10","08:40","09:10"]},
            {"to": "Piata Unirii",       "time": 8,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Gara de Nord",       "time": 15, "cost": 4.0, "type": "tramvai",     "schedule": ["08:00","08:20","08:40","09:00"]},
            {"to": "Shopping City",      "time": 22, "cost": 4.0, "type": "autobuz",     "schedule": ["08:15","08:45","09:15"]},
        ],
        # ── Piata Unirii ─────────────────────────────────────────────────
        "Piata Unirii": [
            {"to": "Piata Victoriei", "time": 8,  "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Medicina",        "time": 11, "cost": 4.0, "type": "autobuz",     "schedule": ["08:00","08:25","08:50"]},
            {"to": "Iulius Mall",     "time": 10, "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Gara de Nord",    "time": 18, "cost": 4.0, "type": "tramvai",     "schedule": ["08:05","08:25","08:45"]},
        ],
        # ── Iulius Mall ──────────────────────────────────────────────────
        "Iulius Mall": [
            {"to": "Complex Studentesc", "time": 18, "cost": 4.0, "type": "autobuz",     "schedule": ["08:05","08:35","09:05"]},
            {"to": "Medicina",           "time": 14, "cost": 4.0, "type": "autobuz",     "schedule": ["08:05","08:35","09:05"]},
            {"to": "Piata Unirii",       "time": 10, "cost": 0.0, "type": "mers pe jos", "schedule": ["oricand"]},
            {"to": "Gara de Nord",       "time": 20, "cost": 4.0, "type": "autobuz",     "schedule": ["08:20","08:50","09:20"]},
            {"to": "Shopping City",      "time": 25, "cost": 4.0, "type": "autobuz",     "schedule": ["08:10","08:40","09:10"]},
        ],
        # ── Gara de Nord ─────────────────────────────────────────────────
        "Gara de Nord": [
            {"to": "UPT",             "time": 24, "cost": 4.0, "type": "tramvai", "schedule": ["08:10","08:40","09:10"]},
            {"to": "Piata Victoriei", "time": 15, "cost": 4.0, "type": "tramvai", "schedule": ["08:00","08:20","08:40","09:00"]},
            {"to": "Piata Unirii",    "time": 18, "cost": 4.0, "type": "tramvai", "schedule": ["08:05","08:25","08:45"]},
            {"to": "Iulius Mall",     "time": 20, "cost": 4.0, "type": "autobuz", "schedule": ["08:20","08:50","09:20"]},
            {"to": "Shopping City",   "time": 17, "cost": 4.0, "type": "autobuz", "schedule": ["08:00","08:30","09:00"]},
        ],
        # ── Shopping City ────────────────────────────────────────────────
        "Shopping City": [
            {"to": "UPT",             "time": 28, "cost": 4.0, "type": "autobuz", "schedule": ["08:05","08:35","09:05"]},
            {"to": "Piata Victoriei", "time": 22, "cost": 4.0, "type": "autobuz", "schedule": ["08:15","08:45","09:15"]},
            {"to": "Iulius Mall",     "time": 25, "cost": 4.0, "type": "autobuz", "schedule": ["08:10","08:40","09:10"]},
            {"to": "Gara de Nord",    "time": 17, "cost": 4.0, "type": "autobuz", "schedule": ["08:00","08:30","09:00"]},
        ],
    }


def save_graph_to_file(graph, filename="routes.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=4, ensure_ascii=False)


def load_graph_from_file(filename="routes.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            graph = json.load(f)
        for station in graph:
            for edge in graph[station]:
                edge.setdefault("type", "transport public")
                edge.setdefault("schedule", ["08:00","08:30","09:00"])
        return graph
    except (FileNotFoundError, json.JSONDecodeError):
        return create_default_graph()


# ─────────────────────────────────────────────
#  VIZUALIZARE GRAF  – stil hartă metro
# ─────────────────────────────────────────────

# Culori fundal & UI (paleta metro întunecată)
MAP_BG        = "#1a1f2e"   # fundal hartă
GRID_COLOR    = "#232840"   # linii grilă subtile
PANEL_BG      = "#12151f"   # bara de jos
TEXT_LIGHT    = "#e8eaf0"
TEXT_DIM      = "#7b82a0"
HIGHLIGHT_COL = "#f5a623"   # portocaliu – ruta activă
HOVER_GLOW    = "#ffffff"

# Pozitii fixe (relative 0-1) – layout metro ordonat
STATION_POSITIONS = {
    "Biblioteca UPT":       (0.14, 0.46),
    "UPT":                  (0.27, 0.60),
    "Complex Studentesc":   (0.39, 0.38),
    "Medicina":             (0.52, 0.24),
    "Piata Victoriei":      (0.42, 0.73),
    "Piata Unirii":         (0.59, 0.61),
    "Iulius Mall":          (0.73, 0.41),
    "Gara de Nord":         (0.70, 0.79),
    "Shopping City":        (0.88, 0.63),
}

# Culori linii – stil metro (groase, clare, saturate)
TRANSPORT_COLORS = {
    "tramvai":          "#e63946",   # roșu – linia T
    "autobuz":          "#4895ef",   # albastru – linia B
    "mers pe jos":      "#4cc9a0",   # verde mentă – pietonal
    "transport public": "#9b5de5",   # violet – generic
}

# Lățimea liniilor normale vs hover
LINE_W_NORMAL = 5
LINE_W_HOVER  = 9
LINE_W_ROUTE  = 10
LINE_W_MUTED  = 3

NODE_R        = 14   # raza cercului exterior (inel alb)
NODE_INNER_R  = 9    # raza cercului interior (culoare linie)


def open_graph_window(graph, highlight_route=None):
    """Hartă metro interactivă cu hover pe stații."""

    win = tk.Toplevel()
    win.title("Rețea de transport – Timișoara")
    win.configure(bg=MAP_BG)
    win.geometry("1000x680")
    win.resizable(True, True)

    W, H = 920, 580

    # ── Canvas hartă ─────────────────────────────────────────────
    canvas = tk.Canvas(win, bg=MAP_BG, width=W, height=H,
                       highlightthickness=0, bd=0)
    canvas.pack(side="top", fill="both", expand=True, padx=0, pady=0)

    # ── Panou info jos ────────────────────────────────────────────
    info_bar = tk.Frame(win, bg=PANEL_BG, height=60)
    info_bar.pack(side="bottom", fill="x")
    info_bar.pack_propagate(False)

    info_lbl = tk.Label(info_bar, text="Treci cu mouse-ul peste o stație pentru detalii",
                        bg=PANEL_BG, fg=TEXT_DIM,
                        font=("Helvetica", 10), anchor="w", padx=16)
    info_lbl.pack(side="left", fill="y")

    # ── Legenda dreapta ───────────────────────────────────────────
    legend_frame = tk.Frame(info_bar, bg=PANEL_BG)
    legend_frame.pack(side="right", padx=16, pady=8)
    for tip, col in TRANSPORT_COLORS.items():
        row = tk.Frame(legend_frame, bg=PANEL_BG)
        row.pack(side="left", padx=8)
        tk.Canvas(row, width=28, height=6, bg=PANEL_BG,
                  highlightthickness=0).pack(side="left")
        # linie colorata
        _lc = tk.Canvas(row, width=28, height=6, bg=col,
                        highlightthickness=0, relief="flat")
        _lc.pack(side="left")
        tk.Label(row, text=f" {tip}", bg=PANEL_BG, fg=TEXT_DIM,
                 font=("Helvetica", 8)).pack(side="left")

    # ── Calculează pozițiile în pixeli ───────────────────────────
    positions = {}
    for name, (rx, ry) in STATION_POSITIONS.items():
        positions[name] = (int(rx * W), int(ry * H))

    # Stații adăugate dinamic → cerc exterior
    extra = [s for s in graph if s not in positions]
    for i, name in enumerate(extra):
        angle = 2 * math.pi * i / max(len(extra), 1)
        px = int(0.5 * W + 0.36 * W * math.cos(angle))
        py = int(0.5 * H + 0.32 * H * math.sin(angle))
        positions[name] = (px, py)

    # ── Muchii ale rutei evidențiate ─────────────────────────────
    highlighted_edges = set()
    if highlight_route:
        for i in range(len(highlight_route) - 1):
            highlighted_edges.add((highlight_route[i], highlight_route[i + 1]))
            highlighted_edges.add((highlight_route[i + 1], highlight_route[i]))

    # ── Detectează culoarea dominantă a unui nod ─────────────────
    def node_line_color(node):
        """Returnează culoarea primei linii care trece prin nod."""
        for src, edges in graph.items():
            for edge in edges:
                if src == node or edge["to"] == node:
                    return TRANSPORT_COLORS.get(edge.get("type", ""), "#7b82a0")
        return "#7b82a0"

    # ── Grilă subtilă de fundal (aspect hartă) ───────────────────
    for gx in range(0, W, 60):
        canvas.create_line(gx, 0, gx, H, fill=GRID_COLOR, width=1)
    for gy in range(0, H, 60):
        canvas.create_line(0, gy, W, gy, fill=GRID_COLOR, width=1)

    # ── Titlu hartă ───────────────────────────────────────────────
    canvas.create_text(W // 2, 22, text="REȚEA DE TRANSPORT · TIMIȘOARA",
                       font=("Helvetica", 13, "bold"), fill=TEXT_DIM,
                       anchor="center", tags="title")

    # ════════════════════════════════════════════════════════════
    #  DESENARE MUCHII
    # ════════════════════════════════════════════════════════════

    edge_items  = {}   # (src,dst) -> [umbra, linie, fundal_eticheta, text_eticheta]
    edge_meta   = {}   # (src,dst) -> edge dict
    edge_draw_data = []
    seen_pairs = set()

    for src, edges in graph.items():
        if src not in positions:
            continue
        for edge in edges:
            dst = edge["to"]
            if dst not in positions:
                continue

            pair = tuple(sorted([src, dst]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            is_highlighted = ((src, dst) in highlighted_edges or
                              (dst, src) in highlighted_edges)
            edge_draw_data.append((is_highlighted, src, dst, edge))

    # Rutele normale se deseneaza primele; ruta activa vine deasupra.
    edge_draw_data.sort(key=lambda item: item[0])

    def _edge_curve_points(src, dst):
        x1, y1 = positions[src]
        x2, y2 = positions[dst]
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy) or 1
        nx, ny = -dy / length, dx / length
        seed = sum(ord(ch) for ch in f"{src}|{dst}")
        direction = -1 if seed % 2 else 1
        bend = direction * min(54, max(18, length * 0.12))
        cx = (x1 + x2) / 2 + nx * bend
        cy = (y1 + y2) / 2 + ny * bend
        return x1, y1, cx, cy, x2, y2, nx, ny

    for is_highlighted, src, dst, edge in edge_draw_data:
        base_color = TRANSPORT_COLORS.get(edge.get("type", ""), "#7b82a0")
        line_color = HIGHLIGHT_COL if is_highlighted else base_color
        if highlight_route and not is_highlighted:
            line_color = "#3b4258"
        lw = LINE_W_ROUTE if is_highlighted else (LINE_W_MUTED if highlight_route else LINE_W_NORMAL)

        x1, y1, cx, cy, x2, y2, nx, ny = _edge_curve_points(src, dst)

        shadow_id = canvas.create_line(
            x1, y1, cx, cy, x2, y2,
            fill="#0c1018", width=lw + 5,
            capstyle="round", joinstyle="round", smooth=True,
            tags=("edge_shadow",)
        )
        line_id = canvas.create_line(
            x1, y1, cx, cy, x2, y2,
            fill=line_color, width=lw,
            capstyle="round", joinstyle="round", smooth=True,
            tags=("edge", f"edge_{src}_{dst}")
        )

        label_x = cx + nx * 12
        label_y = cy + ny * 12
        label_state = "normal" if is_highlighted else "hidden"
        bg_id = canvas.create_oval(
            label_x - 18, label_y - 10,
            label_x + 18, label_y + 10,
            fill="#151a27", outline=HIGHLIGHT_COL if is_highlighted else base_color, width=1,
            state=label_state,
            tags=("edge_label",)
        )
        txt_id = canvas.create_text(
            label_x, label_y,
            text=f"{edge['time']}m",
            font=("Helvetica", 8, "bold"),
            fill=TEXT_LIGHT,
            state=label_state,
            tags=("edge_label",)
        )

        key = (src, dst)
        edge_items[key] = [shadow_id, line_id, bg_id, txt_id]
        edge_meta[key]  = edge

    # ════════════════════════════════════════════════════════════
    #  DESENARE NODURI
    # ════════════════════════════════════════════════════════════

    node_items = {}   # name -> dict cu item ids

    for name, (px, py) in positions.items():
        on_route  = highlight_route and name in highlight_route
        lc        = node_line_color(name)
        ring_col  = HIGHLIGHT_COL if on_route else "#ffffff"
        inner_col = HIGHLIGHT_COL if on_route else lc

        # Umbra subtilă
        shadow = canvas.create_oval(
            px - NODE_R - 1, py - NODE_R - 1,
            px + NODE_R + 3, py + NODE_R + 3,
            fill="#0d1018", outline="", tags=("node_shadow", f"ns_{name}")
        )
        # Inel exterior alb
        ring = canvas.create_oval(
            px - NODE_R, py - NODE_R,
            px + NODE_R, py + NODE_R,
            fill=ring_col, outline="", tags=("node_ring", f"nr_{name}")
        )
        # Cerc interior colorat
        inner = canvas.create_oval(
            px - NODE_INNER_R, py - NODE_INNER_R,
            px + NODE_INNER_R, py + NODE_INNER_R,
            fill=inner_col, outline="", tags=("node_inner", f"ni_{name}")
        )
        # Eticheta stație
        # Poziționare inteligentă: stațiile din stânga – text la stânga
        anchor  = "w" if px < W * 0.55 else "e"
        lbl_off = NODE_R + 5 if anchor == "w" else -(NODE_R + 5)
        label = canvas.create_text(
            px + lbl_off, py,
            text=name,
            font=("Helvetica", 9, "bold"),
            fill=HIGHLIGHT_COL if on_route else TEXT_LIGHT,
            anchor=anchor,
            tags=("node_label", f"nl_{name}")
        )

        node_items[name] = {
            "shadow": shadow, "ring": ring,
            "inner": inner,   "label": label,
            "px": px, "py": py,
            "line_color": lc,
            "on_route": on_route,
        }

    # ── Indicator rută activă ─────────────────────────────────────
    if highlight_route:
        route_str = "  ●  " + "  →  ".join(highlight_route)
        canvas.create_text(
            W // 2, H - 18,
            text=route_str,
            font=("Helvetica", 9, "bold"),
            fill=HIGHLIGHT_COL,
            anchor="center"
        )

    # ════════════════════════════════════════════════════════════
    #  INTERACTIVITATE – hover pe stație
    # ════════════════════════════════════════════════════════════

    hovered = {"node": None}

    def _get_node_at(ex, ey):
        """Returnează numele stației sub cursor, sau None."""
        for name, it in node_items.items():
            if math.hypot(ex - it["px"], ey - it["py"]) <= NODE_R + 6:
                return name
        return None

    def _reset_node(name):
        it = node_items[name]
        on_route = it["on_route"]
        canvas.itemconfig(it["ring"],  fill=HIGHLIGHT_COL if on_route else "#ffffff")
        canvas.itemconfig(it["inner"], fill=HIGHLIGHT_COL if on_route else it["line_color"])
        canvas.itemconfig(it["label"], fill=HIGHLIGHT_COL if on_route else TEXT_LIGHT,
                          font=("Helvetica", 9, "bold"))
        # Resetează liniile adiacente
        for (src, dst), ids in edge_items.items():
            if src == name or dst == name:
                is_hl = (src, dst) in highlighted_edges or (dst, src) in highlighted_edges
                col = HIGHLIGHT_COL if is_hl else TRANSPORT_COLORS.get(
                    edge_meta[(src, dst)].get("type", ""), "#7b82a0")
                if highlight_route and not is_hl:
                    col = "#3b4258"
                lw  = LINE_W_ROUTE if is_hl else (LINE_W_MUTED if highlight_route else LINE_W_NORMAL)
                label_state = "normal" if is_hl else "hidden"
                canvas.itemconfig(ids[0], width=lw + 5)
                canvas.itemconfig(ids[1], fill=col, width=lw)
                canvas.itemconfig(ids[2], outline=HIGHLIGHT_COL if is_hl else col, state=label_state)
                canvas.itemconfig(ids[3], fill=TEXT_LIGHT, state=label_state)

    def _highlight_node(name):
        it = node_items[name]
        canvas.itemconfig(it["ring"],  fill=HOVER_GLOW)
        canvas.itemconfig(it["inner"], fill=HIGHLIGHT_COL)
        canvas.itemconfig(it["label"], fill=HOVER_GLOW,
                          font=("Helvetica", 10, "bold"))
        # Evidențiază liniile adiacente
        for (src, dst), ids in edge_items.items():
            if src == name or dst == name:
                canvas.itemconfig(ids[0], width=LINE_W_HOVER + 5)
                canvas.itemconfig(ids[1], fill=HIGHLIGHT_COL, width=LINE_W_HOVER)
                canvas.itemconfig(ids[2], outline=HIGHLIGHT_COL, state="normal")
                canvas.itemconfig(ids[3], fill=TEXT_LIGHT, state="normal")

    def _build_info(name):
        """Construiește textul pentru bara de info."""
        outgoing = graph.get(name, [])
        if not outgoing:
            return f"  {name}  –  nicio legătură disponibilă"
        parts = []
        for e in outgoing:
            parts.append(f"{e['to']} ({e['time']}min, {e['cost']}lei, {e.get('type','')})")
        connections = "   |   ".join(parts)
        return f"  ● {name}    →    {connections}"

    def on_motion(event):
        node = _get_node_at(event.x, event.y)
        prev = hovered["node"]
        if node == prev:
            return
        if prev:
            _reset_node(prev)
        if node:
            _highlight_node(node)
            info_lbl.config(text=_build_info(node), fg=TEXT_LIGHT)
        else:
            info_lbl.config(
                text="Treci cu mouse-ul peste o stație pentru detalii",
                fg=TEXT_DIM)
        hovered["node"] = node

    canvas.bind("<Motion>", on_motion)


# ─────────────────────────────────────────────
#  DIALOG ADAUGARE STATIE / RUTA
# ─────────────────────────────────────────────

class AddEdgeDialog(tk.Toplevel):
    """Dialog pentru adaugarea unei rute noi (statie sursa → destinatie)."""

    def __init__(self, parent, graph, refresh_cb):
        super().__init__(parent)
        self.title("Adauga ruta noua")
        self.resizable(False, False)
        self.graph = graph
        self.refresh_cb = refresh_cb
        self.result = None

        pad = {"padx": 8, "pady": 5}
        stations = sorted(graph.keys())

        # ── Statie sursa ──────────────────────────────────────────
        ttk.Label(self, text="De la statia:").grid(row=0, column=0, sticky="e", **pad)
        self.from_var = tk.StringVar()
        self.from_combo = ttk.Combobox(self, textvariable=self.from_var,
                                       values=stations + ["[ Statie noua... ]"],
                                       state="readonly", width=28)
        self.from_combo.grid(row=0, column=1, **pad)
        self.from_combo.bind("<<ComboboxSelected>>", self._on_from_changed)

        self.new_from_var = tk.StringVar()
        self.new_from_entry = ttk.Entry(self, textvariable=self.new_from_var, width=30)

        # ── Statie destinatie ─────────────────────────────────────
        ttk.Label(self, text="Spre statia:").grid(row=2, column=0, sticky="e", **pad)
        self.to_var = tk.StringVar()
        self.to_combo = ttk.Combobox(self, textvariable=self.to_var,
                                     values=stations + ["[ Statie noua... ]"],
                                     state="readonly", width=28)
        self.to_combo.grid(row=2, column=1, **pad)
        self.to_combo.bind("<<ComboboxSelected>>", self._on_to_changed)

        self.new_to_var = tk.StringVar()
        self.new_to_entry = ttk.Entry(self, textvariable=self.new_to_var, width=30)

        # ── Detalii muchie ────────────────────────────────────────
        ttk.Label(self, text="Timp (minute):").grid(row=4, column=0, sticky="e", **pad)
        self.time_var = tk.IntVar(value=10)
        ttk.Spinbox(self, from_=1, to=120, textvariable=self.time_var, width=10).grid(row=4, column=1, sticky="w", **pad)

        ttk.Label(self, text="Cost (lei):").grid(row=5, column=0, sticky="e", **pad)
        self.cost_var = tk.DoubleVar(value=4.0)
        ttk.Spinbox(self, from_=0.0, to=50.0, increment=0.5,
                    textvariable=self.cost_var, width=10).grid(row=5, column=1, sticky="w", **pad)

        ttk.Label(self, text="Tip transport:").grid(row=6, column=0, sticky="e", **pad)
        self.type_var = tk.StringVar(value="autobuz")
        ttk.Combobox(self, textvariable=self.type_var,
                     values=["autobuz", "tramvai", "mers pe jos", "metrou", "bicicleta"],
                     state="readonly", width=18).grid(row=6, column=1, sticky="w", **pad)

        ttk.Label(self, text="Program (ex: 08:00,08:30):").grid(row=7, column=0, sticky="e", **pad)
        self.sched_var = tk.StringVar(value="08:00,08:30,09:00")
        ttk.Entry(self, textvariable=self.sched_var, width=30).grid(row=7, column=1, **pad)

        ttk.Label(self, text="Bidirectional:").grid(row=8, column=0, sticky="e", **pad)
        self.bidir_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, variable=self.bidir_var).grid(row=8, column=1, sticky="w", **pad)

        # ── Butoane ───────────────────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Adauga", command=self._add).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Anuleaza", command=self.destroy).pack(side="left", padx=5)

        self.grab_set()

    def _on_from_changed(self, _=None):
        if self.from_var.get() == "[ Statie noua... ]":
            self.new_from_entry.grid(row=1, column=1, padx=8, pady=2)
        else:
            self.new_from_entry.grid_remove()

    def _on_to_changed(self, _=None):
        if self.to_var.get() == "[ Statie noua... ]":
            self.new_to_entry.grid(row=3, column=1, padx=8, pady=2)
        else:
            self.new_to_entry.grid_remove()

    def _add(self):
        src = (self.new_from_var.get().strip()
               if self.from_var.get() == "[ Statie noua... ]"
               else self.from_var.get())
        dst = (self.new_to_var.get().strip()
               if self.to_var.get() == "[ Statie noua... ]"
               else self.to_var.get())

        if not src or not dst:
            messagebox.showerror("Eroare", "Completeaza statia sursa si destinatia.", parent=self)
            return
        if src == dst:
            messagebox.showerror("Eroare", "Sursa si destinatia nu pot fi aceeasi statie.", parent=self)
            return

        try:
            t = int(self.time_var.get())
            c = float(self.cost_var.get())
        except ValueError:
            messagebox.showerror("Eroare", "Timp si cost trebuie sa fie numere.", parent=self)
            return

        schedule = [s.strip() for s in self.sched_var.get().split(",") if s.strip()]
        if not schedule:
            schedule = ["oricand"]

        edge = {"to": dst, "time": t, "cost": c,
                "type": self.type_var.get(), "schedule": schedule}

        self.graph.setdefault(src, []).append(edge)
        if src not in self.graph:
            self.graph[src] = []

        # Adauga si destinatia ca nod (fara muchii) daca nu exista
        self.graph.setdefault(dst, [])

        if self.bidir_var.get():
            reverse = {"to": src, "time": t, "cost": c,
                       "type": self.type_var.get(), "schedule": schedule}
            self.graph[dst].append(reverse)

        self.refresh_cb()
        messagebox.showinfo("Succes",
                            f"Ruta {'bidirectionala' if self.bidir_var.get() else 'unidirectionala'} "
                            f"{src} ↔ {dst} adaugata.", parent=self)
        self.destroy()


# ─────────────────────────────────────────────
#  APLICATIA PRINCIPALA
# ─────────────────────────────────────────────

class TransportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistem de planificare transport studenti")
        self.root.geometry("980x720")

        self.graph = load_graph_from_file(DATA_FILE)
        self.planner = RoutePlanner(self.graph)
        self.simulator = ScenarioSimulator(self.graph)

        # ── Titlu ─────────────────────────────────────────────────
        ttk.Label(root,
                  text="Sistem de planificare a transportului local pentru studenti",
                  font=("Arial", 14, "bold")).pack(pady=8)

        # ── Selectie statie ───────────────────────────────────────
        frame = ttk.Frame(root)
        frame.pack(pady=4)

        ttk.Label(frame, text="Statie plecare:").grid(row=0, column=0, padx=5, pady=4)
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(frame, textvariable=self.start_var,
                                        values=list(self.graph.keys()),
                                        state="readonly", width=30)
        self.start_combo.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(frame, text="Statie destinatie:").grid(row=1, column=0, padx=5, pady=4)
        self.end_var = tk.StringVar()
        self.end_combo = ttk.Combobox(frame, textvariable=self.end_var,
                                      values=list(self.graph.keys()),
                                      state="readonly", width=30)
        self.end_combo.grid(row=1, column=1, padx=5, pady=4)

        # ── Butoane ───────────────────────────────────────────────
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=6)

        # Rand 1 – algoritmi
        ttk.Button(btn_frame, text="⏱  Minim timp",      command=self.shortest_time).grid(row=0, column=0, padx=5, pady=4)
        ttk.Button(btn_frame, text="💰 Minim cost",       command=self.cheapest_route).grid(row=0, column=1, padx=5, pady=4)
        ttk.Button(btn_frame, text="🚏 Minim opriri",     command=self.min_stops).grid(row=0, column=2, padx=5, pady=4)
        ttk.Button(btn_frame, text="⭐ Ruta recomandata", command=self.recommended_route).grid(row=0, column=3, padx=5, pady=4)
        ttk.Button(btn_frame, text="📊 Compara toti",     command=self.compare_all).grid(row=0, column=4, padx=5, pady=4)

        # Rand 2 – simulare
        ttk.Button(btn_frame, text="⏳ Simuleaza intarziere", command=self.gui_delay).grid(row=1, column=0, padx=5, pady=4)
        ttk.Button(btn_frame, text="💸 Creste cost ruta",     command=self.gui_cost_increase).grid(row=1, column=1, padx=5, pady=4)
        ttk.Button(btn_frame, text="🚫 Inchide statie",       command=self.gui_close_station).grid(row=1, column=2, padx=5, pady=4)

        # Rand 3 – retea / date
        ttk.Button(btn_frame, text="🗺  Afiseaza retea (text)", command=self.show_network).grid(row=2, column=0, padx=5, pady=4)
        ttk.Button(btn_frame, text="🔵 Vizualizeaza graf",      command=self.visualize_graph).grid(row=2, column=1, padx=5, pady=4)
        ttk.Button(btn_frame, text="➕ Adauga ruta noua",       command=self.add_route).grid(row=2, column=2, padx=5, pady=4)
        ttk.Button(btn_frame, text="💾 Salveaza reteaua",       command=self.save_network).grid(row=2, column=3, padx=5, pady=4)
        ttk.Button(btn_frame, text="🔄 Resetare retea",         command=self.reset_network).grid(row=2, column=4, padx=5, pady=4)

        # ── Zona rezultate ────────────────────────────────────────
        self.result = tk.Text(root, height=22, width=118, font=("Courier New", 9))
        self.result.pack(pady=8, padx=10)

        self.show_result("Alege statia de plecare si destinatia, apoi selecteaza criteriul de optimizare.\n"
                         "Foloseste 'Compara toti' pentru a vedea toti algoritmii simultan.\n"
                         "Foloseste 'Vizualizeaza graf' pentru a vedea harta retelei.\n"
                         "Datele sunt salvate separat in routes_student_project_v2.json, ca sa nu incarce versiuni vechi.")

    # ── Utilitare UI ──────────────────────────────────────────────

    def refresh_stations(self):
        stations = list(self.graph.keys())
        self.start_combo["values"] = stations
        self.end_combo["values"] = stations
        if self.start_var.get() not in stations:
            self.start_var.set("")
        if self.end_var.get() not in stations:
            self.end_var.set("")
        self.planner = RoutePlanner(self.graph)
        self.simulator = ScenarioSimulator(self.graph)

    def show_result(self, text):
        self.result.delete("1.0", tk.END)
        self.result.insert(tk.END, text)

    def validate_selection(self):
        start = self.start_var.get()
        end = self.end_var.get()
        if not start or not end:
            messagebox.showwarning("Atentie", "Alege statia de plecare si statia destinatie.")
            return None, None
        return start, end

    def format_route(self, title, result):
        if not result:
            return "Nu exista ruta pentru selectia facuta."
        text = f"{'─'*60}\n{title}\n{'─'*60}\n\n"
        text += "Ruta:  " + " → ".join(result["route"]) + "\n\n"
        if "time"  in result: text += f"  Timp total  : {result['time']} minute\n"
        if "cost"  in result: text += f"  Cost total  : {result['cost']} lei\n"
        if "score" in result: text += f"  Scor ruta   : {result['score']:.1f}\n"
        if "stops" in result: text += f"  Nr. opriri  : {result['stops']}\n"
        details = self.planner.get_route_details(result["route"])
        if details:
            text += "\n  Detalii segment cu segment:\n"
            for edge in details:
                text += (f"    → {edge['to']:25s} | {edge['time']:3d} min | "
                         f"{edge['cost']:4.1f} lei | {edge.get('type','N/A'):15s} | "
                         f"{', '.join(edge.get('schedule',[]))}\n")
        return text

    # ── Algoritmi ─────────────────────────────────────────────────

    def shortest_time(self):
        start, end = self.validate_selection()
        if not start: return
        result = self.planner.find_shortest_time(start, end)
        self.show_result(self.format_route("⏱  RUTA OPTIMA DUPA TIMP  (Dijkstra)", result))
        if result:
            open_graph_window(self.graph, highlight_route=result["route"])

    def cheapest_route(self):
        start, end = self.validate_selection()
        if not start: return
        result = self.planner.find_cheapest_route(start, end)
        self.show_result(self.format_route("💰 RUTA OPTIMA DUPA COST  (Dijkstra)", result))
        if result:
            open_graph_window(self.graph, highlight_route=result["route"])

    def min_stops(self):
        start, end = self.validate_selection()
        if not start: return
        result = self.planner.find_min_stops(start, end)
        self.show_result(self.format_route("🚏 RUTA CU CELE MAI PUTINE OPRIRI  (BFS)", result))
        if result:
            open_graph_window(self.graph, highlight_route=result["route"])

    def recommended_route(self):
        start, end = self.validate_selection()
        if not start: return
        result = self.planner.find_recommended_route(start, end)
        self.show_result(self.format_route("⭐ RUTA RECOMANDATA PENTRU STUDENTI  (Dijkstra scor realist)", result))
        if result:
            open_graph_window(self.graph, highlight_route=result["route"])

    # ── NOU: Comparatie algoritmi ─────────────────────────────────

    def compare_all(self):
        start, end = self.validate_selection()
        if not start: return

        results = self.planner.compare_all(start, end)

        text = f"{'═'*70}\n"
        text += f"  COMPARATIE ALGORITMI: {start}  →  {end}\n"
        text += f"{'═'*70}\n\n"

        labels = {
            "Minim timp (Dijkstra)":   ("⏱ ", "timp"),
            "Minim cost (Dijkstra)":   ("💰", "cost"),
            "Recomandata (scor realist)":  ("⭐", "scor realist"),
            "Minim opriri (BFS)":      ("🚏", "opriri"),
        }

        for algo_name, r in results.items():
            icon, criteriu = labels[algo_name]
            text += f"{icon}  {algo_name}\n"
            if not r:
                text += "    ✗  Nu exista ruta.\n\n"
                continue
            text += "    Ruta   : " + " → ".join(r["route"]) + "\n"
            if "time"  in r: text += f"    Timp   : {r['time']} min\n"
            if "cost"  in r: text += f"    Cost   : {r['cost']} lei\n"
            if "score" in r: text += f"    Scor   : {r['score']:.1f}\n"
            if "stops" in r: text += f"    Opriri : {r['stops']}\n"
            text += "\n"

        # Sumar comparativ
        valid = {k: v for k, v in results.items() if v}
        if len(valid) > 1:
            text += f"{'─'*70}\n  SUMAR COMPARATIV:\n{'─'*70}\n"
            times = {k: v.get("time") for k, v in valid.items() if v.get("time") is not None}
            costs = {k: v.get("cost") for k, v in valid.items() if v.get("cost") is not None}
            stops = {k: v.get("stops") for k, v in valid.items() if v.get("stops") is not None}
            if times:
                best_t = min(times, key=times.get)
                text += f"  ⏱  Cel mai rapid : {best_t}  ({times[best_t]} min)\n"
            if costs:
                best_c = min(costs, key=costs.get)
                text += f"  💰 Cel mai ieftin : {best_c}  ({costs[best_c]} lei)\n"
            if stops:
                best_s = min(stops, key=stops.get)
                text += f"  🚏 Cel mai direct: {best_s}  ({stops[best_s]} opriri)\n"
            text += "\n  ℹ  Dijkstra garanteaza optimul global pentru timp/cost.\n"
            text += "     BFS garanteaza minimul de opriri (fara pondere pe muchii).\n"

        self.show_result(text)

    # ── Simulare cu efect inainte/dupa ─────────────────────────────

    def _show_scenario_effect(self, scenario_desc, start, end):
        """Calculeaza ruta optima inainte si dupa scenariu si afiseaza diferenta."""
        before = self.planner.find_recommended_route(start, end)

        # Scenariu deja aplicat la momentul apelului; recalculeaza
        after = self.planner.find_recommended_route(start, end)

        text = f"{'─'*60}\n  SCENARIU: {scenario_desc}\n{'─'*60}\n\n"
        text += f"  Ruta recalculata ({start} → {end}):\n\n"

        if before and after:
            before_route = " → ".join(before["route"])
            after_route  = " → ".join(after["route"])
            route_changed = before_route != after_route

            text += f"  Inainte : {before_route}\n"
            text += f"    Timp: {before.get('time','?')} min  |  Cost: {before.get('cost','?')} lei\n\n"
            text += f"  Dupa    : {after_route}\n"
            text += f"    Timp: {after.get('time','?')} min  |  Cost: {after.get('cost','?')} lei\n\n"

            if route_changed:
                text += "  ⚠  Ruta recomandata s-a SCHIMBAT dupa aplicarea scenariului!\n"
            else:
                dt = (after.get("time", 0) or 0) - (before.get("time", 0) or 0)
                dc = (after.get("cost", 0) or 0) - (before.get("cost", 0) or 0)
                if dt == 0 and dc == 0:
                    text += "  ✓  Scenariul nu a afectat ruta recomandata.\n"
                else:
                    text += f"  ⚠  Aceeasi ruta, dar: +{dt} min, +{dc:.1f} lei fata de inainte.\n"
        else:
            text += "  Nu s-a putut calcula ruta inainte sau dupa scenariu.\n"

        self.show_result(text)

    def gui_delay(self):
        start, end = self.validate_selection()
        if not start: return
        before = self.planner.find_recommended_route(start, end)
        delay = simpledialog.askinteger("Intarziere", "Cate minute de intarziere se adauga pe segmentul selectat?")
        if delay is None: return
        ok = self.simulator.simulate_delay(start, end, delay)
        if ok:
            after = self.planner.find_recommended_route(start, end)
            self._show_before_after(f"Intarziere +{delay} min pe {start} → {end}", before, after, start, end)
        else:
            self.show_result("Legatura directa selectata nu exista in retea.\nVerifica statiile alese si incearca din nou.")

    def gui_cost_increase(self):
        start, end = self.validate_selection()
        if not start: return
        before = self.planner.find_recommended_route(start, end)
        extra_cost = simpledialog.askfloat("Crestere cost", "Cu cati lei creste costul pe segmentul selectat?")
        if extra_cost is None: return
        ok = self.simulator.simulate_cost_increase(start, end, extra_cost)
        if ok:
            after = self.planner.find_recommended_route(start, end)
            self._show_before_after(f"Cost +{extra_cost} lei pe {start} → {end}", before, after, start, end)
        else:
            self.show_result("Legatura directa selectata nu exista in retea.")

    def _show_before_after(self, scenario_desc, before, after, start, end):
        text = f"{'─'*62}\n  SCENARIU: {scenario_desc}\n{'─'*62}\n\n"
        if before:
            text += f"  INAINTE  : {' → '.join(before['route'])}\n"
            text += f"    Timp: {before.get('time','?')} min   Cost: {before.get('cost','?')} lei\n\n"
        if after:
            text += f"  DUPA     : {' → '.join(after['route'])}\n"
            text += f"    Timp: {after.get('time','?')} min   Cost: {after.get('cost','?')} lei\n\n"
        if before and after:
            if before["route"] != after["route"]:
                text += "  ⚠  Ruta recomandata s-a SCHIMBAT dupa scenariu!\n"
            else:
                dt = (after.get("time") or 0) - (before.get("time") or 0)
                dc = (after.get("cost") or 0) - (before.get("cost") or 0)
                text += f"  Aceeasi ruta: +{dt} min, +{dc:.1f} lei fata de inainte.\n"
        self.show_result(text)

    def gui_close_station(self):
        station = self.start_var.get()
        if not station:
            messagebox.showwarning("Atentie", "Alege in campul 'Statie plecare' statia care se inchide.")
            return
        if not messagebox.askyesno("Confirmare", f"Sigur inchizi statia '{station}'?\nAceasta actiune modifica reteaua!"):
            return
        ok = self.simulator.simulate_station_closure(station)
        if ok:
            self.refresh_stations()
            self.show_result(f"Scenariu aplicat: statia '{station}' a fost inchisa.\n"
                             f"Toate legaturile catre si de la aceasta statie au fost eliminate.\n\n"
                             f"Recalculeaza rutele pentru a vedea impactul.")
        else:
            self.show_result("Statia nu a fost gasita in retea.")

    # ── Vizualizare graf ──────────────────────────────────────────

    def visualize_graph(self):
        open_graph_window(self.graph, highlight_route=None)

    # ── Adaugare ruta ─────────────────────────────────────────────

    def add_route(self):
        AddEdgeDialog(self.root, self.graph, self.refresh_stations)

    # ── Retea text ────────────────────────────────────────────────

    def show_network(self):
        text = "═"*60 + "\n  RETEA DE TRANSPORT\n" + "═"*60 + "\n\n"
        for station, edges in self.graph.items():
            text += f"  {station}:\n"
            if not edges:
                text += "    (fara legaturi)\n"
            else:
                for edge in edges:
                    text += (f"    → {edge['to']:25s} | {edge['time']:3d} min | "
                             f"{edge['cost']:4.1f} lei | {edge.get('type','N/A'):15s} | "
                             f"{', '.join(edge.get('schedule',[]))}\n")
            text += "\n"
        self.show_result(text)

    # ── Salvare / resetare ────────────────────────────────────────

    def save_network(self):
        try:
            save_graph_to_file(self.graph, DATA_FILE)
            messagebox.showinfo("Salvare", "Reteaua a fost salvata in routes_student_project_v2.json.")
        except Exception as e:
            messagebox.showerror("Eroare", f"Nu s-a putut salva: {e}")

    def reset_network(self):
        if not messagebox.askyesno("Resetare", "Sigur vrei sa resetezi reteaua la valorile implicite?"):
            return
        self.graph.clear()
        self.graph.update(create_default_graph())
        self.refresh_stations()
        save_graph_to_file(self.graph, DATA_FILE)
        self.show_result("Reteaua a fost resetata la varianta implicita si salvata in fisierul nou.")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = TransportApp(root)
    root.mainloop()
