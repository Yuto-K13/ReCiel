import utils


class MusicError(utils.CustomError):
    pass


class NotConnectedError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="VCに接続していません", ignore=True)


class AlreadyConnectedError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="既にVCに接続しています", ignore=True)


class UserNotInVoiceChannelError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="VCに接続してから実行してください", ignore=True)


class UserNotInSameChannelError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="同じVCに接続してから実行してください", ignore=True)


class UserNotInSameGuildError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="接続しているVCと同じサーバーで実行してください", ignore=True)


class UserNotInGuildError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="サーバーで実行してください", ignore=True)


class NoTrackPlayingError(MusicError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="再生中の曲がありません", ignore=True)


class YouTubeDLPError(MusicError):
    def __init__(self, *args: object, msg: str = "", ignore: bool = False) -> None:
        super().__init__(*args, msg=msg or "yt-dlpでエラーが発生しました", ignore=ignore)


class DownloadError(YouTubeDLPError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args, msg="ダウンロード中にエラーが発生しました", ignore=True)
