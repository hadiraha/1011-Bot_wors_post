from docx import Document
import os

class DocxParser:
    def __init__(self, file_path):
        try:
            self.file_path = file_path
            self.document = Document(file_path)
            print(f"Successfully loaded the document: {file_path}")
        except Exception as e:
            print(f"Error loading document: {e}")
            raise

    def extract_headings_content_with_images(self):
        """
        Extracts text and images under each Heading 4 section.
        Includes the latest Heading 1 above each Heading 4 as a prefix.
        Stops collecting if a new Heading 1, Heading 2, or Heading 3 is encountered.
        Returns a list of dictionaries containing enriched text and all image file paths.
        """
        extracted_data = []
        current_content = None
        current_images = []
        current_heading_1 = ""  # Track the latest Heading 1
        collecting = False  # Flag to indicate we are collecting content under a Heading 4
        custom_heading_text = "خبر!"  # Custom fallback text for empty headings
        images_output_dir = "extracted_images"

        # Ensure the output directory exists
        os.makedirs(images_output_dir, exist_ok=True)

        image_counter = 0
        for para in self.document.paragraphs:
            if para.style.name == 'Heading 1':
                # Update the current Heading 1
                current_heading_1 = para.text.strip() if para.text.strip() else ""

                # If we are collecting and encounter a new Heading 1, save the current section
                if collecting and (current_content or current_images):
                    enriched_text = f"{current_heading_1}\n\n{current_content.strip() if current_content else custom_heading_text}"
                    extracted_data.append({
                        "text": enriched_text.strip(),
                        "images": current_images
                    })
                collecting = False  # Stop collecting content
                current_content = None
                current_images = []

            elif para.style.name == 'Heading 4':
                # Save the current section before moving to the next
                if collecting and (current_content or current_images):
                    enriched_text = f"#{current_heading_1}\n\n{current_content.strip() if current_content else custom_heading_text}"
                    extracted_data.append({
                        "text": enriched_text.strip(),
                        "images": current_images
                    })

                # Start a new section
                current_content = para.text.strip() if para.text.strip() else custom_heading_text
                current_images = []
                collecting = True

            elif collecting:
                # Collect text content
                if para.text.strip():
                    current_content += "\n" + para.text.strip()

                # Check for images in the paragraph's runs
                for run in para.runs:
                    if run.element.xpath(".//a:blip"):
                        for blip in run.element.xpath(".//a:blip"):
                            embed_rel_id = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                            image_part = self.document.part.related_parts[embed_rel_id]
                            # Save image
                            image_ext = image_part.content_type.split("/")[-1]  # Get file extension (e.g., jpg)
                            image_path = os.path.join(images_output_dir, f"image_{image_counter}.{image_ext}")
                            with open(image_path, "wb") as img_file:
                                img_file.write(image_part.blob)
                            current_images.append(image_path)
                            image_counter += 1

        # Add the last section
        if collecting and (current_content or current_images):
            enriched_text = f"{current_heading_1}\n\n{current_content.strip() if current_content else custom_heading_text}"
            extracted_data.append({
                "text": enriched_text.strip(),
                "images": current_images
            })

        return extracted_data