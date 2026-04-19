"""Excepções customizadas do sistema SIDCT."""


class SIDCTBaseError(Exception):
    """Base para todas as excepções SIDCT."""
    def __init__(self, message: str, code: str = "SIDCT_ERROR"):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")


class ValidationError(SIDCTBaseError):
    """Dados de entrada inválidos ou incompletos."""
    def __init__(self, message: str, field: str = ""):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class MissingInputError(ValidationError):
    """Campo obrigatório ausente para o regime seleccionado."""
    def __init__(self, field: str, regime: str = ""):
        msg = f"Campo obrigatório '{field}' ausente" + (f" para regime '{regime}'" if regime else "")
        super().__init__(msg, field)
        self.code = "MISSING_INPUT"


class DatasetMissingError(SIDCTBaseError):
    """Dataset normativo ou técnico ausente — não inventar."""
    def __init__(self, dataset: str, context: str = ""):
        msg = f"Dataset '{dataset}' não disponível" + (f" — {context}" if context else "")
        super().__init__(msg, "DATASET_MISSING")
        self.dataset = dataset
        self.context = context


class OutOfScopeError(SIDCTBaseError):
    """Condições fora do envelope validado do modelo."""
    def __init__(self, message: str, parameter: str = "", value=None, limit=None):
        detail = message
        if parameter and value is not None:
            detail += f" | {parameter} = {value}"
        if limit is not None:
            detail += f" | limite = {limit}"
        super().__init__(detail, "OUT_OF_SCOPE")
        self.parameter = parameter
        self.value = value
        self.limit = limit


class CodeMismatchError(SIDCTBaseError):
    """Catálogo ou código incompatível com o perfil seleccionado."""
    def __init__(self, received: str, expected: str, context: str = ""):
        msg = f"Código/catálogo '{received}' incompatível com perfil (esperado: {expected})"
        if context:
            msg += f" — {context}"
        super().__init__(msg, "CODE_MISMATCH")


class ConvergenceError(SIDCTBaseError):
    """Motor iterativo não convergiu."""
    def __init__(self, method: str, iterations: int, tolerance: float):
        msg = f"'{method}' não convergiu em {iterations} iterações (tol={tolerance})"
        super().__init__(msg, "CONVERGENCE_ERROR")


class ProfileNotFoundError(SIDCTBaseError):
    """Perfil de projeto não encontrado no registo."""
    def __init__(self, profile_id: str):
        super().__init__(f"Perfil '{profile_id}' não encontrado", "PROFILE_NOT_FOUND")


class MaterialNotFoundError(DatasetMissingError):
    """Material não encontrado no catálogo de tensões admissíveis."""
    def __init__(self, material: str, temperature_c: float = None):
        ctx = f"T = {temperature_c}°C" if temperature_c is not None else ""
        super().__init__(f"material:{material}", ctx)
        self.material = material


class WrongEngineError(SIDCTBaseError):
    """Motor hidráulico errado tentado para o serviço."""
    def __init__(self, engine: str, service: str, correct_engine: str):
        msg = (f"Motor '{engine}' não é aplicável ao serviço '{service}'. "
               f"Use '{correct_engine}'.")
        super().__init__(msg, "WRONG_ENGINE")


class ExternalPressureRequiredError(SIDCTBaseError):
    """Verificação de pressão externa não realizada para linha de vácuo."""
    def __init__(self, line_tag: str = ""):
        msg = "Linha de vácuo requer verificação obrigatória de pressão externa/colapso"
        if line_tag:
            msg += f" (linha: {line_tag})"
        super().__init__(msg, "EXTERNAL_PRESSURE_REQUIRED")
