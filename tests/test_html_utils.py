from inboxtriage.html_utils import strip_html


def test_strip_html_removes_tags_and_decodes_entities():
    html = "<html><body><p>Hello &amp; welcome</p><b>there</b></body></html>"
    assert strip_html(html) == "Hello & welcome there"


def test_strip_html_handles_empty_input():
    assert strip_html("") == ""
