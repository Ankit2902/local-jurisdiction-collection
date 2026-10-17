(function (window, $, undefined) {
    var isPageLoad = true;

    $(document).ready(function () {
        if (window.ZP === undefined) window.ZP = {};
        ZP.DocViewer = {
            AutoCollapseWidth: 1200,
           
            ToggleToc: function () {
                $("#doc-viewer").addClass("transition");
                if ($("#doc-viewer").hasClass("toc-collapsed")) {
                    ZP.DocViewer.ExpandToc();
                }
                else {
                    ZP.DocViewer.CollapseToc();
                }
            },
            CollapseToc:function(){
                $("#doc-viewer").addClass("toc-collapsed");
                $("#toc-view-toggle").attr("title", "Show Table of Contents");
                $("#toc-view-toggle span").text("Show Table of Contents");
            },
            ExpandToc: function () {
                $("#doc-viewer").removeClass("toc-collapsed");
                ZP.DocViewer.SetMinTocWidth();
                $("#toc-view-toggle").attr("title", "Hide Table of Contents");
                $("#toc-view-toggle span").text("Hide Table of Contents");
            },
            SetMinTocWidth:function(){
                ZP.DocViewer.SetMinLeftTocWidth();
            },
            SetMinLeftTocWidth:function()
            {
                if( parseInt($("#left-splitter")[0].style.left) < 40){
                    $("#left-splitter").css("left", "80px");
                    var leftSplitterWidth = $("#left-splitter").width();
                    $("#center-content").css("left", (80+leftSplitterWidth) +"px");

                    $("#left-sidebar").css("width", "80px");
                }
            },
            SetMinRightTocWidth: function () {
              
            },
            //in certain rare cases i.e. when running in the debugger, DocView.GetTocId is undefined. This is a duplicate used as a fallback.
            GetTocId: function (hashval, defaultId) {
                if (defaultId == null || defaultId == undefined || defaultId == '') defaultId = 't000';
                if (hashval == null || hashval == undefined || hashval == '') return defaultId;
                if (hashval.substring(0, 7) == "#tocid-") return 't' + hashval.substring(7);
                if (hashval.substring(0, 7) == "#secid-") return 's' + hashval.substring(7);
                return defaultId;
            },
            SplitterStopDragEvent: function (e, obj) {
                ZP.DocViewer.SplitterDragEvent(e, obj);
                $("#doc-viewer").addClass("transition");
                //ZP.DocView.WindowResize();
            },
            SplitterDragEvent: function (e, obj) {ZP.DocViewer.SplitterDragEvent_lft(e,obj);},
            SplitterDragEvent_rgt: function (e, obj) {
                //if (obj.offset.left < 10) obj.offset.right = (obj.window.width() - 10);
                //if (obj.offset.left > (obj.window.width() - 10)) obj.offset.right = 10;
                var minwidth = obj.leftEl.css('min-width');
                minwidth = parseInt(minwidth);
                obj.splitter.css('right', (obj.window.width() - obj.splitter.offset().left - obj.splitter.outerWidth()) + 'px');
                obj.splitter.css('left', 'auto');
                if (obj.splitter.offset().right < obj.window.width() - 781) { obj.splitter.css('right', (obj.window.width() - 780) + 'px'); }
                if (obj.splitter.offset().right > (obj.window.width() - 10)) obj.splitter.css('right', '10px');
				if ((obj.splitter.offset().left) < minwidth) { obj.offset.left = minwidth; obj.splitter.css('left', minwidth);}
                //

                obj.leftEl.width(obj.offset.left - obj.leftEl.offset().left);
                obj.rightEl.css("left", obj.offset.left + obj.splitter.outerWidth());
                var sb = 0;
                if (obj.rightEl.get(0).scrollHeight > obj.rightEl.height()) 
                    sb = 10;
                obj.rightEl.width(obj.container.width() - obj.leftEl.width() - sb);
              
                function getcssval(x) {
                    var y = parseInt(x);
                    return y;
                }
            },
            SplitterDragEvent_lft: function (e, obj) {
                $("#doc-viewer").removeClass("transition");
                $("#doc-viewer").removeClass("toc-collapsed");
             
                var maxwidth = obj.leftEl.css('max-width');
                maxwidth = parseInt(maxwidth);
                if (obj.offset.left < (obj.leftEl.offset().left + 10)) obj.offset.left = (obj.leftEl.offset().left + 10);
                if (obj.offset.left > (obj.window.width() - 10)) obj.offset.left = obj.window.width() - 10;
                if (obj.splitter.offset().left < (obj.leftEl.offset().left+10)) obj.splitter.css('left', '10px');
                if (obj.splitter.offset().left > (obj.window.width() - 10)) obj.splitter.css('left', (obj.window.width() - 10) + 'px');
                if ((obj.splitter.offset().left) > maxwidth) { obj.offset.left = maxwidth; obj.splitter.css('left', maxwidth); }
                obj.leftEl.width(obj.offset.left - obj.leftEl.offset().left);
                obj.rightEl.css("left", obj.offset.left - obj.leftEl.offset().left + obj.splitter.outerWidth());
                // Hide or show TOC contents when crossing collapse width boundary
                if (obj.splitter.offset().left < 40) {
                    $("#doc-viewer").addClass("toc-collapsed");
                    $("#toc-view-toggle").attr("title", "Show Table of Contents")
                    return;
                }
            },
            DocSelected: function (tocid, params) { ZP.DocView.LoadDoc(tocid, params); },
            
            HashChanged: function (e, defaultTocId, params) {
                if (history.state && history.state.id && ZP.DocView.LastHistoryStateId && ZP.DocView.LastHistoryStateId == history.state.id) {
                    history.replaceState(null, '',window.location.href);
                }
                if (ZP.DocView.GetTocId == undefined || ZP.DocView.GetTocId == null) {
                    alert("DocView.GetTocId is undefined");
                    var tocid = ZP.DocViewer.GetTocId(window.location.hash, defaultTocId);
                }
                else
                    var tocid = ZP.DocView.GetTocId(window.location.hash, defaultTocId);
                if (!params) {
                    var hidden = ZP.DocViewer.GetParameterByName("h");
                    if (hidden == "1") params = "h=1";
                }
                if (tocid == null || tocid == undefined || tocid == '') tocid = '999';
                
                if (ZP.DocViewer.ScrollDirectly(e)  ) {
                    if (history.state == null) {
                        //We have moved forward either by pressing the forward button or clicking an xref
                        if (window.location.hash.indexOf("xr") >= 0) {
                            var elmtId = "secid-" + window.location.hash.substring(window.location.hash.indexOf("xr") + 2);
                            elmtId = elmtId.substring(0, elmtId.indexOf("_"));
                            ZP.DocView.ScrollToDocElmt($("#" + elmtId), 0);
                        } else {
                            var elmtId = "secid-" + window.location.hash.substring(window.location.hash.indexOf("bk") + 2).replace("-", "bk");
                            elmtId = elmtId.substring(0, elmtId.indexOf("_"));
                            ZP.DocView.ScrollToDocElmt($("#" + elmtId), 0);
                        }
                    } else {
                        ZP.DocView.ScrollToPosition(history.state.position)
                    }
                    if (history.state == null) {
                        history.replaceState({ position: ZP.DocView.GetDocViewerScrollPosition(), id: ZP.DocView.GetNextHistoryId() }, '', window.location.href);
                    }
                    ZP.DocView.LastHistoryStateId = history.state.id;
                    ZP.DocView.oldURL = window.location.href;
                    return false;
                }
                //ZP.DocViewer.DocSelected(tocid);
                ZP.DocView.oldURL = window.location.href;
                ZP.TOCView.LoadTOC(tocid, params);
                //if (isPageLoad) {
                //                var selectedTOC = $(window.location.hash.replace(/\./g, ''));
                //                if (selectedTOC != null && selectedTOC.position() != null && (selectedTOC.position().top < 0 || selectedTOC.position().top > $('#toc-view').height()))
                //                    setTimeout(function () { $('#toc-view').scrollTop($(window.location.hash.replace(/\./g, '')).position().top); }, 2600);
                // isPageLoad = false;
                //}
            },
            ScrollDirectly: function (e) {
             
                if (window.location.hash.indexOf("xr") >= 0) {
                    var elmtId = "secid-" + window.location.hash.substring(window.location.hash.indexOf("xr") + 2);
                    elmtId = elmtId.substring(0, elmtId.indexOf("_"));
                    return $("#" + elmtId).length > 0;
                }
                if (window.location.hash.indexOf("bk") >= 0) {
                    var elmtId = "secid-" + window.location.hash.substring(window.location.hash.indexOf("bk") + 2).replace("-", "bk");
                    elmtId = elmtId.substring(0, elmtId.indexOf("_"));
                    return $("#" + elmtId).length > 0;
                }
                if (e) {
                    var oldUrlHash = ZP.DocView.oldURL.substring(ZP.DocView.oldURL.indexOf("#"));
                    var newUrlHash = window.location.hash;
                    if (oldUrlHash.indexOf("xr") >= 0 && oldUrlHash.indexOf(newUrlHash) == 0) return true;
                    if (oldUrlHash.indexOf("bk") >= 0 && oldUrlHash.substring(oldUrlHash.indexOf("bk")).indexOf("-") >= 0 && oldUrlHash.indexOf(newUrlHash) == 0) return true;
                }
               
                return false;
            },
            GetParameterByName: function(name, url) {
                if (!url) url = window.location.href;
                name = name.replace(/[\[\]]/g, '\\$&');
                var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
                    results = regex.exec(url);
                if (!results) return null;
                if (!results[2]) return '';
                return decodeURIComponent(results[2].replace(/\+/g, ' '));
            },
            UpdateTOC: function (tocid) {
                ZP.TOCView.LoadTOC(tocid);
            },
            ScrollTOC: function () {
                var selectedTOC = $(window.location.hash.replace(/\-/g, '-x'));
                var footer = $('#main-body-footer');
                var tl = $('#toc-list');
                if (selectedTOC != null && selectedTOC.position() != null && (selectedTOC.position().top < 0 || (selectedTOC.position().top + tl.offset().top) > footer.offset().top))
                    setTimeout(function () { $('#left-sidebar').scrollTop(selectedTOC.position().top); }, 300);
            },
            MinScreenSize: function () {
                var w = $("#main-body");
                var windowWidth = $(window).width();
                if (w == null || w == undefined || w.length == 0) w = $(window).width();
                else w = w.width();
                var min = w - 780;
                // 960 equals width of ipad in portrait mode and with .8 initial scale -> (960 X .8 = 768)
                if (windowWidth <= ZP.DocViewer.AutoCollapseWidth) { min = 375; }
                if (min < 300) {

                    $('#doc-viewer #left-sidebar').width(min);
                    $('#toc-view').width(min);
                    $('#doc-viewer #center-content').css('left', min + $("#left-splitter").width());
                    $('#doc-viewer #left-splitter').css('left', min);
                }

                if (windowWidth <= ZP.DocViewer.AutoCollapseWidth) { ZP.DocViewer.CollapseToc(); $('#toc-view').width(""); }
            },
            PrevWidth:null,
            WindowResize: function (ev, forceExecute) {
                if (forceExecute == null && Math.abs($(window).width() - ZP.DocViewer.PrevWidth) <=2 ) {
                    ZP.DocViewer.PrevWidth = $(window).width();
                    return;
                }
				var sp = splitter.MyElement;
				var minwidth = splitter.LeftEl.css('min-width');
				minwidth = parseInt(minwidth);
				if ((sp.offset().left) < minwidth) { sp.css('left',minwidth+'px');}
				
		
				ZP.DocView.WindowResize();
				if ($(window).width() <= ZP.DocViewer.AutoCollapseWidth) { $("#doc-viewer").addClass("transition"); ZP.DocViewer.CollapseToc(); } else { $("#doc-viewer").addClass("transition"); ZP.DocViewer.ExpandToc(); }
				ZP.DocViewer.PrevWidth = $(window).width();
			},
		
			

        }
        ZP.DocViewer.MinScreenSize();
        $.ajaxSetup({ cache: false });
        $(window).resize(ZP.DocViewer.WindowResize);
    
        ZP.DocView.OnResize = ZP.TOCView.WindowResize;
        ZP.TOCView.OnSelected = ZP.DocViewer.DocSelected;
        ZP.DocView.OnUpdateTOC = ZP.DocViewer.UpdateTOC;
        ZP.DocView.OnDocLoad = ZP.DocViewer.ScrollTOC;
        //var splitter = new ZP.Splitter("#left-splitter", $("#center-content"), $("#left-sidebar"), $("#doc-viewer"));
        var splitter = new ZP.Splitter("#left-splitter", $("#left-sidebar"), $("#center-content"), $("#doc-viewer"));
        splitter.OnDrag = ZP.DocViewer.SplitterDragEvent;
        splitter.OnStopDrag = ZP.DocViewer.SplitterStopDragEvent;
        ZP.DocView.WindowResize();
        ZP.DocView.commentsVisible = false;
      
    });
})(window, jQuery);