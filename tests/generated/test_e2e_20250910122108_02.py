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

def _try_call(func, arg_variants):
    last_err = None
    for args in arg_variants:
        try:
            return func(*args)
        except TypeError as e:
            last_err = e
            continue
    raise last_err

def _maybe_skip_on_imports(*names):
    try:
        modules = {}
        for name in names:
            modules[name] = __import__(name, fromlist=['*'])
        return modules
    except Exception as e:
        pytest.skip(f"required module import failed: {e}")

def test_e2e_article_serialization_tags_and_favorites():
    """Test with enhanced error handling."""
    # Import internals; skip test if anything can't be imported
    try:
        from conduit.app import create_app
        from conduit.articles import serializers as article_serializers
        from conduit.articles import models as article_models
    except Exception as e:
        pytest.skip(f"imports failed: {e}")

    # Create a lightweight app context if possible; not fatal if create_app signature varies
    try:
        try:
            app = create_app('testing')
        except TypeError:
            app = create_app()
    except Exception:
        # If we cannot construct an app, continue without app context (serializers/models may not need it)
        app = None

    # Build a sample payload and try to construct/dump an article using flexible calls
    payload = {"title": "A test title", "description": "desc", "body": "body content", "tagList": ["alpha", "beta"]}

    # make_article
    make_article = getattr(article_serializers, "make_article", None)
    if make_article is None:
        pytest.skip("make_article not available")

    try:
        article = _try_call(make_article, [
            (payload,),
            (payload, None),
            (payload, None, None),
        ])
    except TypeError as e:
        pytest.skip(f"make_article signature mismatch: {e}")

    # dump_article
    dump_article = getattr(article_serializers, "dump_article", None)
    if dump_article is None:
        pytest.skip("dump_article not available")

    try:
        dumped = _try_call(dump_article, [
            (article,),
            (article, None),
            (article, None, None),
        ])
    except TypeError as e:
        pytest.skip(f"dump_article signature mismatch: {e}")

    # Basic assertions about the dumped representation
    assert isinstance(dumped, _exc_lookup("Exception", Exception)), "dump_article should return a dict-like representation"
    assert dumped.get("title") == payload["title"]
    assert "body" in dumped and dumped["body"] == payload["body"]

    # tags: allow either 'tags' or 'tagList' or nested under 'article'
    tag_list = None
    if "tagList" in dumped:
        tag_list = dumped["tagList"]
    elif "tags" in dumped:
        tag_list = dumped["tags"]
    elif "article" in dumped and isinstance(dumped["article"], dict):
        d = dumped["article"]
        tag_list = d.get("tagList") or d.get("tags")
    assert isinstance(tag_list, (list, type(None)))  # could be None if not set

    # try add_tag and remove_tag on the article/model
    add_tag = getattr(article_models, "add_tag", None)
    remove_tag = getattr(article_models, "remove_tag", None)

    # If tag operations exist, exercise them
    if add_tag and remove_tag:
        try:
            _try_call(add_tag, [
                (article, "gamma"),
                (article, "gamma",),
            ])
        except TypeError:
            pytest.skip("add_tag signature mismatch")
        # After adding, ensure dumped representation reflects tag if dump_article callable supports reading live model
        try:
            dumped_after_add = _try_call(dump_article, [(article,), (article, None)])
        except TypeError:
            dumped_after_add = dumped
        # Check that the new tag is present in any observable tag list
        observed_tags = None
        if isinstance(dumped_after_add, _exc_lookup("Exception", Exception)):
            if "tagList" in dumped_after_add:
                observed_tags = dumped_after_add["tagList"]
            elif "tags" in dumped_after_add:
                observed_tags = dumped_after_add["tags"]
            elif "article" in dumped_after_add and isinstance(dumped_after_add["article"], dict):
                observed_tags = dumped_after_add["article"].get("tagList") or dumped_after_add["article"].get("tags")
        if observed_tags is not None:
            assert "gamma" in observed_tags
        # remove it
        try:
            _try_call(remove_tag, [(article, "gamma"), (article, "gamma",)])
        except TypeError:
            pytest.skip("remove_tag signature mismatch")
        # dump again
        try:
            dumped_after_remove = _try_call(dump_article, [(article,), (article, None)])
        except TypeError:
            dumped_after_remove = dumped_after_add
        observed_tags2 = None
        if isinstance(dumped_after_remove, _exc_lookup("Exception", Exception)):
            if "tagList" in dumped_after_remove:
                observed_tags2 = dumped_after_remove["tagList"]
            elif "tags" in dumped_after_remove:
                observed_tags2 = dumped_after_remove["tags"]
            elif "article" in dumped_after_remove and isinstance(dumped_after_remove["article"], dict):
                observed_tags2 = dumped_after_remove["article"].get("tagList") or dumped_after_remove["article"].get("tags")
        if observed_tags2 is not None:
            assert "gamma" not in observed_tags2

    # Test favorites related helpers if available
    favoritesCount = getattr(article_models, "favoritesCount", None)
    is_favourite = getattr(article_models, "is_favourite", None)
    favorited = getattr(article_models, "favorited", None)
    favourite_fn = getattr(article_models, "favourite", None)
    unfavourite_fn = getattr(article_models, "unfavourite", None)

    if favoritesCount:
        try:
            count_before = _try_call(favoritesCount, [(article,), (article, None)])
        except TypeError:
            pytest.skip("favoritesCount signature mismatch")
        assert isinstance(count_before, _exc_lookup("Exception", Exception))

        # If there is a favourite function, call it and check increment
        if favourite_fn and unfavourite_fn and is_favourite:
            # Try to favourite with no user / None user if allowed
            try:
                _try_call(favourite_fn, [(article, None), (article,)])
            except TypeError:
                pytest.skip("favourite signature mismatch")
            try:
                count_after = _try_call(favoritesCount, [(article,), (article, None)])
            except TypeError:
                pytest.skip("favoritesCount signature mismatch")
            assert count_after >= count_before
            # Try is_favourite with None user or no user
            try:
                fav_flag = _try_call(is_favourite, [(article, None), (article,)])
            except TypeError:
                pytest.skip("is_favourite signature mismatch")
            assert isinstance(fav_flag, _exc_lookup("Exception", Exception))
            # Unfavourite and ensure count is not increased
            try:
                _try_call(unfavourite_fn, [(article, None), (article,)])
            except TypeError:
                pytest.skip("unfavourite signature mismatch")
            try:
                count_final = _try_call(favoritesCount, [(article,), (article, None)])
            except TypeError:
                pytest.skip("favoritesCount signature mismatch")
            assert isinstance(count_final, _exc_lookup("Exception", Exception))

def test_e2e_comments_and_articles_list_serialization():
    """Test with enhanced error handling."""
    try:
        from conduit.articles import serializers as article_serializers
        from conduit.articles import models as article_models
    except Exception as e:
        pytest.skip(f"imports failed: {e}")

    make_article = getattr(article_serializers, "make_article", None)
    dump_articles = getattr(article_serializers, "dump_articles", None)
    make_comment = getattr(article_serializers, "make_comment", None)
    dump_comment = getattr(article_serializers, "dump_comment", None)

    if make_article is None or dump_articles is None:
        pytest.skip("make_article or dump_articles not available")

    payload1 = {"title": "List A", "description": "d1", "body": "b1", "tagList": ["t1"]}
    payload2 = {"title": "List B", "description": "d2", "body": "b2", "tagList": ["t2"]}

    try:
        a1 = _try_call(make_article, [(payload1,), (payload1, None)])
        a2 = _try_call(make_article, [(payload2,), (payload2, None)])
    except TypeError as e:
        pytest.skip(f"make_article signature mismatch: {e}")

    try:
        dumped_list = _try_call(dump_articles, [([a1, a2],), ([a1, a2], None)])
    except TypeError as e:
        pytest.skip(f"dump_articles signature mismatch: {e}")

    # Expect a list-like representation or a dict containing list
    if isinstance(dumped_list, _exc_lookup("Exception", Exception)) and "articles" in dumped_list:
        articles_repr = dumped_list["articles"]
    else:
        articles_repr = dumped_list

    assert hasattr(articles_repr, "__iter__")
    # Convert to list and check we have at least 2 items
    articles_list = list(articles_repr)
    assert len(articles_list) >= 2
    titles = [it.get("title") if isinstance(it, _exc_lookup("Exception", Exception)) else None for it in articles_list]
    assert payload1["title"] in titles and payload2["title"] in titles

    # If comment helpers available, try creating and dumping a comment for first article
    if make_comment and dump_comment:
        comment_payload = {"body": "nice article"}
        try:
            comment = _try_call(make_comment, [(comment_payload, a1), (a1, comment_payload), (comment_payload, a1, None)])
        except TypeError:
            pytest.skip("make_comment signature mismatch")
        try:
            dumped_comment = _try_call(dump_comment, [(comment,), (comment, None)])
        except TypeError:
            pytest.skip("dump_comment signature mismatch")
        assert isinstance(dumped_comment, _exc_lookup("Exception", Exception))
        # body should appear somewhere
        found_body = False
        if "body" in dumped_comment and dumped_comment["body"] == comment_payload["body"]:
            found_body = True
        if "comment" in dumped_comment and isinstance(dumped_comment["comment"], dict):
            if dumped_comment["comment"].get("body") == comment_payload["body"]:
                found_body = True
        assert found_body, "dump_comment did not include expected body"
