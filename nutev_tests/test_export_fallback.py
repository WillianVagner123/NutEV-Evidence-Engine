from __future__ import annotations

import pandas as pd

from nutev.export.excel_writer import write_excel_file


def test_excel_writer_falls_back_to_csv(monkeypatch, tmp_path):
    def boom(self, *args, **kwargs):
        raise ModuleNotFoundError("openpyxl")
    monkeypatch.setattr(pd.DataFrame, "to_excel", boom)
    path = tmp_path / "out.xlsx"
    write_excel_file(pd.DataFrame([{"a": 1}]), path)
    assert path.exists()
    assert path.with_suffix(".csv").exists()
