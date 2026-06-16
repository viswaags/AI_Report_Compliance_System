import fitz


class LayoutExtractor:

    @staticmethod
    def extract_pdf_layout(doc):

        pages = []

        for page_index in range(len(doc)):

            page = doc[page_index]

            page_data = {

                "page_number": page_index + 1,

                "width": page.rect.width,

                "height": page.rect.height,

                "text_blocks": [],

                "images": []
            }

            #
            # Text Blocks
            #

            try:

                blocks = page.get_text(
                    "blocks"
                )

                for block in blocks:

                    page_data[
                        "text_blocks"
                    ].append({

                        "x0": block[0],
                        "y0": block[1],
                        "x1": block[2],
                        "y1": block[3],

                        "text": block[4]
                    })

            except Exception:
                pass

            #
            # Images
            #

            try:

                image_list = page.get_images(
                    full=True
                )

                for img in image_list:

                    page_data[
                        "images"
                    ].append({

                        "xref": img[0]
                    })

            except Exception:
                pass

            pages.append(
                page_data
            )

        return pages