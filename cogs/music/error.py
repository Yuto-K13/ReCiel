import utils


class MusicError(utils.CustomError):
    pass


class InvalidAttributeError(MusicError):
    def __init__(self, attribute_name: str, *args: object) -> None:
        super().__init__(f"無効な属性: {attribute_name}", *args)


class NotConnectedError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("VCに接続していません", *args)


class AlreadyConnectedError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("既にVCに接続しています", *args)


class UserNotInVoiceChannelError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("VCに接続してから実行してください", *args)


class UserNotInSameChannelError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("同じVCに接続してから実行してください", *args)


class UserNotInSameGuildError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("接続しているVCと同じサーバーで実行してください", *args)


class UserNotInGuildError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("サーバーで実行してください", *args)


class NoTrackPlayingError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("再生中の曲がありません", *args)


class DownloadError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__("ダウンロード中にエラーが発生しました", *args)
