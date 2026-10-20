import pymupdf
from pdf_reading_order import native_page_content
from reader_core import clean_pdf_text
from pdf_reading_order import ordered_ocr_regions


def ocr_columns():
    parts, regions, position = [], [], 0
    for row in range(4):
        for x, label in [(40, 'Left'), (330, 'Right')]:
            text=f'{label} paragraph line number {row} has original words.'
            parts.append(text)
            regions.append({'start':position,'end':position+len(text),'rect':[x,80+row*20,x+210,95+row*20]})
            position+=len(text)+1
    return '\n'.join(parts), regions


def test_ocr_column_order_preserves_offsets_coordinates_and_idempotence():
    text,regions=ocr_columns()
    ordered,mapped,changed=ordered_ocr_regions(text,regions,600)
    assert changed
    assert ordered.index('Left paragraph line number 3') < ordered.index('Right paragraph line number 0')
    original={text[r['start']:r['end']]:r['rect'] for r in regions}
    assert {ordered[r['start']:r['end']]:r['rect'] for r in mapped}==original
    assert ordered_ocr_regions(ordered,mapped,600)==(ordered,mapped,True)


def test_ocr_order_does_not_drop_unmapped_text_or_reorder_short_cells():
    text,regions=ocr_columns()
    assert ordered_ocr_regions(text+'\nUnmapped caption',regions,600)==(text+'\nUnmapped caption',regions,False)
    assert ordered_ocr_regions(text,regions[:2],600)==(text,regions[:2],False)


def test_existing_ocr_cache_reorders_without_running_model(tmp_path,monkeypatch):
    import reader_core as core
    monkeypatch.setattr(core,'DATA',tmp_path/'state')
    path=tmp_path/'cached.pdf'
    with pymupdf.open() as pdf:
        pdf.new_page(width=600,height=800);pdf.save(path)
    text,regions=ocr_columns()
    cache=core.DATA/'ocr'/core.pdf_key(path)/'0.json'
    core.atomic_json(cache,{'text':text,'regions':regions})
    class NoModel:
        def recognize(self,pix):raise AssertionError('Existing coordinates must not rerun OCR')
    result=core.load_document(path,'auto',ocr=NoModel())
    assert result.pages[0].method=='OCR (cached) · two columns'
    assert result.text.index('Left paragraph line number 3') < result.text.index('Right paragraph line number 0')
    saved=cache.read_bytes()
    assert core.load_document(path,'auto',ocr=NoModel()).text==result.text
    assert cache.read_bytes()==saved
    assert core.load_document(path,'off',ocr=NoModel()).text==''


def paragraph(label):
    return (f'{label} begins this original sample paragraph.\n'
            'Students read each column from top to bottom.\n'
            'The next column follows after this paragraph ends.')


def test_two_column_prose_with_full_width_sections_and_word_order():
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=600,height=800)
        page.insert_text((40,35),'Original heading spanning the middle of the page',fontsize=16)
        # Deliberately reverse the PDF object's creation order.
        page.insert_text((325,90),paragraph('RIGHT'),fontsize=9)
        page.insert_text((40,90),paragraph('LEFT'),fontsize=9)
        page.insert_text((40,200),'Another section spanning the middle of the page',fontsize=16)
        page.insert_text((325,250),paragraph('SECOND RIGHT'),fontsize=9)
        page.insert_text((40,250),paragraph('SECOND LEFT'),fontsize=9)
        text,words,method=native_page_content(page)
        assert method=='Two-column prose'
        assert text.index('LEFT') < text.index('RIGHT') < text.index('Another section')
        assert text.index('Another section') < text.index('SECOND LEFT') < text.index('SECOND RIGHT')
        labels=[w[4] for w in words]
        assert labels.index('LEFT') < labels.index('RIGHT')
        assert clean_pdf_text(text).count('paragraph ends.')==4
        page.set_rotation(90)
        assert native_page_content(page)[0]==text


def test_short_table_cells_keep_row_order():
    with pymupdf.open() as pdf:
        page=pdf.new_page(width=600,height=800)
        for y,left,right in [(50,'Revenue','100'),(80,'Expenses','60'),(110,'Profit','40')]:
            page.insert_text((40,y),left)
            page.insert_text((330,y),right)
        text,_,method=native_page_content(page)
        assert method=='Page order'
        assert text.index('Revenue') < text.index('100') < text.index('Expenses')
