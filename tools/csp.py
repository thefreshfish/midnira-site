"""Keep the site's content security policy in step with its inline style and script.

The policy is in two places: a <meta http-equiv="Content-Security-Policy"> tag
near the top of index.html, and the Content-Security-Policy line in _headers,
which Cloudflare sends as a response header. It allows the page's one inline
<style> and one inline <script> by their SHA-256 hashes, so any edit to either
block changes its hash and both places have to be rewritten, or the browser will
refuse the block.

Run from the site folder:

  python3 tools/csp.py          rewrite both with the current hashes
  python3 tools/csp.py --check  exit 1 if either is missing or out of date

A meta tag cannot carry frame-ancestors, so only the _headers line has it.
"""
import base64
import hashlib
import re
import sys

PAGE = "index.html"
HEADERS = "_headers"
TAG = re.compile(r'<meta http-equiv="Content-Security-Policy" content="[^"]*">\n')
LINE = re.compile(r"^([ \t]+Content-Security-Policy:).*$", re.M)
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
    rules = open(HEADERS, encoding="utf-8").read()
    value = policy(html)
    tag = '<meta http-equiv="Content-Security-Policy" content="%s">\n' % value
    if len(LINE.findall(rules)) != 1:
        sys.exit("csp: expected one Content-Security-Policy line in %s" % HEADERS)
    new_rules = LINE.sub(lambda m: "%s %s; frame-ancestors 'none'" % (m.group(1), value), rules)
    current = TAG.search(html)
    if "--check" in sys.argv:
        if not current or current.group(0) != tag or new_rules != rules:
            sys.exit("csp: the tag or the _headers line is missing or out of date; run python3 tools/csp.py")
        print("csp: up to date")
        return
    if current:
        html = html[:current.start()] + tag + html[current.end():]
    else:
        at = html.index(ANCHOR)
        at = html.index("\n", at) + 1
        html = html[:at] + tag + html[at:]
    open(PAGE, "w", encoding="utf-8").write(html)
    open(HEADERS, "w", encoding="utf-8").write(new_rules)
    print("csp: tag and _headers line written")


if __name__ == "__main__":
    main()
