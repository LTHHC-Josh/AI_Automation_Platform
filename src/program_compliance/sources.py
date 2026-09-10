"""Allowlisted HTTPS retrieval and content-only, structure-preserving parsing."""
from __future__ import annotations
import ipaddress
import re
import socket
import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote
import requests
import urllib3
import certifi


class PinnedResponse:
    def __init__(self,pool,response):
        self.pool=pool;self.response=response;self.status_code=response.status;self.headers=response.headers
    def iter_content(self,size):
        try: yield from self.response.stream(size,decode_content=True)
        except urllib3.exceptions.HTTPError: raise requests.ConnectionError('public_source_stream_failed') from None
    def close(self): self.response.close();self.pool.close()


def pinned_get(url,addresses,headers,timeout):
    """Connect to a prevalidated public IP while validating TLS for the official host."""
    p=urlsplit(url)
    pool=urllib3.HTTPSConnectionPool(sorted(addresses)[0],port=443,server_hostname=p.hostname,assert_hostname=p.hostname,cert_reqs='CERT_REQUIRED',ca_certs=certifi.where(),timeout=urllib3.Timeout(connect=10,read=timeout),maxsize=1)
    try:
        response=pool.urlopen('GET',p.path+('?' +p.query if p.query else ''),headers={**headers,'Host':p.hostname,'User-Agent':'LTHHC-ProgramComplianceMonitor/1.0'},redirect=False,retries=False,preload_content=False)
        return PinnedResponse(pool,response)
    except urllib3.exceptions.HTTPError:
        pool.close();raise requests.ConnectionError('public_source_unavailable') from None


class SourceFailure(RuntimeError):
    pass


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()


def canonical_url(url):
    p=urlsplit(url)
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/') or '/',p.query,''))


def allowed(url, boundaries):
    try:
        p=urlsplit(url);port=p.port
    except ValueError: return False
    if p.scheme!='https' or p.username or p.password or port not in (None,443):
        return False
    path=unquote(p.path)
    if any(x in path for x in ('..','\\','\x00')): return False
    return any(p.hostname==b['host'] and any(path==prefix.rstrip('/') or path.startswith(prefix.rstrip('/')+'/') for prefix in b['paths']) for b in boundaries)


class Retriever:
    def __init__(self,boundaries,max_bytes=8_000_000,timeout=25,session=None,resolver=socket.getaddrinfo):
        self.boundaries=boundaries;self.max_bytes=max_bytes;self.timeout=timeout
        self.session=session
        self.resolver=resolver

    def validate(self,url):
        if not allowed(url,self.boundaries): raise SourceFailure('coverage_boundary')
        try:
            addresses={item[4][0] for item in self.resolver(urlsplit(url).hostname,443,type=socket.SOCK_STREAM)}
            if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
                raise SourceFailure('private_destination')
            return addresses
        except socket.gaierror:
            raise SourceFailure('dns_unavailable') from None

    def get(self,url,metadata=None):
        metadata=metadata or {};headers={}
        if metadata.get('etag'): headers['If-None-Match']=metadata['etag']
        if metadata.get('modified'): headers['If-Modified-Since']=metadata['modified']
        started=time.monotonic()
        for _ in range(5):
            addresses=self.validate(url)
            response=None
            for attempt in range(3):
                try:
                    response=self.session.get(url,headers=headers,timeout=(10,self.timeout),stream=True,allow_redirects=False) if self.session else pinned_get(url,addresses,headers,self.timeout)
                    if response.status_code not in (429,500,502,503,504): break
                    response.close()
                except requests.RequestException:
                    if attempt==2: raise SourceFailure('unavailable') from None
                if attempt<2: time.sleep(2**attempt)
            if response is None: raise SourceFailure('unavailable')
            try:
                if response.status_code in (301,302,303,307,308):
                    url=canonical_url(urljoin(url,response.headers.get('Location','')));headers={};continue
                if response.status_code==304: return {'unchanged':True,'url':url}
                if response.status_code!=200: raise SourceFailure('unavailable')
                content_type=response.headers.get('Content-Type','').lower()
                if not any(t in content_type for t in ('text/html','application/pdf','text/plain')): raise SourceFailure('unsupported_content_type')
                length=response.headers.get('Content-Length')
                if length and (not length.isdigit() or int(length)>self.max_bytes): raise SourceFailure('download_limit')
                parts=[];size=0
                for part in response.iter_content(65536):
                    size+=len(part)
                    if size>self.max_bytes or time.monotonic()-started>90: raise SourceFailure('download_limit')
                    parts.append(part)
                raw=b''.join(parts)
                if len(raw)<80: raise SourceFailure('parser_failed')
                return {'raw':raw,'type':content_type,'url':canonical_url(url),'etag':response.headers.get('ETag'),'modified':response.headers.get('Last-Modified')}
            except requests.RequestException: raise SourceFailure('unavailable') from None
            finally: response.close()
        raise SourceFailure('redirect_limit')


class ContentParser(HTMLParser):
    """Capture main/article or Drupal body fields; exclude menus/scripts/forms."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[];self.chunks=[];self.links=[];self.active=0;self.skip=0

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        classes=attrs.get('class','')
        start=tag in ('main','article') or 'field--name-body' in classes or attrs.get('property')=='content:encoded'
        skip=tag in ('script','style','nav','header','footer','form','noscript','iframe') or attrs.get('role')=='navigation'
        if tag in ('meta','link','img','input','br','hr','source','wbr'):
            if self.active and not self.skip and tag in ('br','hr'): self.chunks.append('\n')
            return
        self.stack.append((tag,start,skip));self.active+=start;self.skip+=skip
        if self.active and not self.skip:
            if tag in ('h1','h2','h3','h4','p','li','tr','div','section'): self.chunks.append('\n')
            if tag in ('h1','h2','h3','h4'): self.chunks.append('#'*int(tag[1])+' ')
            if tag=='li': self.chunks.append('• ')
            if tag in ('td','th'): self.chunks.append(' | ')
            if tag=='a' and attrs.get('href'): self.links.append(attrs['href'])

    def handle_endtag(self,tag):
        if self.active and not self.skip and tag in ('h1','h2','h3','h4','p','li','tr'): self.chunks.append('\n')
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i][0]==tag:
                for _,start,skip in self.stack[i:]: self.active-=start;self.skip-=skip
                del self.stack[i:];break

    def handle_data(self,data):
        if self.active and not self.skip: self.chunks.append(re.sub(r'\s+',' ',data))


def parse(raw,content_type,url):
    if 'pdf' in content_type:
        # Parsing occurs in an isolated bounded subprocess, never in a DP OCR worker.
        import subprocess,sys
        try:
            result=subprocess.run([sys.executable,'-m','src.program_compliance.pdf_text'],input=raw,capture_output=True,timeout=25)
        except subprocess.TimeoutExpired: raise SourceFailure('parser_failed') from None
        if result.returncode or len(result.stdout)>2_000_000: raise SourceFailure('parser_failed')
        text=result.stdout.decode('utf-8');links=[]
    elif 'text/plain' in content_type:
        text=raw.decode('utf-8',errors='replace');links=[]
    else:
        p=ContentParser();p.feed(raw.decode('utf-8',errors='replace'))
        text=''.join(p.chunks);links=sorted(set(canonical_url(urljoin(url,x)) for x in p.links if not x.startswith(('#','mailto:','javascript:'))))
    lines=[normalize(line) for line in text.splitlines() if normalize(line)]
    lines=[line for line in lines if 'Printer-friendly version' not in line and line.lstrip('# ').strip() not in ('Body','This is the new HHS Forms and Handbooks website. Please update your bookmarks.')]
    if len(' '.join(lines))<80 or any(s in ' '.join(lines).lower() for s in ('access denied','verify you are human','enable javascript to continue')): raise SourceFailure('parser_failed')
    sections=[];heading='Document';body=[]
    for line in lines:
        if line.startswith('#'):
            if body: sections.append({'heading':heading,'text':'\n'.join(body)})
            heading=line.lstrip('# ').strip();body=[]
        else: body.append(line)
    if body: sections.append({'heading':heading,'text':'\n'.join(body)})
    return {'sections':sections,'links':links,'text':'\n'.join(lines)}
