"""Seed the persistent store with ready-made Russian documents for the UI.

Creates a ``ui-demo`` collection so the web dashboard has something to show out
of the box. Re-running only recreates ``ui-demo`` — other collections are left
untouched. Uses a smaller chunk size than the default so each document splits
into several chunks, which makes the knowledge graph more interesting.

    python -m scripts.seed_ui_data

Restart the API afterwards if it is already running so it reloads the store.
"""

from __future__ import annotations

from app.config import Settings
from app.dependencies import build_container

COLLECTION = "ui-demo"

DOCUMENTS: list[tuple[str, str]] = [
    (
        "машинное_обучение.md",
        "Машинное обучение — это раздел искусственного интеллекта, в котором модели "
        "учатся находить закономерности в данных, а не программируются вручную. "
        "При обучении с учителем модель тренируется на размеченных примерах, при "
        "обучении без учителя — ищет структуру в неразмеченных данных, а при "
        "обучении с подкреплением оптимизирует поведение через награды.\n\n"
        "Качество модели оценивают на отложенной выборке, чтобы проверить, как она "
        "обобщается на новые данные. Переобучение возникает, когда модель слишком "
        "точно подстраивается под обучающие примеры и теряет способность обобщать.",
    ),
    (
        "эмбеддинги_и_поиск.md",
        "Эмбеддинг превращает фрагмент текста в плотный вектор так, что близкие по "
        "смыслу тексты оказываются рядом в векторном пространстве. Семантический "
        "поиск кодирует запрос в это же пространство и возвращает ближайшие "
        "документы, обычно по косинусной близости.\n\n"
        "Векторные базы данных, такие как Qdrant, Chroma, Milvus, Pinecone и "
        "pgvector, хранят такие векторы и обеспечивают быстрый приближённый поиск "
        "ближайших соседей при большом объёме данных.",
    ),
    (
        "rag.md",
        "Retrieval-Augmented Generation (RAG) объединяет поисковую систему и большую "
        "языковую модель. Вместо того чтобы полагаться только на параметры модели, "
        "RAG сначала извлекает релевантные фрагменты из базы знаний, а затем "
        "передаёт их модели как контекст для генерации ответа.\n\n"
        "Такой подход уменьшает галлюцинации, привязывает ответы к источникам и "
        "позволяет обновлять знания без переобучения модели. Гибридный поиск "
        "объединяет плотные векторы и разреженный BM25, повышая полноту выдачи.",
    ),
    (
        "инфраструктура.md",
        "FastAPI — современный веб-фреймворк на Python для создания API. Он опирается "
        "на аннотации типов и Pydantic для валидации и поддерживает асинхронную "
        "обработку запросов. Uvicorn — это ASGI-сервер, который запускает "
        "приложения FastAPI.\n\n"
        "Docker упаковывает приложение и его зависимости в образ контейнера, чтобы "
        "оно одинаково работало в любой среде. Docker Compose оркестрирует "
        "несколько контейнеров вместе для локальной разработки и деплоя.",
    ),
]


def main() -> None:
    settings = Settings(chunk_size=110, chunk_overlap=20, persist_vectorstore=True)
    container = build_container(settings)

    container.vectorstore.delete_collection(COLLECTION)

    total_chunks = 0
    for source, text in DOCUMENTS:
        result = container.pipeline.ingest_text(
            text, collection=COLLECTION, metadata={"source": source}
        )
        total_chunks += result.chunks
        print(f"  + {source}: {result.chunks} chunks")

    print(
        f"\nSeeded collection '{COLLECTION}' with {len(DOCUMENTS)} documents "
        f"({total_chunks} chunks) into {settings.data_dir}."
    )
    print("Restart the API if it is running so it reloads the store.")


if __name__ == "__main__":
    main()
