"""
RawKee X3D MCP Server
=====================
Implements the Model Context Protocol (Streamable HTTP transport) over a
plain Python HTTPServer — no third-party dependencies required.

Stateful tools (per-session scene):
    create_node  set_field  add_child  def_node  use_node  remove_node
    add_route    get_scene  reset_scene  compose_scene  validate_current_scene

Stateless reference tools:
    list_nodes  describe_node  list_components  list_profiles
    convert_x3d  validate_x3d  validate_semantic  x3dom_page
"""

from __future__ import annotations

import io
import json
import re
import threading
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# ---------------------------------------------------------------------------
# Lazy imports — keep rkx out of module-level to stay importable from hosts
# ---------------------------------------------------------------------------

def _rkx():
    import rawkee.io.RKx3d as m
    return m

def _loader():
    from rawkee.io.RKLoadSceneFromFile import RKLoadSceneFromFile
    return RKLoadSceneFromFile

def _traversal():
    from rawkee.io.RKSceneTraversal import RKSceneTraversal
    return RKSceneTraversal


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class _Session:
    def __init__(self):
        rkx       = _rkx()
        x3d       = rkx.X3D()
        x3d.Scene = rkx.Scene()
        self.x3d  = x3d
        self._nodes: dict[str, Any] = {}   # node_id -> rkx node
        self._defs:  dict[str, str] = {}   # def_name -> node_id

    # ── registry ──────────────────────────────────────────────────────────

    def register(self, node) -> str:
        nid = 'rk_' + uuid.uuid4().hex[:10]
        self._nodes[nid] = node
        return nid

    def node(self, nid: str):
        n = self._nodes.get(nid)
        if n is None:
            raise KeyError(f"Unknown node ID: {nid!r}")
        return n

    def node_by_def(self, def_name: str):
        nid = self._defs.get(def_name)
        if nid is None:
            raise KeyError(f"No node with DEF={def_name!r}")
        return self._nodes[nid], nid

    # ── serialization ──────────────────────────────────────────────────────

    def serialize(self, encoding: str = 'xml') -> str:
        trv = _traversal()()
        trv.collectProfileFromScene(self.x3d)
        buf = io.StringIO()
        trv.startExport(self.x3d, buf, _enc(encoding))
        return buf.getvalue()

    # ── reset ──────────────────────────────────────────────────────────────

    def reset(self):
        rkx       = _rkx()
        x3d       = rkx.X3D()
        x3d.Scene = rkx.Scene()
        self.x3d  = x3d
        self._nodes.clear()
        self._defs.clear()


def _enc(raw: str) -> str:
    return {'json': 'x3dj', 'vrml': 'x3dv', 'classic': 'x3dv',
            'xml': 'x3d', 'x3dj': 'x3dj', 'x3dv': 'x3dv', 'x3d': 'x3d'}.get(raw.lower(), raw)


_sessions: dict[str, _Session] = {}
_lock = threading.Lock()

def _session(sid: str) -> _Session:
    with _lock:
        if sid not in _sessions:
            _sessions[sid] = _Session()
        return _sessions[sid]


# ---------------------------------------------------------------------------
# Stateful tools (operate on a session's scene)
# ---------------------------------------------------------------------------

def _create_node(sess: _Session, node_type: str, fields: dict | None = None) -> str:
    rkx = _rkx()
    cls = getattr(rkx, node_type, None)
    if cls is None or not callable(cls):
        raise ValueError(f"Unknown X3D node type: {node_type!r}")
    node = cls()
    if fields:
        for fname, val in fields.items():
            try:
                setattr(node, fname, val)
            except Exception:
                pass
    return sess.register(node)


def _set_field(sess: _Session, node_id: str, field_name: str, value: Any) -> str:
    setattr(sess.node(node_id), field_name, value)
    return f"Field {field_name!r} set on {node_id}"


def _add_child(sess: _Session, parent_id: str, child_id: str,
               field_name: str | None = None) -> str:
    """Add child to parent. field_name is explicit — no guessing required."""
    rkx    = _rkx()
    child  = sess.node(child_id)

    if parent_id == '__scene__':
        sess.x3d.Scene.children.append(child)
        return f"Added {child_id} to scene root"

    parent = sess.node(parent_id)

    if field_name:
        target = getattr(parent, field_name, None)
        if isinstance(target, list):
            target.append(child)
        else:
            setattr(parent, field_name, child)
        return f"Added {child_id} to {parent_id}.{field_name}"

    # Auto-detect: first MFNode/SFNode field not outputOnly that can hold this child
    if hasattr(type(parent), 'FIELD_DECLARATIONS'):
        for decl in type(parent).FIELD_DECLARATIONS():
            fname  = decl[0]
            ftype  = decl[2]
            access = decl[3]
            if ftype() not in ('SFNode', 'MFNode'):
                continue
            if access() == 'outputOnly':
                continue
            try:
                val = getattr(parent, fname, None)
                if isinstance(val, list):
                    val.append(child)
                else:
                    setattr(parent, fname, child)
                return f"Added {child_id} to {parent_id}.{fname} (auto-detected)"
            except Exception:
                continue
    raise ValueError(
        f"Cannot determine target field on {type(parent).__name__}. "
        f"Provide field_name explicitly."
    )


def _def_node(sess: _Session, node_id: str, name: str) -> str:
    node     = sess.node(node_id)
    node.DEF = name
    sess._defs[name] = node_id
    return f"DEF {name!r} assigned to {node_id}"


def _use_node(sess: _Session, def_name: str) -> str:
    orig, _ = sess.node_by_def(def_name)
    use_node = type(orig)(USE=def_name)
    return sess.register(use_node)


def _remove_node(sess: _Session, node_id: str) -> str:
    node  = sess.node(node_id)
    scene = sess.x3d.Scene
    # Remove from scene root
    if node in (scene.children or []):
        scene.children = [c for c in scene.children if c is not node]
    # Remove from any registered parent
    for other in list(sess._nodes.values()):
        if other is node or not hasattr(type(other), 'FIELD_DECLARATIONS'):
            continue
        for decl in type(other).FIELD_DECLARATIONS():
            if decl[2]() not in ('SFNode', 'MFNode'):
                continue
            try:
                val = getattr(other, decl[0], None)
                if isinstance(val, list) and node in val:
                    setattr(other, decl[0], [x for x in val if x is not node])
                elif val is node:
                    setattr(other, decl[0], None)
            except Exception:
                pass
    def_name = getattr(node, 'DEF', '') or ''
    if def_name and sess._defs.get(def_name) == node_id:
        del sess._defs[def_name]
    del sess._nodes[node_id]
    return f"Removed {node_id}"


def _add_route(sess: _Session, from_node: str, from_field: str,
               to_node: str, to_field: str) -> str:
    fn     = sess.node(from_node)
    tn     = sess.node(to_node)
    fn_def = getattr(fn, 'DEF', '') or ''
    tn_def = getattr(tn, 'DEF', '') or ''
    if not fn_def or not tn_def:
        raise ValueError("Both nodes must have a DEF name before adding a ROUTE.")
    rkx   = _rkx()
    route = rkx.ROUTE(fromNode=fn_def, fromField=from_field,
                      toNode=tn_def,   toField=to_field)
    sess.x3d.Scene.children.append(route)
    return f"ROUTE {fn_def}.{from_field} -> {tn_def}.{to_field} added"


def _get_scene(sess: _Session, encoding: str = 'xml') -> str:
    return sess.serialize(encoding)


def _reset_scene(sess: _Session) -> str:
    sess.reset()
    return "Scene reset"


def _compose_scene(sess: _Session, objects: list, encoding: str = 'xml') -> str:
    """Build a scene from a declarative list of node descriptors.

    Each descriptor: {"type":"Transform","def":"Name","fields":{...},"children":[...]}
    """
    sess.reset()

    def _build(obj: dict, parent_id: str | None = None, container: str | None = None):
        node_type = obj.get('type') or obj.get('nodeType', '')
        if not node_type:
            return
        nid = _create_node(sess, node_type, obj.get('fields'))
        if obj.get('def') or obj.get('DEF'):
            _def_node(sess, nid, obj.get('def') or obj['DEF'])
        target_parent = parent_id or '__scene__'
        field = container or obj.get('containerField')
        _add_child(sess, target_parent, nid, field)
        for child in (obj.get('children') or []):
            _build(child, nid)

    for obj in objects:
        _build(obj)
    return sess.serialize(encoding)


def _validate_current_scene(sess: _Session) -> str:
    return _validate_semantic(sess.serialize('xml'))


# ---------------------------------------------------------------------------
# Stateless reference tools
# ---------------------------------------------------------------------------

def _list_nodes(component: str | None = None) -> str:
    import inspect
    rkx = _rkx()
    try:
        src = inspect.getsource(rkx.instantiateNodeFromString)
    except Exception:
        return "Unable to inspect node list."
    entry_pat = re.compile(r"'([A-Z]\w+)':\s*\([^{]+(\{[^}]+\})")
    comp_map: dict[str, list[str]] = {}
    for m in entry_pat.finditer(src):
        node_name = m.group(1)
        comps     = {k.strip("' "): int(v)
                     for k, v in re.findall(r"'(\w+)':\s*(\d+)", m.group(2))}
        primary   = max(comps, key=comps.get) if comps else 'Core'
        comp_map.setdefault(primary, []).append(node_name)

    if component:
        nodes = comp_map.get(component, [])
        return (f"{component}: {', '.join(sorted(nodes))}"
                if nodes else f"No nodes in component {component!r}")
    return '\n'.join(
        f"{c} ({len(comp_map[c])}): {', '.join(sorted(comp_map[c]))}"
        for c in sorted(comp_map)
    )


def _describe_node(node_type: str) -> str:
    rkx = _rkx()
    cls = getattr(rkx, node_type, None)
    if cls is None:
        return f"Unknown node type: {node_type!r}"
    lines = [f"Node: {node_type}"]
    if hasattr(cls, 'FIELD_DECLARATIONS'):
        lines.append("Fields:")
        for decl in cls.FIELD_DECLARATIONS():
            fname   = decl[0]
            default = decl[1]
            try:   ftype_s  = decl[2]()
            except: ftype_s = str(decl[2])
            try:   access_s = decl[3]()
            except: access_s = str(decl[3])
            lines.append(f"  {fname:<28} {ftype_s:<18} [{access_s}]  default={default!r}")
    return '\n'.join(lines)


def _list_components() -> str:
    full = _list_nodes()
    lines = []
    for line in full.split('\n'):
        m = re.match(r'^(\w[\w ]*) \((\d+)\)', line)
        if m:
            lines.append(f"{m.group(1)}: {m.group(2)} nodes")
    return '\n'.join(lines)


def _list_profiles() -> str:
    return (
        "Core              — Minimum set of components\n"
        "Interchange       — Core + geometry/appearance exchange\n"
        "CADInterchange    — CAD geometry exchange\n"
        "Interactive       — Interchange + pointing device/keyboard input\n"
        "Immersive         — Full-featured interactive 3D (most common)\n"
        "MedicalInterchange — Medical imaging exchange\n"
        "MPEG4Interactive  — MPEG-4 compliant subset\n"
        "Full              — All components and levels"
    )


def _convert_x3d(content: str, from_encoding: str, to_encoding: str) -> str:
    import os, tempfile
    loader = _loader()()
    enc = from_encoding.lower()
    if enc == 'xml':
        x3d = loader.from_xml_string(content)
    else:
        suffix = '.x3dj' if enc in ('json', 'x3dj') else '.x3dv'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w',
                                         encoding='utf-8') as f:
            f.write(content)
            fname = f.name
        try:
            x3d = loader.disk2x3d(fname)
        finally:
            os.unlink(fname)
    if x3d is None:
        raise ValueError("Failed to parse X3D content")
    trv = _traversal()()
    trv.collectProfileFromScene(x3d)
    buf = io.StringIO()
    trv.startExport(x3d, buf, _enc(to_encoding))
    return buf.getvalue()


def _validate_x3d(content: str, encoding: str = 'xml') -> str:
    if encoding.lower() != 'xml':
        return f"Encoding {encoding!r} structural validation not supported; use validate_semantic."
    try:
        ET.fromstring(content)
    except ET.ParseError as e:
        return f"XML parse error: {e}"
    x3d = _loader()().from_xml_string(content)
    if x3d is None:
        return "XML is well-formed but could not be parsed as a valid X3D document."
    return "Valid X3D XML — well-formed and structurally parseable."


def _validate_semantic(content: str) -> str:
    """Semantic checks: duplicate DEFs, broken USEs/ROUTEs, shapeless Shapes, missing Viewpoint."""
    try:
        x3d = _loader()().from_xml_string(content)
    except Exception as e:
        return f"Parse error: {e}"
    if x3d is None:
        return "Could not parse scene."

    rkx       = _rkx()
    issues    : list[str] = []
    defs_seen : dict[str, int] = {}
    uses      : list[str] = []
    routes    : list      = []
    has_vp    = False
    VP_TYPES  = {'Viewpoint', 'OrthoViewpoint', 'GeoViewpoint'}

    def walk(node, depth: int = 0):
        nonlocal has_vp
        if node is None:
            return
        type_name = type(node).NAME() if hasattr(type(node), 'NAME') else type(node).__name__
        if type_name == 'ROUTE':
            routes.append(node)
            return
        if depth == 1 and type_name in VP_TYPES:
            has_vp = True

        def_ = getattr(node, 'DEF', '') or ''
        use_ = getattr(node, 'USE', '') or ''
        if def_:
            defs_seen[def_] = defs_seen.get(def_, 0) + 1
        if use_:
            uses.append(use_)
            return  # don't recurse into USE nodes

        if type_name == 'Shape' and getattr(node, 'geometry', None) is None:
            loc = f"DEF={def_!r}" if def_ else f"(unnamed, depth {depth})"
            issues.append(f"WARNING  Shape {loc} has no geometry node")

        if not hasattr(type(node), 'FIELD_DECLARATIONS'):
            return
        for decl in type(node).FIELD_DECLARATIONS():
            try:
                ftype_s = decl[2]()
            except Exception:
                continue
            if ftype_s not in ('SFNode', 'MFNode'):
                continue
            try:
                val = getattr(node, decl[0], None)
            except Exception:
                continue
            for child in (val if isinstance(val, list) else ([val] if val else [])):
                walk(child, depth + 1)

    scene = getattr(x3d, 'Scene', None)
    if scene:
        for child in (scene.children or []):
            walk(child, depth=1)

    for def_, count in defs_seen.items():
        if count > 1:
            issues.append(f"ERROR    Duplicate DEF {def_!r} appears {count} times")
    for use in uses:
        if use not in defs_seen:
            issues.append(f"ERROR    USE={use!r} references non-existent DEF")
    for route in routes:
        fn = getattr(route, 'fromNode', '') or ''
        tn = getattr(route, 'toNode',   '') or ''
        if fn and fn not in defs_seen:
            issues.append(f"ERROR    ROUTE fromNode={fn!r} not found in scene")
        if tn and tn not in defs_seen:
            issues.append(f"ERROR    ROUTE toNode={tn!r} not found in scene")
    if not has_vp:
        issues.append("INFO     No Viewpoint node found at scene root level")

    return '\n'.join(issues) if issues else "Semantic validation passed — no issues found."


def _x3dom_page(content: str, title: str = 'X3D Scene',
                width: str = '800px', height: str = '600px',
                show_stats: bool = False, show_log: bool = False) -> str:
    try:
        root = ET.fromstring(content)
        tag  = re.sub(r'\{[^}]*\}', '', root.tag)
        if tag == 'X3D':
            scene_el = root.find('Scene') or root.find('{*}Scene')
            fragment = (''.join(ET.tostring(c, encoding='unicode') for c in scene_el)
                        if scene_el is not None else content)
        else:
            fragment = content
    except Exception:
        fragment = content

    stats = ' showStat="true"' if show_stats else ''
    log   = ' showLog="true"'  if show_log   else ''
    return (
        f'<!DOCTYPE html>\n<html>\n<head><meta charset="utf-8"><title>{title}</title>\n'
        f'<link rel="stylesheet" href="https://www.x3dom.org/release/x3dom.css"/>\n'
        f'<script src="https://www.x3dom.org/release/x3dom.js"></script>\n'
        f'</head>\n<body style="margin:0;background:#000">\n'
        f'<x3d width="{width}" height="{height}"{stats}{log}>\n'
        f'  <scene>\n    {fragment}\n  </scene>\n</x3d>\n</body>\n</html>'
    )


# ---------------------------------------------------------------------------
# Tool registry (MCP tool descriptors)
# ---------------------------------------------------------------------------

_TOOLS = [
    {
        "name": "create_node",
        "description": (
            "Create a new X3D node and return its tracking ID.\n\n"
            "Args:\n"
            "    node_type: X3D node type name (e.g. 'Box', 'Transform', 'Material').\n"
            "    fields: Optional dict of field name -> value to set at creation."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_type": {"type": "string"},
                "fields": {"anyOf": [{"type": "object"}, {"type": "null"}], "default": None},
            },
            "required": ["node_type"],
        },
    },
    {
        "name": "set_field",
        "description": (
            "Set a field value on an existing node.\n\n"
            "Args:\n"
            "    node_id: Tracking ID from create_node.\n"
            "    field_name: Field name (e.g. 'translation', 'diffuseColor').\n"
            "    value: Value to set. Use lists for vector types, e.g. [1,0,0]."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id":    {"type": "string"},
                "field_name": {"type": "string"},
                "value":      {"anyOf": [{"type": "string"}, {"type": "number"},
                                         {"type": "boolean"},
                                         {"type": "array", "items": {}}]},
            },
            "required": ["node_id", "field_name", "value"],
        },
    },
    {
        "name": "add_child",
        "description": (
            "Add a child node to a parent in the scene graph.\n\n"
            "Args:\n"
            "    parent_id: Parent tracking ID, or '__scene__' for the scene root.\n"
            "    child_id:  Child tracking ID.\n"
            "    field_name: Target field name (e.g. 'children', 'geometry', 'material').\n"
            "               Strongly recommended — prevents ambiguity on nodes with\n"
            "               multiple SFNode/MFNode fields."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "parent_id":  {"type": "string"},
                "child_id":   {"type": "string"},
                "field_name": {"anyOf": [{"type": "string"}, {"type": "null"}],
                               "default": None},
            },
            "required": ["parent_id", "child_id"],
        },
    },
    {
        "name": "def_node",
        "description": (
            "Assign a DEF name to a node for USE or ROUTE referencing.\n\n"
            "Args:\n"
            "    node_id: Tracking ID.\n"
            "    name: Unique DEF name."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {"type": "string"},
                "name":    {"type": "string"},
            },
            "required": ["node_id", "name"],
        },
    },
    {
        "name": "use_node",
        "description": (
            "Create a USE reference to a previously DEF'd node.\n\n"
            "Args:\n"
            "    def_name: DEF name of the node to reference."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"def_name": {"type": "string"}},
            "required": ["def_name"],
        },
    },
    {
        "name": "remove_node",
        "description": (
            "Remove a node from the scene and the session registry.\n\n"
            "Args:\n"
            "    node_id: Tracking ID to remove."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"node_id": {"type": "string"}},
            "required": ["node_id"],
        },
    },
    {
        "name": "add_route",
        "description": (
            "Connect two node fields with a ROUTE for event propagation.\n\n"
            "Both nodes must have DEF names assigned first.\n\n"
            "Args:\n"
            "    from_node/from_field: Source node tracking ID and field.\n"
            "    to_node/to_field:     Target node tracking ID and field."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_node":  {"type": "string"},
                "from_field": {"type": "string"},
                "to_node":    {"type": "string"},
                "to_field":   {"type": "string"},
            },
            "required": ["from_node", "from_field", "to_node", "to_field"],
        },
    },
    {
        "name": "get_scene",
        "description": (
            "Return the current session scene in the requested encoding.\n\n"
            "Args:\n"
            "    encoding: 'xml' (default), 'x3dj' (JSON), or 'x3dv' (Classic VRML)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"encoding": {"type": "string", "default": "xml"}},
        },
    },
    {
        "name": "reset_scene",
        "description": "Clear all nodes and reset the session scene to empty.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "compose_scene",
        "description": (
            "Build a complete scene from a declarative node-descriptor list and return the X3D.\n\n"
            "Each descriptor: {\"type\":\"Transform\",\"def\":\"Name\",\"fields\":{...},\"children\":[...]}\n\n"
            "Args:\n"
            "    objects: List of top-level node descriptors.\n"
            "    encoding: Output encoding — 'xml' (default), 'x3dj', or 'x3dv'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "objects":  {"type": "array", "items": {"type": "object"}},
                "encoding": {"type": "string", "default": "xml"},
            },
            "required": ["objects"],
        },
    },
    {
        "name": "list_nodes",
        "description": (
            "List available X3D node types grouped by component.\n\n"
            "Args:\n"
            "    component: Filter by component name (e.g. 'Geometry3D', 'Shape').\n"
            "               Omit to list all nodes across all components."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "component": {"anyOf": [{"type": "string"}, {"type": "null"}],
                              "default": None},
            },
        },
    },
    {
        "name": "describe_node",
        "description": (
            "Get all fields of an X3D node type with their types, access modes, and defaults.\n\n"
            "Args:\n"
            "    node_type: Node type name (e.g. 'Box', 'Material', 'Transform')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"node_type": {"type": "string"}},
            "required": ["node_type"],
        },
    },
    {
        "name": "list_components",
        "description": "List all X3D components and the number of nodes in each.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_profiles",
        "description": "List all X3D profiles with brief descriptions.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "convert_x3d",
        "description": (
            "Convert X3D content between encodings using RawKee's serializer.\n\n"
            "Args:\n"
            "    content:       X3D content string.\n"
            "    from_encoding: Source — 'xml', 'json'/'x3dj', or 'vrml'/'x3dv'.\n"
            "    to_encoding:   Target — 'xml', 'x3dj', or 'x3dv'."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content":       {"type": "string"},
                "from_encoding": {"type": "string"},
                "to_encoding":   {"type": "string"},
            },
            "required": ["content", "from_encoding", "to_encoding"],
        },
    },
    {
        "name": "validate_x3d",
        "description": (
            "Validate X3D content for well-formedness and structural correctness.\n\n"
            "Args:\n"
            "    content:  X3D content string.\n"
            "    encoding: 'xml' (default). Other encodings: use validate_semantic."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content":  {"type": "string"},
                "encoding": {"type": "string", "default": "xml"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "validate_current_scene",
        "description": "Run semantic validation on the current session scene.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "validate_semantic",
        "description": (
            "Run semantic checks on X3D XML content beyond schema validation.\n\n"
            "Detects: duplicate DEFs, USE references to missing DEFs, ROUTE node\n"
            "mismatches, Shape nodes missing geometry, and missing Viewpoints.\n\n"
            "Args:\n"
            "    content: X3D XML string to check."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"content": {"type": "string"}},
            "required": ["content"],
        },
    },
    {
        "name": "x3dom_page",
        "description": (
            "Wrap X3D content in a standalone X3DOM HTML page for browser viewing.\n\n"
            "Args:\n"
            "    content:    X3D XML (full document or scene fragment).\n"
            "    title:      Page title.\n"
            "    width/height: Canvas size (CSS values, e.g. '800px', '100%').\n"
            "    show_stats: Show X3DOM frame-stats overlay.\n"
            "    show_log:   Show X3DOM log panel."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content":    {"type": "string"},
                "title":      {"type": "string", "default": "X3D Scene"},
                "width":      {"type": "string", "default": "800px"},
                "height":     {"type": "string", "default": "600px"},
                "show_stats": {"type": "boolean", "default": False},
                "show_log":   {"type": "boolean", "default": False},
            },
            "required": ["content"],
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _dispatch(name: str, args: dict, sess: _Session) -> str:
    try:
        if name == 'create_node':            return _create_node(sess, **args)
        if name == 'set_field':              return _set_field(sess, **args)
        if name == 'add_child':              return _add_child(sess, **args)
        if name == 'def_node':               return _def_node(sess, **args)
        if name == 'use_node':               return _use_node(sess, **args)
        if name == 'remove_node':            return _remove_node(sess, **args)
        if name == 'add_route':              return _add_route(sess, **args)
        if name == 'get_scene':              return _get_scene(sess, **args)
        if name == 'reset_scene':            return _reset_scene(sess)
        if name == 'compose_scene':          return _compose_scene(sess, **args)
        if name == 'list_nodes':             return _list_nodes(**args)
        if name == 'describe_node':          return _describe_node(**args)
        if name == 'list_components':        return _list_components()
        if name == 'list_profiles':          return _list_profiles()
        if name == 'convert_x3d':            return _convert_x3d(**args)
        if name == 'validate_x3d':           return _validate_x3d(**args)
        if name == 'validate_current_scene': return _validate_current_scene(sess)
        if name == 'validate_semantic':      return _validate_semantic(**args)
        if name == 'x3dom_page':             return _x3dom_page(**args)
        return f"Unknown tool: {name!r}"
    except Exception as exc:
        return f"Error in {name!r}: {exc}"


# ---------------------------------------------------------------------------
# MCP Streamable HTTP transport
# ---------------------------------------------------------------------------

_MCP_VERSION = '2024-11-05'
_SERVER_INFO = {'name': 'rawkee-x3d-mcp', 'version': '1.0.0'}
_CAPS = {
    'experimental': {},
    'prompts':   {'listChanged': False},
    'resources': {'subscribe': False, 'listChanged': False},
    'tools':     {'listChanged': False},
}


def _sse(data: dict) -> bytes:
    return ('event: message\ndata: ' + json.dumps(data) + '\n\n').encode()


class _Handler(BaseHTTPRequestHandler):

    def log_message(self, *_):
        pass  # suppress default request log

    def _reply_sse(self, data: dict, extra: dict | None = None):
        body = _sse(data)
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control',  'no-cache')
        self.send_header('Content-Length', str(len(body)))
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _reply_plain(self, code: int, msg: str):
        body = msg.encode()
        self.send_response(code)
        self.send_header('Content-Type',   'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.rstrip('/') in ('', '/health'):
            body = json.dumps({'status': 'ok', 'server': 'rawkee-x3d-mcp'}).encode()
            self.send_response(200)
            self.send_header('Content-Type',   'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._reply_plain(404, 'Not found')

    def do_POST(self):
        if self.path.rstrip('/') not in ('/mcp',):
            self._reply_plain(404, 'Not found')
            return
        accept = self.headers.get('Accept', '')
        if 'text/event-stream' not in accept and 'application/json' not in accept:
            self._reply_plain(406,
                'Not Acceptable — include "text/event-stream" or "application/json" in Accept')
            return
        length = int(self.headers.get('Content-Length', 0))
        try:
            msg = json.loads(self.rfile.read(length))
        except Exception:
            self._reply_plain(400, 'Bad JSON')
            return

        method = msg.get('method', '')
        rid    = msg.get('id')
        params = msg.get('params') or {}
        sid    = (self.headers.get('Mcp-Session-Id')
                  or self.headers.get('mcp-session-id', ''))

        # ── initialize ────────────────────────────────────────────────────
        if method == 'initialize':
            new_sid = uuid.uuid4().hex
            _session(new_sid)
            self._reply_sse(
                {'jsonrpc': '2.0', 'id': rid, 'result': {
                    'protocolVersion': _MCP_VERSION,
                    'capabilities':    _CAPS,
                    'serverInfo':      _SERVER_INFO,
                }},
                extra={'Mcp-Session-Id': new_sid},
            )
            return

        # ── notifications/initialized (no response needed) ────────────────
        if method == 'notifications/initialized':
            self.send_response(204)
            self.end_headers()
            return

        if not sid:
            self._reply_plain(400, 'Missing Mcp-Session-Id header')
            return
        sess = _session(sid)

        # ── tools/list ────────────────────────────────────────────────────
        if method == 'tools/list':
            self._reply_sse({'jsonrpc': '2.0', 'id': rid,
                             'result': {'tools': _TOOLS}})
            return

        # ── tools/call ────────────────────────────────────────────────────
        if method == 'tools/call':
            tool_name = params.get('name', '')
            tool_args = params.get('arguments') or {}
            result    = _dispatch(tool_name, tool_args, sess)
            self._reply_sse({'jsonrpc': '2.0', 'id': rid, 'result': {
                'content': [{'type': 'text', 'text': result}],
                'isError': False,
            }})
            return

        # ── unknown method ────────────────────────────────────────────────
        self._reply_sse({'jsonrpc': '2.0', 'id': rid,
                         'error': {'code': -32601,
                                   'message': f'Method not found: {method!r}'}})


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(host: str = '0.0.0.0', port: int = 8766):
    server = HTTPServer((host, port), _Handler)
    print(f'RawKee X3D MCP server  →  http://{host}:{port}/mcp')
    server.serve_forever()
