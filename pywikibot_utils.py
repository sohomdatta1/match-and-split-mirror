import pywikibot as pwb

def safe_put(page: pwb.Page, text: str, summary: str):
    page.text = text
    page.save(summary, botflag=True)

