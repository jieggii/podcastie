FROM python:3.12

WORKDIR /bot

# install pdm:
RUN pip install pdm==2.15.3

# copy project files:
COPY pyproject.toml pdm.lock* ./
COPY app ./app

# install dependencies and the project:
RUN mkdir __pypackages__ && pdm install --prod --no-lock --no-editable
ENV PYTHONPATH=/bot/__pypackages__/3.12/lib

ENTRYPOINT ["python", "-m", "app"]
