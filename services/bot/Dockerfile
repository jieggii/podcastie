FROM python:3.12 AS builder

WORKDIR /build

# install pdm:
RUN pip install pdm==2.15.4

# copy shared libs:
COPY lib/podcastie_database lib/podcastie_database
COPY lib/podcastie_rss lib/podcastie_rss
COPY lib/podcastie_telegram_html lib/podcastie_telegram_html

# copy bot service pdm files
COPY services/bot/pyproject.toml services/bot/pdm.lock* services/bot/

# install dependencies and the project:
RUN cd services/bot/ && mkdir __pypackages__ && pdm install --prod --no-lock --no-editable --no-self


FROM python:3.12 AS runner

WORKDIR /app

COPY --from=builder /build/services/bot/__pypackages__/ __pypackages__/

# copy bot package
COPY services/bot/bot bot

ENV PYTHONPATH=/app/__pypackages__/3.12/lib
ENTRYPOINT ["python", "-m", "bot"]
