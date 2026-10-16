// Local macOS PDFKit + Vision first-page OCR. No network, credentials, or Codex.
import Foundation
import AppKit
import PDFKit
import Vision
let args=CommandLine.arguments
if args.count != 4 {fputs("Usage: swift vision_pdf_ocr.swift input.pdf page-number output-directory\n",stderr);exit(2)}
let source=URL(fileURLWithPath:args[1]);let pageNo=Int(args[2]) ?? 0;let out=URL(fileURLWithPath:args[3],isDirectory:true)
guard let pdf=PDFDocument(url:source),pageNo>0,pageNo<=pdf.pageCount,let page=pdf.page(at:pageNo-1) else {fputs("PDF/page invalid\n",stderr);exit(2)}
try FileManager.default.createDirectory(at:out,withIntermediateDirectories:true)
let image=page.thumbnail(of:NSSize(width:1700,height:2200),for:.mediaBox)
guard let cg=image.cgImage(forProposedRect:nil,context:nil,hints:nil),let rep=NSBitmapImageRep(cgImage:cg).representation(using:.png,properties:[:]) else {fputs("Cannot render page\n",stderr);exit(2)}
try rep.write(to:out.appendingPathComponent("page.png"))
let request=VNRecognizeTextRequest();request.recognitionLevel = .accurate;request.recognitionLanguages=["en-US"];request.usesLanguageCorrection=false
try VNImageRequestHandler(cgImage:cg,options:[:]).perform([request])
let observations=(request.results ?? []).sorted{a,b in abs(a.boundingBox.midY-b.boundingBox.midY)>0.006 ? a.boundingBox.midY>b.boundingBox.midY:a.boundingBox.minX<b.boundingBox.minX}
let rows:[[String:Any]]=observations.enumerated().compactMap{i,item in guard let c=item.topCandidates(1).first else{return nil};return ["source_line_id":"pdf-page-\(pageNo)-line-\(i+1)","text":c.string,"confidence":c.confidence,"bbox":[item.boundingBox.minX,item.boundingBox.minY,item.boundingBox.width,item.boundingBox.height]]}
let result:[String:Any] = ["schema_version":1,"runtime":"macOS Vision + PDFKit local native OCR","pdf_page_count":pdf.pageCount,"processed_page_number":pageNo,"render_width":cg.width,"render_height":cg.height,"rows":rows,"full_document_processed":false,"human_review_required":true]
let data=try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys]);try data.write(to:out.appendingPathComponent("ocr.json"));print("OCR \(rows.count) lines from page \(pageNo)/\(pdf.pageCount)")
