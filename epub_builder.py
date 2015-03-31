# epub_builder.py
# Basic epub builder for python.
# Copyright 2015 by Paul Huff

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import os,re
from zipfile import ZipFile

class OpfFile:
    def __init__(self, filename, title, author):
        self.filename = filename
        self.outputString = u'''<?xml version="1.0"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf">

  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>%s</dc:title>
    <dc:language>en</dc:language>
    <dc:creator opf:file-as="%s" opf:role="aut">%s</dc:creator>
  </metadata>

  <manifest>
''' % ( title, author, author)
        self.chapters = []

    def finish(self, zipFile):
        for chapter in self.chapters:
            self.outputString += u'''   <item id="%s" href="%s" media-type="application/xhtml+xml" />
''' % (chapter['id'], chapter['fileName'])
        self.outputString += u'''<item id="ncx" href="%s.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>

  <spine toc="ncx">''' % (self.filename, )
        for chapter in self.chapters:
            self.outputString += u'   <itemref idref="%s" />' % (chapter['id'], )
        self.outputString += u'''   </spine>
</package>'''

        zipFile.writestr('OEBPS/%s.opf' % (self.filename, ), self.outputString)

    def addChapter(self, chapter):
        self.chapters.append(chapter)

class NcxFile:
    def __init__(self, filename, title, author):
        self.filename = filename
        self.outputString = u'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
"http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">

<ncx version="2005-1" xml:lang="en" xmlns="http://www.daisy.org/z3986/2005/ncx/">

  <head>
<!-- The following four metadata items are required for all NCX documents,
including those conforming to the relaxed constraints of OPS 2.0 -->

    <meta name="dtb:uid" content="123456789X"/> <!-- same as in .opf -->
    <meta name="dtb:depth" content="1"/> <!-- 1 or higher -->
    <meta name="dtb:totalPageCount" content="0"/> <!-- must be 0 -->
    <meta name="dtb:maxPageNumber" content="0"/> <!-- must be 0 -->
  </head>
  <docTitle>
    <text>%s</text>
  </docTitle>

  <docAuthor>
    <text>%s</text>
  </docAuthor>
  <navMap>
''' % (title, author)
        self.chapters = []


    def finish(self, zipFile):
        chapterNumber = 1
        for chapter in self.chapters:
            self.outputString += u'''   <navPoint class="chapter" id="%s" playorder="%s">
      <navLabel><text>%s</text></navLabel>
      <content src="%s" />
   </navPoint>
''' % (chapter['id'], chapterNumber, chapter['title'], chapter['fileName'])
            chapterNumber += 1

        self.outputString += u'''   </navMap>
</ncx>'''
        zipFile.writestr("OEBPS/%s.ncx" % (self.filename, ), self.outputString)

    def addChapter(self, chapter):
        self.chapters.append(chapter)

class ContainerFile:
    def __init__(self, filename, opfFile):
        self.outputString = u'''<?xml version="1.0" encoding="UTF-8" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="%s" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''' % ('OEBPS/%s.opf' % (filename, ))

    def finish(self, zipFile):
        zipFile.writestr('OEBPS/META-INF/container.xml', self.outputString)

class EpubBuilder:
    def __init__(self, filename, title, authorName, chapters):
        self.filename = filename
        self.title = title
        self.authorName = authorName
        self.chapters = chapters

    def writeMimeTypeFile(self, zipFile):
        zipFile.writestr('mimetype', 'application/epub+zip')

    def writeBookFile(self):
        opf = OpfFile(self.filename, self.title, self.authorName)
        containerFile = ContainerFile(self.filename, opf)
        ncx = NcxFile(self.filename, self.title, self.authorName)
        epub = ZipFile('%s.epub' % (self.filename, ), 'w')
        i = 0
        for chapter in self.chapters:
            chapterText = u'''<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
  <head>
    <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
    <title>%s</title>
</head>
  <body>
%s
  </body>
</html>''' % (chapter['title'], chapter['body'])
            chapter['fileName'] = 'chapter-%s.html' % (i, )
            chapter['id'] = 'chapter-%s' % (i, )
            epub.writestr('OEBPS/chapter-%s.html' % (i, ), chapterText)
            opf.addChapter(chapter)
            ncx.addChapter(chapter)
            i += 1
        ncx.finish(epub)
        opf.finish(epub)
        self.writeMimeTypeFile(epub)
        containerFile.finish(epub)
        epub.close()
