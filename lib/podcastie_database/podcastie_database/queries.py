from .models import User, Podcast

#     async def get_user(self, user_id: int) -> dict:
#         return await self.users.find_one({"user_id": user_id})
#
#     async def create_user(self, user_id: int):
#         return await self.users.insert_one({"user_id": user_id, "subscriptions": []})
#
#     async def add_subscription(self, user_id: int, feed_url: str):
#         await self.users.update_one(
#             {"user_id": user_id}, {"$push": {"subscriptions": feed_url}}
#         )
#
#     async def get_podcast(self, feed_url: str) -> dict:
#         return await self.podcasts.find_one({"feed_url": feed_url})
#
#     async def create_podcast(self, title: str, link: str, feed_url: str):
#         await self.podcasts.insert_one(
#             {"feed_url": feed_url, "title": title, "link": link}
#         )
#
#     async def remove_subscription(self, user_id: int, feed_url: str):
#         await self.users.update_one(
#             {"user_id": user_id}, {"$pull": {"subscriptions": feed_url}}
#         )
#
#     async def get_all_podcasts(self) -> list[dict]:
#         cursor = self.podcasts.find({})
#         return await cursor.to_list(length=None)
