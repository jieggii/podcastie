.PHONY: all
all:
	@echo "todo"

.PHONY: help
help:
	@echo "help"

.PHONY: secrets
secrets:
	mkdir .secrets -p

	touch .secrets/mongo_database

	touch .secrets/telegram_bot_token
	touch .secrets/telegram_api_id
	touch .secrets/telegram_api_hash

.PHONY: fmt
fmt:
	cd ./lib/podcastie_database && pdm run fmt
	cd ./lib/podcastie_rss && pdm run fmt
	cd ./lib/podcastie_telegram_html && pdm run fmt
	cd ./lib/podcastie_core && pdm run fmt

	cd ./services/bot && pdm run fmt
	cd ./services/feed_poller && pdm run fmt
