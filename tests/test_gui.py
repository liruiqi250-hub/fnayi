from file_toolbox.gui import TOOLS, _tool_extensions


def test_excel_tool_extensions_match_openpyxl_supported_formats():
    excel_tool = next(tool for tool in TOOLS if tool.key == "excel")
    assert _tool_extensions(excel_tool) == {".xlsx", ".xlsm"}


def test_excel_file_dialog_filter_lists_supported_formats():
    excel_tool = next(tool for tool in TOOLS if tool.key == "excel")
    assert excel_tool.file_filter == "Excel 文件 (*.xlsx *.xlsm)"


def test_pons_engine_is_available_in_engines():
    from file_toolbox.gui import ENGINES

    pons_entry = [e for e in ENGINES if e[0] == "pons"]
    assert len(pons_entry) == 1
    assert "Pons" in pons_entry[0][1]


def test_organizer_tool_is_defined_in_tools():
    org_tool = next(tool for tool in TOOLS if tool.key == "organizer")
    assert org_tool.uses_translation is False
    assert org_tool.file_filter is None
    assert org_tool.choose_text == "选择文件夹"


def test_organizer_tool_extensions():
    org_tool = next(tool for tool in TOOLS if tool.key == "organizer")
    assert _tool_extensions(org_tool) == set()
