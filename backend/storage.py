import os
import json
import faiss


# =========================================================
# STORAGE DIRECTORY
# =========================================================

DATA_DIR = "data"

FAISS_FILE = os.path.join(
    DATA_DIR,
    "faiss.index"
)

CHUNKS_FILE = os.path.join(
    DATA_DIR,
    "chunks.json"
)

DOCUMENTS_FILE = os.path.join(
    DATA_DIR,
    "documents.json"
)

HASHES_FILE = os.path.join(
    DATA_DIR,
    "hashes.json"
)


# =========================================================
# CREATE DATA DIRECTORY
# =========================================================

def create_data_directory():

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )


# =========================================================
# SAVE RAG STATE
# =========================================================

def save_rag_state(
    index,
    all_chunks,
    documents,
    document_hashes
):

    create_data_directory()


    # -----------------------------------------------------
    # Save FAISS index
    # -----------------------------------------------------

    if index is not None:

        faiss.write_index(
            index,
            FAISS_FILE
        )


    # -----------------------------------------------------
    # Save chunks
    # -----------------------------------------------------

    with open(
        CHUNKS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2
        )


    # -----------------------------------------------------
    # Save document information
    # -----------------------------------------------------

    with open(
        DOCUMENTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            documents,
            file,
            ensure_ascii=False,
            indent=2
        )


    # -----------------------------------------------------
    # Save SHA-256 information
    # -----------------------------------------------------

    hash_data = {}

    for file_hash, information in document_hashes.items():

        hash_data[file_hash] = {

            "document_id":
                information["document_id"],

            "filename":
                information["filename"]
        }


    with open(
        HASHES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            hash_data,
            file,
            ensure_ascii=False,
            indent=2
        )


    print(
        "RAG state saved successfully."
    )


# =========================================================
# LOAD RAG STATE
# =========================================================

def load_rag_state():

    create_data_directory()


    loaded_index = None
    loaded_chunks = []
    loaded_documents = {}
    loaded_hashes = {}


    # -----------------------------------------------------
    # Load FAISS index
    # -----------------------------------------------------

    if os.path.exists(FAISS_FILE):

        loaded_index = faiss.read_index(
            FAISS_FILE
        )

        print(
            "FAISS index loaded."
        )

        print(
            "Vectors loaded:",
            loaded_index.ntotal
        )


    # -----------------------------------------------------
    # Load chunks
    # -----------------------------------------------------

    if os.path.exists(CHUNKS_FILE):

        with open(
            CHUNKS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            loaded_chunks = json.load(
                file
            )

        print(
            "Chunks loaded:",
            len(loaded_chunks)
        )


    # -----------------------------------------------------
    # Load documents
    # -----------------------------------------------------

    if os.path.exists(DOCUMENTS_FILE):

        with open(
            DOCUMENTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            loaded_documents = json.load(
                file
            )

        print(
            "Documents loaded:",
            len(loaded_documents)
        )


    # -----------------------------------------------------
    # Load SHA-256 hashes
    # -----------------------------------------------------

    if os.path.exists(HASHES_FILE):

        with open(
            HASHES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            loaded_hashes = json.load(
                file
            )

        print(
            "Document hashes loaded:",
            len(loaded_hashes)
        )


    return (
        loaded_index,
        loaded_chunks,
        loaded_documents,
        loaded_hashes
    )