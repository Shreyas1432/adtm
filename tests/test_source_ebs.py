"""Unit tests for the EBS source adapter.

No live Oracle and no python-oracledb needed: a fake connection is injected via
`connect_fn`, routing by SQL content. Covers the read-only guard, table listing,
column metadata (PK + comments + length), and streaming extract.
"""
import pytest

from adapters.source_ebs import EbsSourceAdapter, is_readonly_select


# --- fake Oracle connection --------------------------------------------------


class FakeCursor:
    def __init__(self, store):
        self.store = store
        self.arraysize = 100
        self._rows: list = []
        self._pos = 0
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, binds=None):
        s = " ".join(sql.lower().split())
        binds = binds or {}
        if "from dual" in s:
            self._rows, self.description = [(1,)], [("1",)]
        elif "all_tables" in s or "user_tables" in s:
            self._rows = [(t,) for t in self.store["tables"]]
            self.description = [("TABLE_NAME",)]
        elif "constraint_type = 'p'" in s:
            self._rows = [(c,) for c in self.store["pk"]]
            self.description = [("COLUMN_NAME",)]
        elif "data_type" in s:  # column metadata query
            self._rows = list(self.store["columns"])
            self.description = [("COLUMN_NAME",)]
        else:  # treat as an extract SELECT
            data = self.store["extract"]
            self.description = [(c,) for c in data["cols"]]
            self._rows = list(data["rows"])
        self._pos = 0

    def fetchone(self):
        if self._pos < len(self._rows):
            r = self._rows[self._pos]
            self._pos += 1
            return r
        return None

    def fetchall(self):
        r = self._rows[self._pos:]
        self._pos = len(self._rows)
        return r

    def fetchmany(self, n):
        r = self._rows[self._pos:self._pos + n]
        self._pos += len(r)
        return r


class FakeConn:
    def __init__(self, store):
        self.store = store
        self.closed = False

    def cursor(self):
        return FakeCursor(self.store)

    def close(self):
        self.closed = True


def make_adapter(store):
    return EbsSourceAdapter("DEV_SECRET", {"schema": "APPS"}, connect_fn=lambda: FakeConn(store))


# --- read-only guard ---------------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM ap_suppliers",
        "  select vendor_id from ap_suppliers where vendor_name = 'DELETE ME' ",
        "WITH s AS (SELECT 1 FROM dual) SELECT * FROM s",
        "SELECT vendor_id, last_update_date FROM ap_suppliers",  # 'update' inside identifier is fine
    ],
)
def test_guard_allows_readonly(sql):
    assert is_readonly_select(sql) is True


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM ap_suppliers",
        "UPDATE ap_suppliers SET vendor_name = 'x'",
        "INSERT INTO ap_suppliers VALUES (1)",
        "SELECT 1 FROM dual; DROP TABLE ap_suppliers",  # stacked statement
        "DROP TABLE ap_suppliers",
        "BEGIN NULL; END;",
        "",
    ],
)
def test_guard_blocks_writes(sql):
    assert is_readonly_select(sql) is False


def test_extract_rejects_non_readonly():
    a = make_adapter({})
    with pytest.raises(ValueError):
        list(a.extract("UPDATE ap_suppliers SET vendor_name='x'"))


# --- contract methods --------------------------------------------------------


def test_test_connection():
    assert make_adapter({"tables": []}).test_connection() is True


def test_list_tables():
    a = make_adapter({"tables": ["AP_SUPPLIERS", "AP_SUPPLIER_SITES_ALL"]})
    assert a.list_tables() == ["AP_SUPPLIERS", "AP_SUPPLIER_SITES_ALL"]


def test_column_metadata_pk_and_comments():
    store = {
        "pk": ["VENDOR_ID"],
        "columns": [
            # name, data_type, data_length, data_precision, data_scale, nullable, comments
            ("VENDOR_ID", "NUMBER", 22, 15, 0, "N", "Supplier surrogate key"),
            ("VENDOR_NAME", "VARCHAR2", 240, None, None, "N", "Supplier name"),
            ("TAX_ID", "VARCHAR2", 20, None, None, "Y", None),
        ],
    }
    cols = make_adapter(store).column_metadata("ap_suppliers")
    by_name = {c["name"]: c for c in cols}
    assert by_name["VENDOR_ID"]["pk"] is True
    assert by_name["VENDOR_ID"]["length"] == "15,0"      # precision,scale for NUMBER
    assert by_name["VENDOR_NAME"]["pk"] is False
    assert by_name["VENDOR_NAME"]["description"] == "Supplier name"
    assert by_name["VENDOR_NAME"]["length"] == 240       # char length
    assert by_name["TAX_ID"]["nullable"] is True
    assert [c["name"] for c in cols] == ["VENDOR_ID", "VENDOR_NAME", "TAX_ID"]


def test_extract_streams_dicts():
    store = {
        "extract": {
            "cols": ["VENDOR_ID", "VENDOR_NAME"],
            "rows": [(1, "Acme Ltd"), (2, "Globex")],
        }
    }
    rows = list(make_adapter(store).extract("SELECT vendor_id, vendor_name FROM ap_suppliers"))
    assert rows == [
        {"VENDOR_ID": 1, "VENDOR_NAME": "Acme Ltd"},
        {"VENDOR_ID": 2, "VENDOR_NAME": "Globex"},
    ]
