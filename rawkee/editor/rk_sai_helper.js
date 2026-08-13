/**
 * rk_sai_helper.js � X_ITE SAI bridge for RawKee scene editor.
 * Loaded via <script> in x_ite.html before x_ite.min.js.
 * All RK.* calls made before the sentinel fires are queued and replayed.
 */
(function () {
    'use strict';

    // DEF name ? live X_ITE node reference
    const _cache = Object.create(null);

    const _queue = [];
    let   _ready = false;

    function _drainQueue() {
        _ready = true;
        const pending = _queue.splice(0);
        for (const fn of pending) {
            try { fn(); } catch (e) { console.log('RK queue: ' + e); }
        }
    }

    function _onSceneReady() {
        const s = _scene();
        if (s) {
            try {
                const sentinel = s.getNamedNode('__RKReadySentinel__');
                if (sentinel) {
                    const rn = s.rootNodes;
                    for (let i = 0; i < rn.length; i++) {
                        if (rn[i] === sentinel) { rn.splice(i, 1); break; }
                    }
                    try { s.removeNamedNode('__RKReadySentinel__'); } catch (_) {}
                }
            } catch (_) {}
            delete _cache['__RKReadySentinel__'];
        }
        console.log('RK: ready, draining ' + _queue.length + ' queued commands');
        _drainQueue();
    }

    function _defer(fn) {
        return function (...args) {
            if (_ready) { fn(...args); }
            else         { _queue.push(() => fn(...args)); }
        };
    }

    function _browser() { return (document.querySelector('x3d-canvas') || {}).browser || null; }
    function _scene()   { const b = _browser(); return b ? b.currentScene : null; }

    function _node(def) {
        if (_cache[def]) return _cache[def];
        const s = _scene();
        if (!s) return null;
        try { const n = s.getNamedNode(def); if (n) { _cache[def] = n; } return n || null; }
        catch (_) { return null; }
    }

    // MF tuple field info: type name ? [SF constructor name, stride]
    // Used to fill MFVec3f/MFColor/etc. from Python's flat float arrays.
    const _MF_TUPLE = {
        MFVec2f: ['SFVec2f', 2], MFVec2d: ['SFVec2d', 2],
        MFVec3f: ['SFVec3f', 3], MFVec3d: ['SFVec3d', 3], MFColor: ['SFColor', 3],
        MFVec4f: ['SFVec4f', 4], MFVec4d: ['SFVec4d', 4],
        MFColorRGBA:  ['SFColorRGBA',  4],
        MFRotation:   ['SFRotation',   4],
        MFQuaternion: ['SFQuaternion', 4],
        MFMatrix3f: ['SFMatrix3f', 9],  MFMatrix3d: ['SFMatrix3d', 9],
        MFMatrix4f: ['SFMatrix4f', 16], MFMatrix4d: ['SFMatrix4d', 16],
    };

    // Assign a flat numeric array into any X_ITE field using the correct SAI objects.
    function _setField(n, fname, field, flatArr) {
        // getTypeName() returns the canonical name ('MFVec3f') not the internal class name.
        const tname = (field && field.getTypeName && field.getTypeName())
                   || (field && field.constructor && field.constructor.name) || '';
        const info  = _MF_TUPLE[tname];

        if (info) {
            // MF tuple field: create individual SF objects by index assignment.
            const [sfName, stride] = info;
            const SFCtor = (typeof X3D !== 'undefined' && X3D[sfName]);
            const count  = Math.floor(flatArr.length / stride);
            field.length = count;
            for (let i = 0, j = 0; i < count; i++, j += stride) {
                if (SFCtor) {
                    // Spread only the needed components for this stride
                    const args = flatArr.slice(j, j + stride);
                    field[i] = new SFCtor(...args);
                } else {
                    field[i] = flatArr.slice(j, j + stride);
                }
            }
            return;
        }

        if (tname.startsWith('MF')) {
            // MF scalar field (MFFloat, MFInt32, MFBool, MFDouble, MFString, etc.)
            field.length = flatArr.length;
            for (let i = 0; i < flatArr.length; i++) field[i] = flatArr[i];
            return;
        }

        // SF tuple � use X3D namespace constructor with spread.
        const SFCtor = (typeof X3D !== 'undefined' && tname && X3D[tname])
                     || (field && field.constructor);
        if (SFCtor) {
            try { n[fname] = new SFCtor(...flatArr); return; } catch (_) {}
        }
        n[fname] = flatArr;
    }

    // -- Public API -----------------------------------------------------------

    const setField = _defer(function (def, fname, value) {
        try {
            const n = _node(def);
            if (!n) return;
            const f = n[fname];
            if (f === undefined) return;
            if (Array.isArray(value) && value.length > 0) {
                _setField(n, fname, f, value);
            } else {
                n[fname] = value;
            }
        } catch (e) { console.log('RK.setField ' + def + '.' + fname + ': ' + e); }
    });

    const addNode = _defer(function (nodeType, def, parentDef, fieldName, fields) {
        try {
            const s = _scene();
            if (!s) { console.log('RK.addNode: no scene for ' + nodeType); return; }
            const n = s.createNode(nodeType);
            if (!n) { console.log('RK.addNode: createNode null for ' + nodeType); return; }

            // Register name so X_ITE internal lookups (routes, field updates) succeed.
            if (def) {
                _cache[def] = n;
                try { s.updateNamedNode(def, n); } catch (_) {}
            }

            if (fields) {
                for (const [fname, value] of Object.entries(fields)) {
                    try {
                        const f = n[fname];
                        if (f === undefined) continue;
                        if (Array.isArray(value) && value.length > 0) {
                            _setField(n, fname, f, value);
                        } else {
                            n[fname] = value;
                        }
                    } catch (fe) { console.log('RK field ' + fname + '@' + def + ': ' + fe); }
                }
            }

            if (parentDef) {
                const p = _node(parentDef);
                if (!p) { console.log('RK.addNode: parent not found: ' + parentDef); return; }
                // MFNode field ? push; SFNode field ? direct assign.
                try { p[fieldName].push(n); } catch (_) { p[fieldName] = n; }
            } else {
                s.rootNodes.push(n);
            }
            console.log('RK.addNode OK: ' + nodeType + '/' + (def||'(anon)') + ' -> ' + (parentDef||'root'));
        } catch (e) { console.log('RK.addNode ' + nodeType + '/' + def + ': ' + e); }
    });

    const removeNode = _defer(function (def) {
        try {
            const n = _node(def);
            if (!n) return;
            delete _cache[def];
            const s = _scene();
            if (!s) return;
            try { s.removeNamedNode(def); } catch (_) {}
            const rn = s.rootNodes;
            for (let i = 0; i < rn.length; i++) {
                if (rn[i] === n) { rn.splice(i, 1); return; }
            }
            for (const cached of Object.values(_cache)) {
                if (!cached || !cached.getFieldDefinitions) continue;
                try {
                    for (const fd of cached.getFieldDefinitions()) {
                        if (!String(fd.dataType).includes('MF')) continue;
                        const mf = cached[fd.name];
                        if (!mf || !mf.length) continue;
                        for (let i = 0; i < mf.length; i++) {
                            if (mf[i] === n) { mf.splice(i, 1); return; }
                        }
                    }
                } catch (_) {}
            }
        } catch (e) { console.log('RK.removeNode ' + def + ': ' + e); }
    });

    const addRoute = _defer(function (fromDef, fromField, toDef, toField) {
        try {
            const s = _scene();
            if (!s) return;
            const f = _node(fromDef), t = _node(toDef);
            if (!f || !t) return;
            s.addRoute(f, fromField, t, toField);
        } catch (e) { console.log('RK.addRoute: ' + e); }
    });

    const removeRoute = _defer(function (fromDef, fromField, toDef, toField) {
        try {
            const s = _scene();
            if (!s) return;
            const f = _node(fromDef), t = _node(toDef);
            if (!f || !t) return;
            s.deleteRoute(f, fromField, t, toField);
        } catch (e) { console.log('RK.removeRoute: ' + e); }
    });

    const clearScene = _defer(function () {
        try {
            const s = _scene();
            if (s) {
                // Remove named-node registrations first to keep the registry clean.
                for (const k of Object.keys(_cache)) {
                    try { s.removeNamedNode(k); } catch (_) {}
                }
                while (s.rootNodes.length) s.rootNodes.splice(0, 1);
            }
            for (const k of Object.keys(_cache)) delete _cache[k];
        } catch (e) { console.log('RK.clearScene: ' + e); }
    });

    function invalidate(def) {
        if (def) delete _cache[def];
        else for (const k of Object.keys(_cache)) delete _cache[k];
    }

    function resetReady() {
        _ready = false;
        _queue.length = 0;
        invalidate();
    }

    window.RK = {
        setField, addNode, removeNode, addRoute, removeRoute,
        clearScene, invalidate, resetReady, _node, _onSceneReady,
        get _ready() { return _ready; },
    };
})();
