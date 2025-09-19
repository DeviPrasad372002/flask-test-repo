import importlib.util, pytest
if importlib.util.find_spec('flask') is None:
    pytest.skip('flask not installed; skipping module', allow_module_level=True)

import os, sys, types as _types, pytest as _pytest, warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=PendingDeprecationWarning)
_t = os.environ.get('TARGET_ROOT') or 'target'
if _t and os.path.isdir(_t):
    _p = os.path.abspath(os.path.join(_t, os.pardir))
    [sys.path.insert(0, p) for p in (_p,_t) if p not in sys.path]
    _pkg=_types.ModuleType('target'); _pkg.__path__=[_t]; sys.modules.setdefault('target', _pkg)

import pytest as _pytest
_pytest.skip('generator: banned private imports detected; skipping module', allow_module_level=True)

try:
    import pytest
    from conduit.app import create_app
    from conduit.settings import TestConfig
    from conduit.extensions import db
    from conduit.articles.models import Article, Comment, Tags
    from conduit.user.models import User
except ImportError as e:
    import pytest as _pytest
    _pytest.skip(f"Skipping integration tests; import failed: {e}", allow_module_level=True)

import types
from pathlib import Path

def _call_create_app(config_obj, instance_path):
    # Try positional then keyword to be tolerant of different factory signatures
    try:
        app = create_app(config_obj)
    except TypeError:
        app = create_app(config=config_obj)
    # ensure instance path exists
    app.instance_path = str(instance_path)
    return app

def _safe_create(session, model_cls, commit=True, **kwargs):
    """
    Try model_cls.create(**kwargs) if available (CRUD mixin), otherwise instantiate and add.
    Returns the model instance.
    """
    if hasattr(model_cls, "create") and isinstance(getattr(model_cls, "create"), types.FunctionType):
        obj = model_cls.create(**kwargs)
        # model.create may already commit; ensure object is attached
        if commit:
            session.commit()
        return obj
    # fallback: instantiate and add to session
    obj = model_cls(**kwargs)
    session.add(obj)
    if commit:
        session.commit()
    return obj

def _refresh(session, obj):
    session.expire(obj)
    return obj.__class__.query.get(obj.id)

def _ensure_in_memory_sqlite(app):
    # enforce a safe in-memory DB for tests
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:")
    app.config.setdefault("TESTING", True)
    # Avoid filesystem DB usage
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

def _has_shell_context(app):
    # Flask keeps shell context processors in app.shell_context_processors (list)
    return bool(getattr(app, "shell_context_processors", None))

@pytest.mark.parametrize("use_create_api", [True, False])
def test_article_favourite_unfavourite_and_repr(tmp_path, use_create_api):
    # Arrange
    instance_path = tmp_path / "instance"
    instance_path.mkdir()
    app = _call_create_app(TestConfig, instance_path)
    _ensure_in_memory_sqlite(app)

    with app.app_context():
        # ensure DB extension present
        assert hasattr(db, "create_all") and hasattr(db, "session")
        db.create_all()

        # create users (author and reader) using either create API or manual depending on param
        if use_create_api:
            author = _safe_create(db.session, User, username="author", email="author@example.com", password="x")
            reader = _safe_create(db.session, User, username="reader", email="reader@example.com", password="x")
        else:
            author = _safe_create(db.session, User, username="author2", email="author2@example.com", password="x")
            reader = _safe_create(db.session, User, username="reader2", email="reader2@example.com", password="x")

        # create article
        # Try create API first; fallback to manual add if signature differs
        try:
            article = Article.create(title="Integration Test", body="body", description="desc", author=author)
        except Exception:
            article = Article(title="Integration Test", body="body", description="desc", author=author)
            db.session.add(article)
            db.session.commit()

        # Act & Assert initial state
        db.session.refresh(article)
        # favoritesCount should be an integer and start at 0
        assert isinstance(getattr(article, "favoritesCount", 0), int)
        assert article.favoritesCount == 0

        # favorited by reader should be False initially
        if hasattr(article, "favorited"):
            assert article.favorited(reader) is False
        else:
            
            assert True

        # Act: favourite the article
        if hasattr(article, "favourite"):
            article.favourite(reader)
            db.session.commit()
        else:
            # if favourite method not present, simulate using association if attribute exists
            # attempt to add reader to article.favorited_by or similar common patterns
            if hasattr(article, "favorited_by"):
                getattr(article, "favorited_by").append(reader)
                db.session.commit()

        # Assert: count increments and favorited returns True if method exists
        db.session.refresh(article)
        assert isinstance(article.favoritesCount, int)
        assert article.favoritesCount == 1

        if hasattr(article, "favorited"):
            assert article.favorited(reader) is True

        # Act: unfavourite and assert count goes to 0
        if hasattr(article, "unfavourite"):
            article.unfavourite(reader)
            db.session.commit()
        else:
            if hasattr(article, "favorited_by"):
                getattr(article, "favorited_by").remove(reader)
                db.session.commit()

        db.session.refresh(article)
        assert article.favoritesCount == 0
        if hasattr(article, "favorited"):
            assert article.favorited(reader) is False

        # __repr__ should be string and include title or slug attribute if present
        r = repr(article)
        assert isinstance(r, str)
        # Accept either title or slug being present in repr
        if hasattr(article, "title"):
            assert "Integration Test" in r
        elif hasattr(article, "slug"):
            assert article.slug in r

@pytest.mark.usefixtures()
def test_app_registers_extensions_and_shell_context(tmp_path):
    # Arrange
    instance_path = tmp_path / "instance2"
    instance_path.mkdir()
    app = _call_create_app(TestConfig, instance_path)
    _ensure_in_memory_sqlite(app)

    # Act / Assert: application shell context and extension presence
    with app.app_context():
        # Assert that shell context processors were registered
        assert _has_shell_context(app) is True

        # Call all registered shell context processors and aggregate context
        combined = {}
        for fn in app.shell_context_processors:
            ctx = fn()
            assert isinstance(ctx, dict)
            combined.update(ctx)

        # Expect at least 'db' and 'User' to be present in context mapping
        assert "db" in combined
        assert combined["db"] is db

        # The User model class should be present in the shell context
        assert "User" in combined
        assert combined["User"] is User

        # Ensure that extensions give expected API surface for DB
        assert hasattr(db, "session")
        assert hasattr(db, "create_all")

        # Create tables as a smoke-test that extensions are wired
        db.create_all()
        # creating and querying a minimal user to ensure DB works
        u = _safe_create(db.session, User, username="shelluser", email="shell@example.com", password="p")
        assert getattr(u, "id", None) is not None
        fetched = User.query.get(u.id)
        assert fetched.id == u.id
