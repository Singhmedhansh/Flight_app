"use strict";

(function () {
  var avatarToggle = document.getElementById('user-menu-btn');
  var dropdown = document.getElementById('user-dropdown');
  var changePhotoBtn = document.getElementById('change-photo');
  var headerInput = document.getElementById('header_profile_photo');
  var modal = document.getElementById('profile-modal');
  var closeBtn = document.getElementById('modal-close');
  var cancelBtn = document.getElementById('modal-cancel');
  var input = document.getElementById('profile_photo');
  var preview = document.getElementById('preview-container');
  var previewImg = document.getElementById('preview-img');
  var themeToggle = document.getElementById('theme-toggle');
  var dropdownTheme = document.getElementById('dropdown-theme-toggle');

  function closeDropdown() {
    if (dropdown) {
      dropdown.classList.remove('open');
      dropdown.setAttribute('aria-hidden', 'true');
    }

    if (avatarToggle) {
      avatarToggle.setAttribute('aria-expanded', 'false');
      avatarToggle.classList.remove('open');
    }
  }

  function openDropdown() {
    if (dropdown) {
      dropdown.classList.add('open');
      dropdown.setAttribute('aria-hidden', 'false');
    }

    if (avatarToggle) {
      avatarToggle.setAttribute('aria-expanded', 'true');
      avatarToggle.classList.add('open');
    }
  }

  if (avatarToggle) {
    avatarToggle.addEventListener('click', function (e) {
      e.stopPropagation();
      if (dropdown && dropdown.classList.contains('open')) closeDropdown();else openDropdown();
    });
  } // Close dropdown when clicking outside


  document.addEventListener('click', function (e) {
    if (!e.target.closest('.avatar-wrap')) closeDropdown();
  });

  if (changePhotoBtn) {
    changePhotoBtn.addEventListener('click', function (e) {
      e.stopPropagation(); // If a header hidden file input exists, use it for quick selection/upload

      if (headerInput) {
        headerInput.click();
        closeDropdown();
        return;
      }

      if (modal) {
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
      }

      closeDropdown();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener('click', function () {
      if (modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
      }
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', function () {
      if (modal) {
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
      }
    });
  }

  if (input) {
    input.addEventListener('change', function (e) {
      var f = e.target.files[0];
      if (!f) return;
      var url = URL.createObjectURL(f);
      previewImg.src = url;
      preview.style.display = 'block';
    });
  } // Header quick-upload handler: upload via fetch and refresh avatar on success


  if (headerInput) {
    headerInput.addEventListener('change', function _callee(e) {
      var f, fd, res, img, src, newSrc;
      return regeneratorRuntime.async(function _callee$(_context) {
        while (1) {
          switch (_context.prev = _context.next) {
            case 0:
              f = e.target.files[0];

              if (f) {
                _context.next = 3;
                break;
              }

              return _context.abrupt("return");

            case 3:
              fd = new FormData();
              fd.append('profile_photo', f);
              _context.prev = 5;
              _context.next = 8;
              return regeneratorRuntime.awrap(fetch('/upload_profile_photo', {
                method: 'POST',
                body: fd
              }));

            case 8:
              res = _context.sent;

              // Update avatar if upload succeeded. Flask redirects on success; treat any ok response as success.
              if (res.ok) {
                // Update profile image src with cache-busting query so browser fetches new file
                img = document.getElementById('profile-img');

                if (img) {
                  src = img.getAttribute('src') || ''; // If using default svg, try to construct uploads path; otherwise just bust cache

                  newSrc = src.includes('/static/uploads/') ? src.split('?')[0] + '?t=' + Date.now() : src + '?t=' + Date.now();
                  img.setAttribute('src', newSrc); // animate

                  img.classList.remove('updated'); // Force reflow to restart animation

                  void img.offsetWidth;
                  img.classList.add('updated');
                } else {
                  window.location.reload();
                }
              } else {
                window.location.reload();
              }

              _context.next = 16;
              break;

            case 12:
              _context.prev = 12;
              _context.t0 = _context["catch"](5);
              console.error('Upload failed', _context.t0);
              alert('Upload failed');

            case 16:
            case "end":
              return _context.stop();
          }
        }
      }, null, null, [[5, 12]]);
    });
  } // wire theme toggles to same action


  function triggerThemeToggle() {
    var ev = new Event('click'); // Reuse theme.js toggle button if present

    var btn = document.getElementById('theme-toggle');

    if (btn) {
      btn.dispatchEvent(ev);
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener('click', triggerThemeToggle);
  }

  if (dropdownTheme) {
    dropdownTheme.addEventListener('click', function () {
      triggerThemeToggle();
      closeDropdown();
    });
  }
})();