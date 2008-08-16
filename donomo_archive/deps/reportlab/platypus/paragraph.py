#Copyright ReportLab Europe Ltd. 2000-2004
#see license.txt for license details
#history http://www.reportlab.co.uk/cgi-bin/viewcvs.cgi/public/reportlab/trunk/reportlab/platypus/paragraph.py
__version__=''' $Id: paragraph.py 3076 2007-05-03 19:43:03Z andy $ '''
from string import join, whitespace, find
from operator import truth
from types import StringType, ListType
from reportlab.pdfbase.pdfmetrics import stringWidth, getFont
from reportlab.platypus.paraparser import ParaParser
from reportlab.platypus.flowables import Flowable
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.utils import _className
from reportlab.lib.textsplit import wordSplit
from copy import deepcopy
from reportlab.lib.abag import ABag
import re

#on UTF8 branch, split and strip must be unicode-safe!
def split(text, delim=' '):
    if type(text) is str: text = text.decode('utf8')
    if type(delim) is str: delim = delim.decode('utf8')
    return [uword.encode('utf8') for uword in text.split(delim)]

def strip(text):
    if type(text) is str: text = text.decode('utf8')
    return text.strip().encode('utf8')

class ParaLines(ABag):
    """
    class ParaLines contains the broken into lines representation of Paragraphs
        kind=0  Simple
        fontName, fontSize, textColor apply to whole Paragraph
        lines   [(extraSpace1,words1),....,(extraspaceN,wordsN)]

        kind==1 Complex
        lines   [FragLine1,...,FragLineN]
    """

class FragLine(ABag):
    """class FragLine contains a styled line (ie a line with more than one style)

    extraSpace  unused space for justification only
    wordCount   1+spaces in line for justification purposes
    words       [ParaFrags] style text lumps to be concatenated together
    fontSize    maximum fontSize seen on the line; not used at present,
                but could be used for line spacing.
    """

#our one and only parser
# XXXXX if the parser has any internal state using only one is probably a BAD idea!
_parser=ParaParser()

def _lineClean(L):
    return join(filter(truth,split(strip(L))))

def cleanBlockQuotedText(text,joiner=' '):
    """This is an internal utility which takes triple-
    quoted text form within the document and returns
    (hopefully) the paragraph the user intended originally."""
    L=filter(truth,map(_lineClean, split(text, '\n')))
    return join(L, joiner)

def setXPos(tx,dx):
    if dx>1e-6 or dx<-1e-6:
        tx.setXPos(dx)

def _leftDrawParaLine( tx, offset, extraspace, words, last=0):
    setXPos(tx,offset)
    tx._textOut(join(words),1)
    setXPos(tx,-offset)
    return offset

def _centerDrawParaLine( tx, offset, extraspace, words, last=0):
    m = offset + 0.5 * extraspace
    setXPos(tx,m)
    tx._textOut(join(words),1)
    setXPos(tx,-m)
    return m

def _rightDrawParaLine( tx, offset, extraspace, words, last=0):
    m = offset + extraspace
    setXPos(tx,m)
    tx._textOut(join(words),1)
    setXPos(tx,-m)
    return m

def _justifyDrawParaLine( tx, offset, extraspace, words, last=0):
    setXPos(tx,offset)
    text  = join(words)
    if last:
        #last one, left align
        tx._textOut(text,1)
    else:
        nSpaces = len(words)-1
        if nSpaces:
            tx.setWordSpace(extraspace / float(nSpaces))
            tx._textOut(text,1)
            tx.setWordSpace(0)
        else:
            tx._textOut(text,1)
    setXPos(tx,-offset)
    return offset

def _putFragLine(tx,words):
    cur_x = 0
    xtraState = tx.XtraState
    ws = getattr(tx,'_wordSpace',0)
    nSpaces = 0
    for f in words:
        if hasattr(f,'cbDefn'):
            name = f.cbDefn.name
            kind = f.cbDefn.kind
            if kind=='anchor':
                tx._canvas.bookmarkHorizontal(name,cur_x,tx._y+tx._leading)
            else:
                func = getattr(tx._canvas,name,None)
                if not func:
                    raise AttributeError, "Missing %s callback attribute '%s'" % (kind,name)
                func(tx._canvas,kind,f.cbDefn.label)
            if f is words[-1]:
                if not tx._fontname:
                    tx.setFont(xtraState.style.fontName,xtraState.style.fontSize)
                    tx._textOut('',1)
        else:
            cur_x_s = cur_x + nSpaces*ws
            if (tx._fontname,tx._fontsize)!=(f.fontName,f.fontSize):
                tx._setFont(f.fontName, f.fontSize)
            if xtraState.textColor!=f.textColor:
                xtraState.textColor = f.textColor
                tx.setFillColor(f.textColor)
            if xtraState.rise!=f.rise:
                xtraState.rise=f.rise
                tx.setRise(f.rise)
            text = f.text
            tx._textOut(text,f is words[-1])    # cheap textOut
            if not xtraState.underline and f.underline:
                xtraState.underline = 1
                xtraState.underline_x = cur_x_s
                xtraState.underlineColor = f.textColor
            elif xtraState.underline:
                if not f.underline:
                    xtraState.underline = 0
                    xtraState.underlines.append( (xtraState.underline_x, cur_x_s, xtraState.underlineColor) )
                    xtraState.underlineColor = None
                elif xtraState.textColor!=xtraState.underlineColor:
                    xtraState.underlines.append( (xtraState.underline_x, cur_x_s, xtraState.underlineColor) )
                    xtraState.underlineColor = xtraState.textColor
                    xtraState.underline_x = cur_x_s
            if not xtraState.strike and f.strike:
                xtraState.strike = 1
                xtraState.strike_x = cur_x_s
                xtraState.strikeColor = f.textColor
            elif xtraState.strike:
                if not f.strike:
                    xtraState.strike = 0
                    xtraState.strikes.append( (xtraState.strike_x, cur_x_s, xtraState.strikeColor) )
                    xtraState.strikeColor = None
                elif xtraState.textColor!=xtraState.strikeColor:
                    xtraState.strikes.append( (xtraState.strike_x, cur_x_s, xtraState.strikeColor) )
                    xtraState.strikeColor = xtraState.textColor
                    xtraState.strike_x = cur_x_s
            if not xtraState.link and f.link:
                xtraState.link = f.link
                xtraState.link_x = cur_x_s
            elif xtraState.link and f.link is not xtraState.link:
                    xtraState.links.append( (xtraState.link_x, cur_x_s, xtraState.link) )
                    xtraState.link = None
            txtlen = tx._canvas.stringWidth(text, tx._fontname, tx._fontsize)
            cur_x += txtlen
            nSpaces += text.count(' ')
    cur_x_s = cur_x+(nSpaces-1)*ws
    if xtraState.underline:
        xtraState.underlines.append( (xtraState.underline_x, cur_x_s, xtraState.underlineColor) )
    if xtraState.strike:
        xtraState.strikes.append( (xtraState.strike_x, cur_x_s, xtraState.strikeColor) )
    if xtraState.link:
        xtraState.links.append( (xtraState.link_x, cur_x_s, xtraState.link) )

def _leftDrawParaLineX( tx, offset, line, last=0):
    setXPos(tx,offset)
    _putFragLine(tx, line.words)
    setXPos(tx,-offset)
    return offset

def _centerDrawParaLineX( tx, offset, line, last=0):
    m = offset+0.5*line.extraSpace
    setXPos(tx,m)
    _putFragLine(tx, line.words)
    setXPos(tx,-m)
    return m

def _rightDrawParaLineX( tx, offset, line, last=0):
    m = offset+line.extraSpace
    setXPos(tx,m)
    _putFragLine(tx, line.words)
    setXPos(tx,-m)
    return m

def _justifyDrawParaLineX( tx, offset, line, last=0):
    setXPos(tx,offset)
    if last:
        #last one, left align
        _putFragLine(tx, line.words)
    else:
        nSpaces = line.wordCount - 1
        if nSpaces:
            tx.setWordSpace(line.extraSpace / float(nSpaces))
            _putFragLine(tx, line.words)
            tx.setWordSpace(0)
        else:
            _putFragLine(tx, line.words)
    setXPos(tx,-offset)
    return offset

try:
    from _rl_accel import _sameFrag
except ImportError:
    try:
        from reportlab.lib._rl_accel import _sameFrag
    except ImportError:
        #if you modify this you need to modify _rl_accel RGB
        def _sameFrag(f,g):
            'returns 1 if two ParaFrags map out the same'
            if (hasattr(f,'cbDefn') or hasattr(g,'cbDefn')
                    or hasattr(f,'lineBreak') or hasattr(g,'lineBreak')): return 0
            for a in ('fontName', 'fontSize', 'textColor', 'rise', 'underline', 'strike', 'link'):
                if getattr(f,a)!=getattr(g,a): return 0
            return 1

def _getFragWords(frags):
    ''' given a Parafrag list return a list of fragwords
        [[size, (f00,w00), ..., (f0n,w0n)],....,[size, (fm0,wm0), ..., (f0n,wmn)]]
        each pair f,w represents a style and some string
        each sublist represents a word
    '''
    R = []
    W = []
    n = 0
    for f in frags:
        text = f.text
        #del f.text # we can't do this until we sort out splitting
                    # of paragraphs
        if text!='':
            S = split(text)
            if S==[]: S = ['']
            if W!=[] and text[0] in whitespace:
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0

            for w in S[:-1]:
                W.append((f,w))
                n += stringWidth(w, f.fontName, f.fontSize)
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0

            w = S[-1]
            W.append((f,w))
            n += stringWidth(w, f.fontName, f.fontSize)
            if text[-1] in whitespace:
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0
        elif hasattr(f,'cbDefn'):
            W.append((f,''))
        elif hasattr(f, 'lineBreak'):
            #pass the frag through.  The line breaker will scan for it.
            if W!=[]:
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0
            R.append([0,(f,'')])

    if W!=[]:
        W.insert(0,n)
        R.append(W)

    return R

def _split_blParaSimple(blPara,start,stop):
    f = blPara.clone()
    for a in ('lines', 'kind', 'text'):
        if hasattr(f,a): delattr(f,a)

    f.words = []
    for l in blPara.lines[start:stop]:
        for w in l[1]:
            f.words.append(w)
    return [f]

def _split_blParaHard(blPara,start,stop):
    f = []
    lines = blPara.lines[start:stop]
    for l in lines:
        for w in l.words:
            f.append(w)
        if l is not lines[-1]:
            i = len(f)-1
            while hasattr(f[i],'cbDefn'): i = i-1
            g = f[i]
            if g.text and g.text[-1]!=' ': g.text += ' '
    return f

def _drawBullet(canvas, offset, cur_y, bulletText, style):
    '''draw a bullet text could be a simple string or a frag list'''
    tx2 = canvas.beginText(style.bulletIndent, cur_y)
    tx2.setFont(style.bulletFontName, style.bulletFontSize)
    tx2.setFillColor(hasattr(style,'bulletColor') and style.bulletColor or style.textColor)
    if isinstance(bulletText,basestring):
        tx2.textOut(bulletText)
    else:
        for f in bulletText:
            tx2.setFont(f.fontName, f.fontSize)
            tx2.setFillColor(f.textColor)
            tx2.textOut(f.text)

    canvas.drawText(tx2)
    #AR making definition lists a bit less ugly
    #bulletEnd = tx2.getX()
    bulletEnd = tx2.getX() + style.bulletFontSize * 0.6
    offset = max(offset,bulletEnd - style.leftIndent)
    return offset

def _handleBulletWidth(bulletText,style,maxWidths):
    '''work out bullet width and adjust maxWidths[0] if neccessary
    '''
    if bulletText!=None:
        if isinstance(bulletText,basestring):
            bulletWidth = stringWidth( bulletText, style.bulletFontName, style.bulletFontSize)
        else:
            #it's a list of fragments
            bulletWidth = 0
            for f in bulletText:
                bulletWidth = bulletWidth + stringWidth(f.text, f.fontName, f.fontSize)
        bulletRight = style.bulletIndent + bulletWidth + 0.6 * style.bulletFontSize
        indent = style.leftIndent+style.firstLineIndent
        if bulletRight > indent:
            #..then it overruns, and we have less space available on line 1
            maxWidths[0] = maxWidths[0] - (bulletRight - indent)

def splitLines0(frags,widths):
    '''
    given a list of ParaFrags we return a list of ParaLines

    each ParaLine has
    1)  ExtraSpace
    2)  blankCount
    3)  [textDefns....]
        each text definition is a (ParaFrag, start, limit) triplet
    '''
    #initialise the algorithm
    lines   = []
    lineNum = 0
    maxW    = widths[lineNum]
    i       = -1
    l       = len(frags)
    lim     = start = 0
    while 1:
        #find a non whitespace character
        while i<l:
            while start<lim and text[start]==' ': start += 1
            if start==lim:
                i += 1
                if i==l: break
                start = 0
                f = frags[i]
                text = f.text
                lim = len(text)
            else:
                break   # we found one

        if start==lim: break    #if we didn't find one we are done

        #start of a line
        g       = (None,None,None)
        line    = []
        cLen    = 0
        nSpaces = 0
        while cLen<maxW:
            j = find(text,' ',start)
            if j<0: j==lim
            w = stringWidth(text[start:j],f.fontName,f.fontSize)
            cLen += w
            if cLen>maxW and line!=[]:
                cLen = cLen-w
                #this is the end of the line
                while g.text[lim]==' ':
                    lim = lim - 1
                    nSpaces = nSpaces-1
                break
            if j<0: j = lim
            if g[0] is f: g[2] = j  #extend
            else:
                g = (f,start,j)
                line.append(g)
            if j==lim:
                i += 1

def _do_under_line(i, t_off, ws, tx, lm=-0.125):
    y = tx.XtraState.cur_y - i*tx.XtraState.style.leading + lm*tx.XtraState.f.fontSize
    textlen = tx._canvas.stringWidth(join(tx.XtraState.lines[i][1]), tx._fontname, tx._fontsize)
    tx._canvas.line(t_off, y, t_off+textlen+ws, y)

_scheme_re = re.compile('^[a-zA-Z][-+a-zA-Z0-9]+$')
def _doLink(tx,link,rect):
    if type(link) is unicode:
        link = unicode.encode('utf8')
    parts = link.split(':',1)
    scheme = len(parts)==2 and parts[0].lower() or ''
    if _scheme_re.match(scheme) and scheme!='document':
        kind=scheme.lower()=='pdf' and 'GoToR' or 'URI'
        if kind=='GoToR': link = parts[1]
        tx._canvas.linkURL(link, rect, relative=1, kind=kind)
    else:
        if link[0]=='#':
            link = link[1:]
            scheme=''
        tx._canvas.linkRect("", scheme!='document' and link or parts[1], rect, relative=1)

def _do_link_line(i, t_off, ws, tx):
    xs = tx.XtraState
    leading = xs.style.leading
    y = xs.cur_y - i*leading - xs.f.fontSize/8.0 # 8.0 factor copied from para.py
    text = join(xs.lines[i][1])
    textlen = tx._canvas.stringWidth(text, tx._fontname, tx._fontsize)
    _doLink(tx, xs.link, (t_off, y, t_off+textlen+ws, y+leading))

def _do_post_text(i, t_off, tx):
    xs = tx.XtraState
    leading = xs.style.leading
    ff = 0.125*xs.f.fontSize
    y0 = xs.cur_y - i*leading
    y = y0 - ff
    ulc = None
    for x1,x2,c in xs.underlines:
        if c!=ulc:
            tx._canvas.setStrokeColor(c)
            ulc = c
        tx._canvas.line(t_off+x1, y, t_off+x2, y)
    xs.underlines = []
    xs.underline=0
    xs.underlineColor=None

    ys = y0 + 2*ff
    ulc = None
    for x1,x2,c in xs.strikes:
        if c!=ulc:
            tx._canvas.setStrokeColor(c)
            ulc = c
        tx._canvas.line(t_off+x1, ys, t_off+x2, ys)
    xs.strikes = []
    xs.strike=0
    xs.strikeColor=None

    yl = y + leading
    for x1,x2,link in xs.links:
        tx._canvas.line(t_off+x1, y, t_off+x2, y)
        _doLink(tx, link, (t_off+x1, y, t_off+x2, yl))
    xs.links = []
    xs.link=None

class Paragraph(Flowable):
    """ Paragraph(text, style, bulletText=None, caseSensitive=1)
        text a string of stuff to go into the paragraph.
        style is a style definition as in reportlab.lib.styles.
        bulletText is an optional bullet defintion.
        caseSensitive set this to 0 if you want the markup tags and their attributes to be case-insensitive.

        This class is a flowable that can format a block of text
        into a paragraph with a given style.

        The paragraph Text can contain XML-like markup including the tags:
        <b> ... </b> - bold
        <i> ... </i> - italics
        <u> ... </u> - underline
        <strike> ... </strike> - strike through
        <super> ... </super> - superscript
        <sub> ... </sub> - subscript
        <font name=fontfamily/fontname color=colorname size=float>
        <onDraw name=callable label="a label">
        <link>link text</link>
            attributes of links 
                size/fontSize=num
                name/face/fontName=name
                fg/textColor/color=color
                backcolor/backColor/bgcolor=color
                dest/destination/target/href/link=target
        <a>anchor text</a>
            attributes of anchors 
                fontSize=num
                fontName=name
                fg/textColor/color=color
                backcolor/backColor/bgcolor=color
                href=href
        <a name="anchorpoint"/>
        <unichar name="unicode character name"/>
        <unichar value="unicode code point"/>

        The whole may be surrounded by <para> </para> tags

        The <b> and <i> tags will work for the built-in fonts (Helvetica
        /Times / Courier).  For other fonts you need to register a family
        of 4 fonts using reportlab.pdfbase.pdfmetrics.registerFont; then
        use the addMapping function to tell the library that these 4 fonts
        form a family e.g.
            from reportlab.lib.fonts import addMapping
            addMapping('Vera', 0, 0, 'Vera')    #normal
            addMapping('Vera', 0, 1, 'Vera-Italic')    #italic
            addMapping('Vera', 1, 0, 'Vera-Bold')    #bold
            addMapping('Vera', 1, 1, 'Vera-BoldItalic')    #italic and bold

        It will also be able to handle any MathML specified Greek characters.
    """
    def __init__(self, text, style, bulletText = None, frags=None, caseSensitive=1, encoding='utf8'):
        self.caseSensitive = caseSensitive
        self.encoding = encoding
        self._setup(text, style, bulletText, frags, cleanBlockQuotedText)

    def __repr__(self):
        import string
        n = self.__class__.__name__
        L = [n+"("]
        keys = self.__dict__.keys()
        for k in keys:
            v = getattr(self, k)
            rk = repr(k)
            rv = repr(v)
            rk = "  "+string.replace(rk, "\n", "\n  ")
            rv = "    "+string.replace(rv, "\n", "\n    ")
            L.append(rk)
            L.append(rv)
        L.append(") #"+n)
        return string.join(L, "\n")

    def _setup(self, text, style, bulletText, frags, cleaner):
        if frags is None:
            text = cleaner(text)
            _parser.caseSensitive = self.caseSensitive
            style, frags, bulletTextFrags = _parser.parse(text,style)
            if frags is None:
                raise "xml parser error (%s) in paragraph beginning\n'%s'"\
                    % (_parser.errors[0],text[:min(30,len(text))])
            if bulletTextFrags: bulletText = bulletTextFrags

        #AR hack
        self.text = text
        self.frags = frags
        self.style = style
        self.bulletText = bulletText
        self.debug = 0  #turn this on to see a pretty one with all the margins etc.

    def wrap(self, availWidth, availHeight):
        # work out widths array for breaking
        self.width = availWidth
        leftIndent = self.style.leftIndent
        first_line_width = availWidth - (leftIndent+self.style.firstLineIndent) - self.style.rightIndent
        later_widths = availWidth - leftIndent - self.style.rightIndent

        if self.style.wordWrap == 'CJK':
            #use Asian text wrap algorithm to break characters
            self.blPara = self.breakLinesCJK([first_line_width, later_widths])
        else:
            self.blPara = self.breakLines([first_line_width, later_widths])
        self.height = len(self.blPara.lines) * self.style.leading
        return (self.width, self.height)

    def minWidth(self):
        'Attempt to determine a minimum sensible width'
        frags = self.frags
        nFrags= len(frags)
        if not nFrags: return 0
        if nFrags==1:
            f = frags[0]
            fS = f.fontSize
            fN = f.fontName
            words = hasattr(f,'text') and split(f.text, ' ') or f.words
            func = lambda w, fS=fS, fN=fN: stringWidth(w,fN,fS)
        else:
            words = _getFragWords(frags)
            func  = lambda x: x[0]
        return max(map(func,words))

    def _get_split_blParaFunc(self):
        return self.blPara.kind==0 and _split_blParaSimple or _split_blParaHard

    def split(self,availWidth, availHeight):
        if len(self.frags)<=0: return []

        #the split information is all inside self.blPara
        if not hasattr(self,'blPara'):
            self.wrap(availWidth,availHeight)
        blPara = self.blPara
        style = self.style
        leading = style.leading
        lines = blPara.lines
        n = len(lines)
        s = int(availHeight/leading)
        if s<=1:
            del self.blPara
            return []
        if n<=s: return [self]
        func = self._get_split_blParaFunc()

        P1=self.__class__(None,style,bulletText=self.bulletText,frags=func(blPara,0,s))
        #this is a major hack
        P1.blPara = ParaLines(kind=1,lines=blPara.lines[0:s],aH=availHeight,aW=availWidth)
        P1._JustifyLast = 1
        P1._splitpara = 1
        P1.height = s*leading
        P1.width = availWidth
        if style.firstLineIndent != 0:
            style = deepcopy(style)
            style.firstLineIndent = 0
        P2=self.__class__(None,style,bulletText=None,frags=func(blPara,s,n))
        return [P1,P2]

    def draw(self):
        #call another method for historical reasons.  Besides, I
        #suspect I will be playing with alternate drawing routines
        #so not doing it here makes it easier to switch.
        self.drawPara(self.debug)

    def breakLines(self, width):
        """
        Returns a broken line structure. There are two cases

        A) For the simple case of a single formatting input fragment the output is
            A fragment specifier with
                kind = 0
                fontName, fontSize, leading, textColor
                lines=  A list of lines
                        Each line has two items.
                        1) unused width in points
                        2) word list

        B) When there is more than one input formatting fragment the output is
            A fragment specifier with
                kind = 1
                lines=  A list of fragments each having fields
                            extraspace (needed for justified)
                            fontSize
                            words=word list
                                each word is itself a fragment with
                                various settings

        This structure can be used to easily draw paragraphs with the various alignments.
        You can supply either a single width or a list of widths; the latter will have its
        last item repeated until necessary. A 2-element list is useful when there is a
        different first line indent; a longer list could be created to facilitate custom wraps
        around irregular objects."""

        if type(width) <> ListType: maxWidths = [width]
        else: maxWidths = width
        lines = []
        lineno = 0
        style = self.style
        fFontSize = float(style.fontSize)

        #for bullets, work out width and ensure we wrap the right amount onto line one
        _handleBulletWidth(self.bulletText,style,maxWidths)

        maxWidth = maxWidths[0]

        self.height = 0
        frags = self.frags
        nFrags= len(frags)
        if nFrags==1 and not hasattr(frags[0],'cbDefn'):
            f = frags[0]
            fontSize = f.fontSize
            fontName = f.fontName
            words = hasattr(f,'text') and split(f.text, ' ') or f.words
            spaceWidth = stringWidth(' ', fontName, fontSize, self.encoding)
            cLine = []
            currentWidth = - spaceWidth   # hack to get around extra space for word 1
            for word in words:
                #this underscores my feeling that Unicode throughout would be easier!
                wordWidth = stringWidth(word, fontName, fontSize, self.encoding)
                newWidth = currentWidth + spaceWidth + wordWidth
                if newWidth <= maxWidth or not len(cLine):
                    # fit one more on this line
                    cLine.append(word)
                    currentWidth = newWidth
                else:
                    if currentWidth > self.width: self.width = currentWidth
                    #end of line
                    lines.append((maxWidth - currentWidth, cLine))
                    cLine = [word]
                    currentWidth = wordWidth
                    lineno += 1
                    try:
                        maxWidth = maxWidths[lineno]
                    except IndexError:
                        maxWidth = maxWidths[-1]  # use the last one

            #deal with any leftovers on the final line
            if cLine!=[]:
                if currentWidth>self.width: self.width = currentWidth
                lines.append((maxWidth - currentWidth, cLine))

            return f.clone(kind=0, lines=lines)
        elif nFrags<=0:
            return ParaLines(kind=0, fontSize=style.fontSize, fontName=style.fontName,
                            textColor=style.textColor, lines=[])
        else:
            if hasattr(self,'blPara') and getattr(self,'_splitpara',0):
                #NB this is an utter hack that awaits the proper information
                #preserving splitting algorithm
                return self.blPara
            n = 0
            words = []
            for w in _getFragWords(frags):
                spaceWidth = stringWidth(' ',w[-1][0].fontName, w[-1][0].fontSize)

                if n==0:
                    currentWidth = -spaceWidth   # hack to get around extra space for word 1
                    maxSize = 0

                wordWidth = w[0]
                f = w[1][0]
                if wordWidth>0:
                    newWidth = currentWidth + spaceWidth + wordWidth
                else:
                    newWidth = currentWidth

                #test to see if this frag is a line break. If it is we will only act on it
                #if the current width is non-negative or the previous thing was a deliberate lineBreak
                lineBreak = hasattr(f,'lineBreak')
                endLine = (newWidth>maxWidth and n>0) or lineBreak
                if not endLine:
                    if lineBreak: continue      #throw it away
                    nText = w[1][1]
                    if nText: n += 1
                    maxSize = max(maxSize,f.fontSize)
                    if words==[]:
                        g = f.clone()
                        words = [g]
                        g.text = nText
                    elif not _sameFrag(g,f):
                        if currentWidth>0 and ((nText!='' and nText[0]!=' ') or hasattr(f,'cbDefn')):
                            if hasattr(g,'cbDefn'):
                                i = len(words)-1
                                while hasattr(words[i],'cbDefn'): i -= 1
                                words[i].text += ' '
                            else:
                                g.text += ' '
                        g = f.clone()
                        words.append(g)
                        g.text = nText
                    else:
                        if nText!='' and nText[0]!=' ':
                            g.text += ' ' + nText

                    for i in w[2:]:
                        g = i[0].clone()
                        g.text=i[1]
                        words.append(g)
                        maxSize = max(maxSize,g.fontSize)

                    currentWidth = newWidth
                else:  #either it won't fit, or it's a lineBreak tag
                    if lineBreak:
                        g = f.clone()
                        #del g.lineBreak
                        words.append(g)

                    if currentWidth>self.width: self.width = currentWidth
                    #end of line
                    lines.append(FragLine(extraSpace=(maxWidth - currentWidth),wordCount=n,
                                        words=words, fontSize=maxSize))

                    #start new line
                    lineno += 1
                    try:
                        maxWidth = maxWidths[lineno]
                    except IndexError:
                        maxWidth = maxWidths[-1]  # use the last one

                    if lineBreak:
                        n = 0
                        words = []
                        continue

                    currentWidth = wordWidth
                    n = 1
                    maxSize = f.fontSize
                    g = f.clone()
                    words = [g]
                    g.text = w[1][1]

                    for i in w[2:]:
                        g = i[0].clone()
                        g.text=i[1]
                        words.append(g)
                        maxSize = max(maxSize,g.fontSize)

            #deal with any leftovers on the final line
            if words!=[]:
                if currentWidth>self.width: self.width = currentWidth
                lines.append(ParaLines(extraSpace=(maxWidth - currentWidth),wordCount=n,
                                    words=words, fontSize=maxSize))
            return ParaLines(kind=1, lines=lines)

        return lines


    def breakLinesCJK(self, width):
        """Initially, the dumbest possible wrapping algorithm.
        Cannot handle font variations."""

        style = self.style
        #for now we only handle one fragment.  Need to generalize this quickly.
        if len(self.frags) > 1:
            raise ValueError('CJK Wordwrap can only handle one fragment per paragraph for now')
        elif len(self.frags) == 0:
            return ParaLines(kind=0, fontSize=style.fontSize, fontName=style.fontName,
                            textColor=style.textColor, lines=[])
        f = self.frags[0]
        if 1 and hasattr(self,'blPara') and getattr(self,'_splitpara',0):
            #NB this is an utter hack that awaits the proper information
            #preserving splitting algorithm
            return f.clone(kind=0, lines=self.blPara.lines)
        if type(width)!=ListType: maxWidths = [width]
        else: maxWidths = width
        lines = []
        lineno = 0
        fFontSize = float(style.fontSize)

        #for bullets, work out width and ensure we wrap the right amount onto line one
        _handleBulletWidth(self.bulletText, style, maxWidths)

        maxWidth = maxWidths[0]

        self.height = 0


        f = self.frags[0]

        if hasattr(f,'text'):
            text = f.text
        else:
            text = ''.join(getattr(f,'words',[]))

        from reportlab.lib.textsplit import wordSplit
        lines = wordSplit(text, maxWidths[0], f.fontName, f.fontSize)
        #the paragraph drawing routine assumes multiple frags per line, so we need an
        #extra list like this
        #  [space, [text]]
        #
        wrappedLines = [(sp, [line]) for (sp, line) in lines]
        return f.clone(kind=0, lines=wrappedLines)


    def beginText(self, x, y):
        return self.canv.beginText(x, y)

    def drawPara(self,debug=0):
        """Draws a paragraph according to the given style.
        Returns the final y position at the bottom. Not safe for
        paragraphs without spaces e.g. Japanese; wrapping
        algorithm will go infinite."""

        #stash the key facts locally for speed
        canvas = self.canv
        style = self.style
        blPara = self.blPara
        lines = blPara.lines

        #work out the origin for line 1
        leftIndent = style.leftIndent
        cur_x = leftIndent

        if debug:
            bw = 0.5
            bc = Color(1,1,0)
            bg = Color(0.9,0.9,0.9)
        else:
            bw = getattr(style,'borderWidth',None)
            bc = getattr(style,'borderColor',None)
            bg = style.backColor
        
        #if has a background or border, draw it
        if bg or (bc and bw):
            canvas.saveState()
            op = canvas.rect
            kwds = dict(fill=0,stroke=0)
            if bc and bw:
                canvas.setStrokeColor(bc)
                canvas.setLineWidth(bw)
                kwds['stroke'] = 1
                br = getattr(style,'borderRadius',0)
                if br and not debug:
                    op = canvas.roundRect
                    kwds['radius'] = br
            if bg:
                canvas.setFillColor(bg)
                kwds['fill'] = 1
            bp = getattr(style,'borderPadding',0)
            op(leftIndent-bp,
                        -bp,
                        self.width - (leftIndent+style.rightIndent)+2*bp,
                        self.height+2*bp,
                        **kwds)
            canvas.restoreState()

        nLines = len(lines)
        bulletText = self.bulletText
        if nLines > 0:
            _offsets = getattr(self,'_offsets',[0])
            _offsets += (nLines-len(_offsets))*[_offsets[-1]]
            canvas.saveState()
            #canvas.addLiteral('%% %s.drawPara' % _className(self))
            alignment = style.alignment
            offset = style.firstLineIndent+_offsets[0]
            lim = nLines-1
            noJustifyLast = not (hasattr(self,'_JustifyLast') and self._JustifyLast)

            if blPara.kind==0:
                if alignment == TA_LEFT:
                    dpl = _leftDrawParaLine
                elif alignment == TA_CENTER:
                    dpl = _centerDrawParaLine
                elif self.style.alignment == TA_RIGHT:
                    dpl = _rightDrawParaLine
                elif self.style.alignment == TA_JUSTIFY:
                    dpl = _justifyDrawParaLine
                f = blPara
                cur_y = self.height - f.fontSize
                if bulletText <> None:
                    offset = _drawBullet(canvas,offset,cur_y,bulletText,style)

                #set up the font etc.
                canvas.setFillColor(f.textColor)

                tx = self.beginText(cur_x, cur_y)

                #now the font for the rest of the paragraph
                tx.setFont(f.fontName, f.fontSize, style.leading)
                ws = lines[0][0]
                t_off = dpl( tx, offset, ws, lines[0][1], noJustifyLast and nLines==1)
                if f.underline or f.link or f.strike:
                    xs = tx.XtraState = ABag()
                    xs.cur_y = cur_y
                    xs.f = f
                    xs.style = style
                    xs.lines = lines
                    xs.underlines=[]
                    xs.underlineColor=None
                    xs.strikes=[]
                    xs.strikeColor=None
                    xs.links=[]
                    xs.link=f.link
                    canvas.setStrokeColor(f.textColor)
                    dx = t_off+leftIndent
                    if dpl!=_justifyDrawParaLine: ws = 0
                    if f.underline: _do_under_line(0, dx, ws, tx)
                    if f.strike: _do_under_line(0, dx, ws, tx, lm=0.125)
                    if f.link: _do_link_line(0, dx, ws, tx)

                    #now the middle of the paragraph, aligned with the left margin which is our origin.
                    for i in xrange(1, nLines):
                        ws = lines[i][0]
                        t_off = dpl( tx, _offsets[i], ws, lines[i][1], noJustifyLast and i==lim)
                        if dpl!=_justifyDrawParaLine: ws = 0
                        if f.underline: _do_under_line(i, t_off+leftIndent, ws, tx)
                        if f.strike: _do_under_line(i, t_off+leftIndent, tx, ws, lm=0.125)
                        if f.link: _do_link_line(i, t_off+leftIndent, ws, tx)
                else:
                    for i in xrange(1, nLines):
                        dpl( tx, _offsets[i], lines[i][0], lines[i][1], noJustifyLast and i==lim)
            else:
                f = lines[0]
                cur_y = self.height - f.fontSize
                # default?
                dpl = _leftDrawParaLineX
                if bulletText <> None:
                    offset = _drawBullet(canvas,offset,cur_y,bulletText,style)
                if alignment == TA_LEFT:
                    dpl = _leftDrawParaLineX
                elif alignment == TA_CENTER:
                    dpl = _centerDrawParaLineX
                elif self.style.alignment == TA_RIGHT:
                    dpl = _rightDrawParaLineX
                elif self.style.alignment == TA_JUSTIFY:
                    dpl = _justifyDrawParaLineX
                else:
                    raise ValueError, "bad align %s" % repr(alignment)

                #set up the font etc.
                tx = self.beginText(cur_x, cur_y)
                xs = tx.XtraState=ABag()
                xs.textColor=None
                xs.rise=0
                xs.underline=0
                xs.underlines=[]
                xs.underlineColor=None
                xs.strike=0
                xs.strikes=[]
                xs.strikeColor=None
                xs.links=[]
                xs.link=None
                tx.setLeading(style.leading)
                xs.cur_y = cur_y
                xs.f = f
                xs.style = style

                tx._fontname,tx._fontsize = None, None
                t_off = dpl( tx, offset, lines[0], noJustifyLast and nLines==1)
                _do_post_text(0, t_off+leftIndent, tx)

                #now the middle of the paragraph, aligned with the left margin which is our origin.
                for i in range(1, nLines):
                    f = lines[i]
                    t_off = dpl( tx, _offsets[i], f, noJustifyLast and i==lim)
                    _do_post_text(i, t_off+leftIndent, tx)

            canvas.drawText(tx)
            canvas.restoreState()

    def getPlainText(self,identify=None):
        """Convenience function for templates which want access
        to the raw text, without XML tags. """
        frags = getattr(self,'frags',None)
        if frags:
            plains = []
            for frag in frags:
                if hasattr(frag, 'text'):
                    plains.append(frag.text)
            return join(plains, '')
        elif identify:
            text = getattr(self,'text',None)
            if text is None: text = repr(self)
            return text
        else:
            return ''

    def getActualLineWidths0(self):
        """Convenience function; tells you how wide each line
        actually is.  For justified styles, this will be
        the same as the wrap width; for others it might be
        useful for seeing if paragraphs will fit in spaces."""
        assert hasattr(self, 'width'), "Cannot call this method before wrap()"
        if self.blPara.kind:
            func = lambda frag, w=self.width: w - frag.extraSpace
        else:
            func = lambda frag, w=self.width: w - frag[0]
        return map(func,self.blPara.lines)

if __name__=='__main__':    #NORUNTESTS
    def dumpParagraphLines(P):
        print 'dumpParagraphLines(<Paragraph @ %d>)' % id(P)
        lines = P.blPara.lines
        n =len(lines)
        for l in range(n):
            line = lines[l]
            if hasattr(line,'words'):
                words = line.words
            else:
                words = line[1]
            nwords = len(words)
            print 'line%d: %d(%s)\n  ' % (l,nwords,str(getattr(line,'wordCount','Unknown'))),
            for w in range(nwords):
                print "%d:'%s'"%(w,getattr(words[w],'text',words[w])),
            print

    def dumpParagraphFrags(P):
        print 'dumpParagraphFrags(<Paragraph @ %d>) minWidth() = %.2f' % (id(P), P.minWidth())
        frags = P.frags
        n =len(frags)
        for l in range(n):
            print "frag%d: '%s' %s" % (l, frags[l].text,' '.join(['%s=%s' % (k,getattr(frags[l],k)) for k in frags[l].__dict__ if k!=text]))

        l = 0
        cum = 0
        for W in _getFragWords(frags):
            cum += W[0]
            print "fragword%d: cum=%3d size=%d" % (l, cum, W[0]),
            for w in W[1:]:
                print "'%s'" % w[1],
            print
            l += 1


    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    import sys
    TESTS = sys.argv[1:]
    if TESTS==[]: TESTS=['4']
    def flagged(i,TESTS=TESTS):
        return 'all' in TESTS or '*' in TESTS or str(i) in TESTS

    styleSheet = getSampleStyleSheet()
    B = styleSheet['BodyText']
    style = ParagraphStyle("discussiontext", parent=B)
    style.fontName= 'Helvetica'
    if flagged(1):
        text='''The <font name=courier color=green>CMYK</font> or subtractive method follows the way a printer
mixes three pigments (cyan, magenta, and yellow) to form colors.
Because mixing chemicals is more difficult than combining light there
is a fourth parameter for darkness.  For example a chemical
combination of the <font name=courier color=green>CMY</font> pigments generally never makes a perfect
black -- instead producing a muddy color -- so, to get black printers
don't use the <font name=courier color=green>CMY</font> pigments but use a direct black ink.  Because
<font name=courier color=green>CMYK</font> maps more directly to the way printer hardware works it may
be the case that &amp;| &amp; | colors specified in <font name=courier color=green>CMYK</font> will provide better fidelity
and better control when printed.
'''
        P=Paragraph(text,style)
        dumpParagraphFrags(P)
        aW, aH = 456.0, 42.8
        w,h = P.wrap(aW, aH)
        dumpParagraphLines(P)
        S = P.split(aW,aH)
        for s in S:
            s.wrap(aW,aH)
            dumpParagraphLines(s)
            aH = 500

    if flagged(2):
        P=Paragraph("""Price<super><font color="red">*</font></super>""", styleSheet['Normal'])
        dumpParagraphFrags(P)
        w,h = P.wrap(24, 200)
        dumpParagraphLines(P)

    if flagged(3):
        text = """Dieses Kapitel bietet eine schnelle <b><font color=red>Programme :: starten</font></b>
<onDraw name=myIndex label="Programme :: starten">
<b><font color=red>Eingabeaufforderung :: (&gt;&gt;&gt;)</font></b>
<onDraw name=myIndex label="Eingabeaufforderung :: (&gt;&gt;&gt;)">
<b><font color=red>&gt;&gt;&gt; (Eingabeaufforderung)</font></b>
<onDraw name=myIndex label="&gt;&gt;&gt; (Eingabeaufforderung)">
Einf&#xfc;hrung in Python <b><font color=red>Python :: Einf&#xfc;hrung</font></b>
<onDraw name=myIndex label="Python :: Einf&#xfc;hrung">.
Das Ziel ist, die grundlegenden Eigenschaften von Python darzustellen, ohne
sich zu sehr in speziellen Regeln oder Details zu verstricken. Dazu behandelt
dieses Kapitel kurz die wesentlichen Konzepte wie Variablen, Ausdr&#xfc;cke,
Kontrollfluss, Funktionen sowie Ein- und Ausgabe. Es erhebt nicht den Anspruch,
umfassend zu sein."""
        P=Paragraph(text, styleSheet['Code'])
        dumpParagraphFrags(P)
        w,h = P.wrap(6*72, 9.7*72)
        dumpParagraphLines(P)

    if flagged(4):
        text='''Die eingebaute Funktion <font name=Courier>range(i, j [, stride])</font><onDraw name=myIndex label="eingebaute Funktionen::range()"><onDraw name=myIndex label="range() (Funktion)"><onDraw name=myIndex label="Funktionen::range()"> erzeugt eine Liste von Ganzzahlen und f&#xfc;llt sie mit Werten <font name=Courier>k</font>, f&#xfc;r die gilt: <font name=Courier>i &lt;= k &lt; j</font>. Man kann auch eine optionale Schrittweite angeben. Die eingebaute Funktion <font name=Courier>xrange()</font><onDraw name=myIndex label="eingebaute Funktionen::xrange()"><onDraw name=myIndex label="xrange() (Funktion)"><onDraw name=myIndex label="Funktionen::xrange()"> erf&#xfc;llt einen &#xe4;hnlichen Zweck, gibt aber eine unver&#xe4;nderliche Sequenz vom Typ <font name=Courier>XRangeType</font><onDraw name=myIndex label="XRangeType"> zur&#xfc;ck. Anstatt alle Werte in der Liste abzuspeichern, berechnet diese Liste ihre Werte, wann immer sie angefordert werden. Das ist sehr viel speicherschonender, wenn mit sehr langen Listen von Ganzzahlen gearbeitet wird. <font name=Courier>XRangeType</font> kennt eine einzige Methode, <font name=Courier>s.tolist()</font><onDraw name=myIndex label="XRangeType::tolist() (Methode)"><onDraw name=myIndex label="s.tolist() (Methode)"><onDraw name=myIndex label="Methoden::s.tolist()">, die seine Werte in eine Liste umwandelt.'''
        aW = 420
        aH = 64.4
        P=Paragraph(text, B)
        dumpParagraphFrags(P)
        w,h = P.wrap(aW,aH)
        print 'After initial wrap',w,h
        dumpParagraphLines(P)
        S = P.split(aW,aH)
        dumpParagraphFrags(S[0])
        w0,h0 = S[0].wrap(aW,aH)
        print 'After split wrap',w0,h0
        dumpParagraphLines(S[0])

    if flagged(5):
        text = '<para> %s <![CDATA[</font></b>& %s < >]]></para>' % (chr(163),chr(163))
        P=Paragraph(text, styleSheet['Code'])
        dumpParagraphFrags(P)
        w,h = P.wrap(6*72, 9.7*72)
        dumpParagraphLines(P)

    if flagged(6):
        for text in ['''Here comes <FONT FACE="Helvetica" SIZE="14pt">Helvetica 14</FONT> with <STRONG>strong</STRONG> <EM>emphasis</EM>.''',
                     '''Here comes <font face="Helvetica" size="14pt">Helvetica 14</font> with <Strong>strong</Strong> <em>emphasis</em>.''',
                     '''Here comes <font face="Courier" size="3cm">Courier 3cm</font> and normal again.''',
                     ]:
            P=Paragraph(text, styleSheet['Normal'], caseSensitive=0)
            dumpParagraphFrags(P)
            w,h = P.wrap(6*72, 9.7*72)
            dumpParagraphLines(P)

    if flagged(7):
        text = """<para align="CENTER" fontSize="24" leading="30"><b>Generated by:</b>Dilbert</para>"""
        P=Paragraph(text, styleSheet['Code'])
        dumpParagraphFrags(P)
        w,h = P.wrap(6*72, 9.7*72)
        dumpParagraphLines(P)

    if flagged(8):
        text ="""- bullet 0<br/>- bullet 1<br/>- bullet 2<br/>- bullet 3<br/>- bullet 4<br/>- bullet 5"""
        P=Paragraph(text, styleSheet['Normal'])
        dumpParagraphFrags(P)
        w,h = P.wrap(6*72, 9.7*72)
        dumpParagraphLines(P)
        S = P.split(6*72,h/2.0)
        print len(S)
        dumpParagraphLines(S[0])
        dumpParagraphLines(S[1])
