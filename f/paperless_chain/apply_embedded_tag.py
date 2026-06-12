from f.paperless_chain.shared.paperless_client import add_document_tags
from f.paperless_chain.shared.text_utils import EMBEDDED_TAG


def main(doc_id: int) -> dict:
    tag_result = add_document_tags(doc_id, [EMBEDDED_TAG])
    return {
        "doc_id": doc_id,
        "applied_tag": EMBEDDED_TAG,
        "tag_result": tag_result,
    }
