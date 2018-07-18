from lxml import etree


def __init__(self, xml_content, ls=True):

    t = etree.fromstring(xml_content)

    responses = t.xpath(".//d:response", namespaces=t.nsmap)

    for response in responses:
        href = unquote(response.xpath(".//d:href/text()", namespaces=t.nsmap)[0])
        display_name = response.xpath(".//d:displayname/text()", namespaces=t.nsmap)[0] if ls else None
        is_dir = bool(response.xpath(".//d:resourcetype/d:collection", namespaces=t.nsmap))
        content_length = int(response.xpath(".//d:getcontentlength/text()", namespaces=t.nsmap)[0]) if ls else None
        last_modified = datetime.strptime(
            response.xpath(".//d:getlastmodified/text()", namespaces=t.nsmap)[0],
            "%a, %d %b %Y %H:%M:%S %Z"
        ).timestamp()
        owner = response.xpath(".//d:owner/text()", namespaces=t.nsmap)[0]
        mime_type = response.xpath(".//d:getcontenttype/text()", namespaces=t.nsmap)[0]

        readable = bool(response.xpath(".//d:privilege/d:read", namespaces=t.nsmap)) if ls else None
        writable = bool(response.xpath(".//d:privilege/d:write", namespaces=t.nsmap)) if ls else None
        full_privilege = bool(response.xpath(".//d:privilege/d:all", namespaces=t.nsmap)) if ls else None
        read_acl = bool(response.xpath(".//d:privilege/d:read_acl", namespaces=t.nsmap)) if ls else None
        write_acl = bool(response.xpath(".//d:privilege/d:write_acl", namespaces=t.nsmap)) if ls else None
        resource_perm = response.xpath(".//s:resourceperm/text()", namespaces=t.nsmap)[0] if not ls else None

        item = Entity(href=href,
                      display_name=display_name,
                      is_dir=is_dir,
                      content_length=content_length,
                      last_modified=last_modified,
                      owner=owner,
                      mime_type=mime_type,
                      readable=readable,
                      writable=writable,
                      full_privilege=full_privilege,
                      read_acl=read_acl,
                      write_acl=write_acl,
                      resource_perm=resource_perm)
        self.append(item)