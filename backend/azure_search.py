import os

from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)


load_dotenv()


SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY")

INDEX_NAME = "documents-index"


if not SEARCH_ENDPOINT:
    raise ValueError("AZURE_SEARCH_ENDPOINT is missing from .env")

if not SEARCH_KEY:
    raise ValueError("AZURE_SEARCH_KEY is missing from .env")


credential = AzureKeyCredential(SEARCH_KEY)

index_client = SearchIndexClient(
    endpoint=SEARCH_ENDPOINT,
    credential=credential,
)


def create_search_index():
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
        ),

        SimpleField(
            name="document_id",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SearchableField(
            name="filename",
            type=SearchFieldDataType.String,
            filterable=True,
        ),

        SimpleField(
            name="page",
            type=SearchFieldDataType.Int32,
            filterable=True,
            sortable=True,
        ),

        SearchableField(
            name="text",
            type=SearchFieldDataType.String,
        ),

        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(
                SearchFieldDataType.Single
            ),
            searchable=True,
            vector_search_dimensions=384,
            vector_search_profile_name="vector-profile",
        ),

        SimpleField(
            name="sha256",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(
                name="hnsw-config"
            )
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw-config",
            )
        ],
    )

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
    )

    result = index_client.create_or_update_index(index)

    print()
    print("========================================")
    print("Azure AI Search index created successfully")
    print("========================================")
    print("Index name:", result.name)
    print("Endpoint:", SEARCH_ENDPOINT)
    print("Vector dimensions: 384")
    print()


if __name__ == "__main__":
    create_search_index()