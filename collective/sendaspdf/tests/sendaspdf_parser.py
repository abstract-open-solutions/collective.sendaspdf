from HTMLParser import HTMLParser

class SendAsPDFHtmlParser(HTMLParser):
    """ Extracts the data generated by collective.sendaspdf
    in a readable way.
    """

    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)

        # List of nodes encountered
        self.path = []

        # useful data stored while parsing the page.
        self.document_actions = []

        # A few flags: they should all be reseted to False at the end.
        self.in_dl_as_pdf_action = False
        self.in_send_as_pdf_action = False

    def get_document_actions(self):
        """ Returns self.document_actions but casts everything
        to str to avoid errors in tests due to a difference
        like u'blabla' instead of 'blabla'.
        """
        return [dict([(str(k), str(v)) for k, v in action.items()])
                for action in self.document_actions]

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        tag_id = attrs.get('id', '')
        tag_classes = attrs.get('class', '')
        self.path.append({'tag': tag,
                          'id': tag_id,
                          'class': tag_classes})
        
        if tag == 'li':
            if tag_id == 'document-action-download_as_pdf':
                self.in_dl_as_pdf_action = True

            if tag_id == 'document-action-send_as_pdf':
                self.in_send_as_pdf_action = True

        if tag == 'a':
            if self.in_dl_as_pdf_action or self.in_send_as_pdf_action:
                self.document_actions.append({})
                self.document_actions[-1]['href'] = attrs.get('href', '')
                self.document_actions[-1]['text'] = ''

    def handle_endtag(self, tag):
        if not self.path:
            return

        t = self.path.pop()
        tag_id = t.get('id', '')
        tag_classes = t.get('class', '')

        if t['tag'] == 'li':
            if tag_id == 'document-action-download_as_pdf':
                self.in_dl_as_pdf_action = False

            if tag_id == 'document-action-send_as_pdf':
                self.in_send_as_pdf_action = False

                
    def handle_startendtag(self, tag, attrs):
        attrs = dict(attrs)

    def handle_data(self, data):
        if not self.path:
            return

        tag = self.path[-1]

        if tag['tag'] == 'a':
            if self.in_dl_as_pdf_action or self.in_send_as_pdf_action:
                self.document_actions[-1]['text'] += data
