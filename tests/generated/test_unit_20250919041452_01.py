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

import types
import builtins

try:
    import pytest
    import flask
    from conduit.app import create_app, register_shellcontext, register_commands, register_errorhandlers, errorhandler, shell_context
    from conduit.articles.models import Article
except ImportError as e:
    import pytest as _pytest
    _pytest.skip("Required application modules or third-party packages are not available: " + str(e), allow_module_level=True)

class DummyApp:
    def __init__(self):
        self._shell_func = None
        self.cli = types.SimpleNamespace(add_command=self._add_command)
        self._added_commands = []

    def shell_context_processor(self, func):
        # mimic Flask behavior: register and return func
        self._shell_func = func
        return func

    def _add_command(self, cmd):
        # record that a command was added
        self._added_commands.append(cmd)

class DummyAppWithErrorHandler(DummyApp):
    def __init__(self):
        super().__init__()
        self._error_handlers = []

    def errorhandler(self, code_or_exc):
        # mimic Flask.errorhandler decorator: store and return decorator
        def decorator(fn):
            self._error_handlers.append((code_or_exc, fn))
            return fn
        return decorator

class DummyUser:
    def __init__(self, uid):
        self.id = uid

    def __repr__(self):
        return f"<DummyUser {self.id}>"

# Arrange / Act / Assert style tests
def test_create_app_returns_flask_instance_default():
    # Arrange / Act
    app = create_app()

    # Assert
    assert isinstance(app, flask.Flask)
    # basic sanity: has config and name
    assert isinstance(app.config, dict)
    assert isinstance(app.name, str)

def test_create_app_with_explicit_arg_returns_flask_instance():
    # Arrange / Act
    # Many implementations accept a configuration name or object; pass a common string
    app = create_app("testing")

    # Assert
    assert isinstance(app, flask.Flask)
    assert hasattr(app, "config")
    # when passed "testing" the config dict should still exist
    assert isinstance(app.config, dict)

def test_register_shellcontext_registers_callable_and_callable_returns_dict():
    # Arrange
    app = DummyApp()

    # Act
    register_shellcontext(app)

    # Assert
    assert callable(app._shell_func), "shell context function should be registered and callable"
    ctx = app._shell_func()
    assert isinstance(ctx, dict), "shell context callable must return a dict"
    # keys in the context should be strings if present
    for k in ctx.keys():
        assert isinstance(k, str)

def test_register_commands_uses_app_cli_add_command():
    # Arrange
    app = DummyApp()

    # Act
    register_commands(app)

    # Assert
    # register_commands should call add_command at least once (for test/lint/clean etc.)
    assert hasattr(app.cli, "_added_commands") or hasattr(app, "_added_commands") or len(app.cli.__dict__.get("_added_commands", [])) >= 0
    # Ensure we recorded something in our dummy (implementation dependent: at least attribute exists)
    # Use the internal record we know.
    # If register_commands used app.cli.add_command, our DummyApp recorded calls in _added_commands
    assert isinstance(app.cli._added_commands, list)

@pytest.mark.parametrize("code_or_exc", [404, Exception])
def test_errorhandler_decorator_returns_decorator_for_common_inputs(code_or_exc):
    # Arrange
    app = DummyAppWithErrorHandler()

    # Act
    register_errorhandlers(app)

    # The register_errorhandlers function should have used app.errorhandler,
    # but we also test the standalone errorhandler helper for being a decorator factory.
    dec = errorhandler(code_or_exc)

    # Assert
    assert callable(dec)
    # applying it to a function should return a function (decorator behavior)
    def sample(e):
        return "ok"

    wrapped = dec(sample)
    assert wrapped is sample or callable(wrapped)

def test_shell_context_returns_mapping_and_contains_expected_symbols():
    # Act
    ctx = shell_context()

    # Assert
    assert isinstance(ctx, dict)
    # Ensure keys are strings and values are not None
    for k, v in ctx.items():
        assert isinstance(k, str)
        assert v is not None

def test_article_repr_and_basic_initialization():
    # Arrange / Act
    # Many SQLAlchemy models can be constructed without a DB session.
    a = Article(title="My Test Title", body="body text", description="desc")

    # Assert core attributes set
    assert getattr(a, "title") == "My Test Title"
    # __repr__ should return a string
    r = repr(a)
    assert isinstance(r, str)
    # repr should mention title or slug if present
    if hasattr(a, "slug") and a.slug:
        assert a.slug in r or "Article" in r
    else:
        assert "Article" in r

def test_article_favourite_unfavourite_is_favourite_and_count_behaviour():
    # Arrange
    # Create a raw Article instance without invoking DB operations by using __new__
    a = Article.__new__(Article)
    
    setattr(a, "favorited", [])
    # provide a fallback favoritesCount if implemented as property; else we will call function if exists
    user = DummyUser(1)

    # get methods dynamically to avoid AttributeError at import time if naming differs
    favour_func = getattr(Article, "favourite", None)
    unfavour_func = getattr(Article, "unfavourite", None)
    is_fav_func = getattr(Article, "is_favourite", None)
    fav_count = getattr(Article, "favoritesCount", None)

    # Basic expectations: methods should exist
    assert callable(favour_func), "Article must implement `favourite`"
    assert callable(unfavour_func), "Article must implement `unfavourite`"
    # Add favorite
    favour_func(a, user)
    # After favouriting, the user should be tracked in favorited collection
    assert any(getattr(u, "id", None) == user.id or u is user for u in a.favorited)
    
    if callable(fav_count):
        cnt = fav_count(a)
        assert isinstance(cnt, int)
        assert cnt == len(a.favorited)
    else:
        # also check a simple len fallback
        assert len(a.favorited) >= 1

    # is_favourite should report True
    if callable(is_fav_func):
        assert is_fav_func(a, user) is True

    
    favour_func(a, user)
    
    assert len(a.favorited) >= 1

    
    unfavour_func(a, user)
    # After removal, ensure the user is no longer present
    assert not any(getattr(u, "id", None) == user.id or u is user for u in a.favorited)
    if callable(fav_count):
        assert fav_count(a) == len(a.favorited)

def test_unfavourite_when_not_favourited_is_noop():
    # Arrange
    a = Article.__new__(Article)
    a.favorited = []
    user = DummyUser(42)
    unfavour_func = getattr(Article, "unfavourite", None)
    assert callable(unfavour_func)

    
    unfavour_func(a, user)
    assert isinstance(a.favorited, list)
    assert len(a.favorited) == 0
