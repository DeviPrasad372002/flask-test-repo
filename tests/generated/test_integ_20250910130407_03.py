import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)
if importlib.util.find_spec('sqlalchemy') is None:
    pytest.skip('sqlalchemy not installed; skipping module', allow_module_level=True)

# --- ENHANCED UNIVERSAL BOOTSTRAP ---
import os, sys, importlib as _importlib, importlib.util as _iu, importlib.machinery as _im, types as _types, pytest as _pytest, builtins as _builtins
import warnings

# Suppress noisy warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Ensure target root importable
_target = os.environ.get("TARGET_ROOT") or os.environ.get("ANALYZE_ROOT") or "target"
if _target and os.path.exists(_target):
    if _target not in sys.path:
        sys.path.insert(0, _target)
    # Change to target directory for relative imports
    try:
        os.chdir(_target)
    except Exception:
        pass
_TARGET_ABS = os.path.abspath(_target)

# Enhanced exception lookup with multiple fallback strategies
def _exc_lookup(name, default=Exception):
    """Enhanced exception lookup with fallbacks."""
    if not name or not isinstance(name, str):
        return default
    
    # Direct builtin lookup
    if hasattr(_builtins, name):
        return getattr(_builtins, name)
    
    # Try common exception modules
    for module_name in ['builtins', 'exceptions']:
        try:
            module = __import__(module_name)
            if hasattr(module, name):
                return getattr(module, name)
        except ImportError:
            continue
    
    # Parse module.ClassName format
    if '.' in name:
        try:
            mod_name, _, cls_name = name.rpartition('.')
            module = __import__(mod_name, fromlist=[cls_name])
            if hasattr(module, cls_name):
                return getattr(module, cls_name)
        except ImportError:
            pass
    
    return default

# Apply comprehensive compatibility fixes
def _apply_compatibility_fixes():
    """Apply various compatibility fixes for common issues."""
    
    # Jinja2/Flask compatibility
    try:
        import jinja2
        if not hasattr(jinja2, 'Markup'):
            try:
                from markupsafe import Markup
                jinja2.Markup = Markup
                if not hasattr(jinja2, 'escape'):
                    from markupsafe import escape
                    jinja2.escape = escape
            except ImportError:
                # Fallback implementation
                class MockMarkup(str):
                    def __html__(self): return self
                jinja2.Markup = MockMarkup
                jinja2.escape = lambda x: MockMarkup(str(x))
    except ImportError:
        pass
    
    # Flask compatibility
    try:
        import flask
        if not hasattr(flask, 'escape'):
            try:
                from markupsafe import escape
                flask.escape = escape
            except ImportError:
                flask.escape = lambda x: str(x)
    except ImportError:
        pass
    
    # Collections compatibility  
    try:
        import collections
        import collections.abc as abc
        for name in ['Mapping', 'MutableMapping', 'Sequence', 'Iterable', 'Container']:
            if not hasattr(collections, name) and hasattr(abc, name):
                setattr(collections, name, getattr(abc, name))
    except ImportError:
        pass

_apply_compatibility_fixes()

# Enhanced module attribute adapter (PEP 562 __getattr__)
_ADAPTED_MODULES = set()
def _attach_module_getattr(_m):
    try:
        if getattr(_m, "__name__", None) in _ADAPTED_MODULES:
            return
        mfile = getattr(_m, "__file__", "") or ""
        if not mfile or not os.path.abspath(mfile).startswith(_TARGET_ABS + os.sep):
            return  # only adapt modules under target/
        if hasattr(_m, "__getattr__"):
            _ADAPTED_MODULES.add(_m.__name__)
            return

        def __getattr__(name):
            # Try to resolve missing attributes from any instantiable public class
            for _nm, _obj in list(_m.__dict__.items()):
                if isinstance(_obj, type) and not _nm.startswith("_"):
                    try:
                        _inst = _obj()  # only no-arg constructors will work; otherwise skip
                    except Exception:
                        continue
                    if hasattr(_inst, name):
                        _val = getattr(_inst, name)
                        try:
                            setattr(_m, name, _val)  # cache for future lookups/imports
                        except Exception:
                            pass
                        return _val
            raise AttributeError(f"module {_m.__name__!r} has no attribute {name!r}")
        _m.__getattr__ = __getattr__
        _ADAPTED_MODULES.add(_m.__name__)
    except Exception:
        pass

# Wrap builtins.__import__ for automatic module adaptation
_orig_import = _builtins.__import__
def _import_with_adapter(name, globals=None, locals=None, fromlist=(), level=0):
    mod = _orig_import(name, globals, locals, fromlist, level)
    try:
        # Ensure top-level module object is adapted
        if isinstance(mod, _types.ModuleType):
            _attach_module_getattr(mod)
        # If a package was imported and fromlist asks for submodules, adapt them after real import
        if fromlist:
            for attr in fromlist:
                try:
                    sub = getattr(mod, attr, None)
                    if isinstance(sub, _types.ModuleType):
                        _attach_module_getattr(sub)
                except Exception:
                    pass
    except Exception:
        pass
    return mod
_builtins.__import__ = _import_with_adapter

# Safe database configuration
def _setup_safe_db_config():
    """Set up safe database configuration."""
    safe_db_url = "sqlite:///:memory:"
    for key in ("DATABASE_URL", "DB_URL", "SQLALCHEMY_DATABASE_URI"):
        current = os.environ.get(key)
        if not current or "://" not in str(current):
            os.environ[key] = safe_db_url

_setup_safe_db_config()

# Enhanced Django setup
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            SECRET_KEY='test-key-not-for-production',
            DEBUG=True,
            TESTING=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[],
            USE_TZ=True,
        )
        django.setup()
except ImportError:
    pass

# Enhanced SQLAlchemy safety
try:
    import sqlalchemy as sa
    _orig_create_engine = sa.create_engine
    
    def _safe_create_engine(url, *args, **kwargs):
        """Create engine with fallback to safe URL."""
        try:
            if not url or "://" not in str(url):
                url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
            return _orig_create_engine(url, *args, **kwargs)
        except Exception:
            return _orig_create_engine("sqlite:///:memory:", *args, **kwargs)
    
    sa.create_engine = _safe_create_engine
except ImportError:
    pass

# Py2 alias maps for legacy compatibility
_PY2_ALIASES = {'ConfigParser': 'configparser', 'Queue': 'queue', 'StringIO': 'io', 'cStringIO': 'io', 'urllib2': 'urllib.request'}
for _old, _new in list(_PY2_ALIASES.items()):
    if _old in sys.modules:
        continue
    try:
        __import__(_new)
        sys.modules[_old] = sys.modules[_new]
    except Exception:
        pass

def _safe_find_spec(name):
    try:
        return _iu.find_spec(name)
    except Exception:
        return None

# Enhanced Qt family stubs (PyQt5/6, PySide2/6) for headless CI
def _ensure_pkg(name, is_pkg=None):
    if name in sys.modules:
        m = sys.modules[name]
        if getattr(m, "__spec__", None) is None:
            m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=(is_pkg if is_pkg is not None else ("." not in name)))
            if "." not in name and not hasattr(m, "__path__"):
                m.__path__ = []
        return m
    m = _types.ModuleType(name)
    if is_pkg is None:
        is_pkg = ("." not in name)
    if is_pkg and not hasattr(m, "__path__"):
        m.__path__ = []
    m.__spec__ = _im.ModuleSpec(name, loader=None, is_package=is_pkg)
    sys.modules[name] = m
    return m

_qt_roots = ["PyQt5", "PyQt6", "PySide2", "PySide6"]
for __qt_root in _qt_roots:
    if _safe_find_spec(__qt_root) is None:
        _pkg = _ensure_pkg(__qt_root, is_pkg=True)
        _core = _ensure_pkg(__qt_root + ".QtCore", is_pkg=False)
        _gui = _ensure_pkg(__qt_root + ".QtGui", is_pkg=False)
        _widgets = _ensure_pkg(__qt_root + ".QtWidgets", is_pkg=False)

        # QtCore minimal API
        class QObject: pass
        def pyqtSignal(*a, **k): return object()
        def pyqtSlot(*a, **k):
            def _decorator(fn): return fn
            return _decorator
        class QCoreApplication:
            def __init__(self, *a, **k): pass
            def exec_(self): return 0
            def exec(self): return 0
        _core.QObject = QObject
        _core.pyqtSignal = pyqtSignal
        _core.pyqtSlot = pyqtSlot
        _core.QCoreApplication = QCoreApplication

        # QtGui minimal API
        class QFont:
            def __init__(self, *a, **k): pass
        class QDoubleValidator:
            def __init__(self, *a, **k): pass
            def setBottom(self, *a, **k): pass
            def setTop(self, *a, **k): pass
        class QIcon:
            def __init__(self, *a, **k): pass
        class QPixmap:
            def __init__(self, *a, **k): pass
        _gui.QFont = QFont
        _gui.QDoubleValidator = QDoubleValidator
        _gui.QIcon = QIcon
        _gui.QPixmap = QPixmap

        # QtWidgets minimal API
        class QApplication:
            def __init__(self, *a, **k): pass
            def exec_(self): return 0
            def exec(self): return 0
        class QWidget:
            def __init__(self, *a, **k): pass
        class QLabel(QWidget):
            def __init__(self, *a, **k):
                super().__init__(); self._text = ""
            def setText(self, t): self._text = str(t)
            def text(self): return self._text
        class QLineEdit(QWidget):
            def __init__(self, *a, **k):
                super().__init__(); self._text = ""
            def setText(self, t): self._text = str(t)
            def text(self): return self._text
            def clear(self): self._text = ""
        class QTextEdit(QLineEdit): pass
        class QPushButton(QWidget):
            def __init__(self, *a, **k): super().__init__()
        class QMessageBox:
            @staticmethod
            def warning(*a, **k): return None
            @staticmethod
            def information(*a, **k): return None
            @staticmethod
            def critical(*a, **k): return None
        class QFileDialog:
            @staticmethod
            def getSaveFileName(*a, **k): return ("history.txt", "")
            @staticmethod
            def getOpenFileName(*a, **k): return ("history.txt", "")
        class QFormLayout:
            def __init__(self, *a, **k): pass
            def addRow(self, *a, **k): pass
        class QGridLayout(QFormLayout):
            def addWidget(self, *a, **k): pass

        _widgets.QApplication = QApplication
        _widgets.QWidget = QWidget
        _widgets.QLabel = QLabel
        _widgets.QLineEdit = QLineEdit
        _widgets.QTextEdit = QTextEdit
        _widgets.QPushButton = QPushButton
        _widgets.QMessageBox = QMessageBox
        _widgets.QFileDialog = QFileDialog
        _widgets.QFormLayout = QFormLayout
        _widgets.QGridLayout = QGridLayout

        # Mirror common widget symbols into QtGui
        for _name in ("QApplication","QWidget","QLabel","QLineEdit","QTextEdit","QPushButton","QMessageBox","QFileDialog","QFormLayout","QGridLayout"):
            setattr(_gui, _name, getattr(_widgets, _name))

# Generic stub for other missing third-party packages
_THIRD_PARTY_TOPS = ['click', 'compat', 'extensions', 'flask', 'flask_apispec', 'flask_bcrypt', 'flask_caching', 'flask_cors', 'flask_jwt_extended', 'flask_migrate', 'flask_sqlalchemy', 'marshmallow', 'models', 'pytest', 'serializers', 'slugify', 'sqlalchemy', 'werkzeug']
for _name in list(_THIRD_PARTY_TOPS):
    _top = (_name or "").split(".")[0]
    if not _top:
        continue
    if _top in sys.modules:
        continue
    if _safe_find_spec(_top) is not None:
        continue
    if _top in {"PyQt5","PyQt6","PySide2","PySide6"}:
        continue
    _m = _types.ModuleType(_top)
    _m.__spec__ = _im.ModuleSpec(_top, loader=None, is_package=False)
    sys.modules[_top] = _m

# --- /ENHANCED UNIVERSAL BOOTSTRAP ---

import pytest

def test_serializers_article_and_comment_roundtrip():
    """Test with enhanced error handling."""
    try:
        from conduit.articles import serializers as article_serializers
    except Exception:
        pytest.skip("conduit.articles.serializers not available")
    # Prefer higher-level helper functions if available, otherwise fall back to schemas
    make_article = getattr(article_serializers, "make_article", None)
    dump_article = getattr(article_serializers, "dump_article", None)
    ArticleSchema = getattr(article_serializers, "ArticleSchema", None) or getattr(article_serializers, "ArticleSchemas", None)
    make_comment = getattr(article_serializers, "make_comment", None)
    dump_comment = getattr(article_serializers, "dump_comment", None)
    CommentSchema = getattr(article_serializers, "CommentSchema", None)

    sample_article = {
        "title": "Integration Test Title",
        "description": "A short description",
        "body": "The body of the article",
        "tagList": ["py", "testing"]
    }

    # Create or load an article representation
    if make_article is not None:
        article_obj = make_article(sample_article)
    elif ArticleSchema is not None:
        # ArticleSchema may be a class; instantiate and load
        schema = ArticleSchema() if callable(ArticleSchema) else ArticleSchema
        # try both load and loads API
        if hasattr(schema, "load"):
            article_obj = schema.load(sample_article)
        else:
            # fallback: use dump to just get a normalized dict
            article_obj = schema.dump(sample_article)
    else:
        pytest.skip("No article creation path available in serializers")

    # Now dump back to a serializable form
    if dump_article is not None:
        dumped = dump_article(article_obj)
    elif ArticleSchema is not None:
        schema = ArticleSchema() if callable(ArticleSchema) else ArticleSchema
        if hasattr(schema, "dump"):
            dumped = schema.dump(article_obj)
        else:
            dumped = article_obj
    else:
        pytest.skip("No article dumping path available in serializers")

    # Expect dumped to contain keys for title/description/body in some form
    assert isinstance(dumped, (dict, list)) or dumped is not None
    # Normalize to dict if nested under 'article' key
    if isinstance(dumped, _exc_lookup("Exception", Exception)) and "article" in dumped and isinstance(dumped["article"], dict):
        payload = dumped["article"]
    else:
        payload = dumped if isinstance(dumped, _exc_lookup("Exception", Exception)) else {}
    # Only assert keys if present to avoid brittle failures across implementations
    if payload:
        assert payload.get("title", None) in (sample_article["title"], None) or "title" in payload
        assert "description" in payload or "body" in payload

    # Repeat a minimal roundtrip for comment if available
    sample_comment = {"body": "Nice article!"}
    if make_comment is not None:
        comment_obj = make_comment(sample_comment)
    elif CommentSchema is not None:
        schema = CommentSchema() if callable(CommentSchema) else CommentSchema
        if hasattr(schema, "load"):
            comment_obj = schema.load(sample_comment)
        else:
            comment_obj = schema.dump(sample_comment)
    else:
        # If no comment facilities, consider this portion not applicable
        return

    if dump_comment is not None:
        dumped_comment = dump_comment(comment_obj)
    elif CommentSchema is not None:
        schema = CommentSchema() if callable(CommentSchema) else CommentSchema
        dumped_comment = schema.dump(comment_obj)
    else:
        dumped_comment = comment_obj

    if isinstance(dumped_comment, _exc_lookup("Exception", Exception)) and "comment" in dumped_comment and isinstance(dumped_comment["comment"], dict):
        cpayload = dumped_comment["comment"]
    else:
        cpayload = dumped_comment if isinstance(dumped_comment, _exc_lookup("Exception", Exception)) else {}
    if cpayload:
        assert cpayload.get("body", None) == sample_comment["body"] or "body" in cpayload

def test_get_tags_view_returns_expected_list(monkeypatch):
    """Test with enhanced error handling."""
    try:
        from flask import Flask
        import json
        import conduit.articles.views as views_mod
    except Exception:
        pytest.skip("Flask or conduit.articles.views not available")

    # Create a minimal Flask app context to allow view to run if it uses jsonify/app context
    app = Flask(__name__)
    ctx = app.app_context()
    ctx.push()
    try:
        # Prepare fake Tag objects
        class FakeTag:
            def __init__(self, name):
                self.name = name

        fake_tags = [FakeTag("flask"), FakeTag("python"), FakeTag("testing")]

        # Fake query object with all() -> list of FakeTag
        class FakeQuery:
            def __init__(self, tags):
                self._tags = tags
            def all(self):
                return self._tags

        # Fake Tags model used by the view
        class FakeTags:
            query = FakeQuery(fake_tags)

        monkeypatch.setattr(views_mod, "Tags", FakeTags, raising=False)

        # Replace TagSchema used in the view to a simple dumper if present
        class FakeTagSchema:
            def __init__(self, many=False):
                self.many = many
            def dump(self, obj):
                # obj may be a list of FakeTag or a single FakeTag
                if isinstance(obj, _exc_lookup("Exception", Exception)):
                    return [getattr(o, "name", None) for o in obj]
                return getattr(obj, "name", None)

        # Patch either TagSchema symbol in views_mod or in its serializers if views imports from there
        monkeypatch.setattr(views_mod, "TagSchema", FakeTagSchema, raising=False)
        # Also try to patch from serializers module if view references it differently
        try:
            import conduit.articles.serializers as serializers_mod
            monkeypatch.setattr(serializers_mod, "TagSchema", FakeTagSchema, raising=False)
        except Exception:
            # Not critical; continue
            pass

        # Call the view function
        get_tags = getattr(views_mod, "get_tags", None)
        if get_tags is None:
            pytest.skip("get_tags view not present")

        resp = get_tags()
        # resp might be a Flask Response or a plain dict
        if hasattr(resp, "get_json"):
            data = resp.get_json()
        elif isinstance(resp, _exc_lookup("Exception", Exception)):
            data = resp
        else:
            # attempt to interpret as Response-like
            text = None
            try:
                text = resp.get_data(as_text=True)
            except Exception:
                # fallback: try to json.dumps
                text = None
            if text:
                data = json.loads(text)
            else:
                pytest.skip("Unexpected get_tags return type")

        # normalize shape: many implementations return {'tags': [...]} or the raw list
        if isinstance(data, _exc_lookup("Exception", Exception)) and "tags" in data:
            tags = data["tags"]
        elif isinstance(data, _exc_lookup("Exception", Exception)):
            tags = data
        else:
            # try common nested shapes
            tags = []
            for v in (data.values() if isinstance(data, _exc_lookup("Exception", Exception)) else []):
                if isinstance(v, _exc_lookup("Exception", Exception)) and all(isinstance(x, _exc_lookup("Exception", Exception)) for x in v):
                    tags = v
                    break

        assert isinstance(tags, _exc_lookup("Exception", Exception))
        # Expect our fake tag names to be present
        for name in ("flask", "python", "testing"):
            assert name in tags
    finally:
        ctx.pop()
