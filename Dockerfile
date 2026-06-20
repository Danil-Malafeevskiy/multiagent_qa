FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml requirements.txt README.md ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY examples ./examples
RUN pip install --no-cache-dir --no-deps -e .

ENTRYPOINT ["python", "-m", "qa_testgen.cli"]

