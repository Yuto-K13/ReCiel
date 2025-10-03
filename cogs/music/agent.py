from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from pydantic import BaseModel, Field

import utils

from . import youtube

APP_NAME = "CielMusic"


async def search_youtube(word: str) -> list[dict[str, str]]:
    """指定されたキーワードでYouTube上の動画を検索し、最大3件の関連性の高い動画の情報を取得する非同期関数

    Args:
        word (str): 検索に使用するキーワード。

    Returns:
        list[dict[str, str]]: 各要素は以下のキーを持つ辞書
            - title (str): 動画のタイトル
            - url (str): 動画のYouTubeリンク
            - channel (str): 動画を投稿したチャンネル名
            - channel_url (str): チャンネルのURL
            - thumbnail (str): 動画のサムネイル画像URL

    Raises:
        errors.SearchError: YouTube APIからエラーが返された場合や、検索結果が見つからなかった場合に発生。

    Note:
        - GoogleのYouTube Data API v3を利用して動画を検索します。
        - APIキーは環境変数 'GOOGLE_API_KEY' から取得します。
        - 検索結果が1件もない場合やAPIエラー時は例外を送出します。

    """
    utils.logger.debug(f"Searching YouTube (Query: {word})")
    info = await youtube.search(word, results=3)
    items: list[dict] = []
    for item in info["items"]:
        snippet = item.get("snippet", {})
        title = snippet.get("title", "")
        channel = snippet.get("channelTitle", "")

        video_id = item.get("id", {}).get("videoId")
        url = f"https://www.youtube.com/watch?v={video_id}" if video_id is not None else ""

        channel_id = snippet.get("channelId")
        channel_url = f"https://www.youtube.com/channel/{channel_id}" if channel_id is not None else ""

        thumbnails = snippet.get("thumbnails", {})
        for key in ("high", "medium", "default"):
            thumbnail = thumbnails.get(key, {}).get("url")
            if thumbnail is not None:
                break
        else:
            thumbnail = ""

        utils.logger.debug(f"Searched Youtube Video (Title: {title}, Channel: {channel}, URL: {url})")
        items.append(
            {
                "title": title,
                "url": url,
                "channel": channel,
                "channel_url": channel_url,
                "thumbnail": thumbnail,
            },
        )
    return items


class TrackInfo(BaseModel):
    title: str = Field(description="動画のタイトル")
    url: str = Field(description="動画のYouTubeリンク")
    channel: str = Field(description="動画を投稿したチャンネル名")
    channel_url: str = Field(description="チャンネルのURL")
    thumbnail: str = Field(description="動画のサムネイル画像URL")


WOKER_AGENT = Agent(
    name=f"{APP_NAME}Worker",
    model=utils.AgentModel.gemini_2_5_flash,
    description="ユーザーから与えられたキーワードに基づき、YouTube上で関連性の高い楽曲を検索し、最適な楽曲のURLを提案する音楽推薦エージェントです。",
    instruction="""
    あなたは音楽推薦エージェントです。
    ユーザーからキーワードが与えられるため、それに沿ったYouTube上の楽曲を提案してください。

    単純に与えられたキーワードを検索するだけでなく、キーワードの意味や関連語、ジャンル、雰囲気、アーティスト名、時代、シチュエーションなども考慮し、幅広い表現や関連ワードを用いて検索を行い、最も適切な楽曲を選んでください。
    必ず公式ミュージックビデオや公式オーディオ、信頼できる音楽チャンネルからの楽曲を選んでください。
    もし検索結果がキーワードに沿わない場合や、楽曲として不適切な場合は、検索ワードを変えて繰り返し検索し、ユーザーの意図に合致した楽曲が見つかるまで試行してください。
    また可能な限り過去にユーザーへ提案した楽曲と同じものは避けてください。

    最終的に選んだ楽曲についての情報を、以下の情報をすべて含めて出力してください。

    "title": "楽曲のタイトル",
    "url": "楽曲のYouTubeリンク",
    "channel": "楽曲を投稿したチャンネル名",
    "channel_url": "チャンネルのURL",
    "thumbnail": "楽曲のサムネイル画像URL"

    """,
    tools=[search_youtube],
)


FORMAT_AGENT = Agent(
    name=f"{APP_NAME}Formatter",
    model=utils.AgentModel.gemini_2_5_flash,
    description="入力された動画の情報を正しいJSON形式に整形するエージェントです。",
    instruction="""
    あなたはJSONフォーマッターエージェントです。
    動画の情報が与えられるため、以下のjson形式に整形して出力してください。

    {
        "title": "楽曲のタイトル",
        "url": "楽曲のYouTubeリンク",
        "channel": "楽曲を投稿したチャンネル名",
        "channel_url": "チャンネルのURL",
        "thumbnail": "楽曲のサムネイル画像URL"
    }
    """,
    output_schema=TrackInfo,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

AGENT = SequentialAgent(name=APP_NAME, sub_agents=[WOKER_AGENT, FORMAT_AGENT])
SESSION_SERVICE = InMemorySessionService()
RUNNER = Runner(app_name=APP_NAME, agent=AGENT, session_service=SESSION_SERVICE)
