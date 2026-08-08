from PySide6.QtCore    import Qt, QThread, Signal, QEvent, QSettings, QTimer
from PySide6.QtGui     import QTextCursor, QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPlainTextEdit, QLineEdit, QPushButton, QLabel, QCheckBox, QComboBox,
)

import json
import urllib.request
import urllib.error

_SYSTEM_PROMPT = (
    "You are an expert X3D scene authoring assistant embedded in the RawKee "
    "X3D Interaction Editor. Help the user build X3D scenes, write ROUTE "
    "statements, configure node fields, and understand the X3D event model.\n\n"
    "When editing the scene use these local tools — they operate on the editor's in-memory X3D object:\n"
    "- Use 'create_node' to create any X3D node (with optional parent_def and field).\n"
    "- Use 'set_field' to change a field value on an existing node.\n"
    "- Use 'add_route' to connect two nodes with a ROUTE.\n"
    "IMPORTANT: If an MCP server is connected, its tools operate on a SEPARATE remote scene. "
    "NEVER use MCP tools (create_scene, compose_scene, modify_x3d_node, etc.) to build the local editor scene. "
    "Always use the local tools above for all scene editing.\n\n"
    "IMPORTANT — tool-calling rules:\n"
    "You MUST call tools using the tool-calling API. "
    "NEVER describe a tool call as JSON, markdown, a code block, or Python code. "
    "Do not write 'I will call add_node' or show JSON like {\"name\": \"add_node\"}. "
    "Just invoke the tool directly. If you cannot call tools, say so.\n\n"
    "CRITICAL X3D hierarchy rules — always follow these exactly:\n"
    "- Shape goes in Transform.children (field='children').\n"
    "- Appearance goes in Shape.appearance (field='appearance'). NEVER add Appearance to Transform or Group.\n"
    "- Material goes in Appearance.material (field='material'). Use Material by default; only use PhysicalMaterial or UnlitMaterial when the user explicitly asks.\n"
    "- ImageTexture/MovieTexture goes in Appearance.texture (field='texture').\n"
    "- Geometry nodes (Box, Sphere, Cone, Cylinder, IndexedFaceSet, etc.) go in Shape.geometry (field='geometry').\n"
    "- TimeSensor, Script, and sensors go in Transform.children or scene root.\n\n"
    "SCENE AUTHORING PATTERNS — when asked to add a visible shape, always execute ALL "
    "of these steps in sequence using create_node, without stopping:\n"
    "  1. create_node Transform (or use an existing one the user specified)\n"
    "  2. create_node Shape       parent_def=<Transform DEF>   field='children'\n"
    "  3. create_node Appearance  parent_def=<Shape DEF>        field='appearance'\n"
    "  4. create_node Material    parent_def=<Appearance DEF>   field='material'\n"
    "     (use PhysicalMaterial only if the user says 'physical' or 'PBR'; "
    "     use UnlitMaterial only if the user says 'unlit' or 'flat')\n"
    "  5. create_node <geometry>  parent_def=<Shape DEF>        field='geometry'\n"
    "  6. set_field <Material DEF> diffuseColor [r,g,b]  — only if the user specified a color\n"
    "     (for PhysicalMaterial use baseColor instead of diffuseColor)\n"
    "  7. set_field <Transform DEF> translation [x,y,z]  — only if the user specified a translation\n"
    "  8. set_field <Transform DEF> scale [x,y,z]        — only if the user specified a scale\n"
    "  9. set_field <Transform DEF> rotation [x,y,z,a]   — only if the user specified a rotation\n"
    "Execute every step before replying. Do not stop after one step and ask for confirmation.\n\n"
    "If a tool call fails, read the error carefully — it tells you the correct parent and field. "
    "Do NOT retry the exact same call. Adjust the parent_def and field based on the error. "
    "Never call a remove or delete tool when the user asks to add something. "
    "IMPORTANT: Only call set_field when the user explicitly asks you to set a specific field value. "
    "Do NOT call set_field after create_node to configure default values — nodes come with sensible defaults. "
    "IMPORTANT: Only call add_route when the user explicitly asks to connect nodes with a ROUTE. "
    "Do NOT add ROUTEs automatically. Never invent nodes like 'Clock' or 'X3DSceneRoot' that do not exist in the scene. "
    "Be concise in your replies."
)

_MAX_TOOL_ITERS = 12

_TOOL_NAMES = {"add_node", "create_node", "add_child", "set_field", "add_route"}

# Common wrong names models use → correct X3D class names
_NODE_TYPE_ALIASES = {
    "Cube":        "Box",
    "Rectangle":   "Box",
    "Rect":        "Box",
    "Circle":      "Sphere",
    "Ellipse":     "Sphere",
    "Triangle":    "Cone",
    "Plane":       "Box",
    "Mesh":        "IndexedFaceSet",
}


def _extract_phantom_calls(content: str) -> list[dict]:
    """Parse tool calls the model wrote as text/JSON instead of invoking via API."""
    import re
    calls = []
    _ARG_KEYS = ("arguments", "params", "parameters", "input", "args")

    def _parse_obj(obj):
        if not isinstance(obj, dict):
            return None
        name = obj.get("name")
        if name not in _TOOL_NAMES:
            return None
        args = next((obj[k] for k in _ARG_KEYS if isinstance(obj.get(k), dict)), None)
        if args is None:
            args = {k: v for k, v in obj.items() if k not in ("name",) + _ARG_KEYS}
        if "node_type" in args and isinstance(args["node_type"], dict):
            args = dict(args)
            args["node_type"] = next(iter(args["node_type"]), "")
        return {"name": name, "arguments": args}

    # Pattern 1: fenced code blocks
    for block in re.findall(r'```[a-z]*\n(.*?)```', content, re.DOTALL):
        block = block.strip()
        if not block.startswith('{'):
            continue
        try:
            obj = json.loads(re.sub(r'//[^\n]*', '', block))
            result = _parse_obj(obj)
            if result:
                calls.append(result)
        except json.JSONDecodeError:
            pass

    # Pattern 2: bare inline JSON objects (not in code blocks)
    stripped = re.sub(r'```[a-z]*\n.*?```', '', content, flags=re.DOTALL)
    # Match objects up to two levels of nesting
    for match in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', stripped):
        text = match.group()
        if '"name"' not in text:
            continue
        try:
            obj = json.loads(re.sub(r'//[^\n]*', '', text))
            result = _parse_obj(obj)
            if result and result not in calls:
                calls.append(result)
        except json.JSONDecodeError:
            pass

    return calls
    return calls


# Hints returned to the model when add_node fails, keyed by node type.
_X3D_PARENT_HINTS = {
    # --- Shape branch ---
    "Shape":              "Shape goes in a grouping node using field='children'.",
    "Appearance":         "Appearance goes in Shape using field='appearance'.",

    # --- Material / surface ---
    "Material":             "Material goes in Appearance using field='material'.",
    "PhysicalMaterial":     "PhysicalMaterial goes in Appearance using field='material'.",
    "PhysicalMaterialExt":  "PhysicalMaterialExt goes in Appearance using field='material'.",
    "UnlitMaterial":        "UnlitMaterial goes in Appearance using field='material'.",
    "TwoSidedMaterial":     "TwoSidedMaterial goes in Appearance using field='material'.",
    "FillProperties":       "FillProperties goes in Appearance using field='fillProperties'.",
    "LineProperties":       "LineProperties goes in Appearance using field='lineProperties'.",
    "PointProperties":      "PointProperties goes in Appearance using field='pointProperties'.",

    # --- Textures ---
    "ImageTexture":         "ImageTexture goes in Appearance using field='texture'.",
    "ImageTexture3D":       "ImageTexture3D goes in Appearance using field='texture'.",
    "MovieTexture":         "MovieTexture goes in Appearance using field='texture'.",
    "PixelTexture":         "PixelTexture goes in Appearance using field='texture'.",
    "MultiTexture":         "MultiTexture goes in Appearance using field='texture'.",
    "TextureTransform":     "TextureTransform goes in Appearance using field='textureTransform'.",
    "MultiTextureTransform":"MultiTextureTransform goes in Appearance using field='textureTransform'.",

    # --- Geometry nodes (all go in Shape.geometry) ---
    "Box":                  "Box is a geometry node; add it to Shape using field='geometry'.",
    "Sphere":               "Sphere is a geometry node; add it to Shape using field='geometry'.",
    "Cone":                 "Cone is a geometry node; add it to Shape using field='geometry'.",
    "Cylinder":             "Cylinder is a geometry node; add it to Shape using field='geometry'.",
    "Text":                 "Text is a geometry node; add it to Shape using field='geometry'.",
    "ElevationGrid":        "ElevationGrid is a geometry node; add it to Shape using field='geometry'.",
    "Extrusion":            "Extrusion is a geometry node; add it to Shape using field='geometry'.",
    "IndexedFaceSet":       "IndexedFaceSet is a geometry node; add it to Shape using field='geometry'.",
    "IndexedLineSet":       "IndexedLineSet is a geometry node; add it to Shape using field='geometry'.",
    "IndexedTriangleSet":   "IndexedTriangleSet is a geometry node; add it to Shape using field='geometry'.",
    "IndexedTriangleFanSet":"IndexedTriangleFanSet is a geometry node; add it to Shape using field='geometry'.",
    "IndexedTriangleStripSet":"IndexedTriangleStripSet is a geometry node; add it to Shape using field='geometry'.",
    "LineSet":              "LineSet is a geometry node; add it to Shape using field='geometry'.",
    "PointSet":             "PointSet is a geometry node; add it to Shape using field='geometry'.",
    "TriangleSet":          "TriangleSet is a geometry node; add it to Shape using field='geometry'.",
    "TriangleFanSet":       "TriangleFanSet is a geometry node; add it to Shape using field='geometry'.",
    "TriangleStripSet":     "TriangleStripSet is a geometry node; add it to Shape using field='geometry'.",
    "GeoElevationGrid":     "GeoElevationGrid is a geometry node; add it to Shape using field='geometry'.",
    "NurbsCurve":           "NurbsCurve is a geometry node; add it to Shape using field='geometry'.",
    "NurbsPatchSurface":    "NurbsPatchSurface is a geometry node; add it to Shape using field='geometry'.",

    # --- Sub-geometry helpers ---
    "Coordinate":           "Coordinate goes inside a geometry node (e.g. IndexedFaceSet) using field='coord'.",
    "CoordinateDouble":     "CoordinateDouble goes inside a geometry node using field='coord'.",
    "Color":                "Color goes inside a geometry node using field='color'.",
    "ColorRGBA":            "ColorRGBA goes inside a geometry node using field='color'.",
    "Normal":               "Normal goes inside a geometry node using field='normal'.",
    "TextureCoordinate":    "TextureCoordinate goes inside a geometry node using field='texCoord'.",
    "FontStyle":            "FontStyle goes inside a Text node using field='fontStyle'.",

    # --- Grouping nodes (go in other grouping nodes' children) ---
    "Transform":    "Transform goes in a grouping node or scene root using field='children'.",
    "Group":        "Group goes in a grouping node or scene root using field='children'.",
    "StaticGroup":  "StaticGroup goes in a grouping node or scene root using field='children'.",
    "Switch":       "Switch goes in a grouping node using field='children'. Its choices go in field='choice'.",
    "Billboard":    "Billboard goes in a grouping node using field='children'.",
    "Collision":    "Collision goes in a grouping node using field='children'.",
    "LOD":          "LOD goes in a grouping node using field='children'. Its levels go in field='level'.",
    "Anchor":       "Anchor goes in a grouping node using field='children'.",
    "Inline":       "Inline goes in a grouping node or scene root using field='children'.",

    # --- Lights ---
    "DirectionalLight": "DirectionalLight goes in a grouping node using field='children'.",
    "PointLight":       "PointLight goes in a grouping node using field='children'.",
    "SpotLight":        "SpotLight goes in a grouping node using field='children'.",

    # --- Sensors ---
    "TouchSensor":          "TouchSensor goes in a grouping node using field='children'.",
    "TimeSensor":           "TimeSensor goes in a grouping node or scene root using field='children'.",
    "KeySensor":            "KeySensor goes in a grouping node or scene root using field='children'.",
    "CylinderSensor":       "CylinderSensor goes in a grouping node using field='children'.",
    "PlaneSensor":          "PlaneSensor goes in a grouping node using field='children'.",
    "SphereSensor":         "SphereSensor goes in a grouping node using field='children'.",
    "ProximitySensor":      "ProximitySensor goes in a grouping node or scene root using field='children'.",
    "VisibilitySensor":     "VisibilitySensor goes in a grouping node using field='children'.",
    "LoadSensor":           "LoadSensor goes in a grouping node or scene root using field='children'.",

    # --- Interpolators / sequencers (usually at scene root) ---
    "ColorInterpolator":        "ColorInterpolator goes in a grouping node or scene root using field='children'.",
    "CoordinateInterpolator":   "CoordinateInterpolator goes in a grouping node or scene root using field='children'.",
    "NormalInterpolator":       "NormalInterpolator goes in a grouping node or scene root using field='children'.",
    "OrientationInterpolator":  "OrientationInterpolator goes in a grouping node or scene root using field='children'.",
    "PositionInterpolator":     "PositionInterpolator goes in a grouping node or scene root using field='children'.",
    "ScalarInterpolator":       "ScalarInterpolator goes in a grouping node or scene root using field='children'.",
    "SplinePositionInterpolator":"SplinePositionInterpolator goes in a grouping node or scene root using field='children'.",
    "SplineScalarInterpolator": "SplineScalarInterpolator goes in a grouping node or scene root using field='children'.",
    "SquadOrientationInterpolator":"SquadOrientationInterpolator goes in a grouping node or scene root using field='children'.",
    "IntegerSequencer":         "IntegerSequencer goes in a grouping node or scene root using field='children'.",
    "BooleanSequencer":         "BooleanSequencer goes in a grouping node or scene root using field='children'.",

    # --- Navigation / environment ---
    "Viewpoint":        "Viewpoint goes in a grouping node or scene root using field='children'.",
    "OrthoViewpoint":   "OrthoViewpoint goes in a grouping node or scene root using field='children'.",
    "NavigationInfo":   "NavigationInfo goes at scene root using field='children'.",
    "Background":       "Background goes at scene root using field='children'.",
    "TextureBackground":"TextureBackground goes at scene root using field='children'.",
    "Fog":              "Fog goes at scene root or in a grouping node using field='children'.",
    "WorldInfo":        "WorldInfo goes at scene root using field='children'.",

    # --- Sound ---
    "Sound":      "Sound goes in a grouping node or scene root using field='children'.",
    "AudioClip":  "AudioClip goes in a Sound node using field='source'.",
    "MovieTexture":"MovieTexture can also be used as a Sound source via field='source'.",

    # --- Scripts ---
    "Script": "Script goes in a grouping node or scene root using field='children'.",

    # --- HAnim ---
    "HAnimHumanoid": "HAnimHumanoid goes at scene root using field='children'.",
    "HAnimJoint":    "HAnimJoint goes in HAnimHumanoid (field='skeleton') or in another HAnimJoint (field='children'). "
                     "IMPORTANT: every HAnimJoint with a DEF anywhere in the skeleton branch must ALSO be added to "
                     "HAnimHumanoid field='joints' as a second node with USE=<same DEF> and no DEF of its own.",
    "HAnimSegment":  "HAnimSegment goes in HAnimHumanoid using field='segments', or as a child of HAnimJoint.",
    "HAnimDisplacer":"HAnimDisplacer goes in an HAnimSegment using field='displacers'.",
    "HAnimSite":     "HAnimSite goes in HAnimHumanoid using field='sites', or inside HAnimSegment using field='children'.",
    "HAnimMotion":   "HAnimMotion goes in HAnimHumanoid using field='motions'.",
}

_DEFAULT_ENDPOINT = "http://localhost:11434"
_DEFAULT_MODEL    = "llama3.2"

_PRESETS = {
    "Anthropic": {"endpoint": "https://api.anthropic.com", "model": "claude-opus-4-5", "needs_key": True},
    "OpenAI":    {"endpoint": "https://api.openai.com",    "model": "gpt-4o",           "needs_key": True},
    "Custom":    {"endpoint": "",                          "model": "",                 "needs_key": False},
}

_MCP_DEFAULT_URL = "https://x3d-mcp.onrender.com/mcp"

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_node",
            "description": "Create a new X3D node in the local scene. Optionally specify a parent node and field.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_type":  {"type": "string", "description": "X3D node class name, e.g. 'Transform', 'Shape', 'Sphere'."},
                    "parent_def": {"type": "string", "description": "DEF name of the parent node. Omit to add to scene root."},
                    "field":      {"type": "string", "description": "Container field on the parent (e.g. 'children'). Auto-detected if omitted."},
                },
                "required": ["node_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_field",
            "description": "Set a field value on a node identified by its DEF name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "def_name": {"type": "string", "description": "DEF name of the node to modify."},
                    "field":    {"type": "string", "description": "Field name to set."},
                    "value":    {"description": "New value for the field (use Python/JSON literal types)."},
                },
                "required": ["def_name", "field", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_route",
            "description": "Connect two nodes with a ROUTE.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_node":  {"type": "string", "description": "DEF name of the source node."},
                    "from_field": {"type": "string", "description": "Output field name."},
                    "to_node":    {"type": "string", "description": "DEF name of the destination node."},
                    "to_field":   {"type": "string", "description": "Input field name."},
                },
                "required": ["from_node", "from_field", "to_node", "to_field"],
            },
        },
    },
]



def _sanitize_tool(tool: dict) -> dict:
    """Strip JSON Schema keywords that local LLMs (e.g. Ollama) reject."""
    fn     = tool.get("function", {})
    params = fn.get("parameters", {})
    clean  = {"type": params.get("type", "object"),
              "properties": params.get("properties", {})}
    if "required" in params:
        clean["required"] = params["required"]
    return {"type": "function",
            "function": {"name":        fn.get("name", ""),
                         "description": fn.get("description", ""),
                         "parameters":  clean}}


class _MCPClient:
    """Minimal MCP client — Streamable HTTP transport (2025-03-26)."""

    _BASE_HEADERS = {
        "Content-Type": "application/json",
        "Accept":       "application/json, text/event-stream",
    }

    def __init__(self, url: str):
        self.url         = url
        self.tools       = []
        self._tool_names = set()
        self._session_id: str | None = None

    def connect(self):
        self._rpc(1, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities":    {},
            "clientInfo":      {"name": "RawKee", "version": "1.0"},
        })
        try:
            self._rpc(None, "notifications/initialized", {})
        except Exception:
            pass
        resp      = self._rpc(2, "tools/list", {})
        mcp_tools = resp.get("result", {}).get("tools", [])
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name":        t["name"],
                    "description": t.get("description", ""),
                    "parameters":  t.get("inputSchema",
                                         {"type": "object", "properties": {}, "required": []}),
                },
            }
            for t in mcp_tools
        ]
        self._tool_names = {t["function"]["name"] for t in self.tools}

    def call(self, name: str, arguments: dict) -> str:
        resp    = self._rpc(3, "tools/call", {"name": name, "arguments": arguments})
        result  = resp.get("result", {})
        content = result.get("content", [])
        if isinstance(content, list):
            return "\n".join(
                c.get("text", str(c)) for c in content if isinstance(c, dict)
            )
        return str(result)

    def _rpc(self, rpc_id, method: str, params: dict) -> dict:
        body = {"jsonrpc": "2.0", "method": method, "params": params}
        if rpc_id is not None:
            body["id"] = rpc_id
        payload = json.dumps(body).encode()
        headers = dict(self._BASE_HEADERS)
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        req = urllib.request.Request(
            self.url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            # Capture session ID returned by server on initialize
            session_hdr = resp.headers.get("Mcp-Session-Id")
            if session_hdr:
                self._session_id = session_hdr
            raw = resp.read().decode()
        if "data:" in raw:
            for line in raw.splitlines():
                if line.startswith("data:"):
                    text = line[len("data:"):].strip()
                    if text:
                        return json.loads(text)
            return {}
        return json.loads(raw) if raw.strip() else {}


class _MCPInitWorker(QThread):
    succeeded = Signal(object)
    failed    = Signal(str)

    def __init__(self, client: _MCPClient, parent=None):
        super().__init__(parent)
        self._client = client

    def run(self):
        try:
            self._client.connect()
            self.succeeded.emit(self._client)
        except Exception as exc:
            self.failed.emit(str(exc))


class _SubmitOnEnter(QPlainTextEdit):
    """Multi-line input that submits on Enter; Shift+Enter inserts a line break."""
    submit = Signal()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)  # insert line break
            else:
                self.submit.emit()
            return
        super().keyPressEvent(event)


# Renamed from _InferenceWorker — streaming, used when tools are disabled.
class _StreamWorker(QThread):
    token_received = Signal(str)
    finished       = Signal()
    error_occurred = Signal(str)

    def __init__(self, endpoint: str, model: str, messages: list,
                 extra_headers: dict | None = None, parent=None):
        super().__init__(parent)
        self._endpoint      = endpoint.rstrip("/")
        self._model         = model
        self._messages      = messages
        self._extra_headers = extra_headers or {}

    def run(self):
        url     = f"{self._endpoint}/v1/chat/completions"
        payload = json.dumps({
            "model":    self._model,
            "messages": self._messages,
            "stream":   True,
        }).encode()
        headers = {"Content-Type": "application/json", **self._extra_headers}
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                for raw_line in resp:
                    line = raw_line.decode().strip()
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            self.token_received.emit(delta)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            self.error_occurred.emit(f"HTTP {exc.code}: {body or exc.reason}")
        except urllib.error.URLError as exc:
            self.error_occurred.emit(str(exc))
        finally:
            self.finished.emit()


class _CompletionWorker(QThread):
    """Non-streaming completion — used for the tool-calling agentic loop."""
    response_ready = Signal(dict)
    finished       = Signal()
    error_occurred = Signal(str)

    def __init__(self, endpoint: str, model: str, messages: list,
                 tools: list | None = None, extra_headers: dict | None = None,
                 parent=None):
        super().__init__(parent)
        self._endpoint      = endpoint.rstrip("/")
        self._model         = model
        self._messages      = messages
        self._tools         = tools
        self._extra_headers = extra_headers or {}

    def run(self):
        url  = f"{self._endpoint}/v1/chat/completions"
        body = {"model": self._model, "messages": self._messages, "stream": False}
        if self._tools:
            body["tools"] = self._tools
        payload = json.dumps(body).encode()
        headers = {"Content-Type": "application/json", **self._extra_headers}
        req = urllib.request.Request(
            url, data=payload, headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode())
                self.response_ready.emit(data)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            self.error_occurred.emit(f"HTTP {exc.code}: {body or exc.reason}")
        except urllib.error.URLError as exc:
            self.error_occurred.emit(str(exc))
        finally:
            self.finished.emit()


class _OllamaListWorker(QThread):
    models_ready = Signal(list)
    failed       = Signal(str)

    def __init__(self, endpoint: str, parent=None):
        super().__init__(parent)
        self._endpoint = endpoint.rstrip("/")

    def run(self):
        try:
            url = f"{self._endpoint}/api/tags"
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            models = [m["name"] for m in data.get("models", [])]
            self.models_ready.emit(sorted(models))
        except Exception as exc:
            self.failed.emit(str(exc))


class RKAIAssistantPanel(QWidget):
    """Chat panel backed by any OpenAI-compatible local inference server."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._messages        = []
        self._assistant_buf   = ""
        self._worker          = None
        self._tool_iters      = 0
        self._editor          = None
        self._mcp_clients     = {}   # url -> _MCPClient
        self._mcp_rows        = []
        self._ollama_worker   = None
        self._pending_preset  = None  # saved local preset waiting for Ollama models to load
        self._no_saved_preset = True  # True until load_settings finds saved data
        self._build_ui()
        self.load_settings()
        self._refresh_local_models()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Row 1: provider preset + API key
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Provider:"))
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(list(_PRESETS))
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        row1.addWidget(self._preset_combo, 1)
        self._ollama_refresh_btn = QPushButton("↻")
        self._ollama_refresh_btn.setFixedWidth(26)
        self._ollama_refresh_btn.setToolTip("Refresh local Ollama models")
        self._ollama_refresh_btn.clicked.connect(self._refresh_local_models)
        row1.addWidget(self._ollama_refresh_btn)
        row1.addWidget(QLabel("API Key:"))
        self._key_edit = QLineEdit()
        self._key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._key_edit.setPlaceholderText("optional")
        self._key_edit.setEnabled(False)
        row1.addWidget(self._key_edit, 1)
        layout.addLayout(row1)

        # Row 2: endpoint + model
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Endpoint:"))
        self._endpoint_edit = QLineEdit(_DEFAULT_ENDPOINT)
        self._endpoint_edit.setPlaceholderText("http://localhost:11434")
        row2.addWidget(self._endpoint_edit, 2)
        row2.addWidget(QLabel("Model:"))
        self._model_edit = QLineEdit(_DEFAULT_MODEL)
        self._model_edit.setPlaceholderText("llama3.2 / nemotron / …")
        row2.addWidget(self._model_edit, 1)
        layout.addLayout(row2)

        # MCP Servers section
        mcp_hdr = QHBoxLayout()
        mcp_hdr.addWidget(QLabel("MCP Servers:"))
        mcp_hdr.addStretch()
        self._mcp_add_btn = QPushButton("+ Add")
        self._mcp_add_btn.setFixedWidth(54)
        self._mcp_add_btn.clicked.connect(lambda: self._add_mcp_row())
        mcp_hdr.addWidget(self._mcp_add_btn)
        layout.addLayout(mcp_hdr)

        self._mcp_list_widget = QWidget()
        self._mcp_list_layout = QVBoxLayout(self._mcp_list_widget)
        self._mcp_list_layout.setContentsMargins(0, 0, 0, 0)
        self._mcp_list_layout.setSpacing(2)
        layout.addWidget(self._mcp_list_widget)
        self._add_mcp_row(_MCP_DEFAULT_URL)

        # Row 4: scene tools toggle
        row4 = QHBoxLayout()
        self._tools_check = QCheckBox("Enable scene tools")
        self._tools_check.setToolTip(
            "Lets the AI read and modify the scene (add nodes, set fields, add ROUTEs).\n"
            "Requires a model with tool-calling support."
        )
        row4.addWidget(self._tools_check)
        row4.addStretch()
        layout.addLayout(row4)

        self._chat_log = QTextEdit()
        self._chat_log.setReadOnly(True)
        self._chat_log.setPlaceholderText("AI responses will appear here…")
        layout.addWidget(self._chat_log, 1)

        self._input_box = _SubmitOnEnter()
        self._input_box.setPlaceholderText("Ask about X3D nodes, ROUTEs, animation…  (Enter to send, Shift+Enter for new line)")
        self._input_box.setFixedHeight(72)
        self._input_box.submit.connect(self._send)
        layout.addWidget(self._input_box)

        btn_row = QHBoxLayout()
        self._send_btn = QPushButton("Send")
        self._send_btn.clicked.connect(self._send)
        btn_row.addWidget(self._send_btn)
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self._clear_history)
        btn_row.addWidget(self._clear_btn)
        self._spinner_lbl = QLabel()
        self._spinner_lbl.setFixedWidth(24)
        self._spinner_lbl.hide()
        btn_row.addWidget(self._spinner_lbl)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        _FRAMES = ["⠻", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_frame = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(80)
        self._spinner_timer.timeout.connect(self._tick_spinner)

    def _tick_spinner(self):
        _FRAMES = ["⠻", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_lbl.setText(_FRAMES[self._spinner_frame % len(_FRAMES)])
        self._spinner_frame += 1

    def _start_spinner(self):
        self._spinner_frame = 0
        self._spinner_lbl.show()
        self._spinner_timer.start()

    def _stop_spinner(self):
        self._spinner_timer.stop()
        self._spinner_lbl.hide()

    # ------------------------------------------------------------------
    _SETTINGS_ORG = "RawKee"
    _SETTINGS_APP = "RKAIAssistant"

    def save_settings(self):
        s = QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)
        s.setValue("preset",        self._preset_combo.currentText())
        s.setValue("endpoint",      self._endpoint_edit.text())
        s.setValue("model",         self._model_edit.text())
        s.setValue("api_key",       self._key_edit.text())
        s.setValue("tools_enabled", self._tools_check.isChecked())
        mcp = [{"url": r["url"].text(), "checked": r["check"].isChecked()}
               for r in self._mcp_rows]
        s.setValue("mcp_rows", json.dumps(mcp))

    def load_settings(self):
        s = QSettings(self._SETTINGS_ORG, self._SETTINGS_APP)
        if not s.contains("preset"):
            return  # no saved settings yet — _no_saved_preset stays True
        self._no_saved_preset = False
        preset = str(s.value("preset", ""))
        idx = self._preset_combo.findText(preset) if preset else -1
        if idx >= 0:
            self._preset_combo.blockSignals(True)
            self._preset_combo.setCurrentIndex(idx)
            self._preset_combo.blockSignals(False)
            self._on_preset_changed(preset)
        else:
            # Saved preset is a local model not yet in the combo — defer until Ollama loads
            self._pending_preset = preset
        endpoint = str(s.value("endpoint", ""))
        if endpoint:
            self._endpoint_edit.setText(endpoint)
        model = str(s.value("model", ""))
        if model:
            self._model_edit.setText(model)
        key = str(s.value("api_key", ""))
        if key:
            self._key_edit.setText(key)
        tools = s.value("tools_enabled", False)
        self._tools_check.setChecked(tools in (True, "true"))
        mcp_json = str(s.value("mcp_rows", ""))
        if mcp_json:
            try:
                mcp_data = json.loads(mcp_json)
                for row in list(self._mcp_rows):
                    self._remove_mcp_row(row)
                for entry in mcp_data:
                    self._add_mcp_row(entry.get("url", ""), entry.get("checked", False))
            except Exception:
                pass

    # ------------------------------------------------------------------
    def set_editor(self, editor):
        self._editor = editor

    def set_x3d_scene(self, scene):
        pass  # scene access goes through self._editor at dispatch time

    def _ep(self):
        return self._endpoint_edit.text().strip() or _DEFAULT_ENDPOINT

    def _mdl(self):
        return self._model_edit.text().strip() or _DEFAULT_MODEL

    def _refresh_local_models(self):
        if self._ollama_worker and self._ollama_worker.isRunning():
            return
        # Always query localhost for local model discovery regardless of active endpoint
        self._ollama_worker = _OllamaListWorker(_DEFAULT_ENDPOINT, parent=self)
        self._ollama_worker.models_ready.connect(self._on_ollama_models)
        self._ollama_worker.start()

    def _on_ollama_models(self, models: list):
        combo = self._preset_combo
        combo.blockSignals(True)
        # Remove previously discovered local entries (they carry string item data)
        i = 0
        while i < combo.count():
            if combo.itemData(i) is not None:
                combo.removeItem(i)
            else:
                i += 1
        # Insert discovered models at the top
        for idx, model in enumerate(models):
            combo.insertItem(idx, f"Local – {model}", model)
        # Select the right entry based on saved state
        if self._no_saved_preset:
            # First run: default to first local model
            combo.setCurrentIndex(0 if models else combo.count() - 1)
        elif self._pending_preset:
            # Had a saved local preset — find it or fall back to first local
            found = combo.findText(self._pending_preset)
            combo.setCurrentIndex(found if found >= 0 else (0 if models else combo.count() - 1))
            self._pending_preset = None
        # else: user's saved static preset (Anthropic/OpenAI/Custom) is already selected — leave it
        combo.blockSignals(False)
        self._on_preset_changed(combo.currentText())

    def _on_preset_changed(self, name: str):
        # Dynamic local Ollama entry — model name stored as item data
        model_data = self._preset_combo.currentData()
        if model_data is not None:
            self._endpoint_edit.setText(_DEFAULT_ENDPOINT)
            self._model_edit.setText(model_data)
            self._key_edit.setEnabled(False)
            self._key_edit.clear()
            return
        preset = _PRESETS.get(name, {})
        if preset.get("endpoint"):
            self._endpoint_edit.setText(preset["endpoint"])
        if preset.get("model"):
            self._model_edit.setText(preset["model"])
        needs_key = preset.get("needs_key", False)
        self._key_edit.setEnabled(needs_key)
        if not needs_key:
            self._key_edit.clear()

    def _add_mcp_row(self, url: str = "", checked: bool = False):
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        check      = QCheckBox()
        check.setChecked(checked)
        url_edit   = QLineEdit(url)
        url_edit.setPlaceholderText("http://localhost:3000/mcp")
        status_lbl = QLabel()
        status_lbl.setFixedWidth(72)
        remove_btn = QPushButton("\u2715")
        remove_btn.setFixedWidth(22)
        row_layout.addWidget(check)
        row_layout.addWidget(url_edit, 1)
        row_layout.addWidget(status_lbl)
        row_layout.addWidget(remove_btn)
        row = {"check": check, "url": url_edit, "status": status_lbl,
               "remove": remove_btn, "widget": row_widget,
               "client": None, "worker": None}
        check.toggled.connect(lambda on, r=row: self._on_mcp_row_toggled(r, on))
        url_edit.editingFinished.connect(lambda r=row: self._on_mcp_url_changed(r))
        remove_btn.clicked.connect(lambda _, r=row: self._remove_mcp_row(r))
        self._mcp_rows.append(row)
        self._mcp_list_layout.addWidget(row_widget)

    def _remove_mcp_row(self, row: dict):
        self._disconnect_mcp_row(row)
        row["widget"].deleteLater()
        self._mcp_rows.remove(row)

    def _on_mcp_row_toggled(self, row: dict, checked: bool):
        if checked:
            self._connect_mcp_row(row)
        else:
            self._disconnect_mcp_row(row)

    def _on_mcp_url_changed(self, row: dict):
        if row["check"].isChecked():
            self._disconnect_mcp_row(row)
            self._connect_mcp_row(row)

    def _connect_mcp_row(self, row: dict):
        url = row["url"].text().strip()
        if not url:
            return
        row["status"].setText("connecting\u2026")
        client = _MCPClient(url)
        worker = _MCPInitWorker(client, parent=self)
        worker.succeeded.connect(lambda c, r=row: self._on_mcp_row_ready(r, c))
        worker.failed.connect(lambda msg, r=row: self._on_mcp_row_failed(r, msg))
        row["client"] = client
        row["worker"] = worker
        worker.start()

    def _disconnect_mcp_row(self, row: dict):
        client = row.get("client")
        if client:
            self._mcp_clients.pop(client.url, None)
        row["client"] = None
        row["worker"] = None
        row["status"].setText("")

    def _on_mcp_row_ready(self, row: dict, client: _MCPClient):
        self._mcp_clients[client.url] = client
        row["client"] = client
        row["status"].setText(f"\u2713 {len(client.tools)}")
        names = ", ".join(t["function"]["name"] for t in client.tools)
        self._chat_log.append(
            f"<i>[MCP {client.url} \u2014 {len(client.tools)} tools: {names}]</i>")

    def _on_mcp_row_failed(self, row: dict, msg: str):
        row["status"].setText("error")
        self._chat_log.append(
            f"<i>[MCP error ({row['url'].text()}): {msg}]</i>")

    def _build_extra_headers(self) -> dict:
        headers = {}
        key = self._key_edit.text().strip()
        if key:
            headers["Authorization"] = f"Bearer {key}"
            if "anthropic.com" in self._endpoint_edit.text():
                headers["x-api-key"]        = key
                headers["anthropic-version"] = "2023-06-01"
        return headers

    def _active_tools(self) -> list | None:
        if not self._tools_check.isChecked() or self._editor is None:
            return None
        tools = list(_TOOLS)
        for client in self._mcp_clients.values():
            tools += client.tools
        return [_sanitize_tool(t) for t in tools] if tools else None

    # ------------------------------------------------------------------
    # Send / routing
    # ------------------------------------------------------------------
    def _send(self):
        text = self._input_box.toPlainText().strip()
        if not text or self._worker is not None:
            return
        self._input_box.clear()
        self._append_bubble("You", text)
        self._messages.append({"role": "user", "content": text})
        self._send_btn.setEnabled(False)
        self._start_spinner()

        if self._tools_check.isChecked() and self._editor is not None:
            self._editor.begin_ai_batch()
            self._run_completion(self._messages)
        else:
            self._run_stream(self._messages)

    def _run_stream(self, messages):
        msgs = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages
        self._append_bubble("AI", "")
        self._assistant_buf = ""
        self._worker = _StreamWorker(
            self._ep(), self._mdl(), msgs,
            extra_headers=self._build_extra_headers(), parent=self)
        self._worker.token_received.connect(self._on_token)
        self._worker.finished.connect(self._on_stream_done)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _finish_ai_turn(self):
        if self._editor is not None:
            self._editor.end_ai_batch()
        self._stop_spinner()
        self._send_btn.setEnabled(True)

    def _run_completion(self, messages, _iters: int = 0):
        if _iters >= _MAX_TOOL_ITERS:
            self._chat_log.append(
                f"<i>[Stopped after {_MAX_TOOL_ITERS} tool calls — the model could not complete the task.]</i>")
            self._finish_ai_turn()
            return
        self._tool_iters = _iters
        msgs = [{"role": "system", "content": _SYSTEM_PROMPT}] + messages
        self._worker = _CompletionWorker(
            self._ep(), self._mdl(), msgs,
            tools=self._active_tools(),
            extra_headers=self._build_extra_headers(), parent=self)
        self._worker.response_ready.connect(self._on_completion)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_completion_worker_done)
        self._worker.start()

    # ------------------------------------------------------------------
    # Streaming callbacks
    # ------------------------------------------------------------------
    def _on_token(self, token: str):
        cursor = self._chat_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)
        self._chat_log.setTextCursor(cursor)
        self._chat_log.ensureCursorVisible()
        self._assistant_buf += token

    def _on_stream_done(self):
        if self._assistant_buf:
            self._messages.append({"role": "assistant", "content": self._assistant_buf})
        self._assistant_buf = ""
        self._chat_log.append("")
        self._finish_ai_turn()
        self._worker = None

    # ------------------------------------------------------------------
    # Tool-calling callbacks
    # ------------------------------------------------------------------
    def _on_completion_worker_done(self):
        # Only clear if this is still the active worker; a new one may already be running.
        if self.sender() is self._worker:
            self._worker = None

    def _on_completion(self, resp: dict):
        try:
            choice = resp["choices"][0]
            msg    = choice["message"]
            reason = choice.get("finish_reason", "stop")
        except (KeyError, IndexError) as exc:
            self._on_error(f"Unexpected response format: {exc}")
            return

        if reason == "tool_calls":
            tool_calls = msg.get("tool_calls", [])
            self._messages.append(msg)
            call_results = []
            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                try:
                    args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}
                result = self._dispatch_tool(fn_name, args)
                call_results.append(fn_name)
                self._messages.append({
                    "role":         "tool",
                    "tool_call_id": tc["id"],
                    "content":      str(result),
                })
            if call_results:
                names = ", ".join(call_results)
                self._chat_log.append(f"<i>[Tools ({len(call_results)}): {names}]</i>")
            # Inject node list; if no new nodes were created this batch the task is likely done
            node_list = self._scene_node_list()
            new_defs  = getattr(self._editor, "_ai_new_defs", set())
            if node_list:
                note = ("\nAll required nodes are now in the scene." if not any(
                    fn in ("create_node", "add_node", "add_child") for fn in call_results
                ) else "")
                self._messages.append({"role": "user", "content": node_list + note})
            # Continue the agentic loop
            self._run_completion(self._messages, self._tool_iters + 1)
        else:
            content = msg.get("content", "")
            iters   = self._tool_iters
            if content and self._tools_check.isChecked():
                phantom_calls = _extract_phantom_calls(content)
                if phantom_calls:
                    # Execute the calls the model described in text, then continue the loop.
                    self._messages.append({"role": "assistant", "content": content})
                    results      = []
                    last_def     = None  # last DEF returned by a create_node call
                    _PLACEHOLDER = "__previous_result__"
                    for call in phantom_calls:
                        name = call["name"]
                        # Substitute placeholder DEF with the last successfully created DEF
                        args = {
                            k: (v.replace(_PLACEHOLDER, last_def) if isinstance(v, str) and last_def else v)
                            for k, v in call["arguments"].items()
                        }
                        result = self._dispatch_tool(name, args)
                        # Track DEF of the node just created for subsequent placeholder subs
                        if name in ("create_node", "add_node", "add_child"):
                            import re as _re
                            m = _re.search(r"DEF='([^']+)'", result)
                            if m:
                                last_def = m.group(1)
                        results.append((name, result))
                    if results:
                        names = ", ".join(n for n, _ in results)
                        self._chat_log.append(f"<i>[Phantom tools ({len(results)}): {names}]</i>")
                    # Bundle results with the current node list so the model knows DEF names
                    node_list = self._scene_node_list()
                    summary   = "\n".join(f"Tool result for {n}: {r}" for n, r in results) if results else "(no scene changes this step)"
                    if node_list:
                        summary += f"\n\n{node_list}"
                    self._messages.append({"role": "user", "content": summary})
                    self._run_completion(self._messages, iters + 1)
                    return
                elif len(content) > 400:
                    # Model wrote a long response describing actions instead of calling tools
                    self._messages.append({"role": "assistant", "content": content})
                    self._messages.append({"role": "user", "content": (
                        "You described the actions in text instead of calling tools. "
                        "Use create_node and set_field tools directly. "
                        "Do NOT output JSON, markdown, or prose descriptions."
                    )})
                    self._run_completion(self._messages, iters + 1)
                    return
            if content:
                self._messages.append({"role": "assistant", "content": content})
                self._append_bubble("AI", content)
            self._finish_ai_turn()

    def _on_error(self, msg: str):
        # Retry as plain streaming if model doesn't support tool calling
        if ("404" in msg or "does not support tools" in msg) and self._tools_check.isChecked():
            self._chat_log.append("<i>[Model does not support tools — retrying without]</i>")
            self._worker = None
            self._run_stream(self._messages)
            return
        self._chat_log.append(f"\n[Error: {msg}]\n")
        self._finish_ai_turn()
        self._worker = None

    def _clear_history(self):
        self._messages.clear()
        self._assistant_buf = ""
        self._chat_log.clear()

    def reset_for_new_scene(self):
        """Clear conversation history and spinner state when a new scene is loaded."""
        self._clear_history()
        self._tool_iters = 0
        self._stop_spinner()
        if self._worker is not None:
            self._worker.terminate()
            self._worker = None
        self._send_btn.setEnabled(True)

    def _append_bubble(self, role: str, text: str):
        self._chat_log.append(f"<b>{role}:</b> {text}")

    # ------------------------------------------------------------------
    # Tool dispatch
    # ------------------------------------------------------------------
    def _dispatch_tool(self, name: str, args: dict) -> str:
        try:
            if name == "get_scene_xml":                    return self._tool_get_scene_xml()
            if name in ("add_node", "create_node", "add_child"): return self._tool_add_node(args)
            if name == "set_field":                         return self._tool_set_field(args)
            if name == "add_route":                         return self._tool_add_route(args)
            if name == "run_javascript":                    return self._tool_run_javascript(args)
            # Route to the MCP client that registered this tool
            for client in self._mcp_clients.values():
                if name in client._tool_names:
                    return client.call(name, args)
            return f"Unknown tool: {name}"
        except Exception as exc:
            return f"Tool error ({name}): {exc}"

    def _tool_get_scene_xml(self) -> str:
        if self._editor is None or getattr(self._editor, "_x3dObj", None) is None:
            return "No scene loaded."
        import io
        from rawkee.io.RKSceneTraversal import RKSceneTraversal
        buf = io.StringIO()
        trv = RKSceneTraversal()
        trv.collectProfileFromScene(self._editor._x3dObj)
        trv.startExport(self._editor._x3dObj, buf, "x3d")
        return buf.getvalue() or "Could not serialize scene."

    def _tool_add_node(self, args: dict) -> str:
        if self._editor is None:
            return "No editor connected."
        node_type  = _NODE_TYPE_ALIASES.get(args.get("node_type") or "", args.get("node_type") or "")
        parent_def = args.get("parent_def", "")
        field      = args.get("field") or None
        if parent_def:
            parent_node = self._find_node_by_def(parent_def)
            if parent_node is None:
                return f"Node DEF '{parent_def}' not found."
            result = self._editor._add_node_to_editor(node_type, override_field=field,
                                                       direct_parent=parent_node)
        else:
            result = self._editor._add_node_to_editor(node_type, override_field=field)
        if result is None:
            hint = _X3D_PARENT_HINTS.get(node_type, "Check the scene with get_scene_xml and verify the correct parent node and field.")
            ctx  = f" (tried parent='{parent_def}', field='{field}')" if parent_def else ""
            return f"Failed to add {node_type}{ctx}. {hint}"
        return f"Added {node_type} DEF='{getattr(result, 'DEF', '')}'"

    def _tool_set_field(self, args: dict) -> str:
        if self._editor is None:
            return "No editor connected."
        def_name = args.get("def_name", "")
        field    = args.get("field", "")
        value    = args.get("value")
        node = self._find_node_by_def(def_name)
        if node is None:
            return f"Node DEF '{def_name}' not found."
        # X3D SFVec/SFColor/SFRotation fields require tuples, not lists
        if isinstance(value, list):
            value = tuple(value)
        try:
            setattr(node, field, value)
        except Exception as exc:
            return f"Cannot set {def_name}.{field}: {exc}"
        self._editor._sync_xite_via_temp_file()
        return f"Set {def_name}.{field} = {value!r}"

    def _tool_add_route(self, args: dict) -> str:
        if self._editor is None:
            return "No editor connected."
        scene = getattr(self._editor, "_x3dScene", None)
        if scene is None:
            return "No scene loaded."
        import rawkee.io.RKx3d as rkx
        route = rkx.ROUTE(
            fromNode=args.get("from_node", ""),
            fromField=args.get("from_field", ""),
            toNode=args.get("to_node", ""),
            toField=args.get("to_field", ""),
        )
        scene.children.append(route)
        self._editor._sync_xite_via_temp_file()
        return (f"Added ROUTE {args.get('from_node')}.{args.get('from_field')} "
                f"\u2192 {args.get('to_node')}.{args.get('to_field')}")

    def _tool_run_javascript(self, args: dict) -> str:
        if self._editor is None:
            return "No editor connected."
        self._editor.browser.page().runJavaScript(args.get("code", ""))
        return "JavaScript executed."

    # ------------------------------------------------------------------
    # Scene-graph helpers
    # ------------------------------------------------------------------
    def _scene_node_list(self) -> str:
        """Return a hierarchical scene summary so the model sees parent-child relationships."""
        scene = getattr(self._editor, "_x3dScene", None)
        if scene is None:
            return ""
        lines = []
        # Fields to traverse when building the hierarchy display
        _CONTAINER_FIELDS = (
            "children", "appearance", "material", "geometry",
            "texture", "textureTransform", "fillProperties",
            "lineProperties", "source", "skeleton", "joints",
            "segments", "sites", "motions", "displacers",
        )

        new_defs = getattr(self._editor, "_ai_new_defs", set())

        def _visit(node, indent):
            if node is None or isinstance(node, (int, float, str, bool, list)):
                return
            type_name = type(node).__name__
            def_name  = getattr(node, "DEF", "")
            marker    = " ← NEW (use this DEF for set_field)" if def_name in new_defs else ""
            lines.append("  " * indent + type_name + (f" DEF='{def_name}'" if def_name else "") + marker)
            for field in _CONTAINER_FIELDS:
                val = getattr(node, field, None)
                if val is None:
                    continue
                if isinstance(val, list):
                    for child in val:
                        _visit(child, indent + 1)
                else:
                    _visit(val, indent + 1)

        for child in getattr(scene, "children", []):
            _visit(child, 0)

        if not lines:
            return ""
        return "Current scene hierarchy (use DEF names as parent_def):\n" + "\n".join(lines)

    def _find_node_by_def(self, def_name: str):
        if self._editor is None:
            return None
        registry = getattr(self._editor.tree_widget, "_node_registry", {})
        for node in registry.values():
            if getattr(node, "DEF", "") == def_name:
                return node
        return None

    def _select_tree_node(self, node):
        """Select node in the tree so _add_node_to_editor uses it as parent."""
        from PySide6.QtCore import Qt
        key  = str(id(node))
        tree = self._editor.tree_widget

        def _search(item):
            if item.data(0, Qt.ItemDataRole.UserRole) == key:
                tree.setCurrentItem(item)
                return True
            for i in range(item.childCount()):
                if _search(item.child(i)):
                    return True
            return False

        for i in range(tree.topLevelItemCount()):
            if _search(tree.topLevelItem(i)):
                break
