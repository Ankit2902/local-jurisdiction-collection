(function (window, $, undefined) {
    if (window.ZP == undefined) window.ZP = {}
    ZP.DocView = {
        comments: { Initialhtml: null, Initialwidth: null },
        CurrentPrintTocId: "",
        WindowResizeSet: false,
        ZoomClasses: undefined,
        MobileMenuHeight: -1,
        LastHistoryStateId:0,
        Init:function(){
            ZP.DocView.InitPageControls();
            $('#cancel-print').click(ZP.DocView.HidePrintControl);
            $('#print-btn').click(ZP.DocView.PrintSelection);
            ZP.DocView.MobileMenuHeight = $("#TopDiv").height();
            ZP.DocView.InitBreadcrumbsWidthSync();
        },
        BreadcrumbsWidthObserver: null,
        InitBreadcrumbsWidthSync: function () {
            // #thePage-border, not #thePage-wrap: #thePage-wrap is a full-width (100%) wrapper, while
            // #thePage-border is the fit-content box that's actually centered and visible as "the page".
            var pageBorder = document.getElementById('thePage-border');
            var breadCrumbs = document.querySelector('#pageControls div.pageControls_inner.breadCrumbs .breadCrumbs');
            var pageControls = document.getElementById('pageControls');
            if (ZP.DocView.BreadcrumbsWidthObserver) {
                ZP.DocView.BreadcrumbsWidthObserver.disconnect();
                ZP.DocView.BreadcrumbsWidthObserver = null;
            }
            if (!pageBorder || !breadCrumbs) return;
            function sync() {
                // Runs at every screen size, including mobile: the plain-CSS mobile fallback this used to
                // defer to (width:48%) is commented out everywhere in ui.css, so on mobile breadCrumbs was
                // falling through to the unconditional width:100% rule, which resolves against #pageControls
                // (a much wider container than thePage-border, which shrinks to 80% of its own narrower
                // container on mobile) - making breadCrumbs wider than the page. Measuring thePage-border's
                // actual rendered box directly keeps this correct regardless of which breakpoint-specific
                // CSS thePage-border is under.
                // offsetWidth, not getBoundingClientRect(), so the transform:scale(...) applied to both
                // elements at each zoom level isn't double-counted. Uses the full outer width (scrollbar
                // gutter included) since breadCrumbs now sits flush above thePage-border (see customui.css
                // #thePage-border top/.breadCrumbs top+height) rather than overlapping it vertically.
                var w = pageBorder.offsetWidth;
                breadCrumbs.style.width = w + 'px';
                // ui.css's base rule sets right:0 and margin:0 auto (the classic left:0;right:0;margin:auto
                // centering trick). With right and the auto margins still active, the browser splits the
                // leftover space between the two margins, so writes to .style.left below only move the
                // rendered box by HALF the intended amount. Clearing right to auto makes left the sole
                // positioning authority again, restoring the 1:1 relationship the math here assumes.
                breadCrumbs.style.right = 'auto';
                // Measure where left:0 actually renders instead of assuming a position:relative/margin:auto
                // formula - customdoc.css overrides .breadCrumbs to position:absolute with its own left/width,
                // which uses a different containing block than the plain-CSS position:relative case.
                breadCrumbs.style.left = '0px';
                var baseLeft = breadCrumbs.getBoundingClientRect().left;
                var borderLeft = pageBorder.getBoundingClientRect().left;
                breadCrumbs.style.left = (borderLeft - baseLeft) + 'px';
            }
            sync();
            if (window.ResizeObserver) {
                ZP.DocView.BreadcrumbsWidthObserver = new ResizeObserver(sync);
                ZP.DocView.BreadcrumbsWidthObserver.observe(pageBorder);
                if (pageControls) ZP.DocView.BreadcrumbsWidthObserver.observe(pageControls);
            } else {
                $(window).on('resize', sync);
            }
        },
        InitializeZoom: function(zoomLevel){
            if ($.trim(zoomLevel) != "") ZP.DocView.SetZoom(parseInt(zoomLevel));
        },
        SaveZoomLevel: function (zoomLvl) {
            // Not much reason to show error messages, so there is no error handling 
            $.ajax({
                method: "POST",
                url: "doc-view-helper.aspx",
                data: { task: "savezoom", zoomLevel: zoomLvl }
            })
        },
        IncreaseZoom: function () {
            var zoomLevel = ZP.DocView.ChangeZoom(1);
            ZP.DocView.SaveZoomLevel(zoomLevel);
        },
        DecreaseZoom:function(){
            var zoomLevel = ZP.DocView.ChangeZoom(-1);
            ZP.DocView.SaveZoomLevel(zoomLevel);
        },
        ReadZoomLevel: function () {
            if (ZP.DocView.ZoomClasses === undefined) return 1;
            var cssClass = $("#doc-viewer").attr("class");
            if (cssClass === undefined || cssClass === null) cssClass = "";
            var maxZoomIndex = -1;
            for (var i = 0; i < ZP.DocView.ZoomClasses.length; i++) {
                if (cssClass.indexOf(ZP.DocView.ZoomClasses[i]) >= 0 && ZP.DocView.ZoomClasses[i] != "") maxZoomIndex = i;
            }
            if (maxZoomIndex == -1) maxZoomIndex = 1;
            return maxZoomIndex;
        },
        ChangeZoom: function (dif) {
            if (ZP.DocView.ZoomClasses === undefined) return 1;
            var zoomLevel = ZP.DocView.ReadZoomLevel();
            zoomLevel = zoomLevel + dif;
            if (zoomLevel < 0 || zoomLevel > ZP.DocView.ZoomClasses.length - 1) return zoomLevel -dif;
            ZP.DocView.SetZoom(zoomLevel);
            return zoomLevel;
        },
        SetZoom: function (zoomLevel) {
            if ( ZP.DocView.ZoomClasses === undefined) return;
            for (var i = 0; i <  ZP.DocView.ZoomClasses.length; i++) {
                $("#doc-viewer").removeClass(ZP.DocView.ZoomClasses[i]);
            }
            if (ZP.DocView.ZoomClasses[zoomLevel] == "") return;
            $("#doc-viewer").addClass(ZP.DocView.ZoomClasses.slice(0, zoomLevel + 1).join(" "));
        },
        DefaultZoom:function(){
            var zoomLevel = ZP.DocView.ReadZoomLevel();
            var newZoom = ZP.DocView.ChangeZoom(1 - zoomLevel);
            ZP.DocView.SaveZoomLevel(newZoom);
        },
        ReadElmtScale:function(elmt){
            var regx = /.*scale\(([^)]*)\).*/;
         
            var transform = elmt.css("transform");
            if (transform == "none") return 1; //TODO handle null or other possible cases
            var values = transform.match(/-?[\d\.]+/g);
            return parseFloat(values[0]);
        },
        BodyClick: function (e) {
            var subMenu = $('div.pageControls .right ul.submenu');
            if (!subMenu.hasClass('submenu-open')) return true;
            e.stopPropagation();
            ZP.DocView.PgCntrlOverflowClick();
        },
        PgCntrlOverflowClick: function (e) {
            if (e != null) {
                e.stopPropagation();
                e.preventDefault();
            }
            var subMenu = $('div.pageControls .right ul.submenu');
            subMenu.toggleClass('submenu-open');
            if (subMenu.hasClass('submenu-open')) {
                subMenu.show(200);
                subMenu.find("a").first().focus();
            }
            else subMenu.hide(200);
        },
        OpenUnsubscribeDlg: function () {
            ZP.DocView.ClearSubscriptionDialog();
            ZP.DocView.CreateSubscriptionDialog("Unsubscribe from Notifications", 300);
            var target = $(event.target);
            ZP.DocView.LoadSubscriptionDialog(target.attr("href"));
        },
        OpenSubscribeDlg: function () {
     
            ZP.DocView.ClearSubscriptionDialog();
            ZP.DocView.CreateSubscriptionDialog("Subscribe to Notifications", 520);
            var target = $(event.target);
            ZP.DocView.LoadSubscriptionDialog(target.attr("href")+"?chkdef=1");
        },
        LoadSubscriptionDialog: function (url) {
            $.get(url, function (result) {
                ZP.DocView.InsertSubscriptionForm(result);
                ZP.DocView.AddSubscriptionFormHandler();
            }, 'html');
        },
        AddSubscriptionFormHandler: function(){
            $("#sub-form-cntr form").submit(function (e) {
                e.preventDefault();
                $.post($("#sub-form-cntr form").attr("action"), $('#sub-form-cntr form').serialize(), function (response) {
                    var json = $.parseJSON(response);
                    ZP.DocView.ClearSubscriptionDialog();
                    if (json.StatusMsg.length > 0) {
                        $("#sub-message").html(json.StatusMsg);
                        $("#sub-message").closest("div.ui-dialog[tabindex]").focus();
                    } else {
                        ZP.DocView.InsertSubscriptionForm(json.Data);
                        ZP.DocView.AddSubscriptionFormHandler();
                    }
                });
            });
        },
        CreateSubscriptionDialog: function (title, hgt) {         
            $("#subscribe-dialog").dialog({
                resizable: false,
                height: hgt,
                width: 400
            });
            $('#subscribe-dialog').dialog('option', 'title', title);
            $(".ui-dialog").css("z-index", 10);
        },
        ClearSubscriptionDialog: function () { $("#sub-form-cntr").html(""); $("#sub-message").html("");},
        InsertSubscriptionForm: function(html){
            $result = $(html);
            $result.filter(function (index) { return $(this).attr("id") == "subscribe-cntr"; }).appendTo('#sub-form-cntr');
            $('#sub-form-cntr h2').remove();
            $result.filter(function (index) { return $(this).attr("id") == "captcha-script"; }).appendTo('#sub-form-cntr');
            $('#sub-form-cntr').closest("div.ui-dialog[tabindex]").focus();
        },
        GetTocId: function (hashval, defaultId) {
            if (defaultId == null || defaultId == undefined || defaultId == '') defaultId = 't000';
            if (hashval == null || hashval == undefined || hashval == '') return defaultId;
            if (hashval.substring(0, 7) == "#tocid-") return 't' + hashval.substring(7);
            if (hashval.substring(0, 7) == "#secid-") {
               var tocid = 's' + hashval.substring(7);
               if (tocid.indexOf("xr") >= 0) {
                   tocid = tocid.substring(0, tocid.indexOf("xr"));
               }
               if (tocid.indexOf("bk") >= 0) {
                   tocid = tocid.substring(0, tocid.indexOf("bk"));
               }
               return tocid;
            }
            if (hashval.substring(0, 7) == "#catid-") return 'c' + hashval.substring(7);
            return defaultId;
        },
        HashChanged: function (e, defaultTocId, params) {
            var tocid = ZP.DocView.GetTocId(window.location.hash, defaultTocId);
            if (tocid == null || tocid == undefined || tocid == '') return;
            ZP.DocView.LoadDoc(tocid, params);
        },
        LoadNextDoc: function (tocid, params) {
            if (tocid == null || tocid == undefined || tocid == '') return false;
            ZP.DocView.HidePrintControl();
            if (params == null || params == undefined) params = '';
            $.get('doc-view-helper.aspx?tocid=' + tocid + '&task=nextsecid&' + params, function (data) {
                if (data == undefined|| data == null || $.trim(data) == "") return;
                window.location.hash = "secid-" + data;
            });
        },
        LoadPrevDoc: function (tocid, params) {
            if (tocid == null || tocid == undefined || tocid == '') return false;
            ZP.DocView.HidePrintControl();
            if (params == null || params == undefined) params = '';
            $.get('doc-view-helper.aspx?tocid=' + tocid + '&task=prevsecid&' + params, function (data) {
                if (data == undefined || data == null || $.trim(data) == "") return;
                window.location.hash = "secid-" + data;
            });
        },
     
        LoadDoc: function (tocid, params, updateTOC) {
            if (tocid == null || tocid == undefined || tocid == '') return false;
            ZP.DocView.HidePrintControl();
            if (updateTOC == null || updateTOC == undefined || updateTOC == '') updateTOC == false;
            if (params == undefined) params = '';
            if ($.isArray(params)) params = params.join('&');
            const urlParams = new URLSearchParams(window.location.search);
            const language = urlParams.get('language');
            if (language && !params.includes('language'))
                params = params + "&language=" + language;
            var progress = setTimeout(ZP.DocView.ShowProgress, 400);
            var tocParam
            switch (tocid.charAt(0)) {
                case 's': tocParam = 'secid=' + tocid.substring(1); break;
                case 't': tocParam = 'tocid=' + tocid.substring(1); break;
                case 'c': tocParam = 'catid=' + tocid.substring(1); break;
                default: tocParam = 'tocid=' + tocid;
            }
            ZP.DocView.HideDef();
            if (params != null && params != "" && params.charAt(0) != '&') params = '&' + params;
            $.get('doc-view.aspx?ajax=0&' + tocParam + params, function (xdata) {
                clearTimeout(progress);
                var dv = $('#doc-view');
                dv.css('visibility', 'hidden');
                dv.html($(xdata).find('#doc-view-content'));
                
                //The native browser scrolling to an elmenent whose ID is in the hash for some reason slightly scrolls the center-content div.  The following code compenstates for that.
                $("#center-content").on('scroll', function () {
                    $("#center-content").scrollTop(0);
                });
               
                //setTimeout(_loadComplete, 800);
                _loadComplete();
            });
            function _loadComplete() {
                $('#thePage img.thumbnail').bind('click', ZP.DocView.ThumbnailDialog);
                $('#thePage table.sec_comments a.fa-reply').click(ZP.DocView.CommentReplyClick);
                ZP.DocView.InitTwitter();
                ZP.DocView.WindowResize();
                ZP.DocView.HideCommentsForm();
                ZP.DocView.ScrollAfterLoading();
                $("section").attr("tabindex", "-1");
                if (ZP.DocView.OnDocLoad != undefined && typeof ZP.DocView.OnDocLoad == 'function')
                    ZP.DocView.OnDocLoad($('#thePage').attr('tocid'));
                if (updateTOC)
                    if (ZP.DocView.OnUpdateTOC != undefined && typeof ZP.DocView.OnUpdateTOC == 'function')
                        ZP.DocView.OnUpdateTOC(tocid);
                ZP.DocView.InitBreadcrumbsWidthSync();

                setTimeout(function () {


				$('#doc-view').css('visibility', 'visible'); 
					ZP.DocView.CallFunctionAfterRepaint(function(){
                        EC.SortedTable.Init(".ord-tbl, .stat-tbl, .sortable"); 
                        if (!ZP.DoNotSetFixedTable)
                            EC.FixedTableHd.Init("table.general:not(.ord-tbl,.stat-tbl),table.fixed-header");
                        if (ZP.SetFixedTableOrdinance) {
                            EC.FixedTableHd.Init("table.ord-tbl,table.stat-tbl,table.fixed-header");
							var elements = document.getElementsByClassName("table.ord-tbl span.sort-icon");
							for (var i=0, element; element = elements[i]; i++)
							{
								console.log(element);
							}
						}
						if(EC.Tabs && EC.Tabs.PositionLeftTabs)EC.Tabs.PositionLeftTabs();},20)

                }, 200);



                if (ZP.TOCView) {
                    if (typeof ZP.TOCView.BindTreeView === 'function') {
                        ZP.TOCView.BindTreeView();
                    }
                }

                var selectedElement = document.querySelector('[aria-selected="true"]');

                if (selectedElement && typeof selectedElement.focus === 'function') {
                    selectedElement.focus();
                }

            }
        },
		
		CallFunctionAfterRepaint: function (callback, repaintCount) {
            if (!callback) return;
            if (repaintCount == 0) {
                callback();
                return;
            }

            var innerFunc = function (clback, cnt, tm) {
                if (tm) clearTimeout(tm);
                if (cnt == 0) {
                    clback();
                } else {
                    tm = setTimeout(clback, 1000);
                    window.requestAnimationFrame(function () { innerFunc(clback, cnt - 1,tm); })
                }

            }
            innerFunc(callback, repaintCount);
        },
        ScrollAfterLoading:function(){
            if (history.state == null) {
                var hash = window.location.hash;
                if (hash.indexOf("bk") >= 0) {
                   
                    if (hash.substring(hash.indexOf("bk")).indexOf("-") >= 0) {
                        var bkMarkId = hash.substring(hash.indexOf("bk") + 2).replace("-", "bk");
                        bkMarkId = bkMarkId.substring(0, bkMarkId.indexOf("_"));
                        ZP.DocView.ScrollToDocElmt($("#secid-" +bkMarkId), 0);
                    } else {
                        ZP.DocView.ScrollToDocElmt($(hash), 0);
                    }
                   
                }
                if (hash.indexOf("xr") >= 0) {
                    var secid = hash.substring(hash.indexOf("xr") + 2);
                    secid = secid.substring(0, secid.indexOf("_"));
                    ZP.DocView.ScrollToDocElmt($("#secid-" + secid), 0);
                }
                history.replaceState({ position: ZP.DocView.GetDocViewerScrollPosition(), id: ZP.DocView.GetNextHistoryId() }, '', window.location.href);
            } else {
                ZP.DocView.ScrollToPosition(history.state.position);
            }
            ZP.DocView.LastHistoryStateId = history.state.id;
        },
        ThumbnailDialog: function (e) {
            var td = $("#thumbnail-dialog");
            if (td == null || td.length == 0) { $('#doc-viewer').after("<div id='thumbnail-dialog'></div>"); td = $("#thumbnail-dialog"); }
            var i = $(e.target).clone();
            i.height('auto');
            i.width('auto');
            td.empty().append(i);
            td.dialog({ autoOpen: true, height: 'auto', width: 'auto', title: i.attr('alt') });
            return false;
        },
        InitDef: function _InitDef() {
            $('#doc-viewer').delegate('.iLink', 'mouseenter', ZP.DocView.ShowDef);
            $('#doc-viewer').delegate('.iLink', 'mouseleave', ZP.DocView.HideDef);
            $('#doc-viewer').delegate('.iLink', 'click', ZP.DocView.OpenDef);
            $('#doc-viewer').delegate('.xref', 'click', ZP.DocView.OpenXRef);
            $('#doc-viewer').delegate('section .tocLink', 'click', ZP.DocView.OpenTOCLink);
            $('#doc-viewer').delegate('.popup', 'click', ZP.DocView.OpenPopup);
            $('#thePage img.thumbnail').bind('click', ZP.DocView.ThumbnailDialog);
            $('#defFrame').on('mouseenter', function () { clearTimeout(ZP.DocView._hideDefTimer); });
            $('#defFrame').on('mouseleave', ZP.DocView.HideDef);
        },
        InitTwitter: function () {
       },
        OpenDef: function (eventargs) {
            if (ZP.DocView.OpenDefinitionMode == null) return true;
            params = ZP.DocView.OpenDefinitionMode.split(':');
            var winTarget; var winSettings;
            if (params.length > 0) winTarget = params[0];
            if (params.length > 1) winSettings = params[1];

            if (ZP.DocView.OpenDefinitionPage != null) $(eventargs.target).attr('href', $(eventargs.target).attr('href').replace(/^doc-view(er)?.aspx/i, ZP.DocView.OpenDefinitionPage));

            if (winSettings == null || winSettings == '_self') { $(eventargs.target).attr('target', '_self'); return true; }
            var language = ZP.DocView.GetLanguage();
            var hiddenParameter = "&h=0";
            if (ZP.DocView.ShowHiddenDefinitions && ZP.DocView.ShowHiddenDefinitions == true) {
                hiddenParameter = "&h=1";
            }
            window.open($(eventargs.target).attr('href') + "&language=" + language + hiddenParameter, winTarget, winSettings);
            return false;
        },
      
        GetNextHistoryId:function(){
            if (!window.sessionStorage.getItem("historyId")) {
                window.sessionStorage.setItem("historyId", JSON.stringify({ id:1}));
                return 1;
            } else {
                var historyId = JSON.parse(window.sessionStorage.getItem("historyId")).id;
                window.sessionStorage.setItem("historyId", JSON.stringify({ id: historyId + 1 }));
                return historyId + 1;
            }
        },
        GetNextXrefId:function(){
            if (!window.sessionStorage.getItem("xrefId")) {
                window.sessionStorage.setItem("xrefId", JSON.stringify({ id: 1 }));
                return 1;
            } else {
                var xrefId = JSON.parse(window.sessionStorage.getItem("xrefId")).id;
                window.sessionStorage.setItem("xrefId", JSON.stringify({ id: xrefId + 1 }));
                return xrefId + 1;
            }
        },
        RecordScrollPosition:function(){
            if (!history.state) {
                history.replaceState({ position: ZP.DocView.GetDocViewerScrollPosition(), id: ZP.DocView.GetNextHistoryId() }, '', window.location.href);
            } else {
                history.replaceState({ position: ZP.DocView.GetDocViewerScrollPosition(), id: history.state.id }, '', window.location.href);
            }
        },
        OpenTOCLink: function(){
            ZP.DocView.RecordScrollPosition();
            ZP.DocView.LastHistoryStateId = history.state.id;
        },
        OpenXRef: function (eventargs) {
            ZP.DocView.RecordScrollPosition();
           
            ZP.DocView.LastHistoryStateId = history.state.id;
            if (ZP.DocView.XrefTargetAlreadyInView(eventargs)) {
                var anchor = $(eventargs.target);
                var hrf = anchor.attr("href");
                var windowHref = window.location.href;
                var hrfHash = hrf.substring(hrf.indexOf("#"));
                var secidRg = new RegExp('#secid-[0-9]+');
                if (hrfHash.indexOf("bk") == -1) {
                    if (hrfHash.indexOf("_") >= 0) {
                        var newHref = windowHref.substring(0, windowHref.indexOf("#")) + hrfHash.substring(0, hrfHash.indexOf("_")) + "_" + ZP.DocView.GetNextXrefId();
                        anchor.attr("href", newHref);        
                    } else {
                        hrfHash = hrfHash.replace("#secid-", "xr");
                        if (secidRg.test(window.location.hash)) {
                            var match = secidRg.exec(window.location.hash);
                            var newHref = windowHref.substring(0, windowHref.indexOf("#")) + match[0] + hrfHash + "_" + ZP.DocView.GetNextXrefId();
                            anchor.attr("href", newHref);
                        }
                    }
                    
                } else {
                    if (hrfHash.indexOf("_") >= 0) {
                        var newHref = windowHref.substring(0, windowHref.indexOf("#")) + hrfHash.substring(0, hrfHash.indexOf("_")) + "_" + ZP.DocView.GetNextXrefId();
                        anchor.attr("href", newHref);
                    } else {
                        hrfHash = hrfHash.replace("bk", "-");
                        hrfHash = hrfHash.replace("#secid-", "bk");
                        if (secidRg.test(window.location.hash)) {
                            var match = secidRg.exec(window.location.hash);
                            var newHref = windowHref.substring(0, windowHref.indexOf("#")) + match[0] + hrfHash + "_" + ZP.DocView.GetNextXrefId();
                            anchor.attr("href", newHref);
                        }
                    }
                   
                }
              
            }
            if (ZP.DocView.OpenXRefMode == null) return true;
           
            
            params = ZP.DocView.OpenXRefMode.split(':');
            var winTarget; var winSettings;
            if (params.length > 0) winTarget = params[0];
            if (params.length > 1) winSettings = params[1];
            if (ZP.DocView.ScrollToXref(eventargs)) return false;
            if (!$(eventargs.target).attr('href')) return false;
            if (ZP.DocView.OpenXRefPage != null ) {
                $(eventargs.target).attr('href', $(eventargs.target).attr('href').replace(/^doc-view(er)?.aspx.*&(secid)=/i, ZP.DocView.OpenXRefPage));
                $(eventargs.target).attr('href', $(eventargs.target).attr('href').replace(/^doc-view(er)?.aspx.*&(tocid)=/i, ZP.DocView.OpenXRefPage));
            }

           
            if (winSettings == null || winSettings == '_self') { $(eventargs.target).attr('target', '_self'); return true; }
            window.open($(eventargs.target).attr('href'), winTarget, winSettings);
            return false;
        },
        XrefTargetAlreadyInView: function (eventargs) {
            var anchor = $(eventargs.target);
            var hrf = anchor.attr("href");
            if (!hrf) return false;
            var hrfHash = hrf.substring(hrf.indexOf("#"));
            if (hrfHash.indexOf("xr") >= 0) {
                var secid = hrfHash.substring(hrfHash.indexOf("xr") + 2);
                secid = secid.substring(0, secid.indexOf("_"));
                return $("#secid-" + secid).length > 0;
            }
            if (hrfHash.indexOf("bk") >= 0 && hrfHash.indexOf("_") >= 0) {
                var bkMarkId = hrfHash.substring(hrfHash.indexOf("bk") + 2).replace("-", "bk");
                bkMarkId = bkMarkId.substring(0, bkMarkId.indexOf("_"));
                return $("#secid-" + bkMarkId).length > 0;
            }

            try {
                if ($(hrfHash).length > 0) return true;
            }
            catch {
                return false;                
            }
            
            return false;
        },
        ScrollToXref: function (eventargs) {
            return false;

        },
        GetDocViewerScrollPosition: function () {
            var firstSec = $("#thePage section").first();
            var scrollParent = ZP.DocView.FindScrollingParent(firstSec);
            if (!scrollParent) return 0;
            return scrollParent.scrollTop();
        },
        ScrollToPosition:function(pos){
            var firstSec = $("#thePage section").first();
            var scrollParent = ZP.DocView.FindScrollingParent(firstSec);
            if (!scrollParent) return;
            scrollParent.scrollTop(pos);
        },
        ScrollToDocElmt: function (elmt, duration) {

            if (duration == null) duration = 500;
            var scrollParent = ZP.DocView.FindScrollingParent(elmt);
                    if (!scrollParent) return false;
                    
            var elmtOffset = elmt.offset();
                    var currentScrollTop = scrollParent.scrollTop();
                    var scrollOffset = scrollParent.offset();
                    var zoomFactor = ZP.DocView.GetZoomFactor();
            var offsetDif = scrollOffset.top - (elmtOffset.top / zoomFactor);
                    var targetScrollTop = currentScrollTop - offsetDif;
                    if (scrollParent.prop("tagName").toLowerCase() == "html") {
                targetScrollTop = elmtOffset.top - ZP.DocView.MobileMenuHeight;
                    }
            elmt.focus();  // focus first - focusing afer scrolling may scroll the element out of view - especially in mobile views
            scrollParent.stop().animate({ scrollTop: targetScrollTop }, duration);
           
                    return true
        },
        FindScrollingParent: function (elmt) {
            var ancestors = elmt.parents();
            for (var i = 0; i < ancestors.length; i++) {
                var anc = $(ancestors[i]);
                var overflowY = $.trim(anc.css('overflow-y')).toLowerCase();
                var position = $.trim(anc.css('position')).toLowerCase();
                if ((overflowY == "auto" || overflowY == "scroll") && (position == "relative" || position == "absolute")) {
                    if (anc.prop("tagName").toLowerCase() == "body") return $("html");
                    return anc;
                    
                }
            }
            return null;
        },
        GetZoomFactor: function () {
            var zoomLvl = 10;
            while (zoomLvl > -2) {
                var zoomClass = zoomLvl >= 0 ? ".Zoom" + zoomLvl : ".Unzoom" + (-zoomLvl);
                var zoomElements = $(zoomClass);         
                if (zoomElements.length > 0) {
                    if (zoomLvl > 0) return 1 + .2 * zoomLvl;
                    return .8;
                }             
                zoomLvl = zoomLvl - 1;
            }
            return 1;
        },
        OpenPopup: function (eventargs) {
            var winTarget = "_blank"; var winSettings = $(eventargs.currentTarget).attr('params');
            if (winSettings == null || winSettings == undefined || winSettings == "") winSettings = "toobar=0,menubar=0,scrollbars=1,height=900,width=600";
            window.open($(eventargs.currentTarget).attr('href'), winTarget, winSettings);
            return false;
        },       
        ShowDef: function _ShowDef(eventArgs) {
            clearTimeout(ZP.DocView._hideDefTimer);
            var defFrame = $("#defFrame");
            var scale = ZP.DocView.ReadElmtScale($("#thePage-wrap"));
            if (scale === undefined || scale === null || scale <= 0) scale = 1;
            var w = $(window).width();
            var h = $(window).height();
            var p = $('#pageControls');
            if (p.offset() == null || p.offset() == undefined) p = $('#doc-view'); //support webview.aspx
            var t = $(eventArgs.target).offset().top - $(window).scrollTop();
            var l = $(eventArgs.target).offset().left + scale*($(eventArgs.target).width() / 2);
            var popUpWidth = defFrame.width();
            var scaleDif = scale - 1;
            var halfScaleDif = scaleDif / 2;
            l = l + scaleDif * popUpWidth / 2;
          
       

            var href = $(eventArgs.target).closest("a").attr("href");
            if (!href) return;

            var language = ZP.DocView.GetLanguage();
            href = href.replace(/^doc-view(er)?.aspx/i, "viewdef.aspx");
            href = href + "&language=" + encodeURIComponent(language);
            defFrame.load(href, _showDefPopup);
            function _showDefPopup() {
                // prevent popup from being placed on top of page controls
                // keep a minimum of 10px space between top edge of popup and bottom edge of page controls
                if ((p.offset().top + p.height()) > (t - scale * defFrame.height() - 10)) {
                    t = t + halfScaleDif * defFrame.height() + $(eventArgs.target).height()*scale + 2;// 2 creates 2px distance between top of popup and bottom of definition link
                }
                else {
                    t = t - (1 + halfScaleDif) * defFrame.height() - 10;
                }
                // prevent popup from being placed outside right window edge
                // keep a minimum of 10px space between right edge of popup and right edge of window
                if (l + (1+halfScaleDif) * popUpWidth +10 > w) l = w - (1 + halfScaleDif) * popUpWidth - 10;
                defFrame.css('top', t);
                defFrame.css('left', l);
                defFrame.fadeIn(600);
            }
        },
        GetLanguage: function () {
            const urlParams = new URLSearchParams(window.location.search);
            var language = urlParams.get('language');
            if (!language) {
                language = "en";
            }
            return language;    
        },
        HideDef: function _HideDef(eventArgs) {
            ZP.DocView._hideDefTimer = setTimeout(function () {
                $("#defFrame").stop().hide().html('<img src="resources/progress.gif" alt="Loading Image"/>');
            }, 150);
        },
        OpenWord: function (id, isCategory) {
            var mURL = "export2doc.aspx?doctype=d&tocid=" + id; // +"&module=User"
            if (isCategory) mURL = "export2doc.aspx?pdf=1&catid=" + id; // +"&module=User"
            aPopup = window.open(mURL, 'myDoc', 'toolbar=no,location=no,directories=no,status=no,scrollbars=yes,resizable=yes,copyhistory=no,left=20,top=20,width=500,height=500');
        },
        OpenPDF: function _OpenPDF(id,isCategory) {
            var mURL = "export2doc.aspx?pdf=1&tocid=" + id; // +"&module=User"
            if (isCategory)  mURL = "export2doc.aspx?pdf=1&catid=" + id; // +"&module=User"
            aPopup = window.open(mURL, 'myPDF', 'toolbar=no,location=no,directories=no,status=no,scrollbars=yes,resizable=yes,copyhistory=no,left=20,top=20,width=500,height=500');
        },
        ShowProgress: function () { $('#doc-view-content').empty().html($('#progress-template .progress').clone()); },
        OnDocLoad: function () { },
        OnRezise: function () { },
        OnUpdateTOC: function () { },
        ShowCommentsForm:function (threadId) {
            var showing = false;
            return function (threadId) {
                if (showing) return;
                showing = true;
                ZP.DocView.commentsVisible = true;
                var c = $("#commentsCTA");
                c.unbind("click", ZP.DocView.ShowCommentsForm);
                c.unbind("keydown", ZP.DocView.ExitCommentsDlg);
                var secid = $('#thePage').attr('secid');
                if (ZP.DocView.comments.Initialhtml == null) ZP.DocView.comments.Initialhtml = c.html();
                if (ZP.DocView.comments.Initialwidth == null) ZP.DocView.comments.Initialwidth = c.width();
                c.animate({ width: 430 }, 400, function () {
                    showing = false;
                    var threadParam = (threadId != null && !isNaN(threadId) && threadId > 0) ? "&threadid=" + threadId : "";
                    c.load('commentsForm.aspx?secid=' + secid + threadParam, function () {
                        c.find("select").first().focus();
                        c.bind("keydown", ZP.DocView.ExitCommentsDlg);
                        c.attr("role", "");                
                    });
                });
              


            } //end ShowComments inner function
        }(0), //end showCommentsForm
        ExitCommentsDlg: function(ev){
            if (ev.which == 27) {
                $("input[value='Cancel']").click();
            }
        },
        HideCommentsForm: function () {
            if (!ZP.DocView.commentsVisible) return;
            var c = $("#commentsCTA");
            c.html(ZP.DocView.comments.Initialhtml);
            c.animate({ width: ZP.DocView.comments.Initialwidth }, 400, function () {
                ZP.DocView.commentsVisible = false;
                c.click(ZP.DocView.ShowCommentsForm);
            });
            c.attr("role", "button");
        },
        SubmitComments: function () {
            ZP.DocView.StartModalProgress();
            $.post($("#commentForm-form").attr('action'), $("#commentForm-form").serialize(), postComplete);
            setTimeout(ZP.DocView.StopModalProgress, 5000);
            function postComplete(data) {
                ZP.DocView.StopModalProgress();
                $("#commentForm").replaceWith($(data));
                setTimeout(ZP.DocView.HideCommentsForm, 4000);
            }
        },
        SelectCommentSubSection: function () {
            $.get($("#commentForm-subsections").attr('action'), $("#commentForm-subsections").serialize(), getComplete);
            function getComplete(data) {
                $("#commentForm").replaceWith($(data));
                $("#commentForm").find("input").first().focus();
            }
        },
        SubmitCommentsPwd: function () {
            $.post($("#commentForm-pwd").attr('action'), $("#commentForm-pwd").serialize(), postComplete);
            function postComplete(data) {
                $("#commentForm").replaceWith($(data));
            }
        },
        CommentReplyClick: function (e) {
            e.preventDefault();
            var threadId = $(e.currentTarget).attr("data-threadId");
            ZP.DocView.ShowCommentsForm(threadId);
            return false;
        },
        PrintDoc: function (id,isCategory) {
            ZP.DocView.StartModalProgress();
           
            $("#printiframe").attr("src", 'doc-view.aspx?tocid=' + id + '&print=1');
            
          
            setTimeout(ZP.DocView.StopModalProgress, 30000);
        },
        PrintDocSelections: function (id,isCategory) {
            if (isCategory) {
                $("#printiframe").attr("src", 'doc-view.aspx?catid=' + id + '&print=1');
                setTimeout(ZP.DocView.StopModalProgress, 30000);
            } else {
                ZP.DocView.ShowPrintControl(id);
                if (id != ZP.DocView.CurrentPrintTocId) {
                    $("#print-control-inner").html("");
                    $("#print-load-progress").css("display", "block");
                    $.get('component.aspx?name=PrintSelect&tocid=' + encodeURIComponent(id), function (response) {
                        $("#print-load-progress").hide();
                        $("#print-control-inner").html(response);
                        ZP.DocView.RegisterPrintControlHandlers();
                        ZP.DocView.ScrollPrintControl(id);
                        ZP.DocView.CurrentPrintTocId = id;
                    });
                }
            }
        },
        PrintSelection: function () {
            ZP.DocView.StartModalProgress();
            var selections = $("#print-control form").submit();
            setTimeout(ZP.DocView.StopModalProgress, 30000);
        },
        InitPageControls: function () {
            $('body').click(ZP.DocView.BodyClick);
        },
        HidePrintControl: function () {
            $('#print-control').removeClass("expanded");
            $("#button1").focus();
        },
        ShowPrintControl: function (tocid) {
            $('#print-control').addClass("expanded");
            $('#print-control').focus();
        },
        ScrollPrintControl: function (tocid) {
            $("#print-control-med").scrollTop(0);
            var section = $("#print-control-inner input[type='checkbox'][data-tocid='" + tocid + "']").closest("li").position();
            if (section !== undefined) $("#print-control-med").scrollTop(section.top - $("#print-control-med").position().top-5);
        },
        RegisterPrintControlHandlers:function(){
            $("#print-control-inner input[type='checkbox']").click(ZP.DocView.PrintCheckBxClickHandler);
            $("#print-control-inner li .expander").click(ZP.DocView.PrintFolderClickHandler);
        },
        PrintCheckBxClickHandler:function(){
            var clickedChkBox = $(this);
            var descendants = ZP.DocView.GetDescendantPrintTocCheckboxes(clickedChkBox.attr("data-tocid"));
            var checkValue = clickedChkBox.prop("checked");
            $.each(descendants, (function (index, value) { value.prop("checked", checkValue); }));
        },
        PrintFolderClickHandler: function () {
            var clickedIcon = $(this);
         
            if (clickedIcon.attr("data-state") == "expanded") {
                var descendants = ZP.DocView.GetDescendantPrintTocCheckboxes(clickedIcon.attr("data-tocid"));
                $.each(descendants, (function (index, value) {
                    value.closest("li").hide();
                    value.closest("li").find(".expander").attr("src", "resources/browserimages/folder_closed.gif").attr("data-state", "collapsed");
                    value.closest("li").find(".expander i").removeClass("fa-folder-open").addClass("fa-folder");
                    value.closest("li").find(".expander span").each(function () { $(this).text($(this).text().replace("Collapse", "Expand")); });
                }));
            } else {
                var children = ZP.DocView.GetChildrenPrintLis(clickedIcon.attr("data-tocid"));
                $.each(children, (function (index, value) {
                    value.closest("li").show();}))
            }

            if (clickedIcon.attr("data-state") == "expanded") {
                clickedIcon.attr("data-state", "collapsed");
                clickedIcon.attr("src", "resources/browserimages/folder_closed.gif");
                clickedIcon.closest("li").find(".expander i").removeClass("fa-folder-open").addClass("fa-folder");
                clickedIcon.closest("li").find(".expander span").each(function () { $(this).text($(this).text().replace("Collapse", "Expand")); });
            } else {
                clickedIcon.attr("data-state", "expanded");
                clickedIcon.attr("src", "resources/browserimages/folder_open.gif");
                clickedIcon.closest("li").find(".expander i").removeClass("fa-folder").addClass("fa-folder-open");
                clickedIcon.closest("li").find(".expander span").each(function () { $(this).text($(this).text().replace("Expand", "Collapse")); });
            };
            return false;
        },
        GetDescendantPrintTocCheckboxes:function(tocid){
            var descendants = [];
            if (tocid == undefined || $.trim(tocid)=="" ) return descendants;
            $("#print-control-inner input[type='checkbox']").each(function (index) {
                var ckBox = $(this);
                var tcID = ckBox.attr("data-tocid");
                if (tcID !== undefined && tcID.substring(0, tocid.length) == tocid && tcID != tocid) { descendants.push(ckBox); }
            });
            return descendants;
        },
        GetChildrenPrintLis: function (tocid) {
            var children = [];
            if (tocid == undefined || $.trim(tocid) == "") return children;
            $("#print-control-inner input[type='checkbox']").each(function (index) {
                var ckBox = $(this);
                var liTocId = ckBox.attr("data-tocid");
                if (liTocId !== undefined && liTocId.substring(0, tocid.length) == tocid && liTocId.length == tocid.length + 4) { children.push(ckBox.closest("li")); }
            });
            return children;
        },
        IFrameReady: function () {
            var iframeWindow = document.getElementById('printiframe').contentWindow;
            if (iframeWindow.iframeReady == undefined) return;
            iframeWindow.iframeReady = true;
        },
        PrintIframe: function (tocid) {
            ZP.DocView.StopModalProgress();
            window.printiframe.focus(); 
			try {
				 if (!window.printiframe.document.execCommand('print', false, null)) window.frames[printiframe].print();
			} catch(e) {
				 window.printiframe.print();
			}
        },
        StartModalProgress: function () {
            $('body').append("<div id='modalProgress'><img src='maintain/resources/progress-2.gif'/></div>");
        },
        StopModalProgress: function () {
            $('#modalProgress').remove();
        },
        WindowResize: function () { ZP.DocView.WindowResize_lft(); },
        WindowResize_rgt: (function () {
            var resizing = 0;
            var resizeTimer = null;
            var lastwidth = 0;
            return function () {
                if (resizing > 2) return;
                resizing++;
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(resizeDocView, 200);

                function resizeDocView() {
                    var w = $(window);
                    var cc = $('#center-content');
                    var b = $('body');
                    var mb = $('#main-body');
                    var tp = $("#thePage-wrap");
                    var pc = $("#pageControls");
                    var f = $("#main-body-footer");
                    var ls = $('#doc-viewer #left-splitter');
                    if (parseInt(b.css('min-width')) > w.width()) {
                        ls.css('left', '780px');
                    }

                    if (cc != null && cc != undefined && cc.offset() != null) {
                        cc.width(ls.offset().left - 6);
                    }
                    if (ZP.DocView.OnResize != undefined && typeof ZP.DocView.OnResize == 'function')
                        ZP.DocView.OnResize();
                    resizing = 0;
                    function getcssval(x) {
                        var y = parseInt(x);
                        return y;
                    }
                } //end of resizeDocView
            } //end of WindowResize inner anonymous function
        })(), //end of WindowResize outer closure
        WindowResize_lft: (function () {
            var resizing = 0;
            var resizeTimer = null;
            var lastwidth = 0;
            return function () {
                if (resizing > 2) return;
                resizing++;
                clearTimeout(resizeTimer);
                resizeTimer = setTimeout(resizeDocView, 200);

                function resizeDocView() {
                    var w = $(window);
                    var cc = $('#center-content');
                    var tp = $("#thePage-outer");
                    var pc = $("#pageControls");
                    var ls = $('#doc-viewer #left-splitter');
                    if (tp != null && tp != undefined && tp.css('position') == 'relative') {
                        tp.height(cc.height() - tp.position().top - getcssval(tp.css('padding-top')) - getcssval(tp.css('padding-bottom')) - getcssval(pc.css('height')));
                    }
                    if (ZP.DocView.OnResize != undefined && typeof ZP.DocView.OnResize == 'function')
                        ZP.DocView.OnResize();
                    resizing = 0;

                    function getcssval(x) {
                        var y = parseInt(x);
                        return y;
                    }
                } //end of resizeDocView
            } //end of WindowResize inner anonymous function
        })()//end of WindowResize outer closure
    } //end of ZP.DocView
    ZP.DocView.commentsVisible = false;
    ZP.DocView.OpenDefinitionPage = null;
    ZP.DocView.OpenXRefPage = null;
    ZP.DocView.OpenDefinitionMode = null;
    ZP.DocView.OpenXRefMode = null;
  
    $(document).ready(function () {
        $("#commentsCTA").bind("click", ZP.DocView.ShowCommentsForm);
        ZP.DocView.Init();
    });
})(window, jQuery);                                                                                         //end of immediate function wrapper
