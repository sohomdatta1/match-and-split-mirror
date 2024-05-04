import pywikibot.proofreadpage
from ws_namespaces import page as page_prefixes
import re
from celery import shared_task
from app import celery as celery_app
import align
import utils

import pywikibot

from pywikibot_utils import safe_put

E_ERROR = 1
E_OK = 0

# parameters from <pagelist />, used as a cache too.
pl_dict = {}

def rddm_name(year, volume):
    return "Revue des Deux Mondes - %s - tome %s.djvu" % (year, volume)

def get_pl(year, vol):
    global pl_dict
    key = year + "," + vol
    pl = pl_dict.get(key)
    if pl != None:
        return pl

    site = pywikibot.Site('fr', 'wikisource')
    indexpage = pywikibot.Page(site, "Livre:" + rddm_name(year, vol))
    text = indexpage.get()
    m = re.search("(?ms)<pagelist\s+(.*?)/>",text)
    if m:
        el = m.group(1).split()
        l = []
        for item in el:
            mm = re.match("(\d+)=(\d+)",item)
            if mm:
                l.append( (int(mm.group(1)), int(mm.group(2)) ) )

        # FIXME: default sort function should be enough
        l = sorted(l)
        pl_dict[key] = l
    else:
        pl_dict[key] = {}
    return pl_dict[key]

def offset_pagenum(pl, page):
    offset = 0
    for item in pl :
        if page >= item[1]:
            offset = item[0] - item[1]
    return offset + page

def repl(m):
    year = m.group(1)
    vol = m.group(2)
    page = int(m.group(3))
    pagenum = offset_pagenum(get_pl(year, vol), page)
    return "==[[Page:" + rddm_name(year, vol) + "/%d]]==\n" % pagenum


def ret_val(error, text):
    if error:
        print("Error: %d, %s" % (error, text))
    return  { 'error' : error, 'text' : text }

# FIXME, here and everywhere, can't we use mysite.lang and mysite.family.name
# to remove some parameters, does this work for old wikisource?
def do_match(mysite, maintitle, user, codelang):
    prefix = page_prefixes['wikisource'].get(codelang)
    if not prefix:
        return ret_val(E_ERROR, "no prefix")

    print("M&S:do_match() called with mysite = ", mysite, "maintitle = ", maintitle, "user = ", user, "codelang = ", codelang, "and prefix =", prefix)

    page = pywikibot.Page(mysite, maintitle)
    try:
        text = page.get()
    except:
        utils.print_traceback("failed to get page")
        return ret_val(E_ERROR, "failed to get page")

    if text.find("{{R2Mondes")!=-1:
        global pl_dict
        pl_dict = {}
        p0 = re.compile("\{\{R2Mondes\|(\d+)\|(\d+)\|(\d+)\}\}\s*\n")
        try:
            new_text = p0.sub(repl, text)
        except pywikibot.exceptions.NoPageError:
            return ret_val(E_ERROR, "Erreur : impossible de trouver l'index")
        p = re.compile('==\[\[Page:([^=]+)\]\]==\n')

        bl= p.split(new_text)
        for i in range(len(bl)//2):
            title  = bl[i*2+1]
            content = bl[i*2+2]
            filename, pagenum = title.split('/')
            if i == 0:
                cached_text = align.get_djvu(mysite, filename)
            else:
                cached_text = align.get_djvu(mysite, filename)
            if not cached_text:
                return ret_val(E_ERROR, "Erreur : fichier absent")
            if content.find("R2Mondes") != -1:
                p0 = re.compile("\{\{R2Mondes\|\d+\|\d+\|(\d+)\}\}\s*\n")
                bl0 = p0.split(text)
                title0 = bl0[i*2+1].encode("utf8")
                return ret_val(E_ERROR, "Erreur : Syntaxe 'R2Mondes' incorrecte, dans la page "+title0)
            r = align.match_page(content, cached_text[int(pagenum)-1])
            print("%s %s  : %f" % (filename, pagenum, r))
            if r < 0.1:
                return ret_val(E_ERROR, "Erreur : Le texte ne correspond pas, page %s" % pagenum)
        #the page is ok
        new_text = re.sub('<references[ ]*/>', '', new_text)
        new_text = re.sub('[ ]([,])', '\\1', new_text)
        new_text = re.sub('([^.])[ ]([,.])', '\\1\\2', new_text)
        new_text = re.sub('\.\.\.', '…', new_text)

        new_text = re.sub('([^ \s])([;:!?])', '\\1 \\2', new_text)
        new_text = re.sub('([«;:!?])([^ \s…])', '\\1 \\2', new_text)
        # separated from the previous regexp else "word!»" overlap
        new_text = re.sub('([^ \s])([»])', '\\1 \\2', new_text)

        # workaround some buggy text
        new_text = re.sub('([;:!?»]) \n', '\\1\n', new_text)
        new_text = re.sub('([;:!?»])\'\'([ \n])', '\\1\'\'\\2', new_text)
        # <&nbsp;><space>
        #new_text = re.sub('  ([;:!?»])', ' \\1', new_text)
        #new_text = re.sub(' ([;:!?»])', ' \\1', new_text)
        new_text = re.sub('([;:!?»]) <br />', '\\1<br />', new_text)
        new_text = new_text.replace('Page : ', 'Page:')
        new_text = new_text.replace('\n: ', '\n:')
        new_text = new_text.replace('\n:: ', '\n::')
        new_text = new_text.replace('\n::: ', '\n:::')
        new_text = new_text.replace('\n:::: ', '\n::::')
        new_text = new_text.replace('\n::::: ', '\n:::::')
        new_text = re.sub('1er (janvier|février|avril|mars|mai|juin|juillet|août|septembre|octobre|novembre|décembre)', '1{{er}} \\1', new_text)
        new_text = re.sub('([0-9])e ', '\\1{{e}} ', new_text)
        #text = re.sub('([;:!?»]) <div>\n', '\\1\n', new_text)

        # try to move the title inside the M&S
        match_title = re.search(u"{{[Jj]ournal[ ]*\|*(.*?)\|", new_text)
        if match_title:
            pos = re.search('==(.*?)==', new_text)
            if pos:
                new_text = new_text[0:pos.end(0)] + '\n{{c|' + match_title.group(1) + '|fs=140%}}\n\n\n' + new_text[pos.end(0):]

        safe_put(page,new_text,user+": match")
        split.delay(maintitle, codelang, user)
        return ret_val(E_ERROR, "ok : transfert en cours.")

    p = re.compile("==__MATCH__:\[\[" + prefix + ":(.*?)/(\d+)(\|step=(\d+))?\]\]==")
    m = re.search(p,text)
    if m:
        djvuname = m.group(1)
        number = m.group(2)
        pos = text.find(m.group(0))
        head = text[:pos]
        text = text[pos+len(m.group(0)):]
        if m.group(4):
            try:
                step = int(m.group(4))
            except:
                return ret_val(E_ERROR, "match tag invalid")
        else:
            step = 1
    else:
        return ret_val(E_ERROR, "match tag not found")

    pywikibot.output(djvuname + " " + number + " " + str(step))
    try:
        number = int(number)
    except:
        return ret_val(E_ERROR, "illformed __MATCH__: no page number ?")

    cached_text = align.get_djvu(mysite, djvuname)
    if not cached_text:
        return ret_val(E_ERROR, "unable to read djvu, if the File: exists, please retry")

    data = align.do_match(text, cached_text, djvuname, number, verbose = False, prefix = prefix, step = step)
    if not data['error']:
        safe_put(page, head + data['text'], user + ": match")
        data['text'] = ""

    return data

def do_split(mysite, rootname, user, codelang):
    prefix = page_prefixes['wikisource'].get(codelang)
    if not prefix:
        return ret_val(E_ERROR, "no Page: prefix")
    print("M&S:do_split() called with mysite = ", mysite, "rootname = ", rootname, "user = ", user, "codelang = ", codelang, "and prefix =", prefix)

    try:
        page = pywikibot.Page(mysite, rootname)
        text = page.get()
    except:
        return ret_val(E_ERROR, "unable to read page")

    p = re.compile('==\[\[(' + prefix + ':[^=]+)\]\]==\n')
    bl = p.split(text)
    titles = '\n'

    group = ""

    fromsection = ""
    tosection = ""
    fromsection_page = tosection_page = None

    for i in range(len(bl)//2):

        title  = bl[i*2+1]
        content = bl[i*2+2]

        #for illegalChar in ['#', '<', '>', '[', ']', '|', '{', '}', '\n', '\ufffd']:
        #    if illegalChar in title:
        #        title = title.replace(illegalChar,'_')

        #always NOPREFIX
        pagetitle = title

        content = content.rstrip("\n ")

        pl = pywikibot.proofreadpage.ProofreadPage(mysite, pagetitle)

        m =  re.match(prefix + ':(.*?)/(\d+)', pagetitle)
        if m:
            filename = m.group(1)
            pagenum = int(m.group(2))
            if not group:
                group = filename
                pfrom = pagenum
                pto = pfrom
            else:
                if filename != group:
                    titles = titles + "<pages index=\"%s\" from=%d to=%d />\n"%(group,pfrom,pto)
                    group = filename
                    pfrom = pagenum
                    pto = pfrom
                elif pagenum != pto + 1:
                    titles = titles + "<pages index=\"%s\" from=%d to=%d />\n"%(group,pfrom,pto)
                    group = filename
                    pfrom = pagenum
                    pto = pfrom
                else:
                    pto = pagenum
        else:
            if group:
                titles = titles + "<pages index=\"%s\" from=%d to=%d />\n"%(group,pfrom,pto)
                group = False

            titles = titles + "{{"+pagetitle+"}}\n"

        #prepend br
        if content and content[0]=='\n':
            content = '<nowiki />\n'+content

        if pl.exists():
            old_text = pl.get()
#            refs = pl.getReferences(onlyTemplateInclusion = True)
            refs = pl.getReferences(only_template_inclusion = True)
            numrefs = 0
            for ref in refs:
                numrefs += 1

            #first and last pages : check if they are transcluded
            if numrefs > 0 :
                m = re.match("<noinclude>(.*?)</noinclude>(.*)<noinclude>(.*?)</noinclude>",old_text,re.MULTILINE|re.DOTALL)
                if m and (i == 0 or i == (len(bl)//2 -1)):
                    print("creating sections")
                    old_text = m.group(2)
                    if i == 0:
                        first_part = old_text
                        second_part = content
                        fromsection="fromsection=s2 "
                        fromsection_page = ref
                    else:
                        first_part = content
                        second_part = old_text
                        tosection="tosection=s1 "
                        tosection_page = ref

                    content = "<noinclude>"+m.group(1)+"</noinclude><section begin=s1/>"+first_part+"<section end=s1/>\n----\n" \
                        + "<section begin=s2/>"+second_part+"<section end=s2/><noinclude>"+m.group(3)+"</noinclude>"
            else:
                m = re.match("<noinclude><pagequality level=\"1\" user=\"(.*?)\" />(.*?)</noinclude>(.*)<noinclude>(.*?)</noinclude>",
                             old_text,re.MULTILINE|re.DOTALL)
                if m :
                    print("ok, quality 1, first try")
                    content = "<noinclude><pagequality level=\"1\" user=\"" + m.group(1) + "\" />"+m.group(2)+"</noinclude>"+content+"<noinclude>"+m.group(4)+"</noinclude>"
                    m2 = re.match("<noinclude>\{\{PageQuality\|1\|(.*?)\}\}(.*?)</noinclude>(.*)<noinclude>(.*?)</noinclude>",
                                  old_text,re.MULTILINE|re.DOTALL)
                    if m2 :
                        # FIXME: shouldn't use an hardcoded name here
                        print("ok, quality 1, second try")
                        content = "<noinclude><pagequality level=\"1\" user=\"Phe-bot\" />"+m2.group(2)+"</noinclude>"+content+"<noinclude>"+m2.group(4)+"</noinclude>"

        else:
            header = '<noinclude><pagequality level="1" user="Phe-bot" /></noinclude>'
            footer = '<noinclude></noinclude>'
            content = header + content + footer
            

        do_put = True
        if pl.exists():
            if hasattr(pl, '_quality') and pl.quality_level != 1:
                print("quality != 1, not saved")
                do_put = False
            else:
                print("can't get quality level")
        if do_put:
            safe_put(pl,content,user+": split")

    if group:
        titles = titles + "<pages index=\"%s\" from=%d to=%d %s%s/>\n"%(group,pfrom,pto,fromsection,tosection)

    if fromsection and fromsection_page:
        rtext = fromsection_page.get()
        m = re.search("<pages index=\"(.*?)\" from=(.*?) to=(.*?) (fromsection=s2 |)/>",rtext)
        if m and m.group(1)==group:
            rtext = rtext.replace(m.group(0), m.group(0)[:-2]+"tosection=s1 />" )
            print("new rtext")
            safe_put(fromsection_page,rtext,user+": split")

    if tosection and tosection_page:
        rtext = tosection_page.get()
        m = re.search("<pages index=\"(.*?)\" from=(.*?) to=(.*?) (tosection=s1 |)/>",rtext)
        if m and m.group(1)==group:
            rtext = rtext.replace(m.group(0), m.group(0)[:-2]+"fromsection=s2 />" )
            print("new rtext")
            safe_put(tosection_page,rtext,user+": split")

    header = bl[0]
    safe_put(page,header+titles,user+": split")

    return ret_val(E_OK, "")



@shared_task
def match(lang, title, username) -> None:
    site = pywikibot.Site(lang, 'wikisource')
    do_match(site, title, username, lang)

@shared_task
def split(lang, title, username) -> None:
    site = pywikibot.Site(lang,'wikisource')
    do_split(site, title, username, lang)
