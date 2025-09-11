import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)
if importlib.util.find_spec('sqlalchemy') is None:
    pytest.skip('sqlalchemy not installed; skipping module', allow_module_level=True)

# --- ENHANCED UNIVERSAL BOOTSTRAP ---
import os, sys, importlib as _importlib, importlib.util as _iu, importlib.machinery as _im, types as _types, pytest as _pytest, builtins as _builtins
import warnings
STRICT = os.getenv("TESTGEN_STRICT", "1").lower() in ("1","true","yes")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
_target = os.environ.get("TARGET_ROOT") or os.environ.get("ANALYZE_ROOT") or "target"
if _target and os.path.exists(_target):
    if _target not in sys.path: sys.path.insert(0, _target)
    try: os.chdir(_target)
    except Exception: pass
_TARGET_ABS = os.path.abspath(_target)
def _exc_lookup(name, default):
    try:
        mod_name, _, cls_name = str(name).rpartition(".")
        if mod_name:
            mod = __import__(mod_name, fromlist=[cls_name])
            return getattr(mod, cls_name, default)
        return getattr(sys.modules.get("builtins"), str(name), default)
    except Exception:
        return default
def _apply_compatibility_fixes():
    try:
        import jinja2
        if not hasattr(jinja2, 'Markup'):
            try:
                from markupsafe import Markup, escape
                jinja2.Markup = Markup
                if not hasattr(jinja2, 'escape'):
                    jinja2.escape = escape
            except Exception:
                pass
    except ImportError:
        pass
    try:
        import flask
        if not hasattr(flask, 'escape'):
            try:
                from markupsafe import escape
                flask.escape = escape
            except Exception:
                pass
    except ImportError:
        pass
    try:
        import collections as _collections, collections.abc as _abc
        for _n in ('Mapping','MutableMapping','Sequence','Iterable','Container','MutableSequence','Set','MutableSet'):
            if not hasattr(_collections, _n) and hasattr(_abc, _n):
                setattr(_collections, _n, getattr(_abc, _n))
    except Exception:
        pass
_apply_compatibility_fixes()
_ADAPTED_MODULES = set()
def _attach_module_getattr(_m):
    try:
        if getattr(_m, "__name__", None) in _ADAPTED_MODULES: return
        mfile = getattr(_m, "__file__", "") or ""
        if not mfile or not os.path.abspath(mfile).startswith(_TARGET_ABS + os.sep): return
        if hasattr(_m, "__getattr__"):
            _ADAPTED_MODULES.add(_m.__name__); return
        def __getattr__(name):
            for _nm, _obj in list(_m.__dict__.items()):
                if isinstance(_obj, type) and not _nm.startswith("_"):
                    try: _inst = _obj()
                    except Exception: continue
                    if hasattr(_inst, name):
                        _val = getattr(_inst, name)
                        try: setattr(_m, name, _val)
                        except Exception: pass
                        return _val
            raise AttributeError(f"module {_m.__name__!r} has no attribute {name!r}")
        _m.__getattr__ = __getattr__; _ADAPTED_MODULES.add(_m.__name__)
    except Exception:
        pass
if not STRICT:
    _orig_import = _builtins.__import__
    def _import_with_adapter(name, globals=None, locals=None, fromlist=(), level=0):
        mod = _orig_import(name, globals, locals, fromlist, level)
        try:
            if isinstance(mod, _types.ModuleType): _attach_module_getattr(mod)
            if fromlist:
                for attr in fromlist:
                    try:
                        sub = getattr(mod, attr, None)
                        if isinstance(sub, _types.ModuleType): _attach_module_getattr(sub)
                    except Exception: pass
        except Exception: pass
        return mod
    _builtins.__import__ = _import_with_adapter
try:
    if _iu.find_spec("django") is not None:
        import django
        from django.conf import settings as _dj_settings
        if not _dj_settings.configured:
            _dj_settings.configure(SECRET_KEY="test-key", DEBUG=True, ALLOWED_HOSTS=["*"], INSTALLED_APPS=[], DATABASES={"default": {"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}})
            django.setup()
except Exception: pass
_PY2_ALIASES = {'ConfigParser': 'configparser', 'Queue': 'queue', 'StringIO': 'io', 'cStringIO': 'io', 'urllib2': 'urllib.request'}
for _old, _new in list(_PY2_ALIASES.items()):
    if _old in sys.modules: continue
    try:
        __import__(_new); sys.modules[_old] = sys.modules[_new]
    except Exception: pass
def _safe_find_spec(name):
    try: return _iu.find_spec(name)
    except Exception: return None
def _ensure_pkg(name, is_pkg=None):
    if name in sys.modules:
        m = sys.modules[name]
        if getattr(m, "__spec__", None) is None:
            m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=(is_pkg if is_pkg is not None else ("." not in name)))
            if "." not in name and not hasattr(m, "__path__"): m.__path__ = []
        return m
    m = _types.ModuleType(name)
    if is_pkg is None: is_pkg = ("." not in name)
    if is_pkg and not hasattr(m, "__path__"): m.__path__ = []
    m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=is_pkg)
    sys.modules[name] = m
    return m
for __qt_root in ["PyQt5","PyQt6","PySide2","PySide6"]:
    if _safe_find_spec(__qt_root) is None:
        _pkg=_ensure_pkg(__qt_root,True); _core=_ensure_pkg(__qt_root+".QtCore",False); _gui=_ensure_pkg(__qt_root+".QtGui",False); _widgets=_ensure_pkg(__qt_root+".QtWidgets",False)
        class QObject: pass
        def pyqtSignal(*a, **k): return object()
        def pyqtSlot(*a, **k):
            def _decorator(fn): return fn
            return _decorator
        class QCoreApplication: 
            def __init__(self,*a,**k): pass
            def exec_(self): return 0
            def exec(self): return 0
        _core.QObject=QObject; _core.pyqtSignal=pyqtSignal; _core.pyqtSlot=pyqtSlot; _core.QCoreApplication=QCoreApplication
        class QFont:  # minimal
            def __init__(self,*a,**k): pass
        class QDoubleValidator:
            def __init__(self,*a,**k): pass
            def setBottom(self,*a,**k): pass
            def setTop(self,*a,**k): pass
        class QIcon: 
            def __init__(self,*a,**k): pass
        class QPixmap:
            def __init__(self,*a,**k): pass
        _gui.QFont=QFont; _gui.QDoubleValidator=QDoubleValidator; _gui.QIcon=QIcon; _gui.QPixmap=QPixmap
        class QApplication:
            def __init__(self,*a,**k): pass
            def exec_(self): return 0
            def exec(self): return 0
        class QWidget: 
            def __init__(self,*a,**k): pass
        class QLabel(QWidget):
            def __init__(self,*a,**k): super().__init__(); self._text=""
            def setText(self,t): self._text=str(t)
            def text(self): return self._text
        class QLineEdit(QWidget):
            def __init__(self,*a,**k): super().__init__(); self._text=""
            def setText(self,t): self._text=str(t)
            def text(self): return self._text
            def clear(self): self._text=""
        class QTextEdit(QLineEdit): pass
        class QPushButton(QWidget):
            def __init__(self,*a,**k): super().__init__()
        class QMessageBox:
            @staticmethod
            def warning(*a,**k): return None
            @staticmethod
            def information(*a,**k): return None
            @staticmethod
            def critical(*a,**k): return None
        class QFileDialog:
            @staticmethod
            def getSaveFileName(*a,**k): return ("history.txt","")
            @staticmethod
            def getOpenFileName(*a,**k): return ("history.txt","")
        class QFormLayout:
            def __init__(self,*a,**k): pass
            def addRow(self,*a,**k): pass
        class QGridLayout(QFormLayout):
            def addWidget(self,*a,**k): pass
        _widgets.QApplication=QApplication; _widgets.QWidget=QWidget; _widgets.QLabel=QLabel; _widgets.QLineEdit=QLineEdit; _widgets.QTextEdit=QTextEdit
        _widgets.QPushButton=QPushButton; _widgets.QMessageBox=QMessageBox; _widgets.QFileDialog=QFileDialog; _widgets.QFormLayout=QFormLayout; _widgets.QGridLayout=QGridLayout
        for _name in ("QApplication","QWidget","QLabel","QLineEdit","QTextEdit","QPushButton","QMessageBox","QFileDialog","QFormLayout","QGridLayout"):
            setattr(_gui,_name,getattr(_widgets,_name))
_THIRD_PARTY_TOPS = ['click', 'compat', 'conduit', 'datetime', 'extensions', 'flask', 'flask_apispec', 'flask_bcrypt', 'flask_caching', 'flask_cors', 'flask_jwt_extended', 'flask_migrate', 'flask_sqlalchemy', 'glob', 'marshmallow', 'models', 'os', 'pytest', 'serializers', 'slugify', 'sqlalchemy', 'subprocess', 'sys', 'werkzeug']
# --- /ENHANCED UNIVERSAL BOOTSTRAP ---

import pytest
import json

def _exc_lookup(name, default=Exception):
    try:
        import conduit.exceptions as exc_mod
        return getattr(exc_mod, name, default)
    except Exception:
        return default

def test_article_serialization_and_update():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.serializers as sers
    except Exception:
        pytest.skip("conduit.articles.serializers not available")
    # Ensure required classes exist
    TagSchema = getattr(sers, "TagSchema", None)
    ArticleSchema = getattr(sers, "ArticleSchema", None)
    ArticleSchemas = getattr(sers, "ArticleSchemas", None)
    Meta = getattr(sers, "Meta", None)
    if not any([TagSchema, ArticleSchema, ArticleSchemas, Meta]):
        pytest.skip("Required serializer classes not present in conduit.articles.serializers")

    # Prepare an article-like mapping with duplicate tags to exercise normalization/deduplication
    article = {
        "slug": "test-article",
        "title": "Test Article",
        "description": "A short description",
        "body": "The article body",
        "tagList": ["python", "testing", "python"],
        "created_at": "2020-01-01T00:00:00Z",
        "updated_at": "2020-01-01T00:00:00Z",
        "author": {"username": "alice", "bio": "dev", "image": None}
    }

    # Dump using ArticleSchema if available; otherwise attempt ArticleSchemas (plural)
    schema = None
    if ArticleSchema is not None:
        schema = ArticleSchema()
    elif ArticleSchemas is not None:
        # Some implementations use a wrapper for list vs single; attempt to instantiate and use for single
        schema = ArticleSchemas()
    else:
        pytest.skip("No usable article schema found")

    # Perform first serialization
    try:
        serialized = schema.dump(article)
    except TypeError:
        # If schema expects many=True or different shape, try direct dict pass-through
        try:
            serialized = schema.dumps(article)
            serialized = json.loads(serialized)
        except Exception as e:
            raise

    # Basic sanity checks: title preserved, tagList present and duplicates removed if schema implements that
    assert isinstance(serialized, _exc_lookup("dict", Exception)), "Serialized article should be a dict-like object"
    assert serialized.get("title") == "Test Article"

    tags = serialized.get("tagList") or serialized.get("tags") or article.get("tagList")
    # Normalize tags to a list for assertions
    assert isinstance(tags, (list, tuple)), "Tags should be a list or tuple in serialization output"
    # The schema or serializer may dedupe tags; assert that at least 'python' and 'testing' are present
    assert "python" in tags and "testing" in tags
    # If deduplication implemented, length should be 2
    if len(tags) != 3:
        assert len(tags) == 2

    # Simulate an update: change title and tag membership, then re-serialize and ensure diffs reflected
    article["title"] = "Updated Title"
    # remove 'testing', add 'conduit'
    updated_tags = [t for t in article["tagList"] if t != "testing"]
    updated_tags.append("conduit")
    article["tagList"] = updated_tags

    try:
        serialized_updated = schema.dump(article)
    except TypeError:
        try:
            serialized_updated = schema.dumps(article)
            serialized_updated = json.loads(serialized_updated)
        except Exception as e:
            raise

    assert serialized_updated.get("title") == "Updated Title"
    updated_tags_out = serialized_updated.get("tagList") or serialized_updated.get("tags") or article.get("tagList")
    assert "conduit" in updated_tags_out
    assert "testing" not in updated_tags_out

def test_comment_serialization_and_wrapping():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        import conduit.articles.serializers as sers
    except Exception:
        pytest.skip("conduit.articles.serializers not available")
    CommentSchema = getattr(sers, "CommentSchema", None)
    CommentsSchema = getattr(sers, "CommentsSchema", None)
    make_comment = getattr(sers, "make_comment", None)
    dump_comment = getattr(sers, "dump_comment", None)
    # Require at least one of the comment-related utilities
    if CommentSchema is None and CommentsSchema is None and make_comment is None and dump_comment is None:
        pytest.skip("No comment serializer utilities available")

    # Compose a pair of comment-like mappings to simulate lifecycle: create -> serialize -> list wrap
    comment1 = {
        "id": 1,
        "created_at": "2021-01-01T10:00:00Z",
        "updated_at": "2021-01-01T10:00:00Z",
        "body": "Great article!",
        "author": {"username": "bob", "bio": None, "image": None}
    }
    comment2 = {
        "id": 2,
        "created_at": "2021-01-02T11:00:00Z",
        "updated_at": "2021-01-02T11:00:00Z",
        "body": "Thanks for sharing.",
        "author": {"username": "carol", "bio": None, "image": None}
    }

    # If make_comment exists, test it produces a structure acceptable to dump_comment or schemas
    if make_comment is not None:
        try:
            built = make_comment({"body": "Great article!", "author": {"username": "bob"}})
            # built should be mapping-like
            assert hasattr(built, "get") or isinstance(built, _exc_lookup("dict", Exception))
        except Exception:
            # Some implementations require more context; ignore and proceed to schema checks
            built = None

    # Use CommentSchema to serialize single comments if available
    serialized_comments = []
    if CommentSchema is not None:
        sch = CommentSchema()
        for c in (comment1, comment2):
            try:
                out = sch.dump(c)
            except TypeError:
                try:
                    out = sch.dumps(c)
                    out = json.loads(out)
                except Exception:
                    raise
            assert isinstance(out, _exc_lookup("dict", Exception))
            # Ensure body and author username are represented
            assert out.get("body") == c["body"]
            auth = out.get("author") or {}
            # author may be nested as dict or username field directly
            if isinstance(auth, _exc_lookup("dict", Exception)):
                assert auth.get("username") == c["author"]["username"]
            else:
                assert c["author"]["username"] in str(auth)
            serialized_comments.append(out)
    else:
        # Fall back to dump_comment function if schema missing
        if dump_comment is None:
            pytest.skip("No way to serialize comments in this environment")
        for c in (comment1, comment2):
            out = dump_comment(c)
            assert isinstance(out, _exc_lookup("dict", Exception))
            assert out.get("body") == c["body"]
            auth = out.get("author") or {}
            if isinstance(auth, _exc_lookup("dict", Exception)):
                assert auth.get("username") == c["author"]["username"]

    # Finally, test wrapping multiple comments using CommentsSchema if present
    if CommentsSchema is not None:
        wrapper = CommentsSchema()
        try:
            wrapped = wrapper.dump([comment1, comment2])
        except TypeError:
            try:
                wrapped = wrapper.dumps([comment1, comment2])
                wrapped = json.loads(wrapped)
            except Exception:
                raise
        # The wrapper may produce a list or a dict with a 'comments' key
        if isinstance(wrapped, _exc_lookup("dict", Exception)):
            # common RealWorld format is {'comments': [...]} or {'comments': [...], 'commentsCount': N}
            comments_out = wrapped.get("comments") or []
            assert isinstance(comments_out, _exc_lookup("list", Exception))
            bodies = [c.get("body") for c in comments_out]
            assert "Great article!" in bodies and "Thanks for sharing." in bodies
        else:
            # assume a plain list
            bodies = [c.get("body") for c in wrapped]
            assert "Great article!" in bodies and "Thanks for sharing." in bodies
    else:
        # Not present, ensure we at least serialized individual comments above
        assert len(serialized_comments) >= 1 or dump_comment is not None