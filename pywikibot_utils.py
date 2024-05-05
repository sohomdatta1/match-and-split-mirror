import pywikibot as pwb

def safe_put(page: pwb.Page, text: str, summary: str):
    print('TXT:', text)
    print('PAGE:', page.title())
    print('SUMMARY:', summary)
    page.text = text
    page.save(summary + ' (EXPERIMENTAL MATCH AND SPLIT EDIT, REVERT IF INCORRECT)', botflag=True)