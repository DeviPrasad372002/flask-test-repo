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

import inspect
import types
import pytest

try:
    import conduit.commands as commands
    import conduit.exceptions as exceptions
    import conduit.database as database
    import conduit.extensions as extensions
    import sqlalchemy
except ImportError as e:
    pytest.skip(f"Skipping integration tests due to missing imports: {e}", allow_module_level=True)

def _invoke_flexible(fn):
    """
    Call fn either as a factory (returns an instance) or as a raiser (raises an InvalidUsage).
    Build trivial args for required parameters if any.
    Return the resulting instance (either returned or the caught exception instance).
    """
    sig = inspect.signature(fn)
    bound_args = []
    for name, param in sig.parameters.items():
        if param.default is inspect._empty and param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            # supply a harmless dummy
            bound_args.append("test")
    try:
        result = fn(*bound_args)
        return result
    except exceptions.InvalidUsage as exc:
        return exc

def test_exceptions_factory_and_to_json_for_common_errors():
    # Arrange
    funcs = [
        exceptions.user_not_found,
        exceptions.user_already_registered,
        exceptions.unknown_error,
        exceptions.article_not_found,
        exceptions.comment_not_owned,
    ]
    # Act / Assert
    for fn in funcs:
        inst = _invoke_flexible(fn)
        
        assert isinstance(inst, exceptions.InvalidUsage), f"{fn.__name__} did not produce InvalidUsage"
        # to_json must return a dict and template must be serializable text
        j = inst.to_json()
        assert isinstance(j, dict), "to_json must return a dict"
        # template should be a string or bytes
        tpl = inst.template()
        assert isinstance(tpl, (str, bytes)), "template() must return str or bytes"

def test_database_reference_col_creates_foreign_key_column_with_expected_target():
    # Arrange & Act
    col = database.reference_col("user")
    # Assert that a SQLAlchemy Column-like object was produced and that it has foreign keys
    # `foreign_keys` should be an iterable with at least one element referencing the target
    assert hasattr(col, "foreign_keys"), "reference_col should return an object with foreign_keys"
    fks = list(col.foreign_keys)
    assert len(fks) >= 1, "expected at least one foreign key on the returned column"
    fk0 = fks[0]
    # The string representation or target of the foreign key should mention the target table name we provided
    assert "user" in str(fk0).lower() or "user" in getattr(getattr(fk0, "column", None), "table", getattr(fk0, "target_fullname", "")) and True

def test_database_get_by_id_returns_object_and_raises_when_missing():
    # Arrange: construct dummy model classes with a query.get interface
    class DummyQueryPresent:
        def get(self, id_):
            return {"id": id_, "name": "present"} if id_ == 1 else None

    class DummyModelPresent:
        query = DummyQueryPresent()

    # Act: found case
    found = database.get_by_id(DummyModelPresent, 1, "dummy")
    # Assert
    assert isinstance(found, dict), "get_by_id should return the object when found"
    assert found["id"] == 1 and found["name"] == "present"

    # Arrange missing case
    class DummyQueryMissing:
        def get(self, id_):
            return None

    class DummyModelMissing:
        query = DummyQueryMissing()

    
    with pytest.raises(exceptions.InvalidUsage):
        database.get_by_id(DummyModelMissing, 42, "missing_resource")

def test_crudmixin_create_classmethod_constructs_and_saves(monkeypatch):
    # Arrange: create a subclass that implements save and tracks that it was saved
    class MyModel(extensions.CRUDMixin):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self._saved = False

        def save(self):
            # emulate persisting and return self, as many implementations do
            self._saved = True
            return self

    # Ensure create is present on the mixin (commonly a classmethod)
    assert hasattr(MyModel, "create"), "CRUDMixin should provide a create method"

    # Act
    instance = MyModel.create(name="integration-test", value=123)

    # Assert
    assert isinstance(instance, MyModel), "create should return an instance of the model class"
    assert instance.name == "integration-test"
    assert instance.value == 123
    assert getattr(instance, "_saved", False) is True, "the instance must have been saved (save() called)"
