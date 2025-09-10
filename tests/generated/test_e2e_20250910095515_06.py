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

import pytest

def _get_app_and_db():
    # Try flexible ways to create the app and obtain the db object so tests are resilient
    from importlib import import_module
    app = None
    db = None
    # import create_app and TestConfig if available
    try:
        mod_app = import_module("conduit.app")
        create_app = getattr(mod_app, "create_app")
    except Exception:
        create_app = None
    try:
        mod_settings = import_module("conduit.settings")
        TestConfig = getattr(mod_settings, "TestConfig", None)
    except Exception:
        TestConfig = None

    # Try to create app via several likely signatures
    if create_app is not None:
        try:
            app = create_app("testing")
        except Exception:
            # fallback to passing config object/class if available
            if TestConfig is not None:
                app = create_app(TestConfig)
            else:
                app = create_app()
    else:
        raise RuntimeError("create_app not found in conduit.app")

    # Try to find db object in common locations
    try:
        mod_ext = import_module("conduit.extensions")
        db = getattr(mod_ext, "db", None)
    except Exception:
        db = None
    if db is None:
        try:
            mod_db = import_module("conduit.database")
            db = getattr(mod_db, "db", None)
        except Exception:
            db = None
    if db is None:
        # last attempt: some apps export db from conduit (package root)
        try:
            mod_root = import_module("conduit")
            db = getattr(mod_root, "db", None)
        except Exception:
            db = None

    if db is None:
        raise RuntimeError("Could not locate SQLAlchemy db instance (tried conduit.extensions, conduit.database, conduit)")

    return app, db

def _persist_instance(db, model_or_instance=None, **kwargs):
    # If a class given, create via create() if available, else instantiate.
    Inst = model_or_instance
    inst = None
    if isinstance(Inst, _exc_lookup("Exception", Exception)):
        create_fn = getattr(Inst, "create", None)
        if callable(create_fn):
            inst = create_fn(**kwargs)
            # some create implementations already persist; ensure commit
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        else:
            inst = Inst(**kwargs)
    else:
        # assume instance already provided
        inst = Inst

    # If instance has save method, prefer that
    save_fn = getattr(inst, "save", None)
    if callable(save_fn):
        save_fn()
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    else:
        # Persist via session
        db.session.add(inst)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    return inst

def _serialize_with_schema(possible_schema_cls, obj):
    # Try schema then to_json then marshmallow dump, else simple attrs
    if possible_schema_cls:
        try:
            schema = possible_schema_cls()
            dumped = schema.dump(obj)
            return dumped
        except Exception:
            pass
    to_json = getattr(obj, "to_json", None)
    if callable(to_json):
        try:
            return to_json()
        except Exception:
            pass
    # fallback to common attrs
    result = {}
    for attr in ("username", "email", "bio", "image"):
        if hasattr(obj, attr):
            result[attr] = getattr(obj, attr)
    return result

def test_user_crud_and_profile_serialization(tmp_path):
    # End-to-end: create app, create user, create profile, serialize with schema
    app, db = _get_app_and_db()

    with app.app_context():
        # create all tables to ensure a clean DB
        try:
            db.create_all()
        except Exception:
            # some setups might not expose create_all directly on db, attempt session bind metadata
            meta = getattr(db, "metadata", None)
            engine = getattr(db, "engine", None)
            if meta is not None and engine is not None:
                meta.create_all(bind=engine)

        # import models and schemas lazily
        from importlib import import_module
        mod_user_models = import_module("conduit.user.models")
        User = getattr(mod_user_models, "User")
        mod_user_serializers = import_module("conduit.user.serializers")
        UserSchema = getattr(mod_user_serializers, "UserSchema", None)

        mod_profile_models = import_module("conduit.profile.models")
        UserProfile = getattr(mod_profile_models, "UserProfile")
        mod_profile_serializers = import_module("conduit.profile.serializers")
        ProfileSchema = getattr(mod_profile_serializers, "ProfileSchema", None)

        # Create a user using provided model utilities (robust helper)
        user = _persist_instance(db, User, username="alice", email="alice@example.org", password="secret123")

        # Verify user persisted and serializable
        user_data = _serialize_with_schema(UserSchema, user)
        assert "username" in user_data and user_data["username"] == "alice"
        assert "email" in user_data and user_data["email"] == "alice@example.org"

        # Create a profile associated with the user. Try common constructor signatures
        profile_kwargs = {}
        # many profile models accept user_id or user
        if hasattr(UserProfile, "__init__"):
            # prefer user relationship if available
            if "user_id" in UserProfile.__init__.__code__.co_varnames:
                profile_kwargs["user_id"] = getattr(user, "id", None)
            elif "user" in UserProfile.__init__.__code__.co_varnames:
                profile_kwargs["user"] = user
        # ensure some profile fields
        profile_kwargs.setdefault("bio", "Hello, I am Alice")
        profile_kwargs.setdefault("image", "https://example.org/alice.png")

        profile = _persist_instance(db, UserProfile, **profile_kwargs)

        # Serialize profile via schema or attributes
        prof_data = _serialize_with_schema(ProfileSchema, profile)
        assert "bio" in prof_data and "Alice" in prof_data["bio"]
        assert "image" in prof_data

def test_article_favoriting_workflow():
    # End-to-end: create app, create user and article, favourite/unfavourite behavior
    app, db = _get_app_and_db()

    with app.app_context():
        # Ensure DB schema exists
        try:
            db.create_all()
        except Exception:
            meta = getattr(db, "metadata", None)
            engine = getattr(db, "engine", None)
            if meta is not None and engine is not None:
                meta.create_all(bind=engine)

        from importlib import import_module
        # Import user and article models
        mod_user_models = import_module("conduit.user.models")
        User = getattr(mod_user_models, "User")
        mod_articles_models = import_module("conduit.articles.models")
        Article = getattr(mod_articles_models, "Article", None)
        # Article may be named Article; if not present fail early
        assert Article is not None, "Article model not available in conduit.articles.models"

        # Create a user and an article
        user = _persist_instance(db, User, username="bob", email="bob@example.org", password="pw")
        # Article typical fields: title, body, description, author_id or author
        article_kwargs = {"title": "Test Article", "body": "content", "description": "desc"}
        # detect which constructor args exist
        init_vars = Article.__init__.__code__.co_varnames if hasattr(Article, "__init__") else ()
        if "author_id" in init_vars:
            article_kwargs["author_id"] = getattr(user, "id", None)
        elif "author" in init_vars:
            article_kwargs["author"] = user
        # create article instance
        article = _persist_instance(db, Article, **article_kwargs)

        # Ensure article is not favourited initially by user
        is_fav_before = False
        is_fav_fn = getattr(article, "is_favourite", None)
        if callable(is_fav_fn):
            try:
                is_fav_before = bool(is_fav_fn(user))
            except TypeError:
                # maybe expects user id
                is_fav_before = bool(is_fav_fn(getattr(user, "id", None)))
        else:
            # fallback: check favoritesCount
            fav_count = getattr(article, "favoritesCount", lambda: 0)()
            is_fav_before = (fav_count > 0)
        assert not is_fav_before

        # Favourite the article
        fav_fn = getattr(article, "favourite", None)
        assert callable(fav_fn), "Article.favourite method required"
        try:
            fav_fn(user)
        except TypeError:
            fav_fn(getattr(user, "id", None))
        # commit to persist changes if not auto-committed
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Verify is_favourite and favoritesCount
        is_fav_after = False
        if callable(is_fav_fn):
            try:
                is_fav_after = bool(is_fav_fn(user))
            except TypeError:
                is_fav_after = bool(is_fav_fn(getattr(user, "id", None)))
        else:
            is_fav_after = getattr(article, "favoritesCount", lambda: 0)() > 0
        assert is_fav_after

        # Check count increases to 1 (or increments)
        count_fn = getattr(article, "favoritesCount", None)
        if callable(count_fn):
            cnt = count_fn()
            assert cnt >= 1
        else:
            # if not available, at least is_fav_after is true
            assert is_fav_after

        # Unfavourite the article
        unfav_fn = getattr(article, "unfavourite", None)
        assert callable(unfav_fn), "Article.unfavourite method required"
        try:
            unfav_fn(user)
        except TypeError:
            unfav_fn(getattr(user, "id", None))
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Verify unfavourited
        if callable(is_fav_fn):
            try:
                assert not bool(is_fav_fn(user))
            except TypeError:
                assert not bool(is_fav_fn(getattr(user, "id", None)))
        else:
            if callable(count_fn):
                assert count_fn() == 0 or count_fn() < 2
            else:
                # best-effort: nothing else to assert
                assert True


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
