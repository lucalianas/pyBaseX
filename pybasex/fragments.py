from lxml import etree

BASEX_XML_NSPACE = 'http://basex.org/rest'


def build_query_fragment(query):
    """
    <query xmlns="http://basex.org/rest">
        <text><![CDATA[ (//city/name)[position() <= 5] ]]></text>
    </query>
    """
    root = etree.Element('query', nsmap={None: 'http://basex.org/rest'})
    text = etree.SubElement(root, 'text')
    text.text = etree.CDATA(query.strip())
    return root