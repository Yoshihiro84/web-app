// Papers Manager Connector - Background Service Worker

chrome.runtime.onMessage.addListener(function (request, sender, sendResponse) {
  if (request.action === 'savePaper') {
    handleSavePaper(request.serverUrl, request.metadata, request.fetchPdf, request.tabId)
      .then(function (result) { sendResponse(result); })
      .catch(function (err) { sendResponse({ error: err.message }); });
    return true; // async response
  }

  if (request.action === 'testConnection') {
    testConnection(request.serverUrl)
      .then(function (result) { sendResponse(result); })
      .catch(function (err) { sendResponse({ error: err.message }); });
    return true;
  }
});

async function testConnection(serverUrl) {
  var baseUrl = normalizeServerUrl(serverUrl);
  var url = baseUrl + '/api/extension/status';
  var res = await fetch(url);
  if (!res.ok) throw new Error('Server returned ' + res.status);
  return await res.json();
}

async function handleSavePaper(serverUrl, metadata, fetchPdf, tabId) {
  var baseUrl = normalizeServerUrl(serverUrl);
  var url = baseUrl + '/api/extension/import';

  var formData = new FormData();
  formData.append('metadata', JSON.stringify(metadata));

  // Try to fetch PDF if available
  if (fetchPdf && metadata.pdf_url) {
    try {
      var gotPdf = false;
      var filename = (metadata.arxiv_id || 'paper').replace(/[\/\\]/g, '_') + '.pdf';

      // First: try direct fetch from background (works for public URLs like nature.com)
      var pdfRes = await fetch(metadata.pdf_url);
      if (pdfRes.ok) {
        var contentType = pdfRes.headers.get('content-type') || '';
        if (contentType.includes('application/pdf') || contentType.includes('application/octet-stream')) {
          var pdfBlob = await pdfRes.blob();
          formData.append('pdf_file', pdfBlob, filename);
          gotPdf = true;
        } else {
          console.warn('Background fetch: not a PDF (content-type:', contentType, ') — trying content script fallback');
        }
      }

      // Fallback: ask content script to fetch with session cookies (works for session-locked URLs like optica.org)
      if (!gotPdf && tabId) {
        try {
          await chrome.scripting.executeScript({ target: { tabId: tabId }, files: ['content.js'] });
        } catch (e) {
          // Already injected or not injectable — ignore
        }
        var result = await new Promise(function (resolve) {
          chrome.tabs.sendMessage(tabId, { action: 'fetchPdfAsBase64', url: metadata.pdf_url }, resolve);
        });
        if (result && result.base64) {
          var binary = atob(result.base64);
          var bytes = new Uint8Array(binary.length);
          for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
          var pdfBlobFromContent = new Blob([bytes], { type: 'application/pdf' });
          formData.append('pdf_file', pdfBlobFromContent, filename);
        } else {
          console.warn('Content script fallback failed:', result && result.error);
        }
      }
    } catch (e) {
      // PDF fetch failed entirely, continue without PDF
      console.warn('Failed to fetch PDF:', e);
    }
  }

  var res = await fetch(url, { method: 'POST', body: formData });
  var data = await res.json();

  if (!res.ok) {
    var error = new Error(data.error || 'Import failed');
    error.status = res.status;
    error.data = data;
    throw error;
  }

  return data;
}

function normalizeServerUrl(input) {
  var raw = (input || '').trim();
  if (!raw) throw new Error('Server URL is empty');

  var withScheme = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//.test(raw) ? raw : ('http://' + raw);
  var parsed;
  try {
    parsed = new URL(withScheme);
  } catch (e) {
    throw new Error('Invalid server URL: ' + raw);
  }

  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    throw new Error('Server URL must use http or https');
  }

  return parsed.origin;
}
