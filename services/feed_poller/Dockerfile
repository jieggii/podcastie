FROM python:3.12 AS builder

WORKDIR /build

# install pdm:
RUN pip install pdm==2.15.4

# copy shared libs:
COPY lib/podcastie_database lib/podcastie_database
COPY lib/podcastie_rss lib/podcastie_rss
COPY lib/podcastie_telegram_html lib/podcastie_telegram_html
COPY lib/podcastie_core lib/podcastie_core

# copy feed_poller service pdm files
COPY services/feed_poller/pyproject.toml services/feed_poller/pdm.lock* services/feed_poller/

# install dependencies:
RUN cd services/feed_poller/ && mkdir __pypackages__ && pdm install --prod --no-lock --no-editable --no-self

FROM python:3.12 AS runner

WORKDIR /app

COPY --from=builder /build/services/feed_poller/__pypackages__/ __pypackages__/

# copy feed_poller package
COPY services/feed_poller/feed_poller feed_poller

ENV PYTHONPATH=/app/__pypackages__/3.12/lib
ENTRYPOINT ["python", "-m", "feed_poller"]
