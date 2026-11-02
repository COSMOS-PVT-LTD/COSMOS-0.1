"""Bounded in-memory keyword navigation. Hits are not a scientific review."""
import hashlib
import json
import logging
from pathlib import Path
from pypdf import PdfReader

ROOT = Path('/Users/vaibhavkumarn/Desktop/COSMOS/materials ')
OUT = Path(__file__).parent/'PRIORITY_PAGE_MAP.json'
FILES = [
    'research papers/DESIGN AND CFD OPTIMIZATION OF METHANE REGENERATIVE COOLED ROCKET NOZZLES.pdf',
    'research papers/DESIGN OF A REGENERATIVELY COOLED BI-PROPELLANT ROCKET ENGINE USING ADDITIVE MANUFACTURING.pdf',
    'research papers/Designing+and+Testing+Liquid+Engines+for+Additive+Manufacturing.pdf',
    'research papers/cryogenic engine development at deflt university.pdf',
    'research papers/AIAA LRE Manufacturing Training Charts 7-30-2020.pdf',
    'research papers/liquid rocket engine self cooled .pdf',
    'research papers/Design of small liquid propellants rocket engine .pdf',
    'RESEARCH WORK/pintle injector design .pdf',
    'text books /MODERN_ENGINEERING_FOR_DESIGN_OF_LIQUID.pdf',
    'patents /MFS-TOPS-93.pdf',
    'patents /US8177489.pdf',
    'patents /US20200400102A1.pdf',
    'patents /US20220018314A1.pdf',
    'patents /US20220205410A1.pdf',
    'research papers/20110008540.pdf',
]
TERMS = ('cooling channel','manifold','pressure drop','roughness','methane','liquid oxygen','kerosene','ethanol','lattice','helical','powder','conclusion','seal','test firing','hot-fire','additive')

def main():
    logging.getLogger('pypdf').setLevel(logging.CRITICAL)
    rows = []
    for name in FILES:
        path = ROOT/name
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream,'sha256').hexdigest()
        reader = PdfReader(path, strict=False)
        pages = []
        for index,page in enumerate(reader.pages):
            text = page.extract_text() or ''
            compact = ' '.join(text.split())
            matches = [term for term in TERMS if term in compact.lower()]
            if matches:
                pages.append({'pdf_page':index+1,'terms':matches,'heading':compact[:110]})
        row = {'path':str(path),'relative_path':name,'sha256':digest,'page_count':len(reader.pages),
               'review_status':'KEYWORD_NAVIGATION_ONLY_NOT_COMPLETE_REVIEW','matching_pages':pages}
        rows.append(row)
        print(json.dumps({'file':name,'pages':len(reader.pages),'matches':len(pages)},ensure_ascii=False),flush=True)
    with OUT.open('x') as stream:
        json.dump({'schema':'cosmos.reference-keyword-navigation.v1','date':'2026-10-28','records':rows},stream,indent=2,ensure_ascii=False)
        stream.write('\n')

if __name__=='__main__':
    main()
