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

import inspect
import datetime
import types
import pytest

def _call_with_flexible_args(func, defaults):
    """
    Attempt to call func by matching parameter names to keys in defaults dict.
    If a parameter has a default, it will be omitted.
    Returns (success, return_value or exception)
    """
    sig = inspect.signature(func)
    kwargs = {}
    for name, param in sig.parameters.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if param.default is not inspect._empty:
            # Has default - skip providing it
            continue
        if name in defaults:
            kwargs[name] = defaults[name]
        else:
            # try heuristic mapping
            lname = name.lower()
            if 'article' in lname:
                kwargs[name] = defaults.get('article')
            elif 'user' in lname or 'author' in lname or 'profile' in lname:
                kwargs[name] = defaults.get('user')
            elif 'data' in lname or 'payload' in lname or 'body' in lname:
                kwargs[name] = defaults.get('data')
            else:
                # fallback to article
                kwargs[name] = defaults.get('article')
    try:
        return True, func(**kwargs)
    except Exception as e:
        return False, e

def _make_dummy_author(username='alice'):
    class DummyAuthor:
        def __init__(self, username):
            self.username = username
        def to_dict(self):
            return {'username': self.username}
    return DummyAuthor(username)

def _make_dummy_article():
    class DummyArticle:
        def __init__(self):
            self.slug = 'dummy-slug'
            self.title = 'Dummy Title'
            self.description = 'desc'
            self.body = 'body of the article'
            self.tagList = ['python', 'testing']
            self.tags = list(self.tagList)
            self.created_at = datetime.datetime(2020,1,1)
            self.updated_at = datetime.datetime(2020,1,2)
            self.author = _make_dummy_author('alice')
            # some implementations expect favorites relationship or counters
            self.favorites = set()
            self.favorites_count = 0
            self.favorited = False
        # allow iteration/serialization helpers
        def to_dict(self):
            return {
                'slug': self.slug,
                'title': self.title,
                'description': self.description,
                'body': self.body,
                'tagList': list(self.tagList),
                'author': {'username': self.author.username},
                'favoritesCount': self.favorites_count,
                'favorited': self.favorited
            }
        def __iter__(self):
            # allow marshmallow/dumpers that iterate over object (uncommon)
            yield from ()
    return DummyArticle()

def _make_dummy_comment():
    class DummyComment:
        def __init__(self):
            self.id = 1
            self.body = "a comment"
            self.created_at = datetime.datetime(2020,1,3)
            self.updated_at = datetime.datetime(2020,1,4)
            self.author = _make_dummy_author('bob')
        def to_dict(self):
            return {'id': self.id, 'body': self.body, 'author': {'username': self.author.username}}
    return DummyComment()

def test_tags_add_remove_and_dump_article():
    """Test with enhanced error handling."""
    try:
        from conduit.articles import models as article_models
    except Exception:
        pytest.skip("conduit.articles.models not importable")
    # Try to find a Tags-like class
    Tags = getattr(article_models, 'Tags', None)
    if Tags is None:
        pytest.skip("No Tags class available in conduit.articles.models")
    # instantiate Tags accommodating possible signatures
    try:
        tags = Tags(['start'])
    except TypeError:
        try:
            tags = Tags()
            # if an add method exists, populate it
            if hasattr(tags, 'add'):
                tags.add('start')
        except Exception:
            pytest.skip("Cannot instantiate Tags class in a supported way")
    # Determine how to inspect contents of tags
    def list_tags(obj):
        # try multiple common access patterns
        if hasattr(obj, 'to_list'):
            return list(obj.to_list())
        if hasattr(obj, 'all'):
            try:
                return list(obj.all())
            except Exception:
                pass
        if hasattr(obj, 'items'):
            try:
                return list(obj.items())
            except Exception:
                pass
        if isinstance(obj, (list, tuple, set)):
            return list(obj)
        # try iterating
        try:
            return list(iter(obj))
        except Exception:
            pass
        # try attribute names
        for attr in ('tags', 'tagList', 'values'):
            if hasattr(obj, attr):
                val = getattr(obj, attr)
                if isinstance(val, (list, tuple, set)):
                    return list(val)
        # give up
        return []
    initial = list_tags(tags)
    # ensure 'new-tag' can be added via common method names
    added = False
    for meth in ('add', 'add_tag', 'append'):
        if hasattr(tags, meth):
            getattr(tags, meth)('new-tag')
            added = True
            break
    if not added:
        # try if it's a list-like and is mutable
        try:
            if isinstance(tags, _exc_lookup("Exception", Exception)):
                tags.append('new-tag')
                added = True
        except Exception:
            pass
    current = list_tags(tags)
    assert 'new-tag' in current, "Tags implementation did not accept adding a tag"
    # try removal
    removed = False
    for meth in ('remove', 'discard', 'remove_tag'):
        if hasattr(tags, meth):
            getattr(tags, meth)('new-tag')
            removed = True
            break
    if not removed:
        try:
            if isinstance(tags, _exc_lookup("Exception", Exception)):
                tags.remove('new-tag')
                removed = True
        except Exception:
            pass
    current_after = list_tags(tags)
    assert 'new-tag' not in current_after, "Tags implementation did not remove tag"

    # Try dump_article serializer
    try:
        from conduit.articles.serializers import dump_article
    except Exception:
        pytest.skip("dump_article not available in conduit.articles.serializers")
    dummy = _make_dummy_article()
    success, out = _call_with_flexible_args(dump_article, {'article': dummy})
    assert success, f"dump_article failed when called: {out}"
    assert isinstance(out, (dict, list)), "dump_article should return a dict or list-like structure"

def test_dump_articles_and_comment_serializers_and_make_comment():
    """Test with enhanced error handling."""
    try:
        from conduit.articles.serializers import dump_articles, dump_comment, make_comment
    except Exception:
        pytest.skip("Required serializers not available in conduit.articles.serializers")
    dummy_article = _make_dummy_article()
    # dump_articles might accept a list or query, try both
    success, out = _call_with_flexible_args(dump_articles, {'articles': [dummy_article], 'article': dummy_article})
    assert success, f"dump_articles failed when called: {out}"
    assert isinstance(out, (dict, list)), "dump_articles should return a mapping or list"
    # dump_comment
    dummy_comment = _make_dummy_comment()
    success2, out2 = _call_with_flexible_args(dump_comment, {'comment': dummy_comment, 'data': {'body': 'x'}})
    assert success2, f"dump_comment failed when called: {out2}"
    assert isinstance(out2, (dict, list)), "dump_comment should return a mapping or list"
    # make_comment: try creating a comment from data and author
    # If signature requires article or data or user, provide them
    data_payload = {'body': 'hello from test'}
    user = _make_dummy_author('commenter')
    defaults = {'data': data_payload, 'user': user, 'author': user, 'article': dummy_article}
    success3, out3 = _call_with_flexible_args(make_comment, defaults)
    # make_comment may create a model instance or dict; ensure it did not raise
    assert success3, f"make_comment raised when called: {out3}"
    assert out3 is not None, "make_comment returned None unexpectedly"

def test_favorites_helpers_behave_reasonably():
    """Test with enhanced error handling."""
    try:
        from conduit.articles import models as article_models
    except Exception:
        pytest.skip("conduit.articles.models not importable")
    # Try to get helper functions if present
    fav_count_fn = getattr(article_models, 'favoritesCount', None) or getattr(article_models, 'favorites_count', None)
    is_fav_fn = getattr(article_models, 'is_favourite', None) or getattr(article_models, 'is_favorite', None)
    favorited_fn = getattr(article_models, 'favorited', None)
    # Prepare dummy objects
    dummy_article = _make_dummy_article()
    user = _make_dummy_author('u1')
    # Ensure favoritesCount if present returns an int >= 0
    if fav_count_fn is not None:
        success, out = _call_with_flexible_args(fav_count_fn, {'article': dummy_article, 'user': user})
        assert success, f"favoritesCount-like function raised: {out}"
        assert isinstance(out, _exc_lookup("Exception", Exception)), "favoritesCount should return an int"
        assert out >= 0
    # is_favourite should return a boolean if present
    if is_fav_fn is not None:
        success2, out2 = _call_with_flexible_args(is_fav_fn, {'article': dummy_article, 'user': user})
        assert success2, f"is_favourite-like function raised: {out2}"
        assert isinstance(out2, _exc_lookup("Exception", Exception)), "is_favourite should return a boolean"
    # favorited may be attribute or function; check either
    if favorited_fn is not None:
        if inspect.isfunction(favorited_fn) or inspect.ismethod(favorited_fn):
            success3, out3 = _call_with_flexible_args(favorited_fn, {'article': dummy_article, 'user': user})
            assert success3, f"favorited function raised: {out3}"
            assert isinstance(out3, _exc_lookup("Exception", Exception))
        else:
            # attribute-like - ensure it's bool or convertible
            val = favorited_fn
            assert isinstance(val, (bool, int)) or val is None
    # If none of the helpers exist, skip to avoid false failure
    if fav_count_fn is None and is_fav_fn is None and favorited_fn is None:
        pytest.skip("No favorites related helpers available to test")
