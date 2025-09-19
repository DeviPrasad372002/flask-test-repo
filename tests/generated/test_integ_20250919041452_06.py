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

import types
import builtins
import pytest

# Guard third-party / project imports
try:
    from conduit import exceptions as exc_mod
    from conduit import extensions as extensions_mod
    from conduit.settings import Config, DevConfig, ProdConfig, TestConfig
    # schema modules
    import marshmallow
    from conduit.user import serializers as user_serializers
    from conduit.profile import serializers as profile_serializers
    from conduit.articles import serializers as articles_serializers
    from conduit import user as user_mod
except ImportError as e:
    pytest.skip(f"Required project modules unavailable: {e}", allow_module_level=True)

from unittest.mock import Mock

# Arrange / Act / Assert style tests

def test_crud_mixin_create_update_save_calls_db_session(monkeypatch):
    # Arrange
    CRUDMixin = extensions_mod.CRUDMixin

    # Create a fake session to observe calls
    fake_session = types.SimpleNamespace(
        add=Mock(name="add"),
        commit=Mock(name="commit"),
        flush=Mock(name="flush"),
    )
    fake_db = types.SimpleNamespace(session=fake_session)

    # Patch the extensions module db reference
    monkeypatch.setattr(extensions_mod, "db", fake_db)

    # Create a lightweight model class that uses CRUDMixin
    class DummyModel(CRUDMixin):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def __repr__(self):
            return f"<DummyModel {getattr(self, 'name', None)}>"

    # Act
    # create should be a classmethod on CRUDMixin; support either naming styles
    if hasattr(DummyModel, "create") and callable(getattr(DummyModel, "create")):
        created = DummyModel.create(name="alice", value=123)
    else:
        # Fallback: instantiate and call save()
        created = DummyModel(name="alice", value=123)
        created.save()

    # Assert create/save invoked DB session add/commit
    assert isinstance(created, DummyModel)
    assert created.name == "alice"
    assert fake_session.add.call_count >= 1, "expected add() to be called at least once"
    assert fake_session.commit.call_count >= 1, "expected commit() to be called at least once"

    # Act: update attributes via instance method if present
    if hasattr(created, "update") and callable(getattr(created, "update")):
        returned = created.update(value=999, extra="x")
        # Assert update returns self-like object when implemented
        assert returned is created or returned == created

        # After update, commit should have been called
        assert fake_session.commit.call_count >= 2

        # The attribute must have been updated
        assert created.value == 999
        assert getattr(created, "extra") == "x"

    # Act: call save explicitly and verify db invoked
    # reset mocks counts to detect additional calls
    fake_session.add.reset_mock()
    fake_session.commit.reset_mock()
    if hasattr(created, "save") and callable(getattr(created, "save")):
        saved = created.save()
        assert saved is created or saved == created
        fake_session.add.assert_called_once_with(created)
        fake_session.commit.assert_called_once()

@pytest.mark.parametrize(
    "cfg_cls, expected_testing_flag, expected_debug_flag",
    [
        (TestConfig, True, False),    # TestConfig usually enables TESTING
        (DevConfig, False, True),     # DevConfig usually enables DEBUG
        (ProdConfig, False, False),   # ProdConfig usually disables DEBUG/TESTING
    ],
)
def test_config_classes_have_expected_flags(cfg_cls, expected_testing_flag, expected_debug_flag):
    # Arrange / Act
    # Ensure subclassing relationship
    assert issubclass(cfg_cls, Config)

    # Access attributes with defaults for robustness
    testing_value = getattr(cfg_cls, "TESTING", False)
    debug_value = getattr(cfg_cls, "DEBUG", False)

    # Assert
    assert testing_value is expected_testing_flag
    assert debug_value is expected_debug_flag

@pytest.mark.parametrize(
    "schema_factory",
    [
        pytest.param(lambda: user_serializers.UserSchema(), id="UserSchema"),
        pytest.param(lambda: profile_serializers.ProfileSchema(), id="ProfileSchema"),
        pytest.param(lambda: articles_serializers.ArticleSchema(), id="ArticleSchema"),
        pytest.param(lambda: articles_serializers.CommentSchema(), id="CommentSchema"),
        pytest.param(lambda: articles_serializers.TagSchema(), id="TagSchema"),
    ],
)
def test_serializers_are_marshmallow_schema(schema_factory):
    # Arrange / Act
    schema_instance = schema_factory()

    # Assert concrete type
    assert isinstance(schema_instance, marshmallow.Schema)
    # And that dump/load methods exist and are callable
    assert callable(getattr(schema_instance, "dump"))
    assert callable(getattr(schema_instance, "load"))

def test_exceptions_helpers_return_or_raise_InvalidUsage():
    
    helpers = [
        getattr(exc_mod, "user_already_registered", None),
        getattr(exc_mod, "user_not_found", None),
        getattr(exc_mod, "unknown_error", None),
        getattr(exc_mod, "article_not_found", None),
        getattr(exc_mod, "comment_not_owned", None),
    ]
    # Filter out None helpers (in case some are not present)
    helpers = [h for h in helpers if h is not None]

    assert len(helpers) >= 1, "no exception helper functions available to test"

    for helper in helpers:
        
        result = None
        try:
            result = helper()
        except exc_mod.InvalidUsage as raised_exc:
            result = raised_exc

        # Assert: result is an InvalidUsage instance and exposes a status_code int
        assert isinstance(result, exc_mod.InvalidUsage)
        assert hasattr(result, "status_code"), "InvalidUsage must have status_code attribute"
        assert isinstance(result.status_code, int)

        # The InvalidUsage should be an Exception subclass as well
        assert isinstance(result, Exception)
        # str(result) should be non-empty
        assert len(str(result)) >= 1

def test_user_schema_roundtrip_minimal(monkeypatch):
    # Arrange: create a minimal user-like payload
    payload = {"username": "tester", "email": "tester@example.com", "password": "s3cret"}

    # Instantiate schema
    schema = user_serializers.UserSchema()

    # Monkeypatch any external calls e.g., password hashing if schema invokes them
    # Many schemas call a password hashing function. If present, replace it with identity.
    monkeypatch.setattr(user_mod, "bcrypt", types.SimpleNamespace(generate_password_hash=lambda p: f"hashed-{p}"), raising=False)

    # Act: load the payload (validation may occur) and then dump back
    loaded = schema.load(payload)
    dumped = schema.dump(loaded)

    # Assert: loaded and dumped have key fields and types
    assert isinstance(loaded, dict)
    assert "username" in loaded and loaded["username"] == "tester"
    
    assert "username" in dumped
    assert "email" in dumped or "email" in loaded

def test_user_model_has_expected_interface(monkeypatch):
    # Ensure User model exists and supports creation via CRUDMixin interface without hitting DB
    User = getattr(user_mod, "User", None)
    if User is None:
        pytest.skip("User model not found in conduit.user")

    # Create a fake db session like earlier
    fake_session = types.SimpleNamespace(add=Mock(name="add"), commit=Mock(name="commit"), flush=Mock(name="flush"))
    fake_db = types.SimpleNamespace(session=fake_session)
    # Patch the extensions db if User uses extensions.db or user_mod.db
    monkeypatch.setattr(extensions_mod, "db", fake_db, raising=False)
    monkeypatch.setattr(user_mod, "db", fake_db, raising=False)

    # Attempt to create without touching a real DB
    kwargs = {"username": "int_test_user", "email": "it@example.com", "password": "pw"}
    created = None
    
    if hasattr(User, "create") and callable(getattr(User, "create")):
        created = User.create(**{k: v for k, v in kwargs.items() if k in {"username", "email", "password"}})
    else:
        created = User(**kwargs)
        if hasattr(created, "save"):
            created.save()

    # Assert basic contract
    assert created is not None
    assert hasattr(created, "username")
    assert getattr(created, "username") == "int_test_user"
    # Ensure that a DB add/commit was attempted if save/create pipelines are present
    # It's acceptable if no calls were made (implementation may defer persistence), but if save was used we expect DB calls.
    # If fake_session.add was called verify the object was passed through
    if fake_session.add.call_count:
        # Last call argument should be the user instance
        last_call_args = fake_session.add.call_args[0]
        assert last_call_args and last_call_args[0] is created

    # Ensure repr exists and is string
    r = repr(created)
    assert isinstance(r, str)
    assert len(r) > 0
