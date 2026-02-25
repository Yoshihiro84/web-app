// Papers Manager Connector - Content Script
// Extracts metadata from academic paper pages

(function () {
  'use strict';

  function extractArxiv() {
    var title = '';
    var authors = '';
    var abstract = '';
    var arxivId = '';
    var pdfUrl = '';

    // Extract arXiv ID from URL
    var match = location.pathname.match(/\/abs\/(.+)/);
    if (match) {
      arxivId = match[1].replace(/v\d+$/, '');
      pdfUrl = 'https://arxiv.org/pdf/' + match[1];
    }

    // Title
    var titleEl = document.querySelector('.title.mathjax');
    if (titleEl) {
      title = titleEl.textContent.replace(/^Title:\s*/i, '').trim();
    }

    // Authors
    var authorsEl = document.querySelector('.authors');
    if (authorsEl) {
      authors = authorsEl.textContent.replace(/^Authors:\s*/i, '').trim();
    }

    // Abstract
    var abstractEl = document.querySelector('.abstract.mathjax');
    if (abstractEl) {
      abstract = abstractEl.textContent.replace(/^Abstract:\s*/i, '').trim();
    }

    return {
      title: title,
      authors: authors,
      abstract: abstract,
      arxiv_id: arxivId,
      url: location.href,
      pdf_url: pdfUrl,
      source: 'arxiv'
    };
  }

  function extractGoogleScholar() {
    // Try to extract from the first focused/highlighted result
    var results = [];
    var entries = document.querySelectorAll('.gs_ri');

    entries.forEach(function (entry) {
      var titleEl = entry.querySelector('.gs_rt a');
      var authorsEl = entry.querySelector('.gs_a');
      var snippetEl = entry.querySelector('.gs_rs');

      var title = titleEl ? titleEl.textContent.trim() : '';
      var url = titleEl ? titleEl.href : '';
      var authorsText = authorsEl ? authorsEl.textContent : '';

      // Parse authors line: "Author1, Author2 - Journal, Year - Publisher"
      var parts = authorsText.split(' - ');
      var authors = parts[0] ? parts[0].trim() : '';
      var journal = '';
      var year = null;
      if (parts[1]) {
        var journalYear = parts[1].trim();
        var yearMatch = journalYear.match(/(\d{4})/);
        if (yearMatch) year = parseInt(yearMatch[1]);
        journal = journalYear.replace(/,?\s*\d{4}/, '').trim();
      }

      results.push({
        title: title,
        authors: authors,
        journal: journal,
        year: year,
        url: url,
        abstract: snippetEl ? snippetEl.textContent.trim() : '',
        source: 'scholar'
      });
    });

    // Return the first result or an empty object
    return results.length > 0 ? results[0] : { source: 'scholar', title: '' };
  }

  function extractMetaTags() {
    var meta = {};

    function getContent(selectors) {
      for (var i = 0; i < selectors.length; i++) {
        var el = document.querySelector(selectors[i]);
        if (el && el.content) return el.content.trim();
      }
      return '';
    }

    function getAllContent(selectors) {
      var values = [];
      selectors.forEach(function (sel) {
        document.querySelectorAll(sel).forEach(function (el) {
          if (el.content) values.push(el.content.trim());
        });
      });
      return values;
    }

    meta.title = getContent([
      'meta[name="citation_title"]',
      'meta[name="DC.title"]',
      'meta[property="og:title"]'
    ]) || document.title;

    var authorsList = getAllContent([
      'meta[name="citation_author"]',
      'meta[name="DC.creator"]'
    ]);
    meta.authors = authorsList.join(', ');

    meta.doi = getContent([
      'meta[name="citation_doi"]',
      'meta[name="DC.identifier"][scheme="doi"]',
      'meta[name="doi"]'
    ]);

    meta.journal = getContent([
      'meta[name="citation_journal_title"]',
      'meta[name="DC.source"]'
    ]);

    var dateStr = getContent([
      'meta[name="citation_publication_date"]',
      'meta[name="citation_date"]',
      'meta[name="DC.date"]'
    ]);
    if (dateStr) {
      var yearMatch = dateStr.match(/(\d{4})/);
      if (yearMatch) meta.year = parseInt(yearMatch[1]);
    }

    meta.abstract = getContent([
      'meta[name="citation_abstract"]',
      'meta[name="DC.description"]',
      'meta[name="description"]',
      'meta[property="og:description"]'
    ]);
    // Fallback: try to find abstract in page body
    if (!meta.abstract) {
      var abEl = document.querySelector('.abstract, #abstract, [class*="abstract" i], [id*="abstract" i]');
      if (abEl) meta.abstract = abEl.textContent.replace(/^abstract[:\s]*/i, '').trim();
    }

    meta.pdf_url = getContent([
      'meta[name="citation_pdf_url"]'
    ]);

    meta.url = location.href;
    meta.source = 'meta';

    return meta;
  }

  function extractMetadata() {
    var hostname = location.hostname;

    if (hostname.includes('arxiv.org')) {
      return extractArxiv();
    }
    if (hostname.includes('scholar.google')) {
      return extractGoogleScholar();
    }
    // Fallback: use HTML meta tags (works for most publisher sites)
    return extractMetaTags();
  }

  // Listen for messages from popup / background
  chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
    if (request.action === 'extractMetadata') {
      var metadata = extractMetadata();
      sendResponse(metadata);
      return true;
    }

    if (request.action === 'fetchPdfAsBase64') {
      fetch(request.url, { credentials: 'include' })
        .then(function (res) {
          var ct = res.headers.get('content-type') || '';
          if (!res.ok || (!ct.includes('pdf') && !ct.includes('octet-stream'))) {
            sendResponse({ error: 'Not a PDF (content-type: ' + ct + ', status: ' + res.status + ')' });
            return null;
          }
          return res.arrayBuffer();
        })
        .then(function (buf) {
          if (!buf) return;
          var bytes = new Uint8Array(buf);
          var binary = '';
          for (var i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
          }
          sendResponse({ base64: btoa(binary) });
        })
        .catch(function (e) {
          sendResponse({ error: e.message });
        });
      return true; // async
    }

    return true;
  });
})();
