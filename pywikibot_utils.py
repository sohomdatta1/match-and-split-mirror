import pywikibot as pwb
import os

def safe_put(page: pwb.Page, text: str, summary: str):
    print('TITLE:', page.title())
    print('TEXT:', text)
    print('SUMMARY:', summary)
    if os.environ.get('NOTDEV'):
        page.text = text
        page.save(summary=str( summary ) + ' (EXPERIMENTAL MATCH AND SPLIT EDIT, REVERT IF INCORRECT)', botflag=True)