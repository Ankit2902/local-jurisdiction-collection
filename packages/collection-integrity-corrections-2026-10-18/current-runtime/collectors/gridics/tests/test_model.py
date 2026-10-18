import unittest
from collectors.gridics.model import normalize, native_records, dom_records, Invalid

CONFIG={'source_url':'https://codehub.gridics.com/us/ca/example','document_id':'75'}


def node(key,body='',children=None):
    result={'id':key,'path':'/'+key,'docId':'75','text':'Section '+key,'ref':{},'li_attr':{'tag':'h2','dataTag':'section'},'children':children or []}
    if body:
        result['children'].insert(0,{'id':'body-'+key,'path':'/'+key+'/body-'+key,'docId':'75','ref':{'parent':key},'li_attr':{'dataTag':'BodyM'},'text':body})
    return result


class ModelTests(unittest.TestCase):
    def test_images_in_source_order_and_cell(self):
        actual=normalize('<p>Before<img src="a.png">After</p><table><tr><td background="b.png">Map</td><td><picture><source srcset="c.png"><img src="d.png"></picture></td></tr></table><svg><path/></svg>',CONFIG['source_url'])
        self.assertEqual(len(actual['images']),4)
        self.assertEqual(actual['html'].count('[IMAGE]'),4)
        self.assertEqual(actual['tables'][0][0][0]['text'],'[IMAGE]Map')
        self.assertNotIn('<img',actual['html'])
        self.assertNotIn('background=',actual['html'])
        self.assertNotIn('<svg',actual['html'])

    def test_uppercase_image_mime_and_data(self):
        import json
        value=normalize('<object type="IMAGE/PNG" data="https://example.invalid/opaque"></object><source src="DATA:IMAGE/PNG;base64,PIXELS"><input type="IMAGE" src="map.png">',CONFIG['source_url'])
        self.assertEqual(value['text'],'[IMAGE][IMAGE][IMAGE]')
        self.assertEqual(len(value['images']),3)
        self.assertNotIn('PIXELS',json.dumps(value))
        self.assertEqual(value['links'],[])

    def test_image_only_source_retained(self):
        records,_=native_records([node('a','<img src="map.png">')],CONFIG,'/a')
        self.assertEqual(records[0]['source_id'],'a')
        self.assertEqual(records[0]['heading'],'Section a')
        self.assertEqual(records[0]['text'],'[IMAGE]')
        self.assertEqual(records[0]['disposition'],'body')

    def test_video_poster_keeps_position_caption_and_redacts_payload(self):
        import json
        value=normalize('<table><tr><td>Before<video poster="DATA:IMAGE/PNG;base64,SECRETPIXELS"><p>Caption text</p></video>After</td></tr></table>',CONFIG['source_url'])
        self.assertEqual(value['text'].count('[IMAGE]'),1)
        self.assertIn('Before[IMAGE]',value['tables'][0][0][0]['text'])
        self.assertIn('Caption text',value['text'])
        self.assertIn('After',value['text'])
        self.assertEqual(value['images'][0]['kind'],'video_poster')
        self.assertTrue(value['images'][0]['source_locator']['embedded_data_omitted'])
        self.assertNotIn('SECRETPIXELS',json.dumps(value))
        self.assertNotIn('poster=',value['html'])

    def test_empty_not_complete(self):
        records,_=native_records([node('a')],CONFIG,'/a')
        self.assertEqual(records[0]['disposition'],'source_empty_unresolved')

    def test_parent_own_body_not_child_duplicate(self):
        child=node('b','<p>Child</p>')
        child['path']='/a/b';child['ref']={'parent':'a'}
        child['children'][0]['path']='/a/b/body-b'
        parent=node('a','<p>Parent</p>',[child])
        records,_=native_records([parent],CONFIG,'/a')
        self.assertEqual([r['text'] for r in records],['Parent','Child'])
        self.assertEqual(records[0]['source_sequence'],['body-a','b'])

    def test_native_identity_and_hierarchy_reject(self):
        wrong=node('a','text');wrong['docId']='76'
        with self.assertRaises(Invalid):native_records([wrong],CONFIG,'/a')
        wrong=node('a','text');wrong['children'][0]['ref']['parent']='other'
        with self.assertRaises(Invalid):native_records([wrong],CONFIG,'/a')

    def test_rendered_owned_body_independent(self):
        markup='<div class="section" data-path="/a"><div id="anchor-a"><h2>A</h2><span class="share-print">UI</span></div><p>Parent</p><div class="section" data-path="/a/b"><h3>B</h3><img src="x.png"></div><p>Afterword</p></div>'
        records=dom_records(markup,CONFIG)
        self.assertEqual(records['/a']['text'],'Parent\nAfterword')
        self.assertEqual(records['/a/b']['text'],'[IMAGE]')

    def test_inline_word_and_list_markers(self):
        n=normalize('<p>co<em>de</em></p><ol style="list-style-type:upper-alpha" start="2"><li value="3">Third</li></ol>',CONFIG['source_url'])
        self.assertEqual(n['text'],'code\nC. Third')
        self.assertIn('list-style-type:upper-alpha',n['html'])
        self.assertIn('value="3"',n['html'])

    def test_document_links_do_not_become_images(self):
        n=normalize('<a href="/document.pdf">Attachment</a>',CONFIG['source_url'])
        self.assertEqual(n['links'][0]['url'],'https://codehub.gridics.com/document.pdf')
        self.assertEqual(n['images'],[])

    def test_embedded_image_payload_not_normalized_metadata(self):
        import json
        value=normalize('<img src="data:image/png;base64,SECRETPIXELS">',CONFIG['source_url'])
        self.assertNotIn('SECRETPIXELS',json.dumps(value))
        self.assertTrue(value['images'][0]['source_locator']['embedded_data_omitted'])

    def test_image_representations_and_comments(self):
        value=normalize('A<!-- editorial hidden --><style>.x{background:url(map.png)}</style><source srcset="other.png"><object data="map.svg"></object>',CONFIG['source_url'])
        self.assertEqual(value['text'],'A[IMAGE][IMAGE][IMAGE]')
        self.assertNotIn('editorial hidden',value['html'])

    def test_adjacent_cells_separate(self):
        value=normalize('<table><tr><th>Titles</th><th>Chapters</th></tr><tr><td>5</td><td>All</td></tr></table>',CONFIG['source_url'])
        self.assertEqual(value['text'],'Titles Chapters\n5 All')

    def test_jsonl_unicode_line_separators_round_trip(self):
        import json
        from collectors.gridics.collect import json_line
        value={'text':'A\u2028B\u2029C\x85D'}
        line=json_line(value)
        self.assertEqual(len(line.splitlines()),1)
        self.assertEqual(json.loads(line),value)


if __name__=='__main__':
    unittest.main()
