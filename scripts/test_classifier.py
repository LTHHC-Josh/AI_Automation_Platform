from src.ai.classifier import DocumentClassifier

classifier = DocumentClassifier()

document = classifier.classify("sample.pdf")

print()

print("File:")
print(document.file_path)

print()

print("Raw Text:")
print(repr(document.raw_text))

print()

print("Document Type:")
print(document.document_type)

print()

print("Confidence:")
print(document.confidence)

print()

print("Extracted Data:")
print(document.extracted_data)