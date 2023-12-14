import os
from django.conf import settings
import fitz
import pathlib

def generate_certificate(extra_data, lang='en'):
    """ Uses
    data= {
        '[certificate-no]': '45454353',
        '[certificate-url]': 'url -dfg ',
        '[full-name]': 'Manoj Datt',
        '[course-title]': 'test course',
        '[instructor-signature]': 'Manoj',
        '[instructor-name]': 'Manoj',
        '[complete-date]': '2023/02/22',
    }
    from apps.certgen import *
    generate_certificate(data)

    """
    EN_CERT_FIELDS = settings.EN_CERT_FIELDS
    docfile_path = os.path.join(settings.STATIC_ROOT, 'pdfs', f'certificate-{lang}.pdf')
    certfile_file = os.path.join(settings.STATIC_ROOT, 'pdfs', f"{extra_data.get('[course-title]')}-{lang}cert.pdf")
    if os.path.exists(certfile_file):
        os.remove(certfile_file)
    pathlib.Path(certfile_file)
    doc = fitz.open(docfile_path)
    fonts = {
        '[certificate-no]': {
            "size": 10,
            "fontname": "LiberationSerif-Regular",
            "fontfile": "LiberationSerif-Regular.ttf"
        },
        '[certificate-url]': {
            "size": 10,
            "fontname": "LiberationSerif-Regular",
            "fontfile": "LiberationSerif-Regular.ttf"
        },
        '[full-name]': {
            "size": 60,
            "fontname": "LiberationSerif-Regular",
            "fontfile": "LiberationSerif-Regular.ttf"
        },
        '[course-title]': {
            "size": 16,
            "fontname": "LiberationSerif-Regular",
            "fontfile": "LiberationSerif-Regular.ttf"
        },
        '[instructor-signature]': {
            "size": 20,
            "fontname": "Aerotis",
            "fontfile": "Aerotis.otf"
        },
        '[instructor-name]': {
            "size": 10,
            "fontname": "LiberationSerif-Regular",
            "fontfile": "LiberationSerif-Regular.ttf"
        },
        '[complete-date]': {
            "size": 10,
            "fontname": "LiberationSerif-Regular",
            "fontfile": "LiberationSerif-Regular.ttf"
        },
    }
    cert_page = doc[0]
    for field in EN_CERT_FIELDS:
        # search_results = cert_page.search_for(field)
        result = fitz.Rect(*EN_CERT_FIELDS.get(field))
        text = extra_data.get(field)
        font = fonts.get(field)
        if field != '[instructor-signature]':
            annot = cert_page.add_redact_annot(result, 
                                            text, 
                                            fontsize = font.get('size'), 
                                            fill=False, 
                                            align=fitz.TEXT_ALIGN_LEFT,
                                            cross_out=False)
        else:
            annot = cert_page.add_redact_annot(result, 
                                            fontsize = font.get('size'), 
                                            fill=False, 
                                            align=fitz.TEXT_ALIGN_LEFT,
                                            cross_out=False)
        cert_page.apply_redactions()
        annot.set_opacity(0)
        annot.update()
        
        if field == '[instructor-signature]':
            # For signature use different 
            point = fitz.Point(result.x0, result.y0)
            cert_page.insert_text(point,  # anywhere, but outside all redaction rectangles
                text,  # some non-empty string
                fontsize = font.get('size'),
                fontname=font.get('fontname'),  # new, unused reference name
                fontfile=os.path.join(settings.STATIC_ROOT, 'fonts', font.get('fontfile')),  # desired font file
                render_mode=0,  # makes the text invisible
            )


    doc.save(certfile_file, garbage=4, deflate=True, clean=True)
    return certfile_file
