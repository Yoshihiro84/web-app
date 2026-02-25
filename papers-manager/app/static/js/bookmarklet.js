(function(){
  var S = "__SERVER__";

  /* ---- Extract metadata ---- */
  function gM(s){for(var i=0;i<s.length;i++){var e=document.querySelector(s[i]);if(e&&e.content)return e.content.trim()}return""}
  function gA(s){var v=[];s.forEach(function(sl){document.querySelectorAll(sl).forEach(function(e){if(e.content)v.push(e.content.trim())})});return v}
  var m={};var h=location.hostname;
  if(h.indexOf("arxiv.org")>=0){
    var te=document.querySelector(".title.mathjax");
    m.title=te?te.textContent.replace(/^Title:\s*/i,"").trim():"";
    var ae=document.querySelector(".authors");
    m.authors=ae?ae.textContent.replace(/^Authors:\s*/i,"").trim():"";
    var ab=document.querySelector(".abstract.mathjax");
    m.abstract=ab?ab.textContent.replace(/^Abstract:\s*/i,"").trim():"";
    var mx=location.pathname.match(/\/abs\/(.+)/);
    if(mx)m.arxiv_id=mx[1].replace(/v\d+$/,"");
  }else if(h.indexOf("scholar.google")>=0){
    var e=document.querySelector(".gs_ri");
    if(e){var tl=e.querySelector(".gs_rt a");m.title=tl?tl.textContent.trim():"";
    var au=e.querySelector(".gs_a");if(au){var p=au.textContent.split(" - ");m.authors=p[0]||"";
    if(p[1]){var ym=p[1].match(/(\d{4})/);if(ym)m.year=parseInt(ym[1]);m.journal=p[1].replace(/,?\s*\d{4}/,"").trim()}}
    var sn=e.querySelector(".gs_rs");m.abstract=sn?sn.textContent.trim():""}
  }else{
    m.title=gM(['meta[name="citation_title"]','meta[name="DC.title"]','meta[property="og:title"]'])||document.title;
    m.authors=gA(['meta[name="citation_author"]','meta[name="DC.creator"]']).join(", ");
    m.doi=gM(['meta[name="citation_doi"]','meta[name="doi"]']);
    m.journal=gM(['meta[name="citation_journal_title"]','meta[name="DC.source"]']);
    var ds=gM(['meta[name="citation_publication_date"]','meta[name="citation_date"]','meta[name="DC.date"]']);
    if(ds){var ym2=ds.match(/(\d{4})/);if(ym2)m.year=parseInt(ym2[1])}
    m.abstract=gM(['meta[name="citation_abstract"]','meta[name="DC.description"]','meta[name="description"]','meta[property="og:description"]']);
    /* Fallback: try to find abstract in page body */
    if(!m.abstract){
      var abEl=document.querySelector('.abstract, #abstract, [class*="abstract" i], [id*="abstract" i]');
      if(abEl) m.abstract=abEl.textContent.replace(/^abstract[:\s]*/i,"").trim();
    }
  }
  m.url=location.href;

  if(!m.title){alert("No paper metadata found on this page.");return}

  /* ---- POST form submit to server (no URL length limit) ---- */
  var f=document.createElement("form");
  f.method="POST";
  f.action=S+"/papers/import-from-bookmarklet";
  f.target="_blank";
  var inp=document.createElement("input");
  inp.type="hidden";inp.name="metadata";inp.value=JSON.stringify(m);
  f.appendChild(inp);
  document.body.appendChild(f);
  f.submit();
  f.remove();
})();
