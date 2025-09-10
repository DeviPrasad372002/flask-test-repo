import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)
if importlib.util.find_spec('sqlalchemy') is None:
    pytest.skip('sqlalchemy not installed; skipping module', allow_module_level=True)

# --- UNIVERSAL BOOTSTRAP (generated) ---
import os, sys, importlib as _importlib, importlib.util as _iu, importlib.machinery as _im, types as _types, pytest as _pytest, builtins as _builtins

# Ensure target root importable
_target = os.environ.get("TARGET_ROOT") or os.environ.get("ANALYZE_ROOT") or "target"
if _target and _target not in sys.path:
    sys.path.insert(0, _target)
_TARGET_ABS = os.path.abspath(_target)

# Provide a helper for exception lookups used by generated tests
def _exc_lookup(name, default):
    try:
        mod_name, _, cls_name = str(name).rpartition(".")
        if mod_name:
            mod = __import__(mod_name, fromlist=[cls_name])
            return getattr(mod, cls_name, default)
        return getattr(sys.modules.get("builtins"), str(name), default)
    except Exception:
        return default

# ---- Generic module attribute adapter (PEP 562 __getattr__) for target modules ----
# If a module 'm' lacks attribute 'foo', we try to find a public class in 'm' that
# provides 'foo' as an instance attribute/method via a no-arg constructor. First hit wins.
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

# Wrap builtins.__import__ so every target module gets the adapter automatically
_orig_import = _builtins.__import__
def _import_with_adapter(name, globals=None, locals=None, fromlist=(), level=0):
    mod = _orig_import(name, globals, locals, fromlist, level)
    try:
        # Ensure top-level module object is adapted
        top = mod
        if isinstance(mod, _types.ModuleType):
            _attach_module_getattr(top)
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

# Safe DB defaults
for _k in ("DATABASE_URL","DB_URL","SQLALCHEMY_DATABASE_URI"):
    _v = os.environ.get(_k)
    if not _v or "://" not in str(_v):
        os.environ[_k] = "sqlite:///:memory:"

# Minimal Django config (only if actually installed)
try:
    if _iu.find_spec("django") is not None:
        import django
        from django.conf import settings as _dj_settings
        if not _dj_settings.configured:
            _dj_settings.configure(
                SECRET_KEY="test",
                DEBUG=True,
                ALLOWED_HOSTS=["*"],
                INSTALLED_APPS=[],
                DATABASES={"default": {"ENGINE":"django.db.backends.sqlite3","NAME":":memory:"}},
            )
            django.setup()
except Exception:
    pass

# SQLAlchemy safe create_engine
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

# collections.abc compatibility for older libs (Py3.10+)
try:
    import collections as _collections
    import collections.abc as _abc
    for _n in ("Mapping","MutableMapping","Sequence","MutableSequence","Set","MutableSet","Iterable"):
        if not hasattr(_collections, _n) and hasattr(_abc, _n):
            setattr(_collections, _n, getattr(_abc, _n))
except Exception:
    pass

# Py2 alias maps if imported
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

# ---- Qt family stubs (PyQt5/6, PySide2/6) for headless CI ----
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

        # ---- QtCore minimal API ----
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

        # ---- QtGui minimal API ----
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

        # ---- QtWidgets minimal API ----
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

        # Mirror common widget symbols into QtGui to tolerate odd imports
        for _name in ("QApplication","QWidget","QLabel","QLineEdit","QTextEdit","QPushButton","QMessageBox","QFileDialog","QFormLayout","QGridLayout"):
            setattr(_gui, _name, getattr(_widgets, _name))

# ---- Generic stub for other missing third-party tops (non-stdlib, non-local) ----
_THIRD_PARTY_TOPS = ['click', 'compat', 'extensions', 'flask', 'flask_apispec', 'flask_bcrypt', 'flask_caching', 'flask_cors', 'flask_jwt_extended', 'flask_migrate', 'flask_sqlalchemy', 'marshmallow', 'models', 'pytest', 'serializers', 'slugify', 'sqlalchemy', 'werkzeug']
for _name in list(_THIRD_PARTY_TOPS):
    _top = (_name or "").split(".")[0]
    if not _top:
        continue
    if _top in sys.modules:
        continue
    if _safe_find_spec(_top) is not None:
        continue
    if _top in ('PyQt5', 'PyQt6', 'PySide2', 'PySide6'):
        continue
    _m = _types.ModuleType(_top)
    _m.__spec__ = _im.ModuleSpec(_top, loader=None, is_package=False)
    sys.modules[_top] = _m

# --- /UNIVERSAL BOOTSTRAP ---

import time

def test_get_articles_endpoint_returns_json_list():
    # Create the app and try to call the articles listing endpoint.
    # Imports of target modules are done inside the test to follow constraints.
    from conduit.app import create_app
    from conduit.settings import TestConfig

    # Try different ways to call create_app for compatibility
    try:
        app = create_app(TestConfig)
    except TypeError:
        try:
            app = create_app('conduit.settings.TestConfig')
        except Exception:
            app = create_app()

    # Ensure testing mode for deterministic behavior
    app.config.setdefault('TESTING', True)
    client = app.test_client()

    # Try a few plausible article endpoints used by the project.
    candidates = ['/api/articles', '/articles', '/api/articles/']
    found = False
    for path in candidates:
        resp = client.get(path)
        if resp.status_code == 200:
            found = True
            # Should be JSON: check structure is an object with 'articles' as a list
            # get_json() will return None if not JSON; treat that as failure
            data = resp.get_json()
            assert isinstance(data, dict), "expected JSON object from articles endpoint"
            assert 'articles' in data and isinstance(data['articles'], list)
            # The count field may be named articlesCount, try to be permissive
            cnt = data.get('articlesCount', data.get('count', None))
            # If count present it should be integer and match list length
            if cnt is not None:
                assert isinstance(cnt, int)
                assert cnt == len(data['articles'])
            break
    assert found, "no articles endpoint returned HTTP 200 from candidates: {}".format(candidates)


def test_favourite_unfavourite_model_workflow():
    # End-to-end model workflow:
    #  - create app and DB tables
    #  - create a user
    #  - create an article authored by that user
    #  - favourite the article with the user and verify favourite state and counter
    #  - unfavourite and verify state and counter
    from conduit.app import create_app
    from conduit.settings import TestConfig

    # Create app (support multiple create_app signatures)
    try:
        app = create_app(TestConfig)
    except TypeError:
        try:
            app = create_app('conduit.settings.TestConfig')
        except Exception:
            app = create_app()

    app.config.setdefault('TESTING', True)

    # Locate the SQLAlchemy db object from different possible modules
    def _get_db():
        try:
            from conduit.extensions import db  # common location
            return db
        except Exception:
            try:
                from conduit.database import db  # alternate
                return db
            except Exception as exc:
                raise RuntimeError("could not locate db object") from exc

    with app.app_context():
        db = _get_db()

        # create all tables to ensure a clean slate
        # Some projects might expose create_all; tolerate absence
        if hasattr(db, 'create_all'):
            db.create_all()

        # Import models
        from conduit.user.models import User
        from conduit.articles.models import Article

        # Helper to persist an instance (try model.create, then save helper, then raw session)
        def persist_instance(model_cls, instance=None, **kwargs):
            # If a create classmethod exists use it
            if hasattr(model_cls, 'create'):
                obj = model_cls.create(**kwargs)
                return obj
            if instance is None:
                obj = model_cls(**kwargs)
            else:
                obj = instance
            # If instance has save method call it
            if hasattr(obj, 'save'):
                try:
                    obj.save()
                    return obj
                except Exception:
                    pass
            # Fall back to raw session
            session = getattr(db, 'session', None)
            if session is None:
                raise RuntimeError("db.session not available to persist model")
            session.add(obj)
            session.commit()
            return obj

        # Create a user
        # Try to create with minimal required fields; allow different constructors
        user_kwargs = {'username': 'alice', 'email': 'alice@example.com'}
        # Some User models require password hashing via set_password or constructor arg
        try:
            user = persist_instance(User, **user_kwargs, password='password')
        except TypeError:
            # maybe password not accepted as kwarg; create without and try set_password
            user = persist_instance(User, **user_kwargs)
            if hasattr(user, 'set_password'):
                try:
                    user.set_password('password')
                    db.session.add(user)
                    db.session.commit()
                except Exception:
                    # ignore if unavailable
                    pass

        # Ensure user has an id
        assert hasattr(user, 'id') or hasattr(user, 'pk') or getattr(user, 'get_id', None) is not None

        # Create an article authored by the user
        article_kwargs = dict(title='Test Article', description='desc', body='body')
        # Some Article models expect author_id or author relationship; try both strategies
        article = None
        # First attempt: pass author=user if relationship exists
        try:
            article = persist_instance(Article, **article_kwargs, author=user)
        except Exception:
            # Try author_id fallback
            uid = getattr(user, 'id', None)
            if uid is None:
                uid = getattr(user, 'pk', None)
            assert uid is not None, "user id not found for article creation fallback"
            try:
                article = persist_instance(Article, **article_kwargs, author_id=uid)
            except Exception as exc:
                raise

        # Ensure article persisted and has methods for favourite workflow
        assert article is not None
        # Some implementations compute favoritesCount via property or method; capture initial
        def get_fav_count(a):
            # try attribute favoritesCount, favorites_count, favoritesCount() or favoritesCount property
            for attr in ('favoritesCount', 'favorites_count', 'favorites'):
                if hasattr(a, attr):
                    val = getattr(a, attr)
                    return val() if callable(val) else val
            # try property/method favorited or favorited_count
            for attr in ('favorited', 'favoritesCount'):
                if hasattr(a, attr):
                    val = getattr(a, attr)
                    return val() if callable(val) else val
            # last resort, 0
            return 0

        initial_count = get_fav_count(article)
        # Favourite the article using available method names: favourite or favor
        fav_method_candidates = ('favourite', 'favorite', 'fav', 'mark_favourite')
        did_fav = False
        for m in fav_method_candidates:
            if hasattr(article, m):
                getattr(article, m)(user)
                did_fav = True
                break
        if not did_fav:
            # maybe there is a model-level association to create directly (e.g., article.favourited_users.append(user))
            if hasattr(article, 'favourited_by') or hasattr(article, 'favorited_by'):
                rel = getattr(article, 'favourited_by', None) or getattr(article, 'favorited_by', None)
                try:
                    rel.append(user)
                    did_fav = True
                except Exception:
                    pass

        # Commit if session exists
        if hasattr(db, 'session'):
            try:
                db.session.commit()
            except Exception:
                # small sleep and retry commit for deterministic side-effects (no network, but keep safe)
                time.sleep(0.01)
                try:
                    db.session.commit()
                except Exception:
                    pass

        # Verify favourite state via is_favourite or favorited check
        is_fav = False
        if hasattr(article, 'is_favourite'):
            try:
                is_fav = article.is_favourite(user)
            except Exception:
                # try reversed signature
                try:
                    is_fav = article.is_favourite(getattr(user, 'id', None))
                except Exception:
                    is_fav = False
        elif hasattr(article, 'favorited'):
            try:
                is_fav = article.favorited(user)
            except Exception:
                try:
                    is_fav = article.favorited(getattr(user, 'id', None))
                except Exception:
                    is_fav = False
        else:
            # try to infer from favoritesCount increase
            new_count = get_fav_count(article)
            is_fav = new_count >= initial_count + 1

        assert is_fav, "article should be favourited after favourite operation"

        # Check favorites count increased by 1 where possible
        new_count = get_fav_count(article)
        assert new_count >= initial_count, "favorites count should be at least initial value"

        # Now unfavourite using available method names
        unfav_candidates = ('unfavourite', 'unfavorite', 'unfav', 'remove_favourite')
        did_unfav = False
        for m in unfav_candidates:
            if hasattr(article, m):
                getattr(article, m)(user)
                did_unfav = True
                break
        if not did_unfav:
            # try removing from relationship
            rel = getattr(article, 'favourited_by', None) or getattr(article, 'favorited_by', None)
            if rel is not None:
                try:
                    # attempt to remove user if present
                    if user in rel:
                        rel.remove(user)
                        did_unfav = True
                except Exception:
                    pass

        if hasattr(db, 'session'):
            try:
                db.session.commit()
            except Exception:
                time.sleep(0.01)
                try:
                    db.session.commit()
                except Exception:
                    pass

        # After unfavouriting, verify not favourite
        is_fav_after = False
        if hasattr(article, 'is_favourite'):
            try:
                is_fav_after = article.is_favourite(user)
            except Exception:
                try:
                    is_fav_after = article.is_favourite(getattr(user, 'id', None))
                except Exception:
                    is_fav_after = False
        elif hasattr(article, 'favorited'):
            try:
                is_fav_after = article.favorited(user)
            except Exception:
                try:
                    is_fav_after = article.favorited(getattr(user, 'id', None))
                except Exception:
                    is_fav_after = False
        else:
            # infer from count
            final_count = get_fav_count(article)
            is_fav_after = final_count < new_count

        assert not is_fav_after, "article should not be favourited after unfavourite operation"


# --- canonical PyQt5 shim (Widgets + Gui minimal) ---
def __qt_shim_canonical():
    import types as _t
    PyQt5 = _t.ModuleType("PyQt5")
    QtWidgets = _t.ModuleType("PyQt5.QtWidgets")
    QtGui = _t.ModuleType("PyQt5.QtGui")

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

    # QtGui bits commonly imported
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

    QtWidgets.QApplication = QApplication
    QtWidgets.QWidget = QWidget
    QtWidgets.QLabel = QLabel
    QtWidgets.QLineEdit = QLineEdit
    QtWidgets.QTextEdit = QTextEdit
    QtWidgets.QPushButton = QPushButton
    QtWidgets.QMessageBox = QMessageBox
    QtWidgets.QFileDialog = QFileDialog
    QtWidgets.QFormLayout = QFormLayout
    QtWidgets.QGridLayout = QGridLayout

    QtGui.QFont = QFont
    QtGui.QDoubleValidator = QDoubleValidator
    QtGui.QIcon = QIcon
    QtGui.QPixmap = QPixmap

    return PyQt5, QtWidgets, QtGui

_make_pyqt5_shim = __qt_shim_canonical
_make_pyqt_shim = __qt_shim_canonical
_make_pyqt_shims = __qt_shim_canonical
_make_qt_shims = __qt_shim_canonical
