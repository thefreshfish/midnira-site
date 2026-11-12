"""Keep the page's content security policy in step with its inline style and script.

The policy is a <meta http-equiv="Content-Security-Policy"> tag near the top of
index.html. It allows the page's one inline <style> and one inline <script> by
their SHA-256 hashes, so any edit to either block changes its hash and the tag has
to be rewritten, or the browser will refuse the block.

Run from the site folder:

  python3 tools/csp.py          rewrite the tag with the current hashes
  python3 tools/csp.py --check  exit 1 if the tag is missing or out of date

A meta tag cannot carry frame-ancestors or HSTS; those need real response headers.
"""
import base64
import hashlib
import re
import sys

PAGE = "index.html"
TAG = re.compile(r'<meta http-equiv="Content-Security-Policy" content="[^"]*">\n')
ANCHOR = '<meta name="viewport"'


def sha(text):
    return "'sha256-%s'" % base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode()


def one(pattern, html, what):
    found = re.findall(pattern, html, re.S)
    if len(found) != 1:
        sys.exit("csp: expected one %s, found %d" % (what, len(found)))
    return found[0]


def policy(html):
    style = one(r"<style>(.*?)</style>", html, "inline <style>")
    script = one(r"<script>(.*?)</script>", html, "inline <script>")
    if re.search(r'\sstyle="', html):
        sys.exit("csp: a style attribute is in the markup; the policy would block it")
    if re.search(r'\son[a-z]+="', html):
        sys.exit("csp: an inline event handler is in the markup; the policy would block it")
    return "; ".join([
        "default-src 'none'",
        "script-src %s https://static.cloudflareinsights.com" % sha(script),
        "style-src %s https://fonts.googleapis.com" % sha(style),
        "font-src https://fonts.gstatic.com",
        "img-src 'self'",
        "connect-src https://cloudflareinsights.com",
        "base-uri 'none'",
        "form-action 'none'",
    ])


def main():
    html = open(PAGE, encoding="utf-8").read()
    tag = '<meta http-equiv="Content-Security-Policy" content="%s">\n' % policy(html)
    current = TAG.search(html)
    if "--check" in sys.argv:
        if not current or current.group(0) != tag:
            sys.exit("csp: the tag is missing or out of date; run python3 tools/csp.py")
        print("csp: up to date")
        return
    if current:
        html = html[:current.start()] + tag + html[current.end():]
    else:
        at = html.index(ANCHOR)
        at = html.index("\n", at) + 1
        html = html[:at] + tag + html[at:]
    open(PAGE, "w", encoding="utf-8").write(html)
    print("csp: tag written")


if __name__ == "__main__":
    main()
