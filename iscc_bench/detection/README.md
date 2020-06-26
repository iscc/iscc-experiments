# Media Type Detection

*For a reliable construction of Content-IDs, we need a standardized and reproducible 
way  to detect the Media Type (MIME Type) of digital assets. This package takes a closer 
look at existing tools and approaches.*

The most straightforward approach is to rely on filename extensions to deduce the 
Media Type. The problem with this is that the filename is external to the data - 
anybody may change the name without affecting the data. Filenames are unprotected 
metadata.

A more reliable approach is to examine the data itself detect the Media Type. 
Unfortunately, with the many different and complex container based content formats, this 
becomes kind of a dark arts discipline also called MIME sniffing.


## Resources
https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
https://tools.ietf.org/html/rfc6838
https://www.iana.org/assignments/media-types/media-types.xhtml
https://mimesniff.spec.whatwg.org/
https://github.com/jshttp/mime-db
https://tika.apache.org/1.24.1/detection.html
https://pypi.org/project/filetype/
https://pypi.org/project/mimesniff/


