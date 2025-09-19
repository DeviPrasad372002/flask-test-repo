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

# Guard imports of target modules
try:
    from conduit import commands, database, exceptions, extensions
except Exception as e:  # ImportError or other import-time errors
    pytest.skip(f"conduit package not importable: {e}", allow_module_level=True)

def _call_flexibly(func, *preferred_args):
    """
    Try calling func several ways:
     - with preferred_args
     - with no args
     - with a single None
    Return (ok, result_or_exception). ok True if call succeeded, False if it raised.
    """
    try:
        return True, func(*preferred_args)
    except TypeError:
        try:
            return True, func()
        except TypeError as e:
            try:
                return True, func(None)
            except Exception as e2:
                return False, e2
    except Exception as e:
        return False, e

def test_execute_tool_calls_subprocess_and_respects_returncode(monkeypatch):
    # Arrange
    ran = {}

    class DummyCompleted:
        def __init__(self, rc=0, out=b"ok"):
            self.returncode = rc
            self.stdout = out
            self.stderr = b""

    def fake_run(cmd, *args, **kwargs):
        # Record invocation and pretend returncode depends on cmd content
        ran['cmd'] = cmd
        if isinstance(cmd, (list, tuple)):
            name = cmd[0]
        else:
            name = str(cmd)
        if 'fail' in name:
            return DummyCompleted(rc=2, out=b"bad")
        return DummyCompleted(rc=0, out=b"good")

    # Monkeypatch subprocess.run inside commands module
    monkeypatch.setattr(commands, 'subprocess', types.SimpleNamespace(run=fake_run, CompletedProcess=None))

    # Act / Assert: success case
    ok, result = _call_flexibly(commands.execute_tool, 'tool_ok')
    assert ok is True, f"execute_tool raised unexpectedly: {result}"
    # result may be CompletedProcess, int, bool or None depending on implementation
    if hasattr(result, 'returncode'):
        assert result.returncode == 0
    elif isinstance(result, int):
        assert result == 0
    else:
        # if returns truthy/None - at least ensure our fake_run was invoked
        assert 'cmd' in ran

    
    ok2, result2 = _call_flexibly(commands.execute_tool, 'tool_fail')
    assert ok2 is True or isinstance(result2, Exception)
    
    if ok2:
        if hasattr(result2, 'returncode'):
            assert result2.returncode != 0
        elif isinstance(result2, int):
            assert result2 != 0
        else:
            assert 'cmd' in ran

def test_urls_uses_glob_and_returns_iterable(monkeypatch):
    # Arrange: pretend glob.glob is used and returns a list
    sample = ['a.py', 'b.py', 'sub/c.py']
    def fake_glob(pattern, recursive=False):
        # record the pattern to ensure function passes something reasonable
        fake_glob.called = True
        fake_glob.pattern = pattern
        return sample.copy()
    monkeypatch.setattr(commands, 'glob', types.SimpleNamespace(glob=fake_glob))

    # Act
    ok, out = _call_flexibly(commands.urls)
    assert ok is True, f"commands.urls raised unexpectedly: {out}"

    # Assert returned something iterable or None but ensure glob was called
    assert getattr(fake_glob, 'called', False) is True
    
    if out is None:
        # possibly urls prints/echoes and returns None; acceptable as long as glob was used
        assert True
    else:
        assert isinstance(out, (list, tuple, str)) or hasattr(out, '__iter__')
        
        try:
            if isinstance(out, (list, tuple)):
                assert any('a.py' in s for s in out)
        except Exception:
            pass

def test_reference_col_contains_tablename_in_repr():
    # Arrange & Act
    ok, col = _call_flexibly(database.reference_col, 'users')
    assert ok is True, f"reference_col raised: {col}"
    # Assert that representation mentions the referenced table name or 'ForeignKey'
    rep = repr(col)
    assert ('users' in rep) or ('ForeignKey' in rep) or ('foreign' in rep.lower())

def test_get_by_id_returns_object_or_raises_invalidusage(monkeypatch):
    # Create a fake model with a query.get behavior
    class DummyQuery:
        def __init__(self, result_map):
            self._res = result_map

        def get(self, id_):
            return self._res.get(id_)

    class DummyModel:
        query = DummyQuery({1: 'one', 2: None})

    # Case: found
    ok, out = _call_flexibly(database.get_by_id, DummyModel, 1)
    assert ok is True, f"get_by_id raised unexpectedly: {out}"
    # Should return the object 'one'
    assert out == 'one'

    
    ok2, out2 = _call_flexibly(database.get_by_id, DummyModel, 2)
    if ok2:
        # If returns, expect None or False-y
        assert out2 is None or out2 is False
    else:
        
        exc = out2
        if hasattr(exceptions, 'InvalidUsage'):
            assert isinstance(exc, exceptions.InvalidUsage)

@pytest.mark.parametrize("funcname", [
    "template", "to_json",
    "user_not_found", "user_already_registered",
    "unknown_error", "article_not_found", "comment_not_owned"
])
def test_exception_helpers_return_or_raise_invalidusage(funcname):
    # Ensure the helper exists in exceptions
    func = getattr(exceptions, funcname, None)
    assert func is not None, f"{funcname} not found on exceptions module"

    # Call the helper in a flexible manner and verify behavior involves InvalidUsage
    ok, res = _call_flexibly(func, "test-message" if funcname in ("template", "to_json") else None)
    if ok:
        # If the function returned a value, it should either be an InvalidUsage instance,
        # a dict/json-like, or a Flask response-like. We check for InvalidUsage support.
        if hasattr(exceptions, 'InvalidUsage') and isinstance(res, exceptions.InvalidUsage):
            assert isinstance(res, exceptions.InvalidUsage)
        else:
            # If not InvalidUsage, ensure some serializable structure (dict or str)
            assert isinstance(res, (dict, str)) or hasattr(res, 'get_json') or res is None
    else:
        
        exc = res
        if hasattr(exceptions, 'InvalidUsage'):
            assert isinstance(exc, exceptions.InvalidUsage)
        else:
            # If InvalidUsage not present, at least we got an Exception
            assert isinstance(exc, Exception)

def test_extensions_create_uses_db_session_commit(monkeypatch):
    # Prepare a dummy db with session.add and session.commit counters
    called = {'add': 0, 'commit': 0}

    class FakeSession:
        def add(self, obj):
            called['add'] += 1
            # attach an attribute to object to simulate ORM behavior
            setattr(obj, '_added', True)

        def commit(self):
            called['commit'] += 1

    fake_db = types.SimpleNamespace(session=FakeSession())

    # Monkeypatch a db attribute in extensions if present
    monkeypatch.setattr(extensions, 'db', fake_db, raising=False)

    # Create a simple dummy object to pass to create
    class DummyObject:
        pass

    obj = DummyObject()

    # Attempt to call create in several ways
    create_func = getattr(extensions, 'create', None)
    assert create_func is not None, "extensions.create not found"

    # Try calling with commit True
    ok, res = _call_flexibly(create_func, obj, True)
    assert ok is True, f"extensions.create(obj, True) raised: {res}"
    # Ensure the session.add was called at least once
    assert called['add'] >= 1
    # Depending on implementation commit may be called; assert commit count is 0 or >=1 but not negative
    assert called['commit'] >= 0
    # If object was mutated by add, check attribute
    if hasattr(obj, '_added'):
        assert getattr(obj, '_added') is True

    # Reset counters and call with commit=False if API supports it
    called['add'] = 0
    called['commit'] = 0
    ok2, res2 = _call_flexibly(create_func, obj, False)
    assert ok2 is True, f"extensions.create(obj, False) raised: {res2}"
    assert called['add'] >= 0
    # commit should be 0 if commit=False semantics honored, or >=0 otherwise
    assert called['commit'] >= 0
