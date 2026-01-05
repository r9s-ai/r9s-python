class SkillError(Exception):
    pass


class SkillNotFoundError(FileNotFoundError, SkillError):
    pass


class InvalidSkillError(ValueError, SkillError):
    pass


class SecurityError(RuntimeError, SkillError):
    pass
