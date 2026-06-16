import fitz

from docx import Document

from app.services.layout_extractor import (
    LayoutExtractor
)


class DocumentParser:

    @staticmethod
    def parse_pdf(file_path: str):

        doc = fitz.open(file_path)

        text = ""

        image_count = 0

        for page in doc:

            text += page.get_text()

            try:

                image_count += len(
                    page.get_images(
                        full=True
                    )
                )

            except Exception:
                pass

        layout = (
            LayoutExtractor
            .extract_pdf_layout(doc)
        )

        return {

            "file_type": "pdf",

            "page_count": len(doc),

            "image_count": image_count,

            "layout": layout,

            "text": text
        }

    @staticmethod
    def parse_docx(file_path: str):

        doc = Document(file_path)

        text = "\n".join(
            para.text
            for para in doc.paragraphs
        )

        try:

            image_count = len(
                doc.inline_shapes
            )

        except Exception:

            image_count = 0

        return {

            "file_type": "docx",

            "paragraph_count":
                len(doc.paragraphs),

            "image_count":
                image_count,

            "layout":
                [],

            "text":
                text
        }