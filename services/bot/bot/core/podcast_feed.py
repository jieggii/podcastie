# import podcastie_rss
# import aiohttp
#
# class BadFeedException(Exception):
#     pass
#
#
# async def fetch_feed(feed_url: str) -> podcastie_rss.Feed:
#     try:
#         return await podcastie_rss.fetch_feed(feed_url)
#
#     except aiohttp.ClientConnectorError:
#         raise BadFeedException("could not fetch RSS feed")
#
#     except podcastie_rss.MalformedFeedFormatError:
#         raise BadFeedException("RSS feed has malformed format")
#
#     except podcastie_rss.MissingFeedTitleError:
#         raise BadFeedException("RSS feed does not contain podcast title")
#
#     except Exception:
#         raise BadFeedException("unexpected error when attempting to fetch RSS feed")
