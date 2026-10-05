"""DuckDB-over-Parquet helper (ADR-0002)."""
import pyarrow as pa
import pyarrow.parquet as pq

from dataplane.duck import query_parquet


def test_query_parquet_reads_and_filters(tmp_path):
    path = str(tmp_path / "s.parquet")
    pq.write_table(pa.table({"name": ["Acme", "Globex"], "country": ["IE", "US"]}), path)
    rows = query_parquet("SELECT name FROM s WHERE country='IE' ORDER BY name", s=path)
    assert rows == [{"name": "Acme"}]


def test_query_parquet_empty_result(tmp_path):
    path = str(tmp_path / "s.parquet")
    pq.write_table(pa.table({"name": ["Acme"]}), path)
    assert query_parquet("SELECT * FROM s WHERE name='none'", s=path) == []
