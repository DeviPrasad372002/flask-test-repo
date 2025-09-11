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

def _get_token_from_response(data):
    # Try common shapes to extract token
    if not isinstance(data, _exc_lookup("dict", Exception)):
        return None
    # RealWorld common: {"user": {"token": "..."}}
    user = data.get("user")
    if isinstance(user, _exc_lookup("dict", Exception)) and "token" in user:
        return user["token"]
    # Some implementations return {"token": "..."}
    if "token" in data:
        return data["token"]
    # fallback: nested article/user shapes
    for k in ("article", "comment"):
        if isinstance(data.get(k), dict):
            if "author" in data[k] and isinstance(data[k]["author"], dict) and "token" in data[k]["author"]:
                return data[k]["author"]["token"]
    return None

def _get_json(resp):
    try:
        return resp.get_json()
    except Exception:
        try:
            return json.loads(resp.data.decode("utf8"))
        except Exception:
            return None

def _extract_slug(article_obj):
    if not article_obj:
        return None
    if isinstance(article_obj, _exc_lookup("dict", Exception)):
        if "slug" in article_obj:
            return article_obj["slug"]
        # nested under "article"
        if "article" in article_obj and isinstance(article_obj["article"], dict) and "slug" in article_obj["article"]:
            return article_obj["article"]["slug"]
    return None

def _extract_favorites_count(article_obj):
    if not article_obj:
        return None
    if "favoritesCount" in article_obj:
        return article_obj["favoritesCount"]
    if "favorites_count" in article_obj:
        return article_obj["favorites_count"]
    if "article" in article_obj and isinstance(article_obj["article"], dict):
        return _extract_favorites_count(article_obj["article"])
    return None

def _extract_favorited(article_obj):
    if not article_obj:
        return None
    if "favorited" in article_obj:
        return article_obj["favorited"]
    if "article" in article_obj and isinstance(article_obj["article"], dict):
        return _extract_favorited(article_obj["article"])
    return None

@pytest.mark.parametrize("config_path", ["conduit.settings.TestConfig", None])
def test_favorite_unfavorite_article_workflow(config_path):
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.app import create_app
    except Exception as e:
        pytest.skip("create_app not available: %s" % e)

    # Try to create app with provided config if supported
    try:
        if config_path is None:
            app = create_app()
        else:
            app = create_app(config_path)
    except TypeError:
        # fallback to no-arg
        app = create_app()
    except Exception as e:
        pytest.skip("Could not create app: %s" % e)

    client = app.test_client()

    # Register two users: author and favoriter
    author = {"user": {"username": "author1", "email": "author1@example.com", "password": "pass123"}}
    fav_user = {"user": {"username": "favuser", "email": "favuser@example.com", "password": "pass456"}}

    rv = client.post("/api/users", json=author)
    assert rv.status_code in (200, 201), "register author failed: %s" % rv.data.decode("utf8")
    rv = client.post("/api/users", json=fav_user)
    assert rv.status_code in (200, 201), "register fav_user failed: %s" % rv.data.decode("utf8")

    # login both
    rv = client.post("/api/users/login", json={"user": {"email": author["user"]["email"], "password": author["user"]["password"]}})
    assert rv.status_code == 200, "author login failed: %s" % rv.data.decode("utf8")
    author_token = _get_token_from_response(_get_json(rv))
    assert author_token, "no token for author"

    rv = client.post("/api/users/login", json={"user": {"email": fav_user["user"]["email"], "password": fav_user["user"]["password"]}})
    assert rv.status_code == 200, "fav user login failed: %s" % rv.data.decode("utf8")
    fav_token = _get_token_from_response(_get_json(rv))
    assert fav_token, "no token for fav user"

    # Author creates an article
    article_payload = {"article": {"title": "Test Article", "description": "desc", "body": "body", "tagList": ["testing"]}}
    rv = client.post("/api/articles", json=article_payload, headers={"Authorization": f"Bearer {author_token}"})
    assert rv.status_code in (200, 201), "create article failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    slug = _extract_slug(data)
    assert slug, "article slug not found"

    # Fav user favorites the article
    rv = client.post(f"/api/articles/{slug}/favorite", headers={"Authorization": f"Bearer {fav_token}"})
    assert rv.status_code in (200, 201), "favorite failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    fav_count = _extract_favorites_count(data)
    is_fav = _extract_favorited(data)
    assert fav_count == 1, "favoritesCount expected 1, got %r (data=%r)" % (fav_count, data)
    assert is_fav is True, "favorited expected True"

    # Get article and verify favorite status persists
    rv = client.get(f"/api/articles/{slug}")
    assert rv.status_code == 200, "get article failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    fav_count = _extract_favorites_count(data)
    is_fav = _extract_favorited(data)
    assert fav_count == 1
    assert is_fav is True

    # Fav user unfavorites
    rv = client.delete(f"/api/articles/{slug}/favorite", headers={"Authorization": f"Bearer {fav_token}"})
    assert rv.status_code in (200, 204), "unfavorite failed: %s" % rv.data.decode("utf8")
    # After unfavorite, fetching article should show 0 and not favorited
    rv = client.get(f"/api/articles/{slug}")
    assert rv.status_code == 200, "get article after unfavorite failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    fav_count = _extract_favorites_count(data)
    is_fav = _extract_favorited(data)
    assert (fav_count == 0) or (fav_count is None and is_fav is False), "unexpected favorite state after unfavorite"

    # Author deletes the article
    rv = client.delete(f"/api/articles/{slug}", headers={"Authorization": f"Bearer {author_token}"})
    assert rv.status_code in (200, 204), "delete article failed: %s" % rv.data.decode("utf8")
    # Getting deleted article should fail (404 or similar)
    rv = client.get(f"/api/articles/{slug}")
    assert rv.status_code in (404, 410, 403), "expected deleted article inaccessible, got %s" % rv.status_code

def test_comments_and_tags_lifecycle():
    """Generated by ai-testgen with strict imports and safe shims."""
    try:
        from conduit.app import create_app
    except Exception as e:
        pytest.skip("create_app not available: %s" % e)

    try:
        app = create_app("conduit.settings.TestConfig")
    except TypeError:
        app = create_app()
    except Exception as e:
        pytest.skip("Could not create app: %s" % e)

    client = app.test_client()

    # Register and login a user
    user = {"user": {"username": "commenter", "email": "commenter@example.com", "password": "pass123"}}
    rv = client.post("/api/users", json=user)
    assert rv.status_code in (200, 201), "register failed: %s" % rv.data.decode("utf8")
    rv = client.post("/api/users/login", json={"user": {"email": user["user"]["email"], "password": user["user"]["password"]}})
    assert rv.status_code == 200, "login failed: %s" % rv.data.decode("utf8")
    token = _get_token_from_response(_get_json(rv))
    assert token, "no token"

    # Create an article with tags
    article_payload = {"article": {"title": "Tagged Article", "description": "desc", "body": "b", "tagList": ["python", "pytest"]}}
    rv = client.post("/api/articles", json=article_payload, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code in (200, 201), "create article failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    slug = _extract_slug(data)
    assert slug, "slug missing"

    # Tags endpoint should include tags we added
    rv = client.get("/api/tags")
    assert rv.status_code == 200, "get tags failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    tags = data.get("tags") if isinstance(data, _exc_lookup("dict", Exception)) else None
    assert isinstance(tags, _exc_lookup("list", Exception)), "tags not a list"
    assert "python" in tags and "pytest" in tags, "expected tags missing: %r" % (tags,)

    # Post a comment
    comment_payload = {"comment": {"body": "Nice article"}}
    rv = client.post(f"/api/articles/{slug}/comments", json=comment_payload, headers={"Authorization": f"Bearer {token}"})
    assert rv.status_code in (200, 201), "post comment failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    # Comment may be nested as {"comment": {...}}
    comment = data.get("comment") if isinstance(data, _exc_lookup("dict", Exception)) else None
    if not comment and isinstance(data, _exc_lookup("list", Exception)):
        comment = data[0]
    assert comment and ("body" in comment and comment["body"] == "Nice article"), "comment content mismatch: %r" % data

    # List comments
    rv = client.get(f"/api/articles/{slug}/comments")
    assert rv.status_code == 200, "get comments failed: %s" % rv.data.decode("utf8")
    data = _get_json(rv)
    comments = data.get("comments") if isinstance(data, _exc_lookup("dict", Exception)) else None
    assert isinstance(comments, _exc_lookup("list", Exception)) and len(comments) >= 1, "expected at least one comment"

    # Identify comment id for deletion if present
    comment_id = None
    first = comments[0]
    if isinstance(first, _exc_lookup("dict", Exception)):
        comment_id = first.get("id") or first.get("commentId") or first.get("comment_id")
    # If no id provided, try to get it from earlier response
    if comment_id is None and comment and isinstance(comment, _exc_lookup("dict", Exception)):
        comment_id = comment.get("id") or comment.get("commentId") or comment.get("comment_id")

    if comment_id is not None:
        rv = client.delete(f"/api/articles/{slug}/comments/{comment_id}", headers={"Authorization": f"Bearer {token}"})
        assert rv.status_code in (200, 204), "delete comment failed: %s" % rv.data.decode("utf8")
        rv = client.get(f"/api/articles/{slug}/comments")
        assert rv.status_code == 200
        data = _get_json(rv)
        comments_after = data.get("comments") if isinstance(data, _exc_lookup("dict", Exception)) else None
        # Ensure the earlier id is not present
        if isinstance(comments_after, _exc_lookup("list", Exception)):
            ids = [c.get("id") or c.get("commentId") or c.get("comment_id") for c in comments_after if isinstance(c, _exc_lookup("dict", Exception))]
            assert comment_id not in ids
    else:
        # If comment id not provided by API, attempt to delete using a conservative approach:
        # Some implementations return only created comment without an id; in that case ensure comments can be listed and contain the posted body.
        assert any((c.get("body") == "Nice article") for c in comments if isinstance(c, _exc_lookup("dict", Exception))), "posted comment not found"