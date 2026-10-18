The two Boston source-heading-only units remain unqualified. Both original raw
API nodes explicitly declare has_children=false with no passthrough. Their exact
native groups contain only their requested heading rich block. The next native
headings have the same depth/tag (h2/depth2 for16-A1; h4/depth4 for7-13.8.1), and
belong to separately inventoried sibling owners. No explicit reserved/repealed
status or structural-container annotation was found in these source packets.

The titles may serve an editorial grouping purpose, particularly16-A1 before
16-A1.1/16-A1.2, but the retained source does not prove that role. It also cannot
prove whether missing body was intentional. The full retained-native parser has
conserved every rich block; it has not skipped an available body for these two
owners. Other-owner text remains in its original owner with no copies or merges.
No classification change or new collector candidate is warranted by this evidence.

`diagnostic.json` binds rawTOC receipts, original raw-node attributes, exact native
source fragment hashes/character spans, native heading depths, following sibling
identities and their text hashes. Original Boston source SHA256 is
33b2fc7d1a2fdaf15f26356adc67a1e038b72892d23438ab45169f7d33c4233c;
normalized JSONL SHA256 is2040f68476893e62cb37fb1644f344a0c946431f2c53f28347d9ebee26897c44.

This diagnosis performed no network request, image fetch/decode/extraction/render/
OCR, source/production edit, closing refresh or publication-completeness upgrade.
Both exact raw fragments are retained here. The frozen Boston note candidate is
unchanged. To reproduce, copy this study to a new sibling directory and run
`inspect_heading_only.py` with the shared Python3.12.14 interpreter from the project
root. It reads the original Boston run and frozen normalized output using their
project-relative paths and writes only the copied study's diagnostic/fragments.
