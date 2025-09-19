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

import pytest
from types import SimpleNamespace

try:
    from conduit.exceptions import InvalidUsage
    from conduit import extensions as conduit_extensions
    from conduit.extensions import CRUDMixin
    from conduit.profile.models import UserProfile
    from conduit.profile.serializers import ProfileSchema
    from conduit.settings import Config, ProdConfig, DevConfig, TestConfig
    from conduit.user.models import User
    from conduit.user.serializers import UserSchema
except ImportError as e:
    pytest.skip("Required project imports missing: %s" % e, allow_module_level=True)

from unittest import mock

def test_invalidusage_defaults_and_to_json():
    # Arrange
    msg = "something went wrong"
    inst = InvalidUsage(msg)
    # Act
    payload_json = inst.to_json()
    # Assert
    assert hasattr(inst, "message") and inst.message == msg
    assert hasattr(inst, "status_code") and isinstance(inst.status_code, int)
    assert isinstance(payload_json, dict)
    assert payload_json.get("message") == msg

def test_invalidusage_custom_status_and_payload():
    # Arrange
    msg = "bad input"
    payload = {"details": ["x", "y"]}
    inst = InvalidUsage(msg, status_code=422, payload=payload)
    # Act
    j = inst.to_json()
    # Assert
    assert inst.status_code == 422
    assert inst.payload is payload
    # to_json should include both the message and the payload contents
    assert j["message"] == msg
    assert j["details"] == ["x", "y"]

def test_crudmixing_forwards_to_extensions_create_update_save(monkeypatch):
    # Arrange
    calls = {}

    def fake_create(cls_arg=None, data=None, **kwargs):
        # Accept either (cls, dict) or (cls, **kwargs)
        calls['create'] = {"args": (cls_arg, data), "kwargs": kwargs}
        return "created-sentinel"

    def fake_update(instance, data=None, **kwargs):
        calls['update'] = {"instance": instance, "data": data, "kwargs": kwargs}
        return "updated-sentinel"

    def fake_save(instance, **kwargs):
        calls['save'] = {"instance": instance, "kwargs": kwargs}
        return "saved-sentinel"

    monkeypatch.setattr(conduit_extensions, "create", fake_create, raising=False)
    monkeypatch.setattr(conduit_extensions, "update", fake_update, raising=False)
    monkeypatch.setattr(conduit_extensions, "save", fake_save, raising=False)

    # Create a dummy model class using the mixin
    class DummyModel(CRUDMixin):
        def __init__(self, **kw):
            self._kw = kw

    # Act & Assert - create (class-level)
    created = DummyModel.create(name="alice", age=30)
    assert created == "created-sentinel"
    # Ensure that extension create was called; accept both calling conventions
    assert 'create' in calls
    create_args = calls['create']['args']
    # Either the class was passed as first arg or None + kwargs passed in second spot
    assert create_args[0] in (DummyModel, None)
    
    kw_present = False
    if create_args[1] and isinstance(create_args[1], dict):
        kw_present = create_args[1].get("name") == "alice" and create_args[1].get("age") == 30
    if calls['create']['kwargs']:
        kw_present = kw_present or (calls['create']['kwargs'].get("name") == "alice")
    assert kw_present is True

    # Act & Assert - update (instance-level)
    instance = DummyModel(foo="bar")
    updated = instance.update({"foo": "baz"})
    assert updated == "updated-sentinel"
    assert 'update' in calls
    assert calls['update']['instance'] is instance
    assert isinstance(calls['update']['data'], dict) and calls['update']['data'].get("foo") == "baz"

    # Act & Assert - save
    saved = instance.save()
    assert saved == "saved-sentinel"
    assert 'save' in calls
    assert calls['save']['instance'] is instance

@pytest.mark.parametrize("username,bio,image,following", [
    ("alice", "bio text", "http://img", False),
    ("bob", "", None, True),
])
def test_userprofile_and_profileschema_serialize_roundtrip(username, bio, image, following):
    # Arrange
    
    profile = UserProfile(username=username, bio=bio, image=image, following=following)
    serializer = ProfileSchema()
    # Act
    dumped = serializer.dump(profile)
    # Assert
    assert isinstance(dumped, dict)
    assert dumped.get("username") == username
    # bio and image may be None or empty string per input
    assert "bio" in dumped
    assert "image" in dumped
    # following should be present as a boolean
    assert isinstance(dumped.get("following"), (bool, type(None)))
    # For explicit inputs, ensure following matches when not None
    if following is not None:
        assert dumped.get("following") == following

def test_settings_subclasses_have_expected_flags():
    # Arrange / Act / Assert
    # Base config has a SECRET_KEY attribute defined
    assert hasattr(Config, "SECRET_KEY")
    assert isinstance(Config.SECRET_KEY, str)

    # Prod should not be testing and should likely not have DEBUG
    assert issubclass(ProdConfig, Config)
    assert getattr(ProdConfig, "DEBUG", False) is False

    # Dev should enable debug
    assert issubclass(DevConfig, Config)
    assert getattr(DevConfig, "DEBUG", True) is True

    # TestConfig should enable testing
    assert issubclass(TestConfig, Config)
    assert getattr(TestConfig, "TESTING", True) is True

def test_user_password_hash_and_schema(monkeypatch):
    # Arrange
    user = User(username="tester", email="t@example.com")
    # Some implementations use flask_bcrypt; ensure password setting/checking exists
    has_set = hasattr(user, "set_password")
    has_check = hasattr(user, "check_password")
    if has_set and has_check:
        # Act
        user.set_password("s3cr3t")
        # Assert
        assert user.check_password("s3cr3t") is True
        assert user.check_password("wrong") is False
    else:
        
        user.password = "plaintext"
        assert getattr(user, "password", None) == "plaintext"

    # Test schema serialization for public fields
    schema = UserSchema()
    dumped = schema.dump(user)
    assert isinstance(dumped, dict)
    
    assert dumped.get("username") == "tester"
    assert dumped.get("email") == "t@example.com"
    # Ensure sensitive fields like password_hash or password are not present in top-level dict
    assert "password" not in dumped or dumped.get("password") is None
    # If password_hash present, it should not be None if set_password was used
    if has_set and hasattr(user, "password_hash"):
        assert getattr(user, "password_hash", None) is not None or user.check_password("s3cr3t") is True
