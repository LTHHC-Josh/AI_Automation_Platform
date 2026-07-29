from src.ai.ocr.ocr_service import OCRService
from src.ai.llm.llm_service import LLMService


def main():

    print("=" * 50)
    print("Testing AI Platform")
    print("=" * 50)

    ocr = OCRService()
    llm = LLMService()

    text = ocr.extract_text("dummy.pdf")

    print("\nOCR Output:")
    print(text)

    classification = llm.classify(text)

    print("\nClassification:")
    print(classification)

    extracted = llm.extract(text, "")

    print("\nExtracted Data:")
    print(extracted)

    print("\nSUCCESS")


if __name__ == "__main__":
    main()