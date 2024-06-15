.PHONY: all
all:
	@echo "todo"

help:
	@echo "help"

secrets:
	mkdir .secrets
	echo "todo"

fmt:
	cd ./lib/podcastie_configs && pdm run fmt
	cd ./lib/podcastie_database && pdm run fmt
	cd ./lib/podcastie_rss && pdm run fmt

	cd ./services/bot && pdm run fmt
	cd ./services/notifier && pdm run fmt
