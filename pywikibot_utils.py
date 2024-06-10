import pywikibot as pwb
import os
from logger import Logger

def safe_put(page: pwb.Page, text: str, summary: str, logger: Logger):
    logger.log('TITLE:'+ page.title())
    logger.log('TEXT:' + text)
    logger.log('SUMMARY:'+ summary)
    if os.environ.get('NOTDEV'):
        page.text = text
        page.save(summary=str( summary ) + ' (automated match and split edit, revert if incorrect)', botflag=True)