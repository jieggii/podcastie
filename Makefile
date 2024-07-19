.PHONY: all
all:
	@echo "todo"

help:
	@echo "help"

secrets:
	mkdir .secrets
	touch .secrets/bot_token

	touch .secrets/mongo_database
	# touch .secrets/mongo_user
	# touch .secrets/mongo_password

	touch .secrets/tg_api_hash
	touch .secrets/tg_api_id

fmt:
	cd ./lib/podcastie_database && pdm run fmt
	cd ./lib/podcastie_rss && pdm run fmt
	cd ./lib/podcastie_service_config && pdm run fmt
	cd ./lib/podcastie_telegram_html && pdm run fmt

	cd ./services/bot && pdm run fmt
	cd ./services/notifier && pdm run fmt
