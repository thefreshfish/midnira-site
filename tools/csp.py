"""Keep the site's content security policy in step with its pages.

Every page loads its styles from site.css and its script from site.js, so the
policy allows 'self' and needs no hashes. It is in two places: a
<meta http-equiv="Content-Security-Policy"> tag near the top of each page, and
the Content-Security-Policy line in _headers, which Cloudflare sends as a
response header. The meta tag keeps the policy in force wherever a page is
opened without the header.

Run from the site folder after adding a page or changing markup:

  python3 tools/csp.py          write the tag into every page and the _headers line
  python3 tools/csp.py --check  exit 1 if a page breaks the policy or either copy is out of date

The policy would block an inline <style> or <script>, a style="" attribute and
an inline event handler, so the tool refuses to run if a page has one. A meta
tag cannot carry frame-ancestors, so only the _headers line has it.
"""
import glob
import re
import sys

HEADERS = "_headers"
TAG = re.compile(r'<meta http-equiv="Content-Security-Policy" content="[^"]*">\n')
LINE = re.compile(r"^([ \t]+Content-Security-Policy:).*$", re.M)
ANCHOR = '<meta name="viewport"'
POLICY = "; ".join([
    "default-src 'none'",
    "script-src 'self' https://static.cloudflareinsights.com",
    "style-src 'self' https://fonts.googleapis.com",
    "font-src https://fonts.gstatic.com",
    "img-src 'self'",
    "connect-src https://cloudflareinsights.com",
    "base-uri 'none'",
    "form-action 'none'",
])


def problems(html):
    found = []
    if re.search(r"<style[\s>]", html):
        found.append("an inline <style> block")
    for attrs, body in re.findall(r"<script\b([^>]*)>(.*?)</script>", html, re.S):
        if "src=" not in attrs or body.strip():
            found.append("an inline <script>")
    for tag in re.findall(r"<[a-zA-Z][^>]*>", html):
        if re.search(r"\sstyle\s*=", tag):
            found.append("a style attribute")
        if re.search(r"\son[a-z]+\s*=", tag):
            found.append("an inline event handler")
    return sorted(set(found))


def main():
    pages = sorted(glob.glob("*.html"))
    if not pages:
        sys.exit("csp: no pages found; run from the site folder")
    tag = '<meta http-equiv="Content-Security-Policy" content="%s">\n' % POLICY
    check = "--check" in sys.argv
    stale = []
    for page in pages:
        html = open(page, encoding="utf-8").read()
        bad = problems(html)
        if bad:
            sys.exit("csp: %s has %s; the policy would block it" % (page, ", ".join(bad)))
        current = TAG.search(html)
        if check:
            if not current or current.group(0) != tag:
                stale.append(page)
            continue
        if current:
            html = html[:current.start()] + tag + html[current.end():]
        else:
            at = html.index(ANCHOR)
            at = html.index("\n", at) + 1
            html = html[:at] + tag + html[at:]
        open(page, "w", encoding="utf-8").write(html)
    rules = open(HEADERS, encoding="utf-8").read()
    if len(LINE.findall(rules)) != 1:
        sys.exit("csp: expected one Content-Security-Policy line in %s" % HEADERS)
    new_rules = LINE.sub(lambda m: "%s %s; frame-ancestors 'none'" % (m.group(1), POLICY), rules)
    if check:
        if new_rules != rules:
            stale.append(HEADERS)
        if stale:
            sys.exit("csp: out of date in %s; run python3 tools/csp.py" % ", ".join(stale))
        print("csp: up to date (%s)" % ", ".join(pages))
        return
    open(HEADERS, "w", encoding="utf-8").write(new_rules)
    print("csp: tag written to %s and the _headers line" % ", ".join(pages))


if __name__ == "__main__":
    main()
