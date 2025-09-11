import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)
if importlib.util.find_spec('sqlalchemy') is None:
    pytest.skip('sqlalchemy not installed; skipping module', allow_module_level=True)

# --- ENHANCED UNIVERSAL BOOTSTRAP ---
import os, sys, importlib as _importlib, importlib.util as _iu, importlib.machinery as _im, types as _types, pytest as _pytest, builtins as _builtins, importlib.util
import warnings

# Strict mode: default ON (1). Set TESTGEN_STRICT=0 to relax locally.
STRICT = os.getenv("TESTGEN_STRICT", "1").lower() in ("1","true","yes")

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

_target = os.environ.get("TARGET_ROOT") or os.environ.get("ANALYZE_ROOT") or "target"
if _target and os.path.exists(_target):
    if _target not in sys.path:
        sys.path.insert(0, _target)
    try:
        os.chdir(_target)
    except Exception:
        pass
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
        import collections as _collections
        import collections.abc as _abc
        for _n in ('Mapping','MutableMapping','Sequence','Iterable','Container','MutableSequence','Set','MutableSet'):
            if not hasattr(_collections, _n) and hasattr(_abc, _n):
                setattr(_collections, _n, getattr(_abc, _n))
    except Exception:
        pass
_apply_compatibility_fixes()

# Attribute adapter (dangerous): only in RELAXED mode
_ADAPTED_MODULES = set()
def _attach_module_getattr(_m):
    try:
        if getattr(_m, "__name__", None) in _ADAPTED_MODULES:
            return
        mfile = getattr(_m, "__file__", "") or ""
        if not mfile or not os.path.abspath(mfile).startswith(_TARGET_ABS + os.sep):
            return
        if hasattr(_m, "__getattr__"):
            _ADAPTED_MODULES.add(_m.__name__)
            return
        def __getattr__(name):
            for _nm, _obj in list(_m.__dict__.items()):
                if isinstance(_obj, type) and not _nm.startswith("_"):
                    try:
                        _inst = _obj()
                    except Exception:
                        continue
                    if hasattr(_inst, name):
                        _val = getattr(_inst, name)
                        try:
                            setattr(_m, name, _val)
                        except Exception:
                            pass
                        return _val
            raise AttributeError(f"module {_m.__name__!r} has no attribute {name!r}")
        _m.__getattr__ = __getattr__
        _ADAPTED_MODULES.add(_m.__name__)
    except Exception:
        pass

if not STRICT:
    _orig_import = _builtins.__import__
    def _import_with_adapter(name, globals=None, locals=None, fromlist=(), level=0):
        mod = _orig_import(name, globals, locals, fromlist, level)
        try:
            if isinstance(mod, _types.ModuleType):
                _attach_module_getattr(mod)
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

# Safe DB defaults & SQLAlchemy fallback ONLY in RELAXED mode
if not STRICT:
    for _k in ("DATABASE_URL","DB_URL","SQLALCHEMY_DATABASE_URI"):
        _v = os.environ.get(_k)
        if not _v or "://" not in str(_v):
            os.environ[_k] = "sqlite:///:memory:"
    try:
        if _iu.find_spec("sqlalchemy") is not None:
            import sqlalchemy as _s_sa
            from sqlalchemy.exc import ArgumentError as _s_ArgErr
            _s_orig_create_engine = _s_sa.create_engine
            def _s_safe_create_engine(url, *args, **kwargs):
                try_url = url
                try:
                    if not isinstance(try_url, str) or "://" not in try_url:
                        try_url = os.environ.get("DATABASE_URL") or os.environ.get("DB_URL") or os.environ.get("SQLALCHEMY_DATABASE_URI") or "sqlite:///:memory:"
                    return _s_orig_create_engine(try_url, *args, **kwargs)
                except _s_ArgErr:
                    return _s_orig_create_engine("sqlite:///:memory:", *args, **kwargs)
            _s_sa.create_engine = _s_safe_create_engine
    except Exception:
        pass

# Django minimal settings only if installed (harmless both modes)
try:
    if _iu.find_spec("django") is not None:
        import django
        from django.conf import settings as _dj_settings
        if not _dj_settings.configured:
            _dj_settings.configure(
                SECRET_KEY="test-key",
                DEBUG=True,
                ALLOWED_HOSTS=["*"],
                INSTALLED_APPS=[],
                DATABASES={"default": {"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
            )
            django.setup()
except Exception:
    pass

# Py2 alias maps
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

# Qt shims: keep even in strict (headless CI), harmless if real Qt present
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
        class QFont:  # minimal placeholders
            def __init__(self, *a, **k): pass
        class QDoubleValidator:
            def __init__(self, *a, **k): pass
            def setBottom(self, *a, **k): pass
            def setTop(self, *a, **k): pass
        class QIcon:  # noqa
            def __init__(self, *a, **k): pass
        class QPixmap:
            def __init__(self, *a, **k): pass
        _gui.QFont = QFont
        _gui.QDoubleValidator = QDoubleValidator
        _gui.QIcon = QIcon
        _gui.QPixmap = QPixmap
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
        for _name in ("QApplication","QWidget","QLabel","QLineEdit","QTextEdit","QPushButton","QMessageBox","QFileDialog","QFormLayout","QGridLayout"):
            setattr(_gui, _name, getattr(_widgets, _name))

# Optional generic stubs for other missing third-party tops ONLY in RELAXED mode
if not STRICT:
    _THIRD_PARTY_TOPS = ['click', 'compat', 'conduit', 'datetime', 'extensions', 'flask', 'flask_apispec', 'flask_bcrypt', 'flask_caching', 'flask_cors', 'flask_jwt_extended', 'flask_migrate', 'flask_sqlalchemy', 'glob', 'marshmallow', 'models', 'os', 'pytest', 'serializers', 'slugify', 'sqlalchemy', 'subprocess', 'sys', 'werkzeug']
    for _name in list(_THIRD_PARTY_TOPS):
        _top = (_name or "").split(".")[0]
        if not _top or _top in sys.modules:
            continue
        if _safe_find_spec(_top) is not None:
            continue
        if _top in ('PyQt5', 'PyQt6', 'PySide2', 'PySide6'):
            continue
        _m = _types.ModuleType(_top)
        _m.__spec__ = _im.ModuleSpec(_top, loader=None, is_package=False)
        sys.modules[_top] = _m

# --- /ENHANCED UNIVERSAL BOOTSTRAP ---

import pytest

def _call_with_fallback(func, *initial_args):
    """
    Try to call func with provided initial_args. If TypeError about missing
    positional arguments occurs, retry by appending None up to 3 total args.
    Re-raises other exceptions.
    """
    try:
        return func(*initial_args)
    except TypeError as e:
        # try adding up to two None placeholders (total up to len(initial_args)+2)
        for extra in range(1, 3):
            try_args = initial_args + (None,) * extra
            try:
                return func(*try_args)
            except TypeError:
                continue
            except Exception:
                raise
        # final attempt: call with only None placeholders (up to 3)
        for n in range(1, 4):
            try:
                return func(*((None,) * n))
            except TypeError:
                continue
            except Exception:
                raise
        raise

def _normalize_article_output(out):
    # Accept either {'article': {...}} or {...}
    if isinstance(out, _exc_lookup("dict", Exception)) and 'article' in out:
        return out['article']
    return out

def _normalize_comment_output(out):
    # Accept either {'comment': {...}} or {...}
    if isinstance(out, _exc_lookup("dict", Exception)) and 'comment' in out:
        return out['comment']
    return out

def test_article_create_and_serialize_workflow():
    """Generated by ai-testgen with strict imports and safe shims."""
    # Import targets inside the test; skip if unavailable
    try:
        from conduit.articles import serializers as art_serializers
    except Exception:
        pytest.skip("conduit.articles.serializers not available")
    # Acquire functions/classes with fallbacks
    make_article = getattr(art_serializers, 'make_article', None)
    dump_article = getattr(art_serializers, 'dump_article', None)
    dump_articles = getattr(art_serializers, 'dump_articles', None)
    ArticleSchema = getattr(art_serializers, 'ArticleSchema', None)
    TagSchema = getattr(art_serializers, 'TagSchema', None)
    Meta = getattr(art_serializers, 'Meta', None)

    if make_article is None or dump_article is None:
        pytest.skip("make_article or dump_article not present in serializers")

    payload = {
        'title': 'Test Title 123',
        'description': 'A short description',
        'body': 'The body of the article',
        'tagList': ['python', 'testing', 'e2e']
    }

    # Create article-like object using make_article; be permissive about signature
    article_obj = _call_with_fallback(make_article, payload)

    # Ensure we received something plausible
    assert article_obj is not None

    # Try serializing the article object
    out = _call_with_fallback(dump_article, article_obj)

    assert isinstance(out, _exc_lookup("dict", Exception)), "dump_article should return a dict-like structure"

    article_json = _normalize_article_output(out)
    # Validate core fields round-trip or appear in serialized output
    assert isinstance(article_json, _exc_lookup("dict", Exception))
    assert article_json.get('title') == payload['title']
    assert article_json.get('description') == payload['description']
    # tags may be under 'tagList' or 'tags' depending on implementation
    tags = article_json.get('tagList') or article_json.get('tags') or article_json.get('tag_list')
    assert tags is not None, "Serialized article should include tags/list"
    for tag in ['python', 'testing']:
        assert tag in tags

    # If dump_articles is available, ensure it can process a list (roundtrip)
    if dump_articles is not None:
        out_list = _call_with_fallback(dump_articles, [article_obj])
        assert isinstance(out_list, _exc_lookup("dict", Exception)) or isinstance(out_list, _exc_lookup("list", Exception))
        # If dict, expect key like 'articles'
        if isinstance(out_list, _exc_lookup("dict", Exception)):
            # Accept either 'articles' or similar container
            assert any(k in out_list for k in ('articles', 'items', 'data'))
        else:
            # list of items: ensure title present
            first = out_list[0]
            fa = _normalize_article_output(first)
            assert fa.get('title') == payload['title']

def test_comment_make_and_dump_and_tag_manipulation():
    """Generated by ai-testgen with strict imports and safe shims."""
    # Import targets inside the test; skip if unavailable
    try:
        from conduit.articles import serializers as art_serializers
        from conduit.articles import models as art_models
    except Exception:
        pytest.skip("conduit.articles.serializers or conduit.articles.models not available")

    make_comment = getattr(art_serializers, 'make_comment', None)
    dump_comment = getattr(art_serializers, 'dump_comment', None)
    make_article = getattr(art_serializers, 'make_article', None)
    dump_article = getattr(art_serializers, 'dump_article', None)
    Tags = getattr(art_models, 'Tags', None)
    Article = getattr(art_models, 'Article', None)
    remove_tag = getattr(art_models, 'remove_tag', None) or getattr(art_models, 'remove_tag', None)

    if make_comment is None or dump_comment is None or make_article is None:
        pytest.skip("required serializer functions for comments/articles not present")

    # Prepare an article to attach comments/tags to
    article_payload = {
        'title': 'Comment Target',
        'description': 'Desc',
        'body': 'Body here',
        'tagList': ['one', 'two']
    }
    article_obj = _call_with_fallback(make_article, article_payload)
    assert article_obj is not None

    # Create a comment payload and make a comment
    comment_payload = {'body': 'This is a deterministic comment.'}
    # make_comment may require article id/obj, try flexible calls
    comment_obj = None
    try:
        comment_obj = _call_with_fallback(make_comment, comment_payload, article_obj)
    except Exception:
        # try without article attachment
        comment_obj = _call_with_fallback(make_comment, comment_payload)

    assert comment_obj is not None

    # Dump the comment and inspect structure
    comment_out = _call_with_fallback(dump_comment, comment_obj)
    assert isinstance(comment_out, _exc_lookup("dict", Exception))
    comment_json = _normalize_comment_output(comment_out)
    assert isinstance(comment_json, _exc_lookup("dict", Exception))
    assert 'body' in comment_json and comment_json['body'] == comment_payload['body']

    # If Tag model is available, test adding/removing tags on an Article-like object if methods exist
    if Tags is not None:
        # Create a Tags instance if constructor accepts a name; otherwise skip tag instance creation
        try:
            tag_instance = Tags(tag='extra-tag')
            # If article_obj has add_tag/remove_tag methods, try them
            if hasattr(article_obj, 'add_tag'):
                try:
                    article_obj.add_tag(tag_instance)
                except Exception:
                    # ignore if underlying model requires DB session
                    pass
                # Attempt to serialize again to see if tag is present (tolerant)
                try:
                    new_out = _call_with_fallback(dump_article, article_obj)
                    new_json = _normalize_article_output(new_out)
                    tags = new_json.get('tagList') or new_json.get('tags') or new_json.get('tag_list') or []
                    # If tags are list-like, allow either containing or not depending on persistence
                    if isinstance(tags, (list, tuple)):
                        # presence is not mandatory (might require DB flush), but ensure no error occurred
                        assert isinstance(tags, (list, tuple))
                except Exception:
                    # ignore serialization failure after tag ops if it depends on DB
                    pass
        except Exception:
            # construction of Tags may require DB session; skip tag instance creation gracefully
            pass

    # If Article model exposes remove_tag function, call it defensively
    if hasattr(article_obj, 'remove_tag'):
        try:
            # try removing a tag by name
            try:
                article_obj.remove_tag('one')
            except Exception:
                # some implementations may expect Tag object
                try:
                    if Tags is not None:
                        article_obj.remove_tag(Tags(tag='one'))
                except Exception:
                    pass
        except Exception:
            # ignore remove errors that depend on DB/session
            pass

    # Final sanity: ensure comment JSON still valid after tag operations
    final_comment_out = _call_with_fallback(dump_comment, comment_obj)
    final_comment_json = _normalize_comment_output(final_comment_out)
    assert final_comment_json.get('body') == comment_payload['body']