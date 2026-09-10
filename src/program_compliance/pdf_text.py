"""Bounded public PDF extraction subprocess; no OCR or DP state access."""
import io
import sys
from pypdf import PdfReader

def main():
    raw=sys.stdin.buffer.read(8_000_001)
    if len(raw)>8_000_000: return 1
    try:
        reader=PdfReader(io.BytesIO(raw))
        if reader.is_encrypted or len(reader.pages)>200: return 1
        parts=[];size=0
        for i,page in enumerate(reader.pages):
            text=page.extract_text() or ''
            size+=len(text)
            if size>1_000_000: return 1
            parts.append('## Page '+str(i+1)+'\n'+text)
        sys.stdout.buffer.write('\n'.join(parts).encode('utf-8'))
        return 0
    except Exception: return 1

if __name__=='__main__': raise SystemExit(main())
