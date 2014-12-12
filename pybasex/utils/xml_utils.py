from xml.etree import ElementTree


def clean_str_doc(str_doc):
    return str_doc.replace('\n', '')


def str_to_xml(str_doc):
    return ElementTree.fromstring(clean_str_doc(str_doc))


def xml_to_str(xml_doc):
    return ElementTree.tostring(xmll_doc)