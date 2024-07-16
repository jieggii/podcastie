import listparser
from podcastie_database.models import Podcast

def read_opml(data: str) -> list[str]:
    result = listparser.parse(data)
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
