from lxml import etree


def clean_str_doc(str_doc):
    return str_doc.replace('\n', '')


def str_to_xml(str_doc):
    return etree.fromstring(clean_str_doc(str_doc))


def xml_to_str(xml_doc):
    return etree.tostring(xml_doc)