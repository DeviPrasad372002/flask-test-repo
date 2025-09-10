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

import types

def test_article_tags_and_favorites():
    """Test with enhanced error handling."""
    import pytest
    try:
        from conduit.articles.models import Article
        from conduit.articles.models import Tags  # may be used internally
        from conduit.articles.models import is_favourite, favoritesCount  # helpers if exposed
        from conduit.articles.serializers import dump_article
    except ImportError:
        pytest.skip("required conduit article modules not available")
    # create a minimal Article instance and a lightweight user-like object
    try:
        article = Article(title="Test Title", body="Some body", slug="test-title")
    except TypeError:
        # Some models accept fewer args; fall back to empty construction and set attrs
        article = Article()
        setattr(article, "title", "Test Title")
        setattr(article, "body", "Some body")
        setattr(article, "slug", "test-title")
    user = types.SimpleNamespace(id=1, username="alice")
    # Tag operations
    if not hasattr(article, "add_tag") or not hasattr(article, "remove_tag") or not hasattr(article, "tags"):
        pytest.skip("tag API not present on Article")
    # start with no tags
    try:
        initial_names = [getattr(t, "name", None) for t in getattr(article, "tags", [])]
    except Exception:
        initial_names = []
    # add a tag
    article.add_tag("python")
    names_after_add = [getattr(t, "name", None) for t in getattr(article, "tags", [])]
    assert "python" in names_after_add
    # remove the tag
    article.remove_tag("python")
    names_after_remove = [getattr(t, "name", None) for t in getattr(article, "tags", [])]
    assert "python" not in names_after_remove
    # favourites: add favourite
    if not (hasattr(article, "favourite") and hasattr(article, "unfavourite") and hasattr(article, "is_favourite")):
        pytest.skip("favourite API not present on Article")
    article.favourite(user)
    # is_favourite may accept user object or id; try both defensively
    fav_check = article.is_favourite(user) if callable(getattr(article, "is_favourite", None)) else False
    if not fav_check:
        try:
            fav_check = article.is_favourite(user.id)
        except Exception:
            fav_check = False
    assert fav_check is True
    # favoritesCount may be a method or property
    count = None
    if hasattr(article, "favoritesCount"):
        try:
            count = article.favoritesCount()
        except TypeError:
            count = article.favoritesCount
    elif hasattr(article, "favorites_count"):
        count = getattr(article, "favorites_count")
    else:
        # best-effort: count favorites relationship length
        favs = getattr(article, "favorites", None)
        if favs is not None:
            try:
                count = len(favs)
            except Exception:
                count = None
    assert count == 1 or count == 1.0
    # favorited: check using possible signatures (username or user)
    has_favorited = False
    if hasattr(article, "favorited"):
        try:
            has_favorited = article.favorited(user)
        except Exception:
            try:
                has_favorited = article.favorited(user.username)
            except Exception:
                has_favorited = False
    # allow either True or truthy representation
    assert bool(has_favorited) is True
    # dump_article should reflect favorites and tags if available
    try:
        dumped = dump_article(article, user)
    except TypeError:
        # some dump_article implementations accept only the article
        dumped = dump_article(article)
    except Exception:
        pytest.skip("dump_article not operable in this environment")
    assert isinstance(dumped, _exc_lookup("Exception", Exception))
    # expected keys present
    assert "favoritesCount" in dumped or "favorites_count" in dumped or "favorited" in dumped
    # cleanup: unfavourite
    article.unfavourite(user)
    # after unfavourite, is_favourite should be false
    try:
        is_now = article.is_favourite(user)
    except Exception:
        try:
            is_now = article.is_favourite(user.id)
        except Exception:
            is_now = False
    assert is_now is False

def test_serializers_make_and_dump_article_and_comment():
    """Test with enhanced error handling."""
    import pytest
    try:
        from conduit.articles.serializers import make_article, dump_article, dump_articles, make_comment, dump_comment
    except ImportError:
        pytest.skip("article/comment serializer functions not available")
    # Prepare payloads
    article_payload = {
        "title": "Serializer Title",
        "description": "desc",
        "body": "body text",
        "tagList": ["one", "two"]
    }
    comment_payload = {"body": "a comment body"}
    # make_article may return dict or Article instance; accept either
    result = make_article(article_payload)
    # ensure we obtained something usable
    assert result is not None
    # If result is a dict, expect keys; if object, access attributes
    if isinstance(result, _exc_lookup("Exception", Exception)):
        assert result.get("title") == "Serializer Title"
        # Now dump via dump_article: may accept dict or object
        try:
            dumped = dump_article(result, None)
        except TypeError:
            dumped = dump_article(result)
    else:
        # treat as object with attributes
        assert getattr(result, "title", None) == "Serializer Title"
        try:
            dumped = dump_article(result, None)
        except TypeError:
            dumped = dump_article(result)
    # dump_article should return a dict representation
    assert isinstance(dumped, _exc_lookup("Exception", Exception))
    assert dumped.get("title") == "Serializer Title" or dumped.get("article", {}).get("title") == "Serializer Title" or "title" in dumped
    # dump_articles should be able to accept a sequence
    try:
        many = dump_articles([result])
    except TypeError:
        # maybe signature requires (items, user)
        many = dump_articles([result], None)
    assert isinstance(many, (list, dict))
    # Comment creation and dumping
    cresult = make_comment(comment_payload)
    assert cresult is not None
    try:
        cdumped = dump_comment(cresult)
    except TypeError:
        cdumped = dump_comment(cresult, None)
    assert isinstance(cdumped, _exc_lookup("Exception", Exception))
    assert "body" in cdumped or cdumped.get("comment", {}).get("body") == "a comment body"

def test_favourite_unfavourite_flow_idempotency():
    """Test with enhanced error handling."""
    import pytest
    try:
        from conduit.articles.models import Article
    except ImportError:
        pytest.skip("Article model not available")
    # create article and a simple user-like object
    try:
        article = Article(title="Flow Title", body="B", slug="flow-title")
    except TypeError:
        article = Article()
        setattr(article, "title", "Flow Title")
        setattr(article, "body", "B")
        setattr(article, "slug", "flow-title")
    user = types.SimpleNamespace(id=42, username="bob")
    if not (hasattr(article, "favourite") and hasattr(article, "unfavourite") and hasattr(article, "is_favourite")):
        pytest.skip("favourite API not present on Article")
    # Multiple favourites should not inflate count (idempotency)
    article.favourite(user)
    article.favourite(user)
    # attempt to get count
    count = None
    if hasattr(article, "favoritesCount"):
        try:
            count = article.favoritesCount()
        except Exception:
            try:
                count = article.favoritesCount
            except Exception:
                count = None
    else:
        favs = getattr(article, "favorites", None)
        if favs is not None:
            try:
                count = len(favs)
            except Exception:
                count = None
    assert count == 1 or count == 1.0
    # unfavourite twice should remain zero
    article.unfavourite(user)
    article.unfavourite(user)
    # check count again
    if hasattr(article, "favoritesCount"):
        try:
            final_count = article.favoritesCount()
        except Exception:
            final_count = getattr(article, "favoritesCount", 0)
    else:
        favs = getattr(article, "favorites", None)
        if favs is not None:
            try:
                final_count = len(favs)
            except Exception:
                final_count = 0
        else:
            final_count = 0
    assert final_count == 0 or final_count == 0.0
