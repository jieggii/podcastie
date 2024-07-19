import listparser
from podcastie_database import Podcast


class OPMLParseError(Exception):
    pass


def parse_opml(data: bytes) -> list[str]:
    try:
        result = listparser.parse(data)
    except listparser.ListparserError:
        raise OPMLParseError()

    return [feed.url for feed in result.feeds]


def generate_opml(podcasts: list[Podcast]) -> str:
    # todo: escape titles and urls
    outlines = [
        f'\t\t<outline xmlUrl="{podcast.feed_url}" type="rss" text="{podcast.title}"/>'
        for podcast in podcasts
    ]

    data = f"""<opml version="1.0">
    <head>
        <title>Podcastie Feeds</title>
    </head>
    <body>
        <outline text="feeds">
{"\n".join(outlines)}
        </outline>
    </body>
</opml>
    """

    return data
