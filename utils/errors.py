import re

from discord.app_commands import AppCommandError

PATTERN = re.compile(r"\x1b\[[0-9;]*m")  # ANSIエスケープシーケンスを除去


class CustomError(AppCommandError):
    def __init__(self, *args: object, name: str = "", msg: str = "", ignore: bool = False) -> None:
        super().__init__(*args)
        self.name = name or self.__class__.__name__
        self.msg = msg
        self.ignore = ignore

    def __str__(self) -> str:
        if not self.msg:
            return "\n".join(map(self.format, self.args))
        return "\n".join(map(self.format, (self.msg, *self.args)))

    def format(self, msg: object) -> str:
        return PATTERN.sub("", str(msg))


class InvalidAttributeError(CustomError):
    def __init__(self, attribute_name: str, *args: object) -> None:
        super().__init__(*args, msg=f"無効な属性: {attribute_name}")


class MissingPermissionsError(CustomError):
    def __init__(self, *args: object, msg: str = "") -> None:
        super().__init__(*args, msg=msg or "Missing Permissions", ignore=True)


class DeveloperCommandError(MissingPermissionsError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="This Command is Only for Developers.")


class ExtensionNotFoundError(CustomError):
    def __init__(self, extension: str, *args: object) -> None:
        super().__init__(*args, msg=f'Extension "{extension}" Not Found.')
