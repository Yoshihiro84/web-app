document.addEventListener('DOMContentLoaded', function () {
  var rows = document.querySelectorAll('.paper-row');
  var previewContent = document.getElementById('previewContent');
  var selectedPaperId = null;
  var STATUS_CYCLE = ['unread', 'reading', 'done'];

  rows.forEach(function (row) {
    row.addEventListener('click', function (e) {
      // If clicking the status badge in the table, handle status change instead
      if (e.target.closest('.status-badge-btn')) return;

      var paperId = row.dataset.paperId;

      // Toggle selection: clicking same row again deselects
      if (selectedPaperId === paperId) {
        row.classList.remove('selected');
        selectedPaperId = null;
        showPlaceholder();
        return;
      }

      // Clear previous selection
      rows.forEach(function (r) { r.classList.remove('selected'); });

      // Select this row
      row.classList.add('selected');
      selectedPaperId = paperId;

      // Fetch and display preview
      loadPreview(paperId);
    });
  });

  // Status badge click in table rows
  document.querySelectorAll('.status-badge-btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var row = btn.closest('.paper-row');
      var paperId = row.dataset.paperId;
      var currentStatus = btn.dataset.status;
      var nextStatus = nextStatusOf(currentStatus);
      updateStatus(paperId, nextStatus, function (newStatus) {
        // Update table badge
        btn.dataset.status = newStatus;
        btn.className = 'status-badge-btn status-badge status-' + newStatus;
        btn.textContent = newStatus;
        // Update preview if this paper is selected
        if (selectedPaperId === paperId) {
          var previewBadge = document.getElementById('previewStatusBadge');
          if (previewBadge) {
            previewBadge.dataset.status = newStatus;
            previewBadge.className = 'status-badge-btn status-badge status-' + newStatus;
            previewBadge.textContent = newStatus;
          }
        }
      });
    });
  });

  function nextStatusOf(current) {
    var idx = STATUS_CYCLE.indexOf(current);
    return STATUS_CYCLE[(idx + 1) % STATUS_CYCLE.length];
  }

  function updateStatus(paperId, newStatus, onSuccess) {
    fetch('/api/papers/' + paperId + '/status', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    })
      .then(function (res) {
        if (!res.ok) throw new Error('Failed');
        return res.json();
      })
      .then(function (data) {
        onSuccess(data.status);
      })
      .catch(function () {
        // silently fail
      });
  }

  function loadPreview(paperId) {
    previewContent.innerHTML = '<div class="preview-placeholder"><p>Loading...</p></div>';

    fetch('/api/papers/' + paperId)
      .then(function (res) {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then(function (paper) {
        renderPreview(paper);
      })
      .catch(function () {
        previewContent.innerHTML = '<div class="preview-placeholder"><p style="color:var(--danger-text)">Failed to load paper.</p></div>';
      });
  }

  function renderPreview(paper) {
    var html = '';

    // Title
    html += '<div class="preview-title">' + escapeHtml(paper.title) + '</div>';

    // Authors
    if (paper.authors) {
      html += '<div class="preview-authors">' + escapeHtml(paper.authors) + '</div>';
    }

    // Status badge (clickable)
    html += '<div style="margin-bottom:12px">';
    html += '<span id="previewStatusBadge" class="status-badge-btn status-badge status-' + escapeHtml(paper.status) + '" data-status="' + escapeHtml(paper.status) + '" data-paper-id="' + paper.id + '" title="Click to change status">' + escapeHtml(paper.status) + '</span>';
    html += '</div>';

    // Metadata
    var metaItems = [];
    if (paper.year) metaItems.push(String(paper.year));
    if (paper.journal) metaItems.push(paper.journal);
    if (paper.doi) metaItems.push('DOI: ' + paper.doi);
    if (paper.arxiv_id) metaItems.push('arXiv: ' + paper.arxiv_id);
    if (paper.bibtex_type) metaItems.push(paper.bibtex_type);

    if (metaItems.length > 0) {
      html += '<div class="preview-meta">';
      metaItems.forEach(function (item) {
        html += '<span class="preview-meta-item">' + escapeHtml(item) + '</span>';
      });
      html += '</div>';
    }

    // Tags
    if (paper.tags && paper.tags.length > 0) {
      html += '<div class="preview-tags">';
      paper.tags.forEach(function (tag) {
        html += '<span class="preview-tag">' + escapeHtml(tag.name) + '</span>';
      });
      html += '</div>';
    }

    // PDF embed
    if (paper.pdf_drive_file_id) {
      html += '<div class="preview-pdf-embed">';
      html += '<iframe src="/api/papers/' + paper.id + '/pdf" class="preview-pdf-iframe" title="PDF Preview"></iframe>';
      html += '</div>';
    }

    // URL
    if (paper.url) {
      html += '<div style="margin-bottom:12px">';
      html += '<a href="' + escapeHtml(paper.url) + '" target="_blank" class="link-gold text-xs break-all">' + escapeHtml(paper.url) + '</a>';
      html += '</div>';
    }

    // Abstract (show only when no PDF to avoid clutter)
    if (paper.abstract && !paper.pdf_drive_file_id) {
      html += '<div class="preview-section-title">Abstract</div>';
      html += '<div class="preview-abstract">' + escapeHtml(paper.abstract) + '</div>';
    }

    // Notes count
    if (paper.notes && paper.notes.length > 0) {
      html += '<div class="preview-section-title">Notes</div>';
      html += '<p style="font-size:0.75rem;color:var(--text-muted)">' + paper.notes.length + ' note(s)</p>';
    }

    // Actions
    html += '<div class="preview-actions">';
    html += '<a href="/papers/' + paper.id + '" class="preview-btn-primary">Open Detail</a>';
    html += '<a href="/papers/' + paper.id + '/edit" class="preview-btn-secondary">Edit</a>';
    html += '<button onclick="deletePaper(' + paper.id + ')" class="preview-btn-danger">Delete</button>';
    html += '</div>';

    previewContent.innerHTML = html;

    // Bind click on preview status badge
    var previewBadge = document.getElementById('previewStatusBadge');
    if (previewBadge) {
      previewBadge.addEventListener('click', function () {
        var paperId = previewBadge.dataset.paperId;
        var currentStatus = previewBadge.dataset.status;
        var nextStatus = nextStatusOf(currentStatus);
        updateStatus(paperId, nextStatus, function (newStatus) {
          // Update preview badge
          previewBadge.dataset.status = newStatus;
          previewBadge.className = 'status-badge-btn status-badge status-' + newStatus;
          previewBadge.textContent = newStatus;
          // Update table row badge
          var tableRow = document.querySelector('.paper-row[data-paper-id="' + paperId + '"]');
          if (tableRow) {
            var tableBadge = tableRow.querySelector('.status-badge-btn');
            if (tableBadge) {
              tableBadge.dataset.status = newStatus;
              tableBadge.className = 'status-badge-btn status-badge status-' + newStatus;
              tableBadge.textContent = newStatus;
            }
          }
        });
      });
    }
  }

  function showPlaceholder() {
    previewContent.innerHTML =
      '<div class="preview-placeholder">' +
      '<svg class="w-12 h-12 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>' +
      '<p>Click a paper to preview</p>' +
      '</div>';
  }

  function escapeHtml(text) {
    if (!text) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(String(text)));
    return div.innerHTML;
  }

  // Sidebar collection toggle
  document.querySelectorAll('.sidebar-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var targetId = btn.dataset.target;
      var items = document.getElementById(targetId);
      var arrow = btn.querySelector('.toggle-arrow');
      if (items) {
        items.classList.toggle('hidden');
        arrow.classList.toggle('open');
      }
    });
  });

  // Sidebar subitem click -> select paper in table and show preview
  document.querySelectorAll('.sidebar-subitem').forEach(function (item) {
    item.addEventListener('click', function (e) {
      e.preventDefault();
      var paperId = item.dataset.paperId;

      // Highlight subitem
      document.querySelectorAll('.sidebar-subitem').forEach(function (s) { s.classList.remove('active'); });
      item.classList.add('active');

      // Select table row if visible
      rows.forEach(function (r) { r.classList.remove('selected'); });
      var tableRow = document.querySelector('.paper-row[data-paper-id="' + paperId + '"]');
      if (tableRow) {
        tableRow.classList.add('selected');
        tableRow.scrollIntoView({ block: 'nearest' });
      }

      selectedPaperId = paperId;
      loadPreview(paperId);
    });
  });

  // Preview panel resize
  (function () {
    var handle = document.getElementById('resizeHandle');
    var panel = document.getElementById('previewPanel');
    if (!handle || !panel) return;

    var isResizing = false;
    var savedWidth = localStorage.getItem('previewPanelWidth');
    if (savedWidth) {
      panel.style.width = savedWidth + 'px';
    }

    handle.addEventListener('mousedown', function (e) {
      isResizing = true;
      handle.classList.add('active');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
    });

    document.addEventListener('mousemove', function (e) {
      if (!isResizing) return;
      var containerRight = document.getElementById('threePaneApp').getBoundingClientRect().right;
      var newWidth = containerRight - e.clientX;
      if (newWidth < 200) newWidth = 200;
      if (newWidth > window.innerWidth * 0.6) newWidth = window.innerWidth * 0.6;
      panel.style.width = newWidth + 'px';
    });

    document.addEventListener('mouseup', function () {
      if (!isResizing) return;
      isResizing = false;
      handle.classList.remove('active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      localStorage.setItem('previewPanelWidth', parseInt(panel.style.width));
    });
  })();

  // Expose delete function globally
  window.deletePaper = function (paperId) {
    if (!confirm('Are you sure you want to delete this paper?')) return;

    var form = document.createElement('form');
    form.method = 'POST';
    form.action = '/papers/' + paperId + '/delete';
    document.body.appendChild(form);
    form.submit();
  };
});
