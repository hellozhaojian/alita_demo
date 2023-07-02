from builtins import Exception


class MandatoryParameterMissingError(Exception):
    pass


class InvalidParameterError(Exception):
    pass


class NotFittedError(Exception):
    pass


class FileSystemOperationError(Exception):
    pass


class MultiprocessingException(Exception):
    pass


class NotSupportedError(Exception):
    pass


class AIModelNotExists(Exception):
    pass
