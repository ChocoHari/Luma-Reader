"""Package only the explicit original-content marketing deliverables."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DOCUMENTS=['README.md','PAGE_COPY.md','FAQ.md','LAUNCH_COPY.md','DEMO_SCRIPT.md','PAYOUT_RESEARCH.md','demo-captions.srt','demo/study-notes.md']
ASSETS=['pdf-original-page.png','editor-baby-blue-light.png','editor-lavender-dark.png','editor-coral-light.png','editor-soft-brown-dark.png',
        'hero-1600x900.png','social-1200x630.png','book-wave-blue.svg','book-wave-blue.png','book-wave-lavender.svg','book-wave-lavender.png','luma-captioned-tour.mp4']


def main():
    folder=ROOT/'marketing';files=DOCUMENTS+['assets/'+name for name in ASSETS]
    records=[]
    for name in sorted(files):
        data=(folder/name).read_bytes()
        if name.endswith(('.md','.srt','.svg')) and any(token in data for token in (b'C:\\Users\\',b'D:\\U\\',b'file:///')):
            raise ValueError(f'Local path in marketing file: {name}')
        records.append({'file':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    manifest={'status':'local development-preview drafts; not published','original_demo_content':True,
              'payout_eligibility_confirmed':False,'files':records}
    (folder/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    target=ROOT/'dist/Luma-marketing-preview.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files+['PACKAGE_MANIFEST.json']):
            info=zipfile.ZipInfo('Luma-marketing-preview/'+name,(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,(folder/name).read_bytes())
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:raise ValueError('Marketing archive integrity failed')
    sha=hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT/'dist/Luma-marketing-preview.sha256').write_text(f'{sha}  {target.name}\n')
    print(json.dumps({'deliverables':len(records),'bytes':target.stat().st_size,'sha256':sha,'archive_integrity':'passed'}))


if __name__=='__main__':main()
