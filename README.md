# podcastie
<img src="https://imgur.com/kapg35n.jpg" alt="art" width="30%">

Subscribe to your favorite podcasts, share them with friends, and listen to new episodes right within Telegram!

## Roadmap
> [!WARNING]
> The project is put on hold.

- [x] MVP (July)
- [x] [UI/UX redisign](https://github.com/jieggii/podcastie/tree/feature/ui-redesign) (using callback buttons) (Aug)
- [ ] iTunes integration 
- [ ] Antifraud measures 
- [ ] Multiple languages support using i18n 
- [ ] Release 
- [ ] Recommendation system using KNN 

## Features
* **Subscribe to Podcasts**: Simply provide the RSS feed URL or PPID of your favorite podcast to start receiving new episodes.
* **Listen to Podcasts**: Receive episode notifications containing episode audio and listen to them right in the chat.
* **Instant Notifications**: Get instant updates as soon as a new episode is released, so you never miss an episode of your favorite shows.
* **Manage Subscriptions**: Easily manage your podcast subscriptions.
* **Import and Export Subscriptions**: Effortlessly import and export your podcast subscriptions in OPML format for easy management and backup.
* **Share Your Favorite Shows With Friends**: Use inline mode to share your favorite podcasts with friends.
* **Instant Links**: Use Instant Links to follow any show in two taps ([like this one](https://t.me/podcastie_bot?start=YThjYmI5ZmU=)).

## Available interactions:
### Commands in private chat with the bot:
* `/follow` - start following podcast.
* `/unfollow` - stop following podcast.
* `/list` - list podcasts you are following.
* `/import` - import subscriptions from an OPML file.
* `/export` - export subscriptions as OPML file.
* `/faq` - get list of frequently asked questions.
* `/about` - get additional information about the bot.

### Inline mode
Type the bot's username (`@podcastie_bot`) in any chat to see the list of podcasts you follow.
Type search query after it's username to find any podcast among the whole set of shows stored in the bot's database 
and click on podcast you want to share in the current chat!

A podcast card containing an Instant Link to follow it will be sent to the chat.

...

## Podcast RSS feed requirements
> [!NOTE]
> Most popular podcasts comply with these requirements. 
> This documentation serves to clarify the necessary criteria.

For users to successfully follow and access a podcast, 
the podcast's RSS feed must meet the following requirements.

To ensure a podcast is followable, it must:
* Have a title.

For episodes to be delivered to users, each episode must:
* Include a publication date.
* Contain at least one `enclosure` with the following properties:
  * `url`: The URL of the episode file.
  * `file_size`: The size of the file in bytes (Must not exceed X MB).
  * `mime_type`: The MIME type of the file (Must be either `audio/mp3` or `audio/mpeg`).

## Selfhosting
Podcastie can be easily selfhosted. Follow these simple instructions to make it work!

...


---

*Created with ❤️ by [jieggii](https://github.com/jiegii) (art by [ellik](https://www.pixilart.com/ellik))*
