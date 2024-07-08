FROM python:3.12 AS builder

WORKDIR /build

# install pdm:
RUN pip install pdm==2.15.4

# copy shared libs:
COPY lib/podcastie_database lib/podcastie_database
COPY lib/podcastie_rss lib/podcastie_rss
COPY lib/podcastie_telegram_html lib/podcastie_telegram_html

# copy notifier service pdm files
COPY services/notifier/pyproject.toml services/notifier/pdm.lock* services/notifier/

# install dependencies:
RUN cd services/notifier/ && mkdir __pypackages__ && pdm install --prod --no-lock --no-editable --no-self

FROM python:3.12 AS runner

WORKDIR /app

COPY --from=builder /build/services/notifier/__pypackages__/ __pypackages__/

# copy notifier package
COPY services/notifier/notifier notifier

ENV PYTHONPATH=/app/__pypackages__/3.12/lib
ENTRYPOINT ["python", "-m", "notifier"]
