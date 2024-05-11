import pywikibot as pwb

def safe_put(page: pwb.Page, text: str, summary: str):
    print('TITLE:', page.title())
    print('TEXT:', text)
    print('SUMMARY:', summary)
    page.text = text
    page.save(summary=str( summary ) + ' (EXPERIMENTAL MATCH AND SPLIT EDIT, REVERT IF INCORRECT)', botflag=True)