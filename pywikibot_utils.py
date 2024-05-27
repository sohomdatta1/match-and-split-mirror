import pywikibot as pwb
import os
from logger import Logger

def safe_put(page: pwb.Page, text: str, summary: str, logger: Logger):
    print('TITLE:', page.title())
    print('TEXT:', text)
    print('SUMMARY:', summary)
    logger.write('TITLE:', page.title())
    logger.write('TEXT:', text)
    logger.write('SUMMARY:', summary)
    if os.environ.get('NOTDEV'):
        page.text = text
        page.save(summary=str( summary ) + ' (automated match and split edit, revert if incorrect)', botflag=True)