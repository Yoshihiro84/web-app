// Papers Manager Connector - Popup Logic

(function () {
  'use strict';

  var serverUrlInput = document.getElementById('serverUrl');
  var btnTest = document.getElementById('btnTest');
  var btnSaveSettings = document.getElementById('btnSaveSettings');
  var btnExtract = document.getElementById('btnExtract');
  var btnSave = document.getElementById('btnSave');
  var previewSection = document.getElementById('previewSection');
  var statusMsg = document.getElementById('statusMsg');
  var fetchPdfCheckbox = document.getElementById('fetchPdf');
  var pdfCheckboxRow = document.getElementById('pdfCheckboxRow');

  var currentMetadata = null;

  // Load saved server URL
  chrome.storage.local.get(['serverUrl'], function (data) {
    if (data.serverUrl) {
      serverUrlInput.value = data.serverUrl;
    }
  });

  // Save settings
  btnSaveSettings.addEventListener('click', function () {
    chrome.storage.local.set({ serverUrl: serverUrlInput.value.trim() });
    showStatus('Settings saved', 'success');
  });

  // Test connection
  btnTest.addEventListener('click', function () {
    var url = serverUrlInput.value.trim();
    if (!url) { showStatus('Enter a server URL', 'error'); return; }

    showStatus('Testing connection...', 'info');
    chrome.runtime.sendMessage(
      { action: 'testConnection', serverUrl: url },
      function (response) {
        if (chrome.runtime.lastError) {
          showStatus('Failed: ' + chrome.runtime.lastError.message, 'error');
          return;
        }
        if (response && response.error) {
          showStatus('Failed: ' + response.error, 'error');
        } else if (response && response.status === 'ok') {
          var driveInfo = response.drive_configured ? ' (Drive: enabled)' : ' (Drive: not configured)';
          showStatus('Connected!' + driveInfo, 'success');
          chrome.storage.local.set({ serverUrl: url });
        } else {
          showStatus('Unexpected response', 'error');
        }
      }
    );
  });

  // Extract metadata
  btnExtract.addEventListener('click', function () {
    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      if (!tabs[0]) { showStatus('No active tab', 'error'); return; }

      // Inject content script if not on a matched page
      chrome.scripting.executeScript(
        { target: { tabId: tabs[0].id }, files: ['content.js'] },
        function () {
          chrome.tabs.sendMessage(tabs[0].id, { action: 'extractMetadata' }, function (metadata) {
            if (chrome.runtime.lastError) {
              showStatus('Failed to extract: ' + chrome.runtime.lastError.message, 'error');
              return;
            }
            if (!metadata || !metadata.title) {
              showStatus('No paper metadata found on this page', 'error');
              return;
            }
            currentMetadata = metadata;
            displayPreview(metadata);
          });
        }
      );
    });
  });

  // Save paper
  btnSave.addEventListener('click', function () {
    if (!currentMetadata) return;

    var url = serverUrlInput.value.trim();
    if (!url) { showStatus('Set server URL first', 'error'); return; }

    btnSave.disabled = true;
    showStatus('Saving paper...', 'info');

    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      var tabId = tabs[0] ? tabs[0].id : null;
      sendSavePaper(url, tabId);
    });
  });

  function sendSavePaper(url, tabId) {
    chrome.runtime.sendMessage(
      {
        action: 'savePaper',
        serverUrl: url,
        metadata: currentMetadata,
        fetchPdf: fetchPdfCheckbox.checked,
        tabId: tabId
      },
      function (response) {
        btnSave.disabled = false;
        if (chrome.runtime.lastError) {
          showStatus('Failed: ' + chrome.runtime.lastError.message, 'error');
          return;
        }
        if (response && response.error) {
          if (response.data && response.data.paper_id) {
            showStatus('Already exists (ID: ' + response.data.paper_id + ')', 'error');
          } else {
            showStatus(response.error, 'error');
          }
        } else if (response && response.paper_id) {
          var msg = 'Saved! (ID: ' + response.paper_id + ')';
          if (response.pdf_drive_file_id) msg += ' + PDF uploaded';
          showStatus(msg, 'success');
        } else {
          showStatus('Unexpected response', 'error');
        }
      }
    );
  }

  function displayPreview(meta) {
    document.getElementById('previewTitle').textContent = meta.title || '(no title)';
    document.getElementById('previewAuthors').textContent = meta.authors || '-';
    document.getElementById('previewYear').textContent = meta.year || '-';
    document.getElementById('previewJournal').textContent = meta.journal || '-';
    document.getElementById('previewDoi').textContent = meta.doi || '-';
    document.getElementById('previewArxiv').textContent = meta.arxiv_id || '-';
    document.getElementById('previewSource').textContent = meta.source || '-';

    // Show/hide PDF checkbox
    if (meta.pdf_url) {
      pdfCheckboxRow.style.display = 'flex';
      fetchPdfCheckbox.checked = true;
    } else {
      pdfCheckboxRow.style.display = 'none';
      fetchPdfCheckbox.checked = false;
    }

    previewSection.style.display = 'block';
    statusMsg.style.display = 'none';
  }

  function showStatus(message, type) {
    statusMsg.textContent = message;
    statusMsg.className = 'status ' + type;
  }
})();
