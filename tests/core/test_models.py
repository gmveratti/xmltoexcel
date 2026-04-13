# tests/core/test_models.py

"""Testes unitários para os dataclasses e Enums do core.models.

Garantem a integridade das estruturas de dados utilizadas pelo pipeline.
"""

from core.models import (
    DataType,
    DocType,
    ParseResult,
    ErrorInfo,
    WorkerResult,
    StatusMessage,
    StartMessage,
    ProgressMessage,
    NoFilesMessage,
    DoneMessage,
    FatalErrorMessage,
)


class TestDataTypeEnum:
    """Verifica a integridade do Enum DataType."""

    def test_has_exactly_four_values(self):
        """DataType deve ter CTE, NFE, EVENT e IGNORE."""
        members = list(DataType)
        assert len(members) == 4

    def test_contains_cte(self):
        assert DataType.CTE is not None

    def test_contains_event(self):
        assert DataType.EVENT is not None

    def test_contains_ignore(self):
        assert DataType.IGNORE is not None

    def test_contains_nfe(self):
        assert DataType.NFE is not None

    def test_members_are_unique(self):
        """Nenhum membro duplicado."""
        values = [member.value for member in DataType]
        assert len(values) == len(set(values))


class TestParseResult:
    """Verifica o dataclass ParseResult."""

    def test_accepts_cte_data(self):
        result = ParseResult(data_type=DataType.CTE, data={"chv_cte_Id": "123"})
        assert result.data_type == DataType.CTE
        assert result.data["chv_cte_Id"] == "123"

    def test_accepts_none_data_for_ignore(self):
        result = ParseResult(data_type=DataType.IGNORE, data=None)
        assert result.data is None

    def test_accepts_event_data(self):
        result = ParseResult(
            data_type=DataType.EVENT,
            data={"Tipo de Evento": "Cancelamento"},
        )
        assert result.data_type == DataType.EVENT

    def test_accepts_nfe_list_data(self):
        """NF-e retorna List[Dict] — ParseResult deve aceitar."""
        items = [
            {"chv_nfe_Id": "123", "nItem": "1"},
            {"chv_nfe_Id": "123", "nItem": "2"},
        ]
        result = ParseResult(data_type=DataType.NFE, data=items)
        assert result.data_type == DataType.NFE
        assert isinstance(result.data, list)
        assert len(result.data) == 2


class TestDocTypeEnum:
    """Verifica a integridade do Enum DocType."""

    def test_has_exactly_two_values(self):
        """DocType deve ter CTE e NFE."""
        members = list(DocType)
        assert len(members) == 2

    def test_contains_cte(self):
        assert DocType.CTE is not None

    def test_contains_nfe(self):
        assert DocType.NFE is not None

    def test_lookup_by_name(self):
        """UI converte string para Enum via DocType[name]."""
        assert DocType["CTE"] == DocType.CTE
        assert DocType["NFE"] == DocType.NFE

    def test_members_are_unique(self):
        values = [member.value for member in DocType]
        assert len(values) == len(set(values))


class TestWorkerResult:
    """Verifica o dataclass WorkerResult."""

    def test_with_success(self):
        parse_result = ParseResult(data_type=DataType.CTE, data={"key": "val"})
        worker = WorkerResult(result=parse_result, error=None)
        assert worker.result is not None
        assert worker.error is None

    def test_with_error(self):
        error = ErrorInfo(
            xml_file="test.xml",
            error_msg="XML mal-formado",
            traceback="Traceback ...",
        )
        worker = WorkerResult(result=None, error=error)
        assert worker.result is None
        assert worker.error.xml_file == "test.xml"

    def test_with_both_result_and_error(self):
        """É possível ter resultado + erro parcial (worker não impede)."""
        parse_result = ParseResult(data_type=DataType.CTE, data={})
        error = ErrorInfo("f.xml", "warn", "tb")
        worker = WorkerResult(result=parse_result, error=error)
        assert worker.result is not None
        assert worker.error is not None


class TestErrorInfo:
    """Verifica o dataclass ErrorInfo."""

    def test_stores_all_fields(self):
        error = ErrorInfo(
            xml_file="/path/to/broken.xml",
            error_msg="Unexpected tag",
            traceback="File line 42...",
        )
        assert error.xml_file == "/path/to/broken.xml"
        assert "Unexpected tag" in error.error_msg
        assert "42" in error.traceback


class TestUiMessages:
    """Verifica os dataclasses de mensagens da UI."""

    def test_status_message(self):
        msg = StatusMessage(text="Processando...")
        assert msg.text == "Processando..."

    def test_start_message(self):
        msg = StartMessage(total_files=500)
        assert msg.total_files == 500

    def test_progress_message(self):
        msg = ProgressMessage(current=250, total=500)
        assert msg.current == 250
        assert msg.total == 500

    def test_no_files_message(self):
        msg = NoFilesMessage()
        assert msg is not None

    def test_done_message(self):
        msg = DoneMessage(total_read=500, total_success=495, total_errors=5)
        assert msg.total_read == 500
        assert msg.total_success == 495
        assert msg.total_errors == 5

    def test_fatal_error_message(self):
        msg = FatalErrorMessage(error_msg="Out of memory")
        assert msg.error_msg == "Out of memory"
